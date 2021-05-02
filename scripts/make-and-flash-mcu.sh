#!/bin/bash

# Should be run as root.
service klipper stop
cd /home/pi/klipper
make clean
make
./scripts/flash-sdcard.sh /dev/klipper btt-skr-pro-v1.2
service klipper start