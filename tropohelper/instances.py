import troposphere.elasticache as elasticache
from troposphere import Base64, Ref, Tags
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration
from troposphere.ec2 import Instance, SecurityGroup, SecurityGroupRule
from troposphere.rds import DBInstance, DBParameterGroup, DBSecurityGroup


def create_ec2_instance(stack,
                        name,
                        ami,
                        subnetid,
                        keyname,
                        instance_profile='',
                        instance_type='t1.micro',
                        security_groups=(),
                        user_data=''):
    """Add EC2 Instance Resource."""

    return stack.stack.add_resource(
        Instance(
            '{0}'.format(name),
            ImageId=ami,
            InstanceType=instance_type,
            KeyName=keyname,
            SecurityGroupIds=list(security_groups),
            SubnetId=subnetid,
            Tags=Tags(Name=name),
            UserData=Base64(user_data),
            IamInstanceProfile=instance_profile))


def create_launch_config(stack,
                         name,
                         ami,
                         security_group,
                         instance_type,
                         profile,
                         block_devices=[],
                         user_data=''):
    """Add EC2 LaunchConfiguration Resource."""

    return stack.stack.add_resource(
        LaunchConfiguration(
            '{0}{1}LC'.format(stack.env, name.replace('_', '')),
            ImageId=ami,
            KeyName=Ref(stack.ssh_key_param),
            SecurityGroups=security_group,
            InstanceType=instance_type,
            IamInstanceProfile=profile,
            UserData=Base64(user_data),
            BlockDeviceMappings=block_devices))


def create_autoscale_group(stack,
                           name,
                           launch_con,
                           vpc_zones,
                           elbs=[],
                           target_groups=[]):
    """Add EC2 AutoScalingGroup Resource."""

    return stack.stack.add_resource(
        AutoScalingGroup(
            '{0}{1}ASG'.format(stack.env, name.replace('_', '')),
            LaunchConfigurationName=Ref(launch_con),
            MinSize='0',
            MaxSize='5',
            HealthCheckType='EC2',
            VPCZoneIdentifier=vpc_zones,
            TerminationPolicies=['OldestInstance'],
            LoadBalancerNames=elbs,
            TargetGroupARNs=target_groups,
        ))


def create_db_param_group(stack, name, description, family, parameters={}):
    """Create a DB Parameter Group"""

    return stack.stack.add_resource(
        DBParameterGroup(
            '{0}DBParamGroup'.format(name),
            Description='{0} Parameter Group'.format(description),
            Family=family,
            Parameters=parameters))


def create_rds_instance(stack,
                        db_instance_identifier,
                        db_name,
                        db_instance_class,
                        db_username,
                        db_password,
                        db_subnet_group,
                        db_security_groups,
                        vpc_security_groups,
                        db_param_group,
                        allocated_storage='20',
                        engine='MySQL',
                        engine_version='5.7.17',
                        storage_encrypted='True',
                        deletion_policy='Retain',
                        multi_az=False,
                        public=False):
    """Add RDS Instance Resource."""

    return stack.stack.add_resource(
        DBInstance(
            '{0}RDSInstance'.format(db_instance_identifier.replace('-', '')),
            DBInstanceIdentifier=db_instance_identifier,
            DBName=db_name,
            DBInstanceClass=db_instance_class,
            AllocatedStorage=allocated_storage,
            Engine=engine,
            EngineVersion=engine_version,
            MasterUsername=db_username,
            MasterUserPassword=db_password,
            DBSubnetGroupName=db_subnet_group,
            DBSecurityGroups=list(db_security_groups),
            VPCSecurityGroups=list(vpc_security_groups),
            DBParameterGroupName=db_param_group,
            StorageEncrypted=storage_encrypted,
            DeletionPolicy=deletion_policy,
            PubliclyAccessible=public,
            MultiAZ=multi_az))
