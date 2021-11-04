#!/usr/bin/env python3

import argparse
import boto3
import datetime
import re
import sys
import time
import yaml

## define variables
cfg_file=''
default_aws_profile = ''
bash_file = '' ## path to .bashrc type file that will include new alias

with open (cfg_file, 'r') as cfg_f:
	aws_conf = yaml.safe_load(cfg_f)

parser = argparse.ArgumentParser()

parser.add_argument('-a','--add',
			help='add new instance')
parser.add_argument('-r','--remove',
			help='remove instance')
parser.add_argument('-l','--list',
			action='store_true',
			help='list running instances')
parser.add_argument('-p','--profile',
			help='specify AWS profile')
parser.add_argument('-d','--describe',
			action='store_true',
			help='list available AWS profiles')

args = parser.parse_args()

if args.profile is None:
	args.profile = default_aws_profile 

aws_profile = aws_conf[args.profile]['profile']
template_name = aws_conf[args.profile]['template']
template_version = str(aws_conf[args.profile]['template_version'])
subnet_id= aws_conf[args.profile]['subnet']
ssh_key= aws_conf[args.profile]['key']

time_now = datetime.datetime.now()
time_suffix = "{}{}{}-{}-{}-{}".format(time_now.year,time_now.month,time_now.day,time_now.hour,time_now.minute,time_now.second)

def describe_profiles():
	print("\n  Available AWS profiles:")
	for profile in aws_conf:
		print("\t" + profile)
	print("\n  Default profile is " + args.profile + "\n")

def make_session():
	session = boto3.Session(profile_name=aws_profile)
	return session

def create_new(instance_name):
	session = make_session()
	client = session.client('ec2')
	instance_tag = "{}-{}".format(instance_name,time_suffix)
	response = client.run_instances(
		MinCount=1,
		MaxCount=1,
		SubnetId=subnet_id,
		TagSpecifications=[{
			'ResourceType':'instance',
			'Tags':[{
				'Key':'UID',
				'Value':instance_tag },
				{
				'Key':'ShortName',
				'Value':instance_name },
				{
				'Key':'Name',
				'Value':instance_name },
				{
				'Key':'Origin',
				'Value':'boto3'}] }],
		LaunchTemplate={
			'LaunchTemplateName':template_name,
			'Version':template_version })


	time.sleep(15)

	instance_info = client.describe_instances(
		Filters=[
			{ 'Name':'tag:UID',
			  'Values':[instance_tag] }])

	instance_ip = instance_info['Reservations'][0]['Instances'][0]['PublicIpAddress']

	## create and insert the new alias for .bash_local
	alias_update = "alias {}='ssh -i ~/.ssh/{} ubuntu@{}'\n".format(instance_name,ssh_key,instance_ip)
	with open (bash_file,"a") as bash_out:
		bash_out.write(alias_update)

        ## print out a summary of what has been done
	print("\nA new AWS instance is available for use.")
	print("Type \". ~/.bash_local\" and then you")
	print("can type \'{}\' to ssh into the host.\n".format(instance_name))

def delete_existing(instance_name):
	## thought here might be to return a list
	## if i create an instance with the same ShortName, the routine won't delete the running instance
	instance_id = get_id(instance_name)

	session = make_session()
	client = session.client('ec2')
	response = client.terminate_instances(
		InstanceIds=[ instance_id ])

	#instance_name = get_name(instance_id)
	with open(bash_file, "r+") as f:
		d = f.readlines()
		f.seek(0)
		for i in d:
			if re.match("alias\ {}".format(instance_name),i):
				pass
			f.write(i)
		f.truncate()

	print("\nSuccessfully shutting down {}\n".format(instance_name))
	
def get_state(instance_id):
	session = make_session()
	ec2 = session.resource('ec2')
	ec2_data = ec2.Instance(instance_id)
	for state in ec2_data.state:
		if state == 'Name':
			instance_state = ec2_data.state[state]

	return instance_state

def get_name(instance_id):
	session = make_session()
	ec2 = session.resource('ec2')
	short_name = ''
	ec2_data = ec2.Instance(instance_id)
	for tags in ec2_data.tags:
		if tags['Key'] == 'ShortName':
			short_name = tags['Value']

	return short_name

def get_id(short_name):
	session = make_session()
	client = session.client('ec2')

	response = client.describe_instances(
		Filters=[{
			'Name':'tag:ShortName',
			'Values':[short_name] }])
		
	instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
	return instance_id
	
def list_existing():
	session = make_session()
	client = session.client('ec2')
	response = client.describe_instances(
		Filters=[{
			'Name':'tag:Origin',
			'Values':['boto3'] }])
	count = 0
	print("{:<22}{:<15}{}".format('Instance ID:','State:','Name:'))
	for i in response['Reservations']:
		for j in i['Instances']:
			instance_name = get_name(j['InstanceId'])
			instance_state =  get_state(j['InstanceId'])
			print("{:<22}{:<15}{}".format(j['InstanceId'], instance_state, instance_name))
			count += 1
	if count == 0:
		print("\nNo instances are configured.\n")

def display_usage():
	print("\nRun mkec -h for usage.\n")
	exit()

## Start main routine
def main():

	if args.list:
		list_existing()
	elif args.remove:
		try:
			delete_existing(args.remove)
		except:
			display_usage()	
	elif args.add:
		try:
			create_new(args.add)
		except:
			display_usage()
	elif args.describe:
		try:
			describe_profiles()
		except:
			display_usage()
	else:
		display_usage()

main()
