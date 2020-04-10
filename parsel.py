#!/usr/bin/env python3

import binascii
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--logfile','-l',required=True)
parser.add_argument('--id','-i',required=True)
args = parser.parse_args()

log_file = args.logfile
file_id = args.id

struct = {}
new_file = ''

with open (log_file,'r') as work_log:
	for line in work_log:
		if line.split()[9] == 'TXT':
			seq = int(line.split()[7].split('.')[0],16)
			val = line.split()[7].split('.')[1]
			struct[seq] = val

with open (binascii.unhexlify(struct[1]),'wb') as f:
	for key, val in sorted(struct.items()):
		if key != 1:
			new_file = new_file + val
			
	f.write(binascii.unhexlify(new_file))
f.close()
