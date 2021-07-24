#!/bin/bash

cp -f /home/pi/klipper_config/config/boards/btt-skr-pro-12/firmware.config /home/pi/klipper/.config
cd /home/pi/klipper
make olddefconfig
make clean
make
sudo service klipper stop
./scripts/flash-sdcard.sh /dev/klipper btt-skr-pro-v1.2
if [$? -e 0]; then
    echo "Flashing succesful!"
else
    echo "Flashing failed :("
    sudo service klipper start
    exit 1
fi
sudo service klipper start