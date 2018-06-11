from troposphere.firehose import DeliveryStream, EncryptionConfiguration, \
                                 KMSEncryptionConfig, S3DestinationConfiguration, \
                                 BufferingHints, CloudWatchLoggingOptions


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
