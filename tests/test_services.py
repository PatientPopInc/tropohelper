from troposphere import Template, GetAtt, Ref
from tropohelper.services import (
    create_kinesis_stream,
    create_json_redshift_firehose_from_stream,
    create_cloud_watch_logs_metric_filter,
    create_sns_topic,
    create_sns_notification_alarm,
    create_log_group,
    create_log_stream
)

class test_stack(object):
    """Test stack."""
    def __init__(self):
        """Intitialize our test stack."""
        self.stack = Template()
        self.env = "test"

    def setup(self):
        """Create our test environment."""
        self.stack = test_stack()

    def test_create_json_redshift_firehose_from_stream(self):
        """Test creating json redshift firehose from Kinesis stream."""

        log_group = create_log_group(self.stack, 'log-group-1')
        redshift_log_stream = create_log_stream(self.stack, Ref(log_group), 'Redshift')
        s3_log_stream = create_log_stream(self.stack, Ref(log_group), 'S3')

        assert self.stack.stack.to_dict()['Resources']['loggroup1LogGroup']['Type'] == 'AWS::Logs::LogGroup'
        redshift_log_group_properties = self.stack.stack.to_dict()['Resources']['loggroup1LogGroup']['Properties']
        assert redshift_log_group_properties['RetentionInDays'] == 7

        create_kinesis_stream(self.stack, 'stream1', 5)
        assert self.stack.stack.to_dict()['Resources']['stream1Stream']['Type'] == 'AWS::Kinesis::Stream'
        assert self.stack.stack.to_dict()['Resources']['stream1Stream']['Properties']['ShardCount'] == 5

        create_json_redshift_firehose_from_stream(self.stack, 'firehose1', 'firehose_arn',
                                                  'arn:aws:kinesis:::stream1Stream', 'arn:aws:role:::role1',
                                                  'jdbc:redshift://localhost:123/redshift_db1',
                                                  'redshift_username', 'redshift_password',
                                                  'redshift_db_table1',
                                                  Ref(log_group),
                                                  Ref(redshift_log_stream),
                                                  Ref(s3_log_stream),
                                                  'arn:aws:s3:::bucket1',
                                                  'arn:aws:kms:us-east-1:1234',
                                                  'arn:aws:iam::1234:role/firehose_delivery_role')
        assert self.stack.stack.to_dict()['Resources']['firehose1Firehose']['Type'] == 'AWS::KinesisFirehose::DeliveryStream'
        properties = self.stack.stack.to_dict()['Resources']['firehose1Firehose']['Properties']

        kinesis_stream_source_configuration = properties['KinesisStreamSourceConfiguration']
        assert kinesis_stream_source_configuration['RoleARN'] == 'arn:aws:role:::role1'
        assert kinesis_stream_source_configuration['KinesisStreamARN'] == 'arn:aws:kinesis:::stream1Stream'

        assert properties['DeliveryStreamType'] == 'KinesisStreamAsSource'

        redshift_destination_configuration = properties['RedshiftDestinationConfiguration']
        assert redshift_destination_configuration['Username'] == 'redshift_username'
        assert redshift_destination_configuration['ClusterJDBCURL'] == 'jdbc:redshift://localhost:123/redshift_db1'
        assert redshift_destination_configuration['Password'] == 'redshift_password'

        copy_command = redshift_destination_configuration['CopyCommand']
        assert copy_command['DataTableName'] == 'redshift_db_table1'
        assert copy_command['CopyOptions'] == "JSON 'auto' GZIP"

        s3_configuration = redshift_destination_configuration['S3Configuration']
        assert s3_configuration['RoleARN'] == 'arn:aws:iam::1234:role/firehose_delivery_role'
        assert s3_configuration['CompressionFormat'] == 'GZIP'
        assert s3_configuration['BufferingHints']['IntervalInSeconds'] == 300
        assert s3_configuration['BufferingHints']['SizeInMBs'] == 5
        assert s3_configuration['EncryptionConfiguration']['KMSEncryptionConfig']['AWSKMSKeyARN'] == 'arn:aws:kms:us-east-1:1234'
        assert s3_configuration['Prefix'] == 'firehose1'
        assert s3_configuration['BucketARN'] == 'arn:aws:s3:::bucket1'

        s3_cloud_watch_logging_options = s3_configuration['CloudWatchLoggingOptions']
        assert s3_cloud_watch_logging_options['Enabled'] == 'true'

        redshift_cloud_watch_logging_options = redshift_destination_configuration['CloudWatchLoggingOptions']
        assert redshift_cloud_watch_logging_options['Enabled'] == 'true'

    def test_create_email_notification_alarm_for_cloud_watch_logs_metric(self):
        """Test creating email notification alarm for cloud watch logs metric."""

        log_group = create_log_group(self.stack, 'log-group-1')

        assert self.stack.stack.to_dict()['Resources']['loggroup1LogGroup']['Type'] == 'AWS::Logs::LogGroup'
        redshift_log_group_properties = self.stack.stack.to_dict()['Resources']['loggroup1LogGroup']['Properties']
        assert redshift_log_group_properties['RetentionInDays'] == 7

        create_cloud_watch_logs_metric_filter(self.stack, 'metric-1', Ref(log_group), 'error')

        metric_filter = self.stack.stack.to_dict()['Resources']['metric1MetricFilter']
        assert metric_filter['Type'] == 'AWS::Logs::MetricFilter'
        metric_filter_properties = metric_filter['Properties']
        assert metric_filter_properties['FilterPattern'] == 'error'
        assert metric_filter_properties['LogGroupName']['Ref'] == 'loggroup1LogGroup'
        metric_transformations = metric_filter_properties['MetricTransformations'][0]
        assert metric_transformations['DefaultValue'] == 0.0
        assert metric_transformations['MetricName'] == 'metric1Metric'
        assert metric_transformations['MetricNamespace'] == 'LogMetrics'
        assert metric_transformations['MetricValue'] == '1'

        create_sns_topic(self.stack, 'topic-1', 'https://events.pagerduty.com/integration/1234/enqueue')

        sns_topic = self.stack.stack.to_dict()['Resources']['topic1Topic']
        assert sns_topic['Type'] == 'AWS::SNS::Topic'
        sns_topic_properties = sns_topic['Properties']
        assert sns_topic_properties['DisplayName'] == 'topic-1'
        assert sns_topic_properties['Subscription'][0]['Endpoint'] == 'https://events.pagerduty.com/integration/1234/enqueue'
        assert sns_topic_properties['Subscription'][0]['Protocol'] == 'https'
        assert sns_topic_properties['TopicName'] == 'topic-1Topic'

        create_sns_notification_alarm(
            stack=self.stack,
            name='alarm-1',
            description='description for alarm_1',
            metric_name='metric1',
            metric_namespace='LogMetrics',
            sns_topic_arn=GetAtt(sns_topic, 'Arn'),
            dimensions={'Resource': 'loggroup1LogGroup'}
        )
        sns_notification_alarm = self.stack.stack.to_dict()['Resources']['alarm1Alarm']
        assert sns_notification_alarm['Type'] == 'AWS::CloudWatch::Alarm'
        sns_notification_alarm_properties = sns_notification_alarm['Properties']
        assert sns_notification_alarm_properties['AlarmName'] == 'alarm-1Alarm'
        assert sns_notification_alarm_properties['AlarmDescription'] == 'description for alarm_1'
        assert sns_notification_alarm_properties['AlarmActions'][0]['Fn::GetAtt'][0]['Properties']['TopicName'] == 'topic-1Topic'
        assert sns_notification_alarm_properties['ComparisonOperator'] == 'GreaterThanThreshold'
        assert sns_notification_alarm_properties['Dimensions'][0] == {'Name': 'Resource', 'Value': 'loggroup1LogGroup'}
        assert sns_notification_alarm_properties['EvaluationPeriods'] == '1'
        assert sns_notification_alarm_properties['MetricName'] == 'metric1Metric'
        assert sns_notification_alarm_properties['Namespace'] == 'LogMetrics'
        assert sns_notification_alarm_properties['Period'] == '60'
        assert sns_notification_alarm_properties['Statistic'] == 'Minimum'
        assert sns_notification_alarm_properties['Threshold'] == '0'

