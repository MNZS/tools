#!/usr/bin/env bash

LOG='/var/log/pac-check.log'
TMP_FILE='/tmp/pac.update'

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

  /sbin/shutdown -r 05:00
}

function check_for_updates() {

  TIME=$(calendar ymdhms)

  echo "$TIME - Checking for updates" >> $LOG 2>&1

  ##/usr/bin/apt update > /tmp/apt.update 2>&1
  /bin/pacman -Sy
  /bin/pacman -Qu > $TMP_FILE 2>&1 

  if [ $(grep -c "\->" $TMP_FILE) -gt 0 ]; then
    NUM=`wc -l $TMP_FILE | cut -d' ' -f1`
    TIME=$(calendar ymdhms)

    if [ $NUM -eq '1' ]; then
	    NOUN='update'
    else
	    NOUN='updates'
    fi
    echo "$TIME - $NUM $NOUN found" >> $LOG 2>&1

    if [ $(grep -G ^linux $TMP_FILE) -gt 0 ]; then
      update_motd
    fi

    while read -r line; do
      #PKG=`echo $line | cut -d ' ' -f1` 2>&1
      #echo "  $PKG" >> $LOG 2>&1
      echo "  $line" >> $LOG 2>&1
    done < $TMP_FILE

    /bin/pacman -Su --noconfirm 2>&1
    TIME=$(calendar ymdhms)
    echo "$TIME - Updates completed" >> $LOG 2>&1
  else
    TIME=$(calendar ymdhms)
    echo "$TIME - No updates found" >> $LOG 2>&1
  fi

  #rm -f $TMP_FILE
}

function run_error_check {
  echo " "
  echo "  You must specify an action: "
  echo "    update  - check for updates to installed packages "
  echo " "
}

## main
if [ -z $1 ]; then
  run_error_check
  exit 0
elif [ $1 == 'cleanup' ]; then
  cleanup_motd
  exit 0
elif [ $1 == 'update' ]; then
  check_for_updates
else
  run_error_check
  exit 0
fi
