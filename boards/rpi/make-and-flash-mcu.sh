#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

pushd /home/pi/klipper
service klipper stop
echo "flashing rpi-mcu"
cp -f /home/pi/klipper_config/config/boards/rpi/firmware.config /home/pi/klipper/.config
make olddefconfig
make clean
make flash

# Reset ownership
chown pi:pi -R /home/pi/klipper

service klipper start
popd