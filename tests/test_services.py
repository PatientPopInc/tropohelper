import json
from nose import with_setup
from troposphere import Template, GetAtt
from tropohelper.services import (
    create_kinesis_stream,
    create_json_redshift_firehose_from_stream,
    create_cloud_watch_logs_metric_filter,
    create_sns_topic,
    create_sns_notification_alarm
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

        create_kinesis_stream(self.stack, 'stream1', 5)
        assert self.stack.stack.to_dict()['Resources']['stream1Stream']['Type'] == 'AWS::Kinesis::Stream'
        assert self.stack.stack.to_dict()['Resources']['stream1Stream']['Properties']['ShardCount'] == 5

        create_json_redshift_firehose_from_stream(self.stack, 'firehose1', 'firehose_arn',
                                                  'arn:aws:kinesis:::stream1Stream', 'arn:aws:role:::role1',
                                                  'jdbc:redshift://localhost:123/redshift_db1',
                                                  'redshift_username', 'redshift_password',
                                                  'redshift_db_table1',
                                                  'arn:aws:s3:::bucket1',
                                                  'arn:aws:kms:us-east-1:1234',
                                                  'arn:aws:iam::1234:role/firehose_delivery_role')
        assert self.stack.stack.to_dict()['Resources']['firehose1Firehose']['Type'] == 'AWS::KinesisFirehose::DeliveryStream'
        properties = self.stack.stack.to_dict()['Resources']['firehose1Firehose']['Properties']

        kinesis_stream_source_configuration = properties['KinesisStreamSourceConfiguration']
        assert kinesis_stream_source_configuration['RoleARN'] == 'arn:aws:role:::role1'
        assert kinesis_stream_source_configuration['KinesisStreamARN'] == 'arn:aws:kinesis:::stream1Stream'

        assert properties['DeliveryStreamType'] == 'KinesisStreamAsSource'
        assert properties['DeliveryStreamName'] == 'firehose1'

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
        assert s3_cloud_watch_logging_options['LogGroupName'] == 'firehose-streams'
        assert s3_cloud_watch_logging_options['LogStreamName'] == 'firehose1'

        redshift_cloud_watch_logging_options = redshift_destination_configuration['CloudWatchLoggingOptions']
        assert redshift_cloud_watch_logging_options['Enabled'] == 'true'
        assert redshift_cloud_watch_logging_options['LogGroupName'] == 'redshift-firehose'
        assert redshift_cloud_watch_logging_options['LogStreamName'] == 'firehose1'

    def test_create_email_notification_alarm_for_cloud_watch_logs_metric(self):
        """Test creating email notification alarm for cloud watch logs metric."""

        create_cloud_watch_logs_metric_filter(self.stack, 'metric-1', 'log_group_1', 'error')
        assert self.stack.stack.to_dict()['Resources']['metric1MetricFilter']['Type'] == 'AWS::Logs::MetricFilter'
        assert self.stack.stack.to_dict()['Resources']['metric1MetricFilter']['Properties']['FilterPattern'] == 'error'
        assert self.stack.stack.to_dict()['Resources']['metric1MetricFilter']['Properties']['LogGroupName'] == 'log_group_1'
        assert self.stack.stack.to_dict()['Resources']['metric1MetricFilter']['Properties']['MetricTransformations'][0]['DefaultValue'] == 0.0
        assert self.stack.stack.to_dict()['Resources']['metric1MetricFilter']['Properties']['MetricTransformations'][0]['MetricName'] == 'metric1Metric'
        assert self.stack.stack.to_dict()['Resources']['metric1MetricFilter']['Properties']['MetricTransformations'][0]['MetricNamespace'] == 'LogMetrics'
        assert self.stack.stack.to_dict()['Resources']['metric1MetricFilter']['Properties']['MetricTransformations'][0]['MetricValue'] == '1'

        create_sns_topic(self.stack, 'topic-1', 'https://events.pagerduty.com/integration/1234/enqueue')
        assert self.stack.stack.to_dict()['Resources']['topic1Topic']['Type'] == 'AWS::SNS::Topic'
        assert self.stack.stack.to_dict()['Resources']['topic1Topic']['Properties']['DisplayName'] == 'topic-1'
        assert self.stack.stack.to_dict()['Resources']['topic1Topic']['Properties']['Subscription'][0]['Endpoint'] == 'https://events.pagerduty.com/integration/1234/enqueue'
        assert self.stack.stack.to_dict()['Resources']['topic1Topic']['Properties']['Subscription'][0]['Protocol'] == 'https'
        assert self.stack.stack.to_dict()['Resources']['topic1Topic']['Properties']['TopicName'] == 'topic-1Topic'

        create_sns_notification_alarm(self.stack, 'alarm-1', 'description for alarm_1',
                                      'metric1', 'LogMetrics',
                                      GetAtt(self.stack.stack.to_dict()['Resources']['topic1Topic'], 'Arn'))
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Type'] == 'AWS::CloudWatch::Alarm'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['AlarmName'] == 'alarm-1Alarm'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['AlarmDescription'] == 'description for alarm_1'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['AlarmActions'][0]['Fn::GetAtt'][0]['Properties']['TopicName'] == 'topic-1Topic'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['ComparisonOperator'] == 'GreaterThanThreshold'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['EvaluationPeriods'] == '1'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['MetricName'] == 'metric1Metric'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['Namespace'] == 'LogMetrics'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['Period'] == '60'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['Statistic'] == 'Minimum'
        assert self.stack.stack.to_dict()['Resources']['alarm1Alarm']['Properties']['Threshold'] == '0'
