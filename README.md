## tools repository 

exfil.py - send stuff via dns tunneling. 

parsel.py - put the stuff you sent back together. relies on bind9 querylog.

ec2mgr.py - spin up and tear down ec2 instances from the cli. support by the
aws.yaml file

dodrop.py - create and destroy droplets on Digital Ocean from the cli.

pw_check.py - proof of concept for HaveIBeenPwned API range checks for passwords

apt-check.sh - update and upgrade Debian from a cron job. Puts WAY too much 
power in the hands of a script.

pac-check.sh - update arch linux from a cron job.
