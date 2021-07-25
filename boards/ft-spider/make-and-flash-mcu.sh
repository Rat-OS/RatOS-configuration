#!/bin/bash

cp -f /home/pi/klipper_config/config/boards/ft-spider/firmware.config /home/pi/klipper/.config
cd /home/pi/klipper
make olddefconfig
make clean
make
sudo service klipper stop
if [ -e $MCU ]; then
    echo "Flashing Spider via path"
    make flash FLASH_DEVICE=$MCU
else
    echo "Flashing Spider via vendor and device ids"
    make flash FLASH_DEVICE=$VENDORDEVICEID
fi
sleep 5
if [$? -e 0]; then
    echo "Flashing succesful!"
else
    echo "Flashing failed :("
    sudo service klipper start
    exit 1
fi
sudo service klipper start