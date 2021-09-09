#!/bin/bash

MCU=/dev/fysetc-spider
cp -f /home/pi/klipper_config/config/boards/fysetc-spider/firmware.config /home/pi/klipper/.config
cd /home/pi/klipper
make olddefconfig
make clean
make
sudo service klipper stop
if [ -e $MCU ]; then
    echo "Flashing Spider via path"
    make flash FLASH_DEVICE=$MCU
    tstat=$?
else
    echo "No USB connection found"
    sudo service klipper start
    exit 1
fi
sleep 5
if [ "$tstat" -eq 0 ]; then
    echo "Flashing successful!"
else
    echo "Flashing failed :("
    sudo service klipper start
    exit 1
fi
sudo service klipper start
