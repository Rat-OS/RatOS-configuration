#!/bin/bash
MCU=/dev/mellow-fly-sht-36
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi
../../scripts/flash-path.sh $MCU
