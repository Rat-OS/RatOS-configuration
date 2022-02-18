#!/bin/bash
if [ "$EUID" -ne 0 ]
  then 
  echo "ERROR: Please run as root"
  exit
fi

if [ "$#" -ne 1 ]
  then 
  echo "Missing hostname parameter"
  exit
fi

CURRENT_HOSTNAME=`cat /etc/hostname | tr -d " \t\n\r"`
echo $1 > /etc/hostname
sed -i "s/127.0.1.1.*$CURRENT_HOSTNAME/127.0.1.1\t$1/g" /etc/hosts
if [ $? -eq 0 ] 
then
	echo "Hostname has been changed, please reboot your Raspberry Pi for the change to take effect"
else
	echo "An error occured while attempting to change the hostname"
	exit 1
fi
