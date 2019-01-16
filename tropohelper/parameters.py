from troposphere import Parameter


def create_vpc_param(stack, network):
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


def create_subnet_param(stack, name, network):
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


def create_ami_param(stack, name):
    """Create an AMI Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            "{0}AmiIdParam".format(name),
            Type="String",
            Description="The AMI ID for the {0} instances".format(name),
            Default="ami-12345678"
        ))


def create_ssh_key_param(stack):
    """Create a SSH Key Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            "SSHKeyParam",
            Type="String",
            Description="The SSH Key to use for autoscaling groups",
            Default=""
        ))


def create_bool_param(stack, parameter_name):
    """Create a custom Bool Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            "{0}BoolParam".format(parameter_name),
            Type="String",
            Description="Use {0}?".format(parameter_name),
            Default="NO",
            AllowedValues=["YES", "NO"],
            ))


def create_dbpass_param(stack):
    """Create a Database Password Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            "DbPassParam",
            Type="String",
            Description="The db admin password",
            NoEcho=True
        ))


def create_instance_type_param(stack, name, itype="Standard", default="t2.medium"):
    """Create an Instance Type Parameter."""
    instance_sizes = ["t2.medium", "t2.large", "t2.xlarge", "t2.2xlarge",
                      "c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge",
                      "r4.large", "r4.xlarge", "r4.2xlarge", "r4.4xlarge",
                      "m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge"]
    if itype == "DB":
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


def create_cache_instance_type_param(stack, name):
    """Create a Cache Instance Type Parameter."""
    return stack.stack.add_parameter(
        Parameter(
            '{0}CacheNodeType'.format(name.replace('-', '')),
            Description='The compute and memory capacity of the nodes in the Cache Cluster',
            Type='String',
            Default='cache.t2.small',
            AllowedValues=['cache.t2.micro', 'cache.t2.small', 'cache.t2.medium',
                           'cache.m3.medium', 'cache.m4.large', 'cache.m4.2xlarge'],
            ConstraintDescription='must select a valid Cache Node type.',
        ))


def create_misc_string_param(stack, name, description="String", no_echo=False):
    """Create a Misc. String parameter."""
    return stack.stack.add_parameter(
        Parameter(
            '{0}StringParam'.format(name),
            Description='{0}'.format(description),
            Type='String',
            NoEcho=no_echo
        ))
