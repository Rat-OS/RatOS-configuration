#!/bin/bash

MCU=/dev/btt-octopus-11
VENDORDEVICEID=0483:df11
cp -f /home/pi/klipper_config/config/boards/btt-octopus-11/firmware.config /home/pi/klipper/.config
cd /home/pi/klipper
make olddefconfig
make clean
make
sudo service klipper stop
if [ -e $MCU ]; then
    echo "Flashing Octopus via path"
    make flash FLASH_DEVICE=$MCU
else
    echo "Flashing Octopus via vendor and device ids - 1st pass"
    make flash FLASH_DEVICE=$VENDORDEVICEID
fi
if [ -ne $MCU]; then
    echo "Flashing Octopus via vendor and device ids - 2nd pass"
    make flash FLASH_DEVICE=$VENDORDEVICEID
fi
sudo service klipper start