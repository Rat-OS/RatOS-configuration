#!/bin/bash

cp -f /home/pi/klipper_config/config/boards/mellow-super-infinity/firmware.config /home/pi/klipper/.config
cd /home/pi/klipper
make olddefconfig
make clean
make
sudo service klipper stop
./scripts/flash-sdcard.sh /dev/mellow-super-infinity mellow-super-infinity-v1.0
if [ $? -eq 0 ]; then
    echo "Flashing successful!"
else
    echo "Flashing failed :("
    sudo service klipper start
    exit 1
fi
sudo service klipper start
