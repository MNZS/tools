#!/usr/bin/env python3

import json
import re
import requests
import sys
import time

## user variables
do_api = ''
do_region = ''
do_inst_size = ''
do_inst_image = ''
do_ssh_key = ''
bash_file = '' ## full path to .bashrc type of file that will allow for new alias to be created

## global variables
do_base_url='https://api.digitalocean.com/v2'
do_droplets_endpoint = do_base_url + '/droplets'
do_headers = { 'Authorization': 'Bearer '+do_api, 'Content-Type':'application/json' }

## gets information from DO on a specific droplet
def get_droplet(d_id):
	do_droplet_get_endpoint = "%s/%s" % (do_droplets_endpoint, d_id)
	do_r = requests.get(do_droplet_get_endpoint, headers=do_headers)
	do_droplet_data = do_r.json()
	return do_droplet_data

## create a new DO droplet
def add_droplet(d_name):
	## define the new droplet atttributes
	do_droplet_add_attributes = {	'name': d_name,
					'region': do_region,
					'size': do_inst_size,
					'image': do_inst_image,
					'tags':	[ d_name ],
					'ssh_keys': [ do_ssh_key ] }

	## send the request to DO, receive feedback on success
	do_r = requests.post(do_droplets_endpoint, headers=do_headers, json=do_droplet_add_attributes)
	do_data = do_r.json()

	## confirm creation or spit out error message 
	## TBD

	## pause the application to allow for the droplet creation to complete at DO
	time.sleep(20)

	## create a new api endpoint based on the droplet's id to grab ip address
	do_droplet_get_endpoint = "%s/%i" % (do_droplets_endpoint, do_data['droplet']['id'])
	do_get_r = requests.get(do_droplet_get_endpoint, headers=do_headers)
	do_get_data = do_get_r.json()
	droplet_ip = do_get_data['droplet']['networks']['v4'][1]['ip_address']

	#time.sleep(60)

	## create and insert the new alias for .bash_local
	alias_update = "alias %s='ssh -i ~/.ssh/majick_rsa root@%s'\n" % (d_name, droplet_ip)
	with open (bash_file,"a") as bash_out:
		bash_out.write(alias_update)

	## print out a summary of what has been done
	print("\nA new droplet is available for use.")
	print("Type \". ~/{}\" and then you".format(bash_file.split('/')[-1]))
	print("can type \"%s\" to ssh into the host.\n" % (d_name))

## delete an existing droplet
def delete_droplets(d_name):

	## create a new endpoint with the droplet's tag name
	do_droplet_del_endpoint = "%s?tag_name=%s" % (do_droplets_endpoint, d_name)
	do_r = requests.delete(do_droplet_del_endpoint, headers=do_headers)
	#do_del_data = do_r.json()
	## check on success/fail

	## request confirmation of the droplet's deletion
	## use the id to make a call for name and linux version to confirm
	## probably break this out into its own subroutine

	## remove the alias from .bash_local
	with open(bash_file, "r+") as f:
		d = f.readlines()
		f.seek(0)
		for i in d:
			if re.match("alias\ %s" % d_name,i):
				pass
			else:
				f.write(i)
		f.truncate()
	## print out summary of what has been done	

## print out a list of existing droplets
def list_droplets():
	do_r = requests.get(do_droplets_endpoint, headers=do_headers)
	do_data = do_r.json()

	drop_tot = len(do_data['droplets'])

	count = 0
	print("{:<22}{:<15}{}".format('Name:','ID:','IP:'))
	while count < drop_tot:
		d_name = do_data['droplets'][count]['name']
		d_id = do_data['droplets'][count]['id']
		d_ip = do_data['droplets'][count]['networks']['v4'][1]['ip_address']
		print("{:<22}{:<15}{}".format(d_name,d_id,d_ip))
		count += 1	

	if count == 0:
		print("\nNo instances are configured.\n")

def print_usage():
	print("\nUsage:")
	print("\tdodrop add <droplet name>")
	print("\tdodrop rm <droplet name>")
	print("\tdodrop ls\n")

## Start main routine
def main():
	if len(sys.argv) < 2:
		print_usage()
		exit()
	elif sys.argv[1] == 'ls':
		list_droplets()
	elif sys.argv[1] == 'rm':
		delete_droplets(sys.argv[2])
	elif sys.argv[1] == 'add':
		add_droplet(sys.argv[2])
	else:
		print_usage()
		exit()

main()
