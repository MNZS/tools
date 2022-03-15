#!/usr/bin/env python3

import requests
import hashlib
import getpass

def submit_password():
  hibp_api = 'https://api.pwnedpasswords.com/range/'
  pw_plaintext = getpass.getpass("\n  Please type in the password to evaluate:\n")

  ## encode the user input
  pw_encoded = pw_plaintext.encode()
  ## create the sha1 hash value
  pw_hash = hashlib.sha1(pw_encoded)
  ## create an ascii representation of the sha1 hash value
  pw_sha1 = pw_hash.hexdigest()
  ## grab the first five digits of the hash
  pw_prefix = pw_sha1[0:5]
  ## grab the remainder of the hash 
  pw_suffix = pw_sha1[5:]

  ## get a list of suffixes from HIPB that match the prefix
  response = requests.get(hibp_api+pw_prefix)

  ## print a summary of what we're looking for
  print("full hash: {}\nprefix: {}\nsuffix: {}\n".format(pw_sha1,pw_prefix,pw_suffix))

  count = 0
  ## look at each suffix received from HIBP
  ## .content is a byte field. conver to str and split on CR/NL
  for line in str(response.content).split("\\r\\n"): 
    ## each line is composed of suffix:count
    ## we extract just the suffix value
    hibp_response =  line.split(":")[0]
    ## if our suffix value is in the line then increment the value of count and break out of the loop
    ## need to match upper case to align with how HIBP values are returned
    if pw_suffix.upper() in hibp_response:
      count += 1
      break

  ## print out findings:
  if count > 0:
    print("  UNSAFE: This password is in the HIPB list.\n")
  else:
    print("  SAFE: This password is NOT in the HIPB list.\n")

  try_again = input('Try another password? (y/N)>')
  if try_again == 'y' or try_again == 'Y':
    submit_password()
  else:
    exit()
  
submit_password()
