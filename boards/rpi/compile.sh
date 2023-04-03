#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

pushd /home/pi/klipper || exit
echo "flashing rpi-mcu"
cp -f /home/pi/printer_data/config/RatOS/boards/rpi/firmware.config /home/pi/klipper/.config
make olddefconfig
make clean
# Reset ownership
chown pi:pi -R /home/pi/klipper
popd || exit
