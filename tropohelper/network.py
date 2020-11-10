import troposphere.elasticloadbalancing as elb
import troposphere.elasticloadbalancingv2 as alb
from troposphere import GetAtt, Ref
from troposphere.ec2 import (EIP, VPC, InternetGateway, NatGateway, Route,
                             RouteTable, Subnet, SubnetRouteTableAssociation,
                             VPCGatewayAttachment, VPCPeeringConnection)
from troposphere.rds import DBSubnetGroup
from troposphere.route53 import HostedZone, RecordSetType


def create_vpc(stack, name, address=None):
    """Add VPC Resource."""

    if address is None:
        address = Ref(stack.vpc_address_param)

    return stack.stack.add_resource(
        VPC(
            '{0}VPC'.format(name),
            EnableDnsSupport='true',
            CidrBlock=address,
            EnableDnsHostnames='true',
            Tags=[
                {
                    'Key': 'Name',
                    'Value': '{0}'.format(name)
                },
            ],
        ))


def create_vpc_peer(stack, connection, peer_region='us-east-1'):
    """Add VPC Peering Connection Resource."""

    return stack.stack.add_resource(
        VPCPeeringConnection(
            '{0}VpcPeeringConnection'.format(connection.replace('-', '')),
            PeerVpcId=connection,
            PeerRegion=peer_region,
            VpcId=Ref(stack.vpc),
        ))


def create_internet_gateway(stack):
    """Add VPC Internet Gateway Resource."""

    return stack.stack.add_resource(
        InternetGateway(
            'InternetGateway',
            Tags=[
                {
                    'Key': 'Name',
                    'Value': '{0}'.format(stack.env)
                },
            ],
        ))


def attach_gateway(stack):
    """Add VPC Gateway attachment Resource."""
    stack.stack.add_resource(
        VPCGatewayAttachment(
            'GatewayAttachment',
            VpcId=Ref(stack.vpc),
            InternetGatewayId=Ref(stack.internet_gateway),
        ))


def create_elastic_ip(stack, name):
    """Add VPC Elastic IP Resource."""

    return stack.stack.add_resource(EIP('{0}eip'.format(name)))


def associate_routes(stack, subnet_list=()):
    """Add Route Association Resources."""

    for association in subnet_list:
        stack.stack.add_resource(
            SubnetRouteTableAssociation(
                '{0}RouteAssociation'.format(association['name']),
                SubnetId=Ref(association['subnet']),
                RouteTableId=Ref(association['route_table'])))


def create_subnet(stack,
                  name,
                  subnet_cidr,
                  avail_zone='us-east-1a',
                  public_ip=False):
    """Add VPC Subnet Resource."""

    return stack.stack.add_resource(
        Subnet(
            '{0}Subnet'.format(name),
            CidrBlock=Ref(subnet_cidr),
            MapPublicIpOnLaunch=public_ip,
            AvailabilityZone=avail_zone,
            VpcId=Ref(stack.vpc),
            Tags=[
                {
                    'Key': 'Name',
                    'Value': '{0}{1}'.format(stack.env, name)
                },
            ],
        ))


def create_db_subnet(stack, name, description, subnet_ids=()):
    """Add DB Subnet Resource."""

    return stack.stack.add_resource(
        DBSubnetGroup(
            '{0}DBSubnet'.format(name),
            DBSubnetGroupDescription='{0} Subnet Group'.format(description),
            SubnetIds=subnet_ids))


def create_nat_gateway(stack):
    """Add VPC NAT Gateway Resource."""

    return stack.stack.add_resource(
        NatGateway(
            'Nat',
            AllocationId=GetAtt(stack.nat_eip, 'AllocationId'),
            SubnetId=Ref(stack.public1_subnet),
            Tags=[
                {
                    'Key': 'Name',
                    'Value': '{0}'.format(stack.env)
                },
            ],
        ))


def create_route_table(stack, env, name):
    """Add VPC Route table Resource."""

    return stack.stack.add_resource(
        RouteTable(
            '{0}{1}RouteTable'.format(env, name),
            VpcId=Ref(stack.vpc),
            Tags=[
                {
                    'Key': 'Name',
                    'Value': '{0}{1}'.format(env, name)
                },
            ],
        ))


def populate_routes(stack, routes):
    """Add VPC Routes Resources."""
    tables = {
        'private': stack.private_route_table,
        'public': stack.public_route_table
    }
    gateways = {'igw': stack.internet_gateway, 'nat': stack.nat_gateway}

    for route in routes:
        if route['route'] == 'igw':
            stack.stack.add_resource(
                Route(
                    '{0}'.format(route['route']),
                    GatewayId=Ref(gateways[route['route']]),
                    DestinationCidrBlock='{0}'.format(route['cidrblock']),
                    RouteTableId=Ref(tables[route['routetable']])))
        elif route['route'] == 'nat':
            stack.stack.add_resource(
                Route(
                    '{0}'.format(route['route']),
                    NatGatewayId=Ref(gateways[route['route']]),
                    DestinationCidrBlock='{0}'.format(route['cidrblock']),
                    RouteTableId=Ref(tables[route['routetable']])))
        elif 'vpc_peer' in route.keys():
            create_peer_route(
                stack, '{0}{1}'.format(route['route'], route['routetable']),
                route['vpc_peer'], '{0}'.format(route['cidrblock']),
                Ref(tables[route['routetable']]))


def create_peer_route(stack, name, peer, destination_cidr, route_table):
    stack.stack.add_resource(
        Route(
            '{0}'.format(name),
            VpcPeeringConnectionId=peer,
            DestinationCidrBlock=destination_cidr,
            RouteTableId=route_table))


def create_frontend_elb(stack, cert=None):
    """Add EC2 ELB Resource."""

    return stack.stack.add_resource(
        elb.LoadBalancer(
            'ElasticLoadBalancer',
            Subnets=[Ref(stack.frontend1_subnet),
                     Ref(stack.frontend2_subnet)],
            Listeners=[
                elb.Listener(
                    LoadBalancerPort='80',
                    InstancePort='80',
                    Protocol='HTTP',
                    InstanceProtocol='HTTP',
                ),
                elb.Listener(
                    LoadBalancerPort='443',
                    InstancePort='443',
                    Protocol='HTTPS',
                    InstanceProtocol='HTTPS',
                    SSLCertificateId=cert,
                ),
            ],
            HealthCheck=elb.HealthCheck(
                Target='SSL:443',
                HealthyThreshold='5',
                UnhealthyThreshold='2',
                Interval='15',
                Timeout='5',
            ),
            CrossZone=True,
            SecurityGroups=[Ref(stack.frontend_security_group)],
            Scheme='internet-facing',
        ))


def create_target_group(stack,
                        name,
                        port,
                        protocol='HTTPS',
                        targets=[],
                        http_codes='200',
                        health_check_path='/',
                        target_type='instance',
                        attributes=False):
    """Add Target Group Resource."""
    target_objects = []

    for target in targets:
        target_objects.append(alb.TargetDescription(Id=target))

    tg_atts = []

    if not attributes:
        tg_atts.append(
            alb.TargetGroupAttribute(
                Key='deregistration_delay.timeout_seconds', Value='300'))
    else:
        for att, value in attributes.items():
            tg_atts.append(alb.TargetGroupAttribute(Key=att, Value=value))

    if http_codes is not None:
        return stack.stack.add_resource(
            alb.TargetGroup(
                '{0}TargetGroup'.format(name),
                HealthCheckIntervalSeconds='30',
                HealthCheckProtocol=protocol,
                HealthCheckTimeoutSeconds='10',
                HealthyThresholdCount='4',
                HealthCheckPath=health_check_path,
                Matcher=alb.Matcher(HttpCode=http_codes),
                Name='{0}Target'.format(name),
                Port=port,
                Protocol=protocol,
                Targets=target_objects,
                TargetType=target_type,
                UnhealthyThresholdCount='3',
                TargetGroupAttributes=tg_atts,
                VpcId=Ref(stack.vpc)))

    return stack.stack.add_resource(
        alb.TargetGroup(
            '{0}TargetGroup'.format(name),
            HealthCheckIntervalSeconds='30',
            HealthCheckProtocol=protocol,
            HealthCheckTimeoutSeconds='10',
            HealthyThresholdCount='3',
            Name='{0}Target'.format(name),
            Port=port,
            Protocol=protocol,
            Targets=targets,
            UnhealthyThresholdCount='3',
            TargetType=target_type,
            TargetGroupAttributes=tg_atts,
            VpcId=Ref(stack.vpc)))


def create_alb(stack,
               name,
               subnets=[],
               security_groups=[],
               condition_field='',
               scheme='internet-facing',
               LoadBalancerAttributes=[]):
    """Add Application Loadbalancer Resource."""

    return stack.stack.add_resource(
        alb.LoadBalancer(
            '{0}ALB'.format(name),
            Condition=condition_field,
            Name='{0}ALB'.format(name),
            Scheme=scheme,
            SecurityGroups=security_groups,
            Subnets=subnets,
            LoadBalancerAttributes=LoadBalancerAttributes))


def create_alb_listener(stack,
                        name,
                        alb_arn,
                        target_group,
                        port=443,
                        protocol='HTTPS',
                        certificates=[],
                        condition_field=''):
    """Add ALB Listener Resource."""
    certificate_arns = [
        alb.Certificate(
            '{0}Cert'.format(name), CertificateArn=certificate_arn)

        for certificate_arn in certificates
    ]

    return stack.stack.add_resource(
        alb.Listener(
            '{0}Listener'.format(name),
            Condition=condition_field,
            Port=port,
            Protocol=protocol,
            Certificates=certificate_arns,
            LoadBalancerArn=alb_arn,
            DefaultActions=[
                alb.Action(Type='forward', TargetGroupArn=target_group)
            ]))


def create_alb_listener_rule(stack,
                             name,
                             listener,
                             condition,
                             target_group,
                             priority=1,
                             condition_field=''):
    """Add ALB Listener Rule Resource."""

    return stack.stack.add_resource(
        alb.ListenerRule(
            '{0}ListenerRule'.format(name),
            Condition=condition_field,
            ListenerArn=listener,
            Conditions=[
                alb.Condition(
                    Field=condition['field'], Values=condition['values'])
            ],
            Actions=[alb.Action(Type='forward', TargetGroupArn=target_group)],
            Priority=priority))


def create_hosted_zone(stack, name):
    """Add Route53 HostedZone Resource."""

    return stack.stack.add_resource(
        HostedZone('{0}HostedZone'.format(name.replace('.', '')), Name=name))


def create_or_update_dns_record(stack,
                                record_name,
                                record_type,
                                record_value,
                                hosted_zone_name,
                                condition_field=''):
    """Create or Update Route53 Record Resource."""

    return stack.stack.add_resource(
        RecordSetType(
            '{0}'.format(
                record_name.replace('.', '').replace('*', 'wildcard')),
            Condition=condition_field,
            HostedZoneName='{0}.'.format(hosted_zone_name),
            Type=record_type,
            TTL='60',
            Name='{0}.'.format(record_name),
            ResourceRecords=record_value))
