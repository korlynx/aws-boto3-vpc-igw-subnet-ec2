import boto3

# ec2 = boto3.resource('ec2', aws_access_key_id='AWS_ACCESS_KEY_ID',
#                     aws_secret_access_key='AWS_SECRET_ACCESS_KEY',
#                     region_name='eu-central-1')

instance_name = 'my-ec2Instance'
keypair_name = 'my-keypair'
vpc_name = 'my-vpc'
securityGroup_name = 'my-sg'
route_table_name = 'my-route-table'

# get all available vpc in a region
ec2 = boto3.resource('ec2')

# stop and terminate ec2 instance
instances =ec2.instances.filter()
for instance in instances:
    if instance.tags[0]['Value'] == instance_name:
        instance.stop()
        instance.wait_until_stopped()
        #print('instance {} successfully stopped'.format(instance_name))
        # terminate instance
        instance.terminate()
        instance.wait_until_terminated()
        #print('instance {} successfully terminated'.format(instance_name))
        
    else:
        pass
        print('instance with name {} does not exit'.format(instance_name))

# Delete key-pair
key_pair = ec2.KeyPair(keypair_name)
key_pair.delete()


# Delete vpc: The  resource attached to the vpc (Subnets, internet gateway, route table...) must be deleted first!
vpc_iterator = ec2.vpcs.filter()
for vpc in vpc_iterator:
    # pass default vpc 
    if vpc.tags is None: pass
    elif vpc.tags[0]['Value'] == vpc_name:
        # delete internet gateway
        for igw in vpc.internet_gateways.filter():
            vpc.detach_internet_gateway(InternetGatewayId=igw.id)
            igw.delete()
 
            # delet vpc security group
        for security_group in vpc.security_groups.filter():
            #
            if security_group.tags is None: pass
            elif security_group.tags[0]['Value'] == securityGroup_name:
                security_group.delete(GroupName=securityGroup_name)

        # delete vpc subnets
        for subnet in vpc.subnets.filter():
            subnet.delete()

        # # delete vpc
        for route_table in vpc.route_tables.filter():
            if len(route_table.tags) == 0: pass
            elif route_table.tags[0]['Value']==route_table_name:
                route_table.delete()
  
        vpc.delete()

    
