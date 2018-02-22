from nose import with_setup
from troposphere import Template
from tropohelper.parameters import create_vpc_param, create_subnet_param, create_ami_param, \
                                   create_bool_param, create_instance_type_param, create_ssh_key_param, \
                                   create_cache_instance_type_param, create_dbpass_param


class test_stack(object):
    """Test stack."""
    def __init__(self):
        """Intitialize our test stack."""
        self.stack = Template()
        self.env = "test"


class TestParameters:
    """Test all the parameter functions."""

    def setup(self):
        """Create our test environment."""
        self.stack = test_stack()

    def test_create_vpc_param(self):
        """Test creating vpc parameter."""
        create_vpc_param(self.stack, "10.99.0.0/16")
        assert self.stack.stack.to_dict()['Parameters']['VPCParam']['Default'] == "10.99.0.0/16"

    def test_create_ami_param(self):
        """Test creating ami paramter."""
        create_ami_param(self.stack, 'TestServer')
        default_ami = self.stack.stack.to_dict()['Parameters']['TestServerAmiIdParam']['Default']
        assert default_ami == "ami-12345678"

    def test_create_subnet_param(self):
        """Test creating subnet parameter."""
        create_subnet_param(self.stack, 'TestSubnet', '10.99.1.0/8')
        subnet = self.stack.stack.to_dict()['Parameters']['TestSubnetSubnetParam']['Default']
        assert subnet == "10.99.1.0/8"

    def test_create_ssh_key_param(self):
        """Test creating ssh_key parameter."""
        create_ssh_key_param(self.stack)
        assert self.stack.stack.to_dict()['Parameters']['SSHKeyParam']

    def test_create_bool_param(self):
        """Test creating bool parameter."""
        create_bool_param(self.stack, "TestBool")
        assert self.stack.stack.to_dict()['Parameters']['TestBoolBoolParam']['Default'] == "NO"

    def test_create_dbpass_param(self):
        """Test creating database password parameter."""
        create_dbpass_param(self.stack)
        assert self.stack.stack.to_dict()['Parameters']['DbPassParam']

    def test_create_instance_type_param(self):
        """Test creating normal instance type parameter."""
        create_instance_type_param(self.stack, 'TestType')
        assert "r3.large" in self.stack.stack.to_dict()['Parameters']['TestTypeboxsizeParam']['AllowedValues']

    def test_create_instance_type_db_param(self):
        """Test creating db instance type parameter."""
        create_instance_type_param(self.stack, 'TestTypeDB', 'DB', 'db.t2.medium')
        assert "db.r3.4xlarge" in self.stack.stack.to_dict()['Parameters']['TestTypeDBboxsizeParam']['AllowedValues']

    def test_create_cache_instance_type_param(self):
        """Test creating cache instance type paramter."""
        create_cache_instance_type_param(self.stack)
        cache_default_size = self.stack.stack.to_dict()['Parameters']['CacheNodeType']['Default']
        assert cache_default_size == 'cache.t2.small'
