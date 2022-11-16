#!/bin/bash
MCU=/dev/btt-manta-m8p
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi
../../scripts/flash-path.sh $MCU
