import boto3, sys
client = boto3.client('ec2')
print(len(client.describe_instance_status()['InstanceStatuses']))
instanceIds = []
for instance in client.describe_instance_status()['InstanceStatuses']:
    print(instance['InstanceId'])
    instanceIds.append(instance['InstanceId'])

client.terminate_instances(InstanceIds=instanceIds)    
