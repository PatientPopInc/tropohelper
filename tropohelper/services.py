from troposphere import Ref
from troposphere.firehose import DeliveryStream, EncryptionConfiguration, \
                                 KMSEncryptionConfig, S3DestinationConfiguration, \
                                 BufferingHints, CloudWatchLoggingOptions
from troposphere.ec2 import SecurityGroupRule, SecurityGroup
import troposphere.elasticache as elasticache


def create_firehose(stack, name, bucket_arn, buffering_seconds=300, buffering_size=5):
    """Add Kinesus Firehose Resource."""
    return stack.stack.add_resource(DeliveryStream(
        '{0}Firehose'.format(name.replace('-', '')),
        DeliveryStreamName=name,
        S3DestinationConfiguration=S3DestinationConfiguration(
            BucketARN=bucket_arn,
            Prefix=name,
            BufferingHints=BufferingHints(IntervalInSeconds=buffering_seconds, SizeInMBs=buffering_size),
            CompressionFormat='GZIP',
            EncryptionConfiguration=EncryptionConfiguration(
                KMSEncryptionConfig=KMSEncryptionConfig(
                    AWSKMSKeyARN='arn:aws:kms:us-east-1:347225174248:key/232e45d1-6b15-4681-8de7-8629b0ed6b22')),
            CloudWatchLoggingOptions=CloudWatchLoggingOptions(
                Enabled=True,
                LogGroupName='firehose-streams',
                LogStreamName=name),
            RoleARN="arn:aws:iam::347225174248:role/firehose_delivery_role")
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
