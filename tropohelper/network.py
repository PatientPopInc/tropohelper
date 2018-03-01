from troposphere import Ref, GetAtt
from troposphere.ec2 import VPC, RouteTable, Route, InternetGateway, NatGateway, \
 EIP, Subnet, SubnetRouteTableAssociation, VPCGatewayAttachment, VPCPeeringConnection
import troposphere.elasticloadbalancing as elb


def create_vpc(stack, name):
    """Add VPC Resource."""
    return stack.stack.add_resource(
        VPC(
            '{0}VPC'.format(name),
            EnableDnsSupport="true",
            CidrBlock=Ref(stack.vpc_address_param),
            EnableDnsHostnames="true",
            Tags=[
                {'Key': 'Name', 'Value': '{0}'.format(name)},
            ],
        ))


def create_vpc_peer(stack, connection):
    """Add VPC Peering Connection Resource."""
    return stack.stack.add_resource(
        VPCPeeringConnection(
            '{0}VpcPeeringConnection'.format(connection.replace('-', '')),
            PeerVpcId=connection,
            VpcId=Ref(stack.vpc),
        ))


def create_internet_gateway(stack):
    """Add VPC Internet Gateway Resource."""
    return stack.stack.add_resource(
        InternetGateway(
            'InternetGateway',
            Tags=[
                {'Key': 'Name', 'Value': '{0}'.format(stack.env)},
            ],
        ))


def attach_gateway(stack):
    """Add VPC Gateway attachment Resource."""
    stack.stack.add_resource(
        VPCGatewayAttachment(
            "GatewayAttachment",
            VpcId=Ref(stack.vpc),
            InternetGatewayId=Ref(stack.internet_gateway),
        ))


def create_elastic_ip(stack, name):
    """Add VPC Elastic IP Resource."""
    return stack.stack.add_resource(
        EIP(
            '{0}eip'.format(name)
        ))


def associate_routes(stack, subnet_list=()):
    """Add Route Association Resources."""
    for association in subnet_list:
        stack.stack.add_resource(
            SubnetRouteTableAssociation(
                '{0}RouteAssociation'.format(association['name']),
                SubnetId=Ref(association['subnet']),
                RouteTableId=Ref(association['route_table'])
            ))


def create_subnet(stack, name, subnet_cidr, avail_zone='us-east-1a', public_ip=False):
    """Add VPC Subnet Resource."""
    return stack.stack.add_resource(
        Subnet(
            '{0}Subnet'.format(name),
            CidrBlock=Ref(subnet_cidr),
            MapPublicIpOnLaunch=public_ip,
            AvailabilityZone=avail_zone,
            VpcId=Ref(stack.vpc),
            Tags=[
                {'Key': 'Name', 'Value': '{0}{1}'.format(stack.env, name)},
            ],
        ))


def create_nat_gateway(stack):
    """Add VPC NAT Gateway Resource."""
    return stack.stack.add_resource(
        NatGateway(
            'Nat',
            AllocationId=GetAtt(stack.nat_eip, 'AllocationId'),
            SubnetId=Ref(stack.public1_subnet),
            Tags=[
                {'Key': 'Name', 'Value': '{0}'.format(stack.env)},
            ],
        ))


def create_route_table(stack, env, name):
    """Add VPC Route table Resource."""
    return stack.stack.add_resource(
        RouteTable(
            '{0}{1}RouteTable'.format(env, name),
            VpcId=Ref(stack.vpc),
            Tags=[
                {'Key': 'Name', 'Value': '{0}{1}'.format(env, name)},
            ],
        ))


def populate_routes(stack, routes):
    """Add VPC Routes Resources."""
    tables = {
        'private': stack.private_route_table,
        'public': stack.public_route_table
    }
    gateways = {
        'igw': stack.internet_gateway,
        'nat': stack.nat_gateway
    }
    for route in routes:
        if route['route'] == "igw":
            stack.stack.add_resource(
                Route(
                    '{0}'.format(route['route']),
                    GatewayId=Ref(gateways[route['route']]),
                    DestinationCidrBlock='{0}'.format(route['cidrblock']),
                    RouteTableId=Ref(tables[route['routetable']])
                ))
        elif route['route'] == "nat":
            stack.stack.add_resource(
                Route(
                    '{0}'.format(route['route']),
                    NatGatewayId=Ref(gateways[route['route']]),
                    DestinationCidrBlock='{0}'.format(route['cidrblock']),
                    RouteTableId=Ref(tables[route['routetable']])
                ))
        elif route['route'] == "vpc":
            stack.stack.add_resource(
                Route(
                    '{0}{1}'.format(route['route'], route['routetable']),
                    VpcPeeringConnectionId=route['vpc_peer'],
                    DestinationCidrBlock='{0}'.format(route['cidrblock']),
                    RouteTableId=Ref(tables[route['routetable']])
                ))


def create_frontend_elb(stack, cert=None):
    """Add EC2 ELB Resource."""
    return stack.stack.add_resource(
        elb.LoadBalancer(
            'ElasticLoadBalancer',
            Subnets=[Ref(stack.frontend1_subnet), Ref(stack.frontend2_subnet)],
            Listeners=[
                elb.Listener(
                    LoadBalancerPort="80",
                    InstancePort="80",
                    Protocol="HTTP",
                    InstanceProtocol="HTTP",
                ),
                elb.Listener(
                    LoadBalancerPort="443",
                    InstancePort="443",
                    Protocol="HTTPS",
                    InstanceProtocol="HTTPS",
                    SSLCertificateId=cert,
                ),
            ],
            HealthCheck=elb.HealthCheck(
                Target="SSL:443",
                HealthyThreshold="5",
                UnhealthyThreshold="2",
                Interval="15",
                Timeout="5",
            ),
            CrossZone=True,
            SecurityGroups=[Ref(stack.frontend_security_group)],
            Scheme="internet-facing",
        ))
