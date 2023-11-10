#!/usr/bin/env python3

import argparse
import boto3
import botocore
import datetime
import os
import re
import requests
import time
import yaml

## configuration file defined as .tools.yaml in user home dir
cfg_home = os.path.expanduser("~")
cfg_file = cfg_home+'/.tools.yaml'

## read in config file 
with open (cfg_file, 'r') as cfg_f:
  cloud_conf = yaml.safe_load(cfg_f)

## get command line options
parser = argparse.ArgumentParser()

parser.add_argument('-a','--add',
      help='add new instance')
parser.add_argument('-r','--remove',
      help='remove instance')
parser.add_argument('-c','--cloud',
      help='cloud platform: aws/do/ln')
parser.add_argument('-l','--list',
      action='store_true',
      help='list running instances')

args = parser.parse_args()

## read in config file 
if args.cloud is None:
  args.cloud = 'aws'

with open (cfg_file, 'r') as cfg_f:
  cloud_conf = yaml.safe_load(cfg_f)

if args.cloud == 'aws':
  aws_profile = cloud_conf['aws']['profile']
  template_name = cloud_conf['aws']['template_id']
  template_version = str(cloud_conf['aws']['template_version'])
  ssh_key = cloud_conf['aws']['key']
  bash_file = cloud_conf['aws']['alias']
elif args.cloud == 'do':
  do_base_url='https://api.digitalocean.com/v2'
  do_droplets_endpoint = do_base_url + '/droplets'
  do_headers = { 'Authorization': 'Bearer '+cloud_conf['do']['api'], 'Content-Type':'application/json' }
elif args.cloud == 'ln':
  lin_api = cloud_conf['linode']['api']
  lin_base_url = 'https://api.linode.com/v4/'
  lin_headers = { 'Authorization': 'Bearer '+lin_api, 'Content-Type':'application/json' }
else:
  print('wrong syntax')
  exit()

## grab current time and format for logging
time_now = datetime.datetime.now()
time_suffix = "{}{}{}-{}-{}-{}".format(time_now.year,
                                        time_now.month,
                                        time_now.day,
                                        time_now.hour,
                                        time_now.minute,
                                        time_now.second)

## establish an AWS api session
def make_aws_session():
  session = boto3.Session(profile_name=aws_profile)
  return session

## gets information from DO on a specific droplet
def get_droplet(d_id):
  do_droplet_get_endpoint = "%s/%s" % (do_droplets_endpoint, d_id)
  do_r = requests.get(do_droplet_get_endpoint, headers=do_headers)
  do_droplet_data = do_r.json()
  return do_droplet_data

## add a new instance
def create_new(instance_name):

  if args.cloud == 'aws':
    session = make_aws_session()
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

  elif args.cloud == 'do':
    ## define the new droplet atttributes
    do_droplet_add_attributes = { 'name': instance_name,
                                  'region': cloud_conf['do']['region'],
                                  'size': cloud_conf['do']['size'],
                                  'image': cloud_conf['do']['image'],
                                  'tags': [ instance_name ],
                                  'ssh_keys': [ cloud_conf['do']['ssh_key'] ] }

    ## send the request to DO, receive feedback on success
    do_r = requests.post(do_droplets_endpoint, headers=do_headers, json=do_droplet_add_attributes)
    do_data = do_r.json()

    ## confirm creation or spit out error message
    ## TBD

    ## pause the application to allow for the droplet creation to complete at DO
    time.sleep(45)
    
    ## create a new api endpoint based on the droplet's id to grab ip address
    do_droplet_get_endpoint = "%s/%i" % (do_droplets_endpoint, do_data['droplet']['id'])
    do_get_r = requests.get(do_droplet_get_endpoint, headers=do_headers)
    do_get_data = do_get_r.json()
    droplet_ip = do_get_data['droplet']['networks']['v4'][0]['ip_address']

    ## create and insert the new alias for .bash_local
    alias_update = "alias %s='ssh root@%s'\n" % (instance_name, droplet_ip)
    with open (cloud_conf['do']['alias'],"a") as bash_out:
      bash_out.write(alias_update)

    ## print out a summary of what has been done
    print("\nA new Ocean Droplet is available for use.")
    print("Type \". ~/{}\" and then you".format(cloud_conf['do']['alias'].split('/')[-1]))
    print("can type \"%s\" to ssh into the host.\n" % (instance_name))

  elif args.cloud == 'ln':
    ## define the endpoint url
    lin_endpoint_url = lin_base_url+'linode/instances'

    ## define the attributes of the new node in a dictionary
    node_attr = {
                  'image': cloud_conf['linode']['image'],
                  'label': instance_name,
                  'root_pass': cloud_conf['linode']['root'],
                  'type': cloud_conf['linode']['type'],
                  'authorized_users': [ cloud_conf['linode']['ssh_user'] ],
                  'region': cloud_conf['linode']['region'],
    }

    lin_r = requests.post(lin_endpoint_url,
                        headers=lin_headers,
                        json=node_attr)
    lin_data = lin_r.json()

    print(lin_data['ipv4'][0])

    ## create and insert the new alias for .bash_local
    alias_update = "alias %s='ssh root@%s'\n" % (instance_name, lin_data['ipv4'][0])
    with open (cloud_conf['linode']['alias'],"a") as bash_out:
      bash_out.write(alias_update)

    ## print out a summary of what has been done
    print("\nA new Linode is available for use.")
    print("Type \". ~/{}\" and then you".format(cloud_conf['linode']['alias'].split('/')[-1]))
    print("can type \"%s\" to ssh into the host.\n" % (instance_name))

## terminate an existing instance
def delete_existing(instance_name):

  if args.cloud == 'aws':
    ## get the id for the instance 
    instance_id = get_id(instance_name)

    ## send the terminate request
    session = make_aws_session()
    client = session.client('ec2')
    response = client.terminate_instances(
      InstanceIds=[ instance_id ])

    ## update the local bash file to remove alias
    with open(cloud_conf['aws']['alias'], "r+") as f:
      d = f.readlines()
      f.seek(0)
      for i in d:
        if re.match("alias\ {}".format(instance_name),i):
          continue 
        f.write(i)
      f.truncate()

    print("\nSuccessfully shutting down {}\n".format(instance_name))

  elif args.cloud == 'do':

    print('gonna try to remove something from do')

    ## create a new endpoint with the droplet's tag name
    do_droplet_del_endpoint = "%s?tag_name=%s" % (do_droplets_endpoint, instance_name)
    do_r = requests.delete(do_droplet_del_endpoint, headers=do_headers)
    #do_del_data = do_r.json()
    ## check on success/fail

    ## request confirmation of the droplet's deletion
    ## use the id to make a call for name and linux version to confirm
    ## probably break this out into its own subroutine

    ## remove the alias from .bash_local
    with open(cloud_conf['do']['alias'], "r+") as f:
      d = f.readlines()
      f.seek(0)
      for i in d:
        if re.match("alias\ %s" % instance_name,i):
          continue 
        else:
          f.write(i)
      f.truncate()

    ## print out summary of what has been done
    print("\nSuccessfully shutting down {}\n".format(instance_name))

## get the current running state of a specific instance
def get_state(instance_id):
  session = make_aws_session()
  ec2 = session.resource('ec2')
  ec2_data = ec2.Instance(instance_id)
  for state in ec2_data.state:
    if state == 'Name':
      instance_state = ec2_data.state[state]

  return instance_state

## get the name or label of a specific running instance
def get_name(instance_id):
  session = make_aws_session()
  ec2 = session.resource('ec2')
  short_name = ''
  ec2_data = ec2.Instance(instance_id)
  for tags in ec2_data.tags:
    if tags['Key'] == 'ShortName':
      short_name = tags['Value']

  return short_name

## get the id of a specific running instance based on its label
def get_id(short_name):
  session = make_aws_session()
  client = session.client('ec2')

  response = client.describe_instances(
    Filters=[{
      'Name':'tag:ShortName',
      'Values':[short_name] }])
    
  instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
  return instance_id
 
## print out a list of existing instances and their runnning state
def list_existing():
  if args.cloud == 'aws':
    session = make_aws_session()
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

  elif args.cloud == 'do':
    do_r = requests.get(do_droplets_endpoint, headers=do_headers)
    do_data = do_r.json()

    drop_tot = len(do_data['droplets'])

    count = 0
    print("{:<22}{:<15}{}".format('Name:','ID:','IP:'))
    while count < drop_tot:
      d_name = do_data['droplets'][count]['name']
      d_id = do_data['droplets'][count]['id']
      d_ip = do_data['droplets'][count]['networks']['v4'][0]['ip_address']
      print("{:<22}{:<15}{}".format(d_name,d_id,d_ip))
      count += 1

    if count == 0:
      print("\nNo instances are configured.\n")

## error output
def display_usage():
  print("\nRun instmgr -h for usage.\n")
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
  else:
    display_usage()

main()
