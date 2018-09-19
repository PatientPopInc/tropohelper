from troposphere import Ref
from troposphere.firehose import (
    BufferingHints,
    CloudWatchLoggingOptions,
    CopyCommand,
    DeliveryStream,
    EncryptionConfiguration,
    KMSEncryptionConfig,
    RedshiftDestinationConfiguration,
    S3Configuration,
    S3DestinationConfiguration,
    KinesisStreamSourceConfiguration
)
from troposphere.cloudwatch import Alarm
from troposphere.logs import MetricFilter, MetricTransformation, LogGroup
from troposphere.sns import Topic, Subscription
from troposphere.kinesis import Stream
from troposphere.ec2 import SecurityGroupRule, SecurityGroup
import troposphere.elasticache as elasticache


def create_s3_firehose(stack, name, bucket_arn, kms_key_arn, role_arn,
                       buffering_seconds=300, buffering_size=5,
                       compression_format='GZIP', log_group_name='firehose-streams'):
    """Add Kinesis S3 Firehose Resource."""
    return stack.stack.add_resource(DeliveryStream(
        '{0}Firehose'.format(name.replace('-', '')),
        DeliveryStreamName=name,
        S3DestinationConfiguration=S3DestinationConfiguration(
            BucketARN=bucket_arn,
            Prefix=name,
            BufferingHints=BufferingHints(IntervalInSeconds=buffering_seconds, SizeInMBs=buffering_size),
            CompressionFormat=compression_format,
            EncryptionConfiguration=EncryptionConfiguration(
                KMSEncryptionConfig=KMSEncryptionConfig(
                    AWSKMSKeyARN=kms_key_arn)),
            CloudWatchLoggingOptions=CloudWatchLoggingOptions(
                Enabled=True,
                LogGroupName=log_group_name,
                LogStreamName=name),
            RoleARN=role_arn)
    ))


def create_kinesis_stream(stack, name, shard_count):
    """Add Kinesis Stream with the specified shard count and default retention period."""
    return stack.stack.add_resource(Stream(
        '{0}Stream'.format(name.replace('-', '')),
        ShardCount=shard_count,
        Name='{0}Stream'.format(name)
    ))


def create_json_redshift_firehose_from_stream(stack, name, firehose_arn,
                                              source_stream_arn, source_stream_role_arn,
                                              redshift_cluster_jdbc_url_param,
                                              redshift_username, redshift_password,
                                              redshift_db_table_name,
                                              log_group_name,
                                              s3_bucket_arn, s3_kms_key_arn, s3_role_arn,
                                              s3_buffering_seconds=300, s3_buffering_size=5,
                                              s3_compression_format='GZIP'):
    """Add Kinesus Redshift Firehose Resource with another Kinesis Stream as source and json as payload."""

    return stack.stack.add_resource(DeliveryStream(
        '{0}Firehose'.format(name.replace('-', '')),
        DeliveryStreamName=name,
        DeliveryStreamType='KinesisStreamAsSource',
        KinesisStreamSourceConfiguration=KinesisStreamSourceConfiguration(
            KinesisStreamARN=source_stream_arn,
            RoleARN=source_stream_role_arn
        ),
        RedshiftDestinationConfiguration=RedshiftDestinationConfiguration(
            CloudWatchLoggingOptions=CloudWatchLoggingOptions(
                Enabled=True,
                LogGroupName=log_group_name,
                LogStreamName=name),
            ClusterJDBCURL=redshift_cluster_jdbc_url_param,
            CopyCommand=CopyCommand(
                CopyOptions="JSON 'auto' " + s3_compression_format,
                DataTableName=redshift_db_table_name,
            ),
            Password=redshift_password,
            RoleARN=firehose_arn,
            S3Configuration=S3Configuration(
                BucketARN=s3_bucket_arn,
                Prefix=name,
                BufferingHints=BufferingHints(IntervalInSeconds=s3_buffering_seconds, SizeInMBs=s3_buffering_size),
                CompressionFormat=s3_compression_format,
                EncryptionConfiguration=EncryptionConfiguration(
                    KMSEncryptionConfig=KMSEncryptionConfig(
                        AWSKMSKeyARN=s3_kms_key_arn)),
                CloudWatchLoggingOptions=CloudWatchLoggingOptions(
                    Enabled=True,
                    LogGroupName=log_group_name,
                    LogStreamName=name),
                RoleARN=s3_role_arn),
            Username=redshift_username)
    ))


def create_cloud_watch_logs_metric_filter(stack, name, log_group_name, filter_pattern,
                                          metric_namespace='LogMetrics', metric_value='1', metric_default_value=0.0):
    """Add a Cloud Watch logs metric filter pointing to an existing log group."""

    return stack.stack.add_resource(MetricFilter(
        '{0}MetricFilter'.format(name.replace('-', '')),
        FilterPattern=filter_pattern,
        LogGroupName=log_group_name,
        MetricTransformations=[
            MetricTransformation(
                DefaultValue=metric_default_value,
                MetricName='{0}Metric'.format(name.replace('-', '')),
                MetricNamespace=metric_namespace,
                MetricValue=metric_value
            )
        ]
    ))


def create_log_group(stack, name, retention_in_days=7):
    """Add a log group."""
    return stack.stack.add_resource(LogGroup(
        '{0}LogGroup'.format(name.replace('-', '')),
        LogGroupName='{0}LogGroup'.format(name.replace('-', '')),
        RetentionInDays=retention_in_days
    ))


def create_sns_topic(stack, name, endpoint, protocol='https'):
    """Add a SNS topic."""
    return stack.stack.add_resource(Topic(
        '{0}Topic'.format(name.replace('-', '')),
        DisplayName=name,
        Subscription=[
            Subscription(
                Endpoint=endpoint,
                Protocol=protocol
            )
        ],
        TopicName='{0}Topic'.format(name)
    ))


def create_sns_notification_alarm(stack, name, description,
                                  metric_name, metric_namespace,
                                  sns_topic_arn,
                                  comparison_operator='GreaterThanThreshold',
                                  threshold='0',
                                  evaluation_periods='1',
                                  period_secs='60',
                                  statistic='Minimum'):
    """Add SNS notification alarm for a cloud watch log metric which triggers alarm based on the specified criteria."""
    return stack.stack.add_resource(Alarm(
        '{0}Alarm'.format(name.replace('-', '')),
        AlarmName='{0}Alarm'.format(name),
        AlarmDescription=description,
        AlarmActions=[
            sns_topic_arn
        ],
        ComparisonOperator=comparison_operator,
        EvaluationPeriods=evaluation_periods,
        MetricName='{0}Metric'.format(metric_name.replace('-', '')),
        Namespace=metric_namespace,
        Period=period_secs,
        Statistic=statistic,
        Threshold=threshold
    ))


def create_cache_cluster(stack, name, cache_type, vpc, cidrs, subnet_ids, instance_type, num_cache_clusters):
    """Add Elasticache Cache cluster Resource."""
    ports = {
        'redis': 6379,
        'memcached': 11211
    }
    ingress = []
    for idx, cidr in enumerate(cidrs):
        ingress.append(SecurityGroupRule(
            "{0}{1}{2}".format(name.replace('-', ''), cache_type, idx),
            CidrIp=cidr,
            FromPort=ports[cache_type],
            ToPort=ports[cache_type],
            IpProtocol="tcp",
        ))
    secgroup = stack.stack.add_resource(SecurityGroup(
        '{0}{1}SecurityGroup'.format(name.replace('-', ''), cache_type),
        GroupDescription="{0} {1} Security Group".format(name, cache_type),
        SecurityGroupIngress=ingress,
        VpcId=vpc,
    ))

    subnet_group = stack.stack.add_resource(
        elasticache.SubnetGroup(
            '{0}{1}cache'.format(name.replace('-', ''), cache_type),
            Description='{0}{1} cache'.format(name, cache_type),
            SubnetIds=subnet_ids,
        ))

    if num_cache_clusters > 1:
        stack.stack.add_resource(
            elasticache.ReplicationGroup(
                '{0}CacheCluster'.format(name.replace('-', '')),
                ReplicationGroupId='{0}'.format(name),
                ReplicationGroupDescription='{0}cluster'.format(name),
                Engine='{0}'.format(cache_type),
                EngineVersion='3.2.6',
                CacheNodeType=instance_type,
                NumCacheClusters=num_cache_clusters,
                CacheSubnetGroupName=Ref(subnet_group),
                SecurityGroupIds=[Ref(secgroup)],
                AtRestEncryptionEnabled=True
            ))
    else:
        stack.stack.add_resource(
            elasticache.CacheCluster(
                '{0}CacheCluster'.format(name.replace('-', '')),
                ClusterName='{0}'.format(name),
                Engine='{0}'.format(cache_type),
                EngineVersion='3.2.10',
                CacheNodeType=instance_type,
                NumCacheNodes=num_cache_clusters,
                VpcSecurityGroupIds=[Ref(secgroup)],
                CacheSubnetGroupName=Ref(subnet_group)
            ))
