#!/bin/bash
# NOTE: This script ONLY WORKS if the board has already been flashed with
# klipper via SD card PRIOR to installing the boot0 jumper.
# The first time the board is booted after the jumper has been installed
# the board needs to be flashed via the dfu vendor:device id. After that
# it can be flashed via the /dev/btt-octopus-11 path, but it then fails
# to exit dfu mode, and then one needs to flash it yet again with the
# vendor:device id. Then it correctly exits DFU mode. Except those times
# where it doesn't, for that we have a 3rd pass...


sudo service klipper stop
echo "flashing rpi-mcu"
cp -f /home/pi/klipper_config/config/boards/rpi/firmware.config /home/pi/klipper/.config
make olddefconfig
make clean
make flash
sudo service klipper start
