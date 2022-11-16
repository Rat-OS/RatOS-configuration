#!/bin/bash
/dev/btt-skr-mini-e3-30
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi
../../scripts/flash-path.sh $MCU
