import boto3

# Before using Boto3, you need to set up authentication credentials for your AWS account 
# using either the IAM Console or the AWS CLI. In this tutorial, i have configured my authentication using the 
# AWS CLI 'aws configure' before hand.
#
# You can also use boto3 resource to setup your authentication credentials
# ec2 = boto3.resource('ec2', aws_access_key_id='AWS_ACCESS_KEY_ID',
#                     aws_secret_access_key='AWS_SECRET_ACCESS_KEY',
#                     region_name='eu-central-1')

# create VPC
ec2 = boto3.resource('ec2')
vpc = ec2.create_vpc(CidrBlock='172.20.0.0/16',
                         TagSpecifications=[
        {
            'ResourceType': 'vpc',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'my-vpc'
                },
            ]
        },
    ],)
# Assign name 'my-vpc' to the vpc 
vpc.create_tags(Tags=[{'Key':'Name', 'Value':'my-vpc'}])
vpc.wait_until_available()
vpc_id = vpc.id

# create an internet gateway and attach it to the VPC
igw = ec2.create_internet_gateway(
    TagSpecifications=[
        {
            'ResourceType': 'internet-gateway',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'my-igw'
                },
            ]
        },
    ],
)
# attach the internet gateway to the VPC
igw.attach_to_vpc(VpcId=vpc_id)
igw_id = igw.id

# create a route table for the vpc and a public route with the vpc
route_table = vpc.create_route_table(
    TagSpecifications=[
        {
            'ResourceType': 'route-table',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'my-route-table'
                },
            ]
        },
    ],
)
# allow for public access into the instances launched inside the subnet
route = route_table.create_route(
    GatewayId= igw_id,
    DestinationCidrBlock='0.0.0.0/0'
    
)

# Create Subnets in two different availability zones (one subnet for each zone) for high reliability
subnet1 = vpc.create_subnet(
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'subnet1'
                },
            ]
        },
    ],
    AvailabilityZone = 'eu-central-1a',
    CidrBlock= '172.20.1.0/24'
)

subnet2 = vpc.create_subnet(
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'subnet2'
                },
            ]
        },
    ],
    AvailabilityZone = 'eu-central-1c',
    CidrBlock= '172.20.2.0/24'

)
# Associate route-table with the two created subnets
subnet1_id = subnet1.id
subnet2_id = subnet2.id

subnets_id = [subnet1_id, subnet2_id]
for subnet_id in subnets_id:
    route_table_association = route_table.associate_with_subnet(SubnetId = subnet_id)

# Create security group 
security_group = ec2.create_security_group(
    Description="my security group",
    GroupName="test-sg",
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'security-group',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'my-sg'
                },
            ]
        },
    ]   
)
security_group_id = security_group.id

# Set security group inbound rule to allow SSH, HTTP and HTTPs 
security_group.authorize_ingress(
    IpPermissions=[
        {
            'FromPort': 80,
            'IpProtocol': 'tcp',
            'ToPort': 80,
            'IpRanges': [
                {
                    'CidrIp': '0.0.0.0/0'
                },
            ]
        },
        {
            'FromPort': 22,
            'IpProtocol': 'tcp',
            'ToPort': 22,
            'IpRanges': [
                {
                    'CidrIp': '0.0.0.0/0'
                },
            ]
        },
        {
            'FromPort': 443,
            'IpProtocol': 'tcp',
            'ToPort': 443,
            'IpRanges': [
                {
                    'CidrIp': '0.0.0.0/0'
                },
            ],
        }
    ]
)

# create SSH key-pair, to allow for ssh into the instance
key_pair = ec2.create_key_pair(
    KeyName='my-keypair',
    KeyType='rsa',
    TagSpecifications=[
        {
            'ResourceType': 'key-pair',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'my-key'
                },
            ]
        },
    ],
    KeyFormat='pem'
)


# Launch an EC2 instance in one the subnet and AZ. Also creates a txt file inside the temp directory 
# using the "user data" option
instances = ec2.create_instances(
    ImageId='ami-0faab6bdbac9486fb',
    InstanceType='t2.micro',
    KeyName='my-keypair',
    Placement={'AvailabilityZone': 'eu-central-1a'},
    MaxCount=1,
    MinCount=1,
    UserData='''#!/bin/bash
    echo 'Hello World!' > /tmp/test.txt''',
    NetworkInterfaces=[
        {
            'AssociatePublicIpAddress': True,
            'Groups': [security_group_id],
            'SubnetId': subnet1.id,
            'DeviceIndex': 0
        },
    ],
    # IamInstanceProfile={
    #     'Arn': 'string',
    #     'Name': 'string'
    # },
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'my-ec2Instance'
                },
            ]
        },
    ],
)
# the output of instances is a list of created instance(s)
instances[0].wait_until_running()
print(instances[0])