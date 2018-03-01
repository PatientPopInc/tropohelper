from troposphere.iam import Role, InstanceProfile, ManagedPolicy, Group, User, AccessKey
from troposphere import Ref, Output, GetAtt
from troposphere.ec2 import SecurityGroup, SecurityGroupRule
from awacs.sts import AssumeRole
from awacs.aws import Action, Allow, Policy, Principal, Statement


def create_iam_role(stack, role_name, managed_policies=(), instance_profile=False):
    """Add IAM role resource."""
    managed_policy_arns = ['arn:aws:iam::aws:policy/{0}'.format(policy)
                           for policy in managed_policies]
    new_role = stack.stack.add_resource(Role(
        '{0}Role'.format(role_name.replace('-', '')),
        RoleName=role_name,
        ManagedPolicyArns=managed_policy_arns,
        AssumeRolePolicyDocument=Policy(
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[AssumeRole],
                    Principal=Principal('Service', ['ec2.amazonaws.com'])
                )
            ])
        ))

    if instance_profile:
        stack.stack.add_resource(InstanceProfile(
            '{}instanceprofile'.format(role_name.replace('-', '')),
            InstanceProfileName=role_name,
            Roles=[(Ref(new_role))]
        ))
    return new_role


def create_iam_group(stack, group_name, managed_policies=()):
    """Add IAM group resource."""
    managed_policy_arns = ['arn:aws:iam::aws:policy/{0}'.format(policy)
                           for policy in managed_policies]
    return stack.stack.add_resource(Group(group_name,
                                          GroupName=group_name,
                                          ManagedPolicyArns=managed_policy_arns))


def create_iam_user(stack, name, groups=()):
    """Add IAM User Resource."""
    return stack.stack.add_resource(User(
        '{0}User'.format(name),
        Groups=groups,
        UserName=name
    ))


def create_access_key(stack, name, user):
    """Add IAM User Access/Secret Key Resource."""
    access_key = stack.stack.add_resource(AccessKey(
        '{0}AccessKey'.format(name),
        Status="Active",
        UserName=user
    ))
    stack.stack.add_output(Output(
        '{0}AccessOutput'.format(name),
        Value=Ref(access_key),
        Description="Access Key for {0}".format(name)
    ))
    stack.stack.add_output(Output(
        '{0}SecretOutput'.format(name),
        Value=GetAtt(access_key, "SecretAccessKey"),
        Description="Secret Key for {0}".format(name)
    ))


def create_instance_profile(stack, name, iam_role):
    """Add IAM Instance Profile Resource."""
    return stack.stack.add_resource(InstanceProfile(
        '{0}InstanceProfile'.format(name),
        Roles=[Ref(iam_role)]
        ))


def create_iam_policy(stack, policy_name, actions, groups=[], roles=[], users=[], resources=['*']):
    """Add IAM policy resource."""
    return stack.stack.add_resource(
        ManagedPolicy(policy_name,
                      ManagedPolicyName=policy_name,
                      Groups=groups,
                      Roles=roles,
                      Users=users,
                      PolicyDocument=Policy(
                          Version="2012-10-17",
                          Statement=[
                              Statement(
                                  Effect=Allow,
                                  Action=[Action('{0}'.format(action.split(':')[0]),
                                                 "{0}".format(action.split(':')[1]))
                                          for action in actions],
                                  Resource=resources
                              )])))


def create_security_group(stack, name, rules=()):
    """Add EC2 Security Group Resource."""
    ingress_rules = []
    for rule in rules:
        ingress_rules.append(
            SecurityGroupRule(
                "{0}".format(rule['name']),
                CidrIp=rule['cidr'],
                FromPort=rule['from_port'],
                ToPort=rule['to_port'],
                IpProtocol=rule['protocol'],
                )
        )
    return stack.stack.add_resource(
        SecurityGroup(
            '{0}SecurityGroup'.format(name),
            GroupDescription="{0} Security Group".format(name),
            SecurityGroupIngress=ingress_rules,
            VpcId=Ref(stack.vpc),
        ))
