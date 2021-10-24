#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

cp -f /home/pi/klipper_config/config/boards/btt-skr-pro-12/firmware.config /home/pi/klipper/.config
pushd /home/pi/klipper
make olddefconfig
make clean
make
service klipper stop
./scripts/flash-sdcard.sh /dev/btt-skr-pro-12 btt-skr-pro-v1.2
if [ $? -eq 0 ]; then
    echo "Flashing successful!"
else
    echo "Flashing failed :("
    service klipper start
    popd
    exit 1
fi
service klipper start
popd