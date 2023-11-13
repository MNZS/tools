## tools repository 

<b>Security</b><p>
&nbsp;&nbsp;&nbsp;&nbsp;exfil.py - send stuff via dns tunneling. 

&nbsp;&nbsp;&nbsp;&nbsp;parsel.py - put the stuff you sent back together. relies on bind9 querylog.

&nbsp;&nbsp;&nbsp;&nbsp;pw_check.py - proof of concept for HaveIBeenPwned API range checks for passwords

<b>Cloud</b><p>
&nbsp;&nbsp;&nbsp;&nbsp;instmgr.py - launch and terminate instances from the cli. 
Supports AWS, Digital Ocean, and Linode

<b>Linux</b><p>
&nbsp;&nbsp;&nbsp;&nbsp;apt-check.sh - update and upgrade Debian from a cron job. 

&nbsp;&nbsp;&nbsp;&nbsp;pac-check.sh - update arch linux from a systemd.timers job.
