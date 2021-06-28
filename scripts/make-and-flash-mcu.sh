#!/bin/bash

# Should be run as root.
sudo service klipper stop
cd /home/pi/klipper
make clean
make
./scripts/flash-sdcard.sh /dev/btt-skr-pro-12 btt-skr-pro-v1.2
sudo service klipper start
