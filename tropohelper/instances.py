from troposphere import Ref, Base64, Equals, Tags
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration
from troposphere.ec2 import SecurityGroupRule, SecurityGroup, Instance
from troposphere.rds import DBInstance, DBSubnetGroup, DBParameterGroup
import troposphere.elasticache as elasticache


def create_ec2_instance(stack, name, ami, subnetid, keyname, instance_type="t1.micro", security_groups=(),
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
            UserData=Base64(user_data)
        ))


def create_launch_config(stack, name, ami, security_group, instance_type, profile, user_data=""):
    """Add EC2 LaunchConfiguration Resource."""
    return stack.stack.add_resource(
        LaunchConfiguration(
            '{0}{1}LC'.format(stack.env, name.replace('_', '')),
            ImageId=ami,
            KeyName=Ref(stack.ssh_key_param),
            SecurityGroups=security_group,
            InstanceType=instance_type,
            IamInstanceProfile=profile,
            UserData=Base64(user_data)
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


def create_autoscale_group(stack, name, launch_con, vpc_zones, elbs=()):
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
        ))


def create_rds_instance(stack):
    """Add RDS Instance Resource."""
    conditions = {
        "LaunchRDS": Equals(
            Ref(stack.rds_param),
            "YES"
        ),
    }
    for each in conditions:
        stack.stack.add_condition(each, conditions[each])

    db_subnetgroup = stack.stack.add_resource(
        DBSubnetGroup(
            'DBSubnetGroup',
            Condition="LaunchRDS",
            DBSubnetGroupDescription="{0} Subnet Group".format(stack.env),
            SubnetIds=[Ref(stack.backend1_subnet), Ref(stack.backend2_subnet)]
        )
    )

    db_security_group = stack.stack.add_resource(
        SecurityGroup(
            'DBSecurityGroup',
            Condition="LaunchRDS",
            GroupDescription="{0} DB".format(stack.env),
            VpcId=Ref(stack.vpc),
            SecurityGroupIngress=[
                SecurityGroupRule(
                    "MYSQL",
                    CidrIp="10.0.0.0/8",
                    FromPort=3306,
                    ToPort=3306,
                    IpProtocol="tcp",
                ),
            ]
        )
    )
    db_param_group = stack.stack.add_resource(
        DBParameterGroup(
            'DbParamGroup',
            Condition="LaunchRDS",
            Description="{0} Parameter Group".format(stack.env),
            Family="MySQL5.7",
        )
    )

    return stack.stack.add_resource(
        DBInstance(
            'RDSInstance',
            Condition="LaunchRDS",
            DBInstanceIdentifier="{0}Master".format(stack.env),
            DBName=Ref(stack.db_name_param),
            DBInstanceClass=Ref(stack.db_instance_type_param),
            AllocatedStorage="200",
            Engine="MySQL",
            EngineVersion="5.7.17",
            MasterUsername=Ref(stack.db_user_param),
            MasterUserPassword=Ref(stack.dbpass_param),
            DBSubnetGroupName=Ref(db_subnetgroup),
            VPCSecurityGroups=[Ref(db_security_group)],
            DBParameterGroupName=Ref(db_param_group),
            StorageEncrypted="True",
            DeletionPolicy="Retain"
        ))
