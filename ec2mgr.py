#!/usr/bin/env python3

import argparse
import boto3
import botocore
import datetime
import os
import re
#import sys
import time
import yaml

## configuration file defined as .tools.yaml in user home dir
cfg_home = os.path.expanduser("~")
cfg_file = cfg_home+'/.tools.yaml'

## read in config file 
with open (cfg_file, 'r') as cfg_f:
  aws_conf = yaml.safe_load(cfg_f)

aws_profile = aws_conf['aws']['profile']
template_name = aws_conf['aws']['template_id']
template_version = str(aws_conf['aws']['template_version'])
ssh_key = aws_conf['aws']['key']
bash_file = aws_conf['aws']['alias']

## get command line options
parser = argparse.ArgumentParser()

parser.add_argument('-a','--add',
      help='add new instance')
parser.add_argument('-r','--remove',
      help='remove instance')
parser.add_argument('-l','--list',
      action='store_true',
      help='list running instances')

args = parser.parse_args()

## grab current time and format for logging
time_now = datetime.datetime.now()
time_suffix = "{}{}{}-{}-{}-{}".format(time_now.year,
                                        time_now.month,
                                        time_now.day,
                                        time_now.hour,
                                        time_now.minute,
                                        time_now.second)

## establish an AWS api session
def make_session():
  session = boto3.Session(profile_name=aws_profile)
  return session

## add a new instance
def create_new(instance_name):

  session = make_session()
  client = session.client('ec2')
  ## create a logging tag for instance metadata
  instance_tag = "{}-{}".format(instance_name,time_suffix)

  ## deliver instance configuration specs
  response = client.run_instances(
    MinCount=1,
    MaxCount=1,
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
      'LaunchTemplateId':template_name,
      'Version':template_version })

  ## give aws a few seconds to spin up the instance
  time.sleep(15)

  ## get details of instance for output to confirm success
  instance_info = client.describe_instances(
    Filters=[
      { 'Name':'tag:UID',
        'Values':[instance_tag] }])

  instance_ip = instance_info['Reservations'][0]['Instances'][0]['PublicIpAddress']

  ## create and insert the new alias for bash file
  alias_update = "alias {}='ssh admin@{}'\n".format(instance_name,instance_ip)
  with open (bash_file,"a") as bash_out:
    bash_out.write(alias_update)

  ## print out a summary of what has been done
  print("\nA new AWS instance is available for use.")
  print("Type \". ~/{}\" and then you".format(bash_file.split('/')[-1]))
  print("can type \'{}\' to ssh into the host.\n".format(instance_name))

## terminate an existing instance
def delete_existing(instance_name):
 
  ## get the id for the instance 
  instance_id = get_id(instance_name)

  ## send the terminate request
  session = make_session()
  client = session.client('ec2')
  response = client.terminate_instances(
    InstanceIds=[ instance_id ])

  ## update the local bash file to remove alias
  with open(bash_file, "r+") as f:
    d = f.readlines()
    f.seek(0)
    for i in d:
      if re.match("alias\ {}".format(instance_name),i):
        continue 
      f.write(i)
    f.truncate()

  print("\nSuccessfully shutting down {}\n".format(instance_name))

## get the current running state of a specific instance
def get_state(instance_id):
  session = make_session()
  ec2 = session.resource('ec2')
  ec2_data = ec2.Instance(instance_id)
  for state in ec2_data.state:
    if state == 'Name':
      instance_state = ec2_data.state[state]

  return instance_state

## get the name or label of a specific running instance
def get_name(instance_id):
  session = make_session()
  ec2 = session.resource('ec2')
  short_name = ''
  ec2_data = ec2.Instance(instance_id)
  for tags in ec2_data.tags:
    if tags['Key'] == 'ShortName':
      short_name = tags['Value']

  return short_name

## get the id of a specific running instance based on its label
def get_id(short_name):
  session = make_session()
  client = session.client('ec2')

  response = client.describe_instances(
    Filters=[{
      'Name':'tag:ShortName',
      'Values':[short_name] }])
    
  instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
  return instance_id
 
## print out a list of existing instances and their runnning state
def list_existing():
  session = make_session()
  client = session.client('ec2')

  ## request a list of instances that were created by this script
  response = client.describe_instances(
    Filters=[{
      'Name':'tag:Origin',
      'Values':['boto3'] }])
  count = 0

  ## create the header for the print table
  print("{:<22}{:<15}{}".format('Instance ID:','State:','Name:'))

  ## print out the table of instances
  for i in response['Reservations']:
    for j in i['Instances']:
      instance_name = get_name(j['InstanceId'])
      instance_state =  get_state(j['InstanceId'])
      print("{:<22}{:<15}{}".format(j['InstanceId'], instance_state, instance_name))
      count += 1
  if count == 0:
    print("\nNo instances are configured.\n")

## error output
def display_usage():
  print("\nRun ec2mgr -h for usage.\n")
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
    except botocore.exceptions.ClientError as error:
      raise error
  elif args.describe:
    try:
      describe_profiles()
    except:
      display_usage()
  else:
    display_usage()

main()
