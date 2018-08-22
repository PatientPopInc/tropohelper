import json
from nose import with_setup
from troposphere import Template
from tropohelper.services import create_kinesis_stream, create_json_redshift_firehose_from_stream

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
        assert copy_command['CopyOptions'] == "JSON 'auto'"

        s3_configuration = redshift_destination_configuration['S3Configuration']
        assert s3_configuration['RoleARN'] == 'arn:aws:iam::1234:role/firehose_delivery_role'
        assert s3_configuration['CompressionFormat'] == 'GZIP'
        assert s3_configuration['BufferingHints']['IntervalInSeconds'] == 300
        assert s3_configuration['BufferingHints']['SizeInMBs'] == 5
        assert s3_configuration['EncryptionConfiguration']['KMSEncryptionConfig']['AWSKMSKeyARN'] == 'arn:aws:kms:us-east-1:1234'
        assert s3_configuration['Prefix'] == 'firehose1'
        assert s3_configuration['BucketARN'] == 'arn:aws:s3:::bucket1'

        cloud_watch_logging_options = s3_configuration['CloudWatchLoggingOptions']
        assert cloud_watch_logging_options['Enabled'] == 'true'
        assert cloud_watch_logging_options['LogGroupName'] == 'firehose-streams'
        assert cloud_watch_logging_options['LogStreamName'] == 'firehose1'
