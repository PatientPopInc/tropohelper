from troposphere import Ref, Base64, Equals, Tags
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration
from troposphere.ec2 import SecurityGroupRule, SecurityGroup, Instance
from troposphere.rds import DBParameterGroup, DBSecurityGroup, DBInstance
import troposphere.elasticache as elasticache


def create_ec2_instance(stack, name, ami, subnetid, keyname, instance_profile="", instance_type="t1.micro", security_groups=(),
                 user_data=""):
    """Add EC2 Instance Resource."""
    return stack.stack.add_resource(
        Instance(
            "{0}".format(name),
            ImageId=ami,
            InstanceType=instance_type,
            KeyName=keyname,
            SecurityGroupIds=list(security_groups),
            SubnetId=subnetid,
            Tags=Tags(Name=name),
            UserData=Base64(user_data),
            IamInstanceProfile=instance_profile
        ))


def create_launch_config(stack, name, ami, security_group, instance_type, profile, block_devices=[], user_data=""):
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
            BlockDeviceMappings=block_devices
        ))


def create_cache_cluster(stack, cache_type):
    """Add Elasticache Cache cluster Resource."""
    ports = {
        'redis': 6379,
        'memcached': 11211
        }
    secgroup = stack.stack.add_resource(SecurityGroup(
        '{0}SecurityGroup'.format(cache_type),
        GroupDescription="{0} Security Group".format(cache_type),
        SecurityGroupIngress=[
            SecurityGroupRule(
                "{0}".format(cache_type),
                CidrIp=Ref(stack.vpc_address_param),
                FromPort=ports[cache_type],
                ToPort=ports[cache_type],
                IpProtocol="tcp",
            )],
        VpcId=Ref(stack.vpc),
    ))

    subnet_group = stack.stack.add_resource(
        elasticache.SubnetGroup(
            '{0}cache'.format(stack.env),
            Description='{0} cache'.format(stack.env),
            SubnetIds=[Ref(stack.backend1_subnet), Ref(stack.backend2_subnet)],
        ))

    stack.stack.add_resource(
        elasticache.ReplicationGroup(
            'CacheCluster',
            ReplicationGroupId='{0}cluster'.format(stack.env),
            ReplicationGroupDescription='{0}cluster'.format(stack.env),
            Engine='{0}'.format(cache_type),
            CacheNodeType=Ref(stack.cache_instance_type_param),
            NumCacheClusters='2',
            CacheSubnetGroupName=Ref(subnet_group),
            SecurityGroupIds=[Ref(secgroup)]
        ))


def create_autoscale_group(stack, name, launch_con, vpc_zones, elbs=[], target_groups=[]):
    """Add EC2 AutoScalingGroup Resource."""
    return stack.stack.add_resource(
        AutoScalingGroup(
            '{0}{1}ASG'.format(stack.env, name.replace('_', '')),
            LaunchConfigurationName=Ref(launch_con),
            MinSize="0",
            MaxSize="5",
            HealthCheckType="EC2",
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
            Description="{0} Parameter Group".format(description),
            Family=family,
            Parameters=parameters
        ))

def create_rds_instance(stack, db_instance_identifier, db_name, db_instance_class, db_username, db_password,
    db_subnet_group, db_security_groups, vpc_security_groups, db_param_group, 
    allocated_storage="20", engine="MySQL", engine_version="5.7.17", 
    storage_encrypted="True", deletion_policy="Retain", multi_az=False):
    
    """Add RDS Instance Resource."""

    return stack.stack.add_resource(
        DBInstance(
            'RDSInstance',
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
            MultiAZ=multi_az
        ))
