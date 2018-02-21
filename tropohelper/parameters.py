from troposphere import Parameter


def vpc_address(stack, network):
    """Create a VPC Address Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            'VPCParam',
            Description='VPC Address',
            Type='String',
            MinLength='9',
            MaxLength='15',
            Default='{0}'.format(network),
            AllowedPattern="(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})",
            ConstraintDescription=("Must be a valid IP network address in the form x.x.x.x/x"),
        ))


def subnet_param(stack, name, network):
    """Create a Subnet Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            '{0}SubnetParam'.format(name),
            Description='{0} Subnet Declaration'.format(name),
            Type='String',
            MinLength='9',
            MaxLength='18',
            Default='{0}'.format(network),
            AllowedPattern="(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})",
            ConstraintDescription=("Must be a valid IP CIDR range of the form x.x.x.x/x."),
        ))


def ami(stack, name):
    """Create an AMI Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            "{0}AmiIdParam".format(name),
            Type="String",
            Description="The AMI ID for the {0} instances".format(name),
            Default="ami-375d2221"
        ))


def ssh_key_param(stack):
    """Create a SSH Key Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            "SSHKeyParam",
            Type="String",
            Description="The SSH Key to use for autoscaling groups",
            Default=""
        ))


def bool_param(stack, parameter_name):
    """Create a custom Bool Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            "{0}BoolParam".format(parameter_name),
            Type="String",
            Description="Use {0}?".format(parameter_name),
            Default="NO",
            AllowedValues=["YES", "NO"],
            ))


def dbpass_param(stack):
    """Create a Database Password Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            "DbPassParam",
            Type="String",
            Description="The db admin password",
            Default=""
        ))


def instance_type(stack, name, default="t2.medium"):
    """Create an Instance Type Parameter."""
    instance_sizes = ["t2.medium", "t2.large", "c4.large", "c4.xlarge",
                      "c4.4xlarge", "r3.large", "r3.xlarge", "r3.4xlarge",
                      "m4.large", "m4.xlarge", "m4.4xlarge", "m4.8xlarge",
                      "m4.16xlarge"]
    if name == "DB":
        instance_sizes = ["db.t2.medium", "db.t2.large", "db.m4.large",
                          "db.m4.xlarge", "db.m4.2xlarge", "db.m4.4xlarge",
                          "db.m3.10xlarge", "db.r3.large", "db.r3.xlarge",
                          "db.r3.2xlarge", "db.r3.4xlarge", "db.r3.8xlarge"]

    return stack.stack.add_parameter(
        Parameter(
            "{0}boxsizeParam".format(name),
            Type="String",
            Default="{0}".format(default),
            AllowedValues=instance_sizes,
            Description="{0} instance type".format(name),
            ConstraintDescription="must be a valid instance type.",
        ))


def cache_instance_type(stack):
    """Create a Cache Instance Type Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            'CacheNodeType',
            Description='The compute and memory capacity of the nodes in the Cache Cluster',
            Type='String',
            Default='cache.t2.small',
            AllowedValues=['cache.t2.small', 'cache.t2.medium',
                           'cache.m4.large', 'cache.m4.2xlarge'],
            ConstraintDescription='must select a valid Cache Node type.',
        ))
