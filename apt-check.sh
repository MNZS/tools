#!/usr/bin/env bash

## This tool is used via cron to check for updates to install deb packages
## In addition, once each month, it will check for an updated OS verion
## In both cases, it will install updates and log the results.

LOG='/var/log/apt/apt-check.log'
APT='/etc/logrotate.d/apt'

function calendar () {
  if [ $1 == 'ymdhms' ]; then
    CURRENT=`date '+%Y-%m-%d %H:%M:%S'`
  elif [ $1 == 'ymd' ]; then
    CURRENT=`date +%Y%m%d`
  fi
  echo $CURRENT
}

function cleanup_motd () {
        echo " "
        echo "  The motd file has been cleared "
        echo " "
        cat /etc/motd.1 > /etc/motd
        exit 0
}

function log_rotate () {
  echo >> $APT
  echo "/var/log/apt/apt-check.log {" >> $APT
  echo "  rotate 12" >> $APT
  echo "  monthly" >> $APT
  echo "  missingok" >> $APT
  echo "  notifempty" >> $APT
  echo "}" >> $APT
}

function update_motd () {
  if [ ! -f /etc/motd.1 ]; then
    cp /etc/motd /etc/motd.1
  fi
  echo > /etc/motd
  echo >> /etc/motd
  echo "  This machine was rebooted!" >> /etc/motd
  echo "  The kernel has been updated by apt-check " >> /etc/motd
  echo "  This message created on $(calendar ymdhms) " >> /etc/motd
  echo " " >> /etc/motd
  echo "  Run /root/bin/apt-check cleanup to clear " >> /etc/motd
  echo "  this message " >> /etc/motd
  echo >> /etc/motd
  echo >> /etc/motd

  #/sbin/shutdown -r 05:00 
}

function check_for_updates() {

  TIME=$(calendar ymdhms)

  echo "$TIME - Checking for updates" >> $LOG 2>&1
  /bin/bash /root/bin/disco.sh "$TIME - Checking for updates"

  /usr/bin/apt update > /tmp/apt.update 2>&1

  if [ $(grep -c 'can be upgraded' /tmp/apt.update) -gt 0 ]; then
    NUM=`tail -1 /tmp/apt.update | cut -d ' ' -f 1`
    TIME=$(calendar ymdhms)
    echo "$TIME - $NUM updates found" >> $LOG 2>&1
    /bin/bash /root/bin/disco.sh "$TIME - $NUM updates found (apt-check)"

    apt list --upgradable | grep '/' >/tmp/apt.update

    if [ $(grep -c 'linux-image' /tmp/apt.update) -gt 0 ]; then
      update_motd
    fi

    while read -r line; do
      PKG=`echo $line | cut -d '[' -f1` 2>&1
      echo "  $PKG" >> $LOG 2>&1
      /bin/bash /root/bin/disco.sh "-- $PKG updated"
    done < /tmp/apt.update

    /usr/bin/apt full-upgrade -y 2>&1
    
    ## attempt to avoid error output
    dpkg --configure -a

    TIME=$(calendar ymdhms)
    echo "$TIME - Updates completed" >> $LOG 2>&1
    /bin/bash /root/bin/disco.sh "$TIME - Updates completed"
  else
    TIME=$(calendar ymdhms)	
    echo "$TIME - No updates found" >> $LOG 2>&1
    /bin/bash /root/bin/disco.sh "$TIME - No updates found"
  fi

  #rm -f /tmp/apt.update
}

function check_for_upgrade () {

  TIME=$(calendar ymdhms)
  echo "$TIME - Checking for new Debian Release" >> $LOG 2>&1

  ## Current $VERSION_CODENAME
  . /etc/os-release

  ## Sources list
  SOURCES='/etc/apt/sources.list'

  DEB_MIRROR='http://ftp.us.debian.org/debian/dists/stable/Release'

  MIRROR_CODENAME=`curl $DEB_MIRROR | grep -i codename | cut -d' ' -f2` 2>&1
  if [ -z $MIRROR_CODENAME ]; then
    echo "$TIME - ERROR when checking for new Debian Release" >> $LOG 2>&1
    echo "  Could not get Release information from Debian mirror" >> $LOG 2>&1
    exit 1
  elif [ $VERSION_CODENAME == $MIRROR_CODENAME ]; then
    TIME=$(calendar ymdhms)
    echo "$TIME - No upgrade found." >> $LOG 2>&1
    echo "  $VERSION_CODENAME is current" >> $LOG 2>&1
    check_for_updates
    exit 0
  else
    TIME=$(calendar ymd)
    echo "$TIME - Upgrade found!" >> $LOG 2>&1
    echo "  $VERSION_CODENAME moving to $MIRROR_CODENAME" >> $LOG 2>&1

    ## backup sources.list
    cp -a $SOURCES $SOURCES-$TIME

    ## update sources with new codename
    /usr/bin/sed -i "s/$VERSION_CODENAME/$MIRROR_CODENAME/g" $SOURCES-$TODAY
  
    ## update the list of available deb packages
    apt update

    ## do a soft upgrade
    apt upgrade

    ## do a full upgrade
    apt full-upgrade

    ## get rid of dependencies
    apt autoremove --purge

    ## testing to avoid errors
    dpkg --configure -a
    
    TIME=$(calendar ymd)
    echo "$TIME - Upgrade completed." >> $LOG 2>&1
  fi
}

function run_error_check {
  echo " "
  echo "  You must specify an action: "
  echo "    update  - check for updates to installed packages "
  echo "    upgrade - check for a major distro update "
  echo " "
}

## main
if [ $(grep -c 'apt-check' /etc/logrotate.d/apt) -eq 0 ]; then
	log_rotate
fi

if [ -z $1 ]; then
  run_error_check
  exit 1
elif [ $1 == 'cleanup' ]; then
  cleanup_motd
  exit 1
elif [ $1 == 'update' ]; then
  TODATE=`date +%d`
  if [ $TODATE == '20' ]; then
    check_for_upgrade
  else 
    check_for_updates
  fi
elif [ $1 == 'upgrade' ]; then
  check_for_upgrade
else
  run_error_check
  exit 1
fi
