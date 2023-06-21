#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

cp -f /home/pi/printer_data/config/RatOS/boards/btt-skr-14-turbo/firmware.config /home/pi/klipper/.config
pushd /home/pi/klipper || exit
make olddefconfig
make clean
make

if [ ! -d "/home/pi/printer_data/config/firmware_binaries" ]
then
    mkdir /home/pi/printer_data/config/firmware_binaries
    chown pi:pi /home/pi/printer_data/config/firmware_binaries
fi
cp -f /home/pi/klipper/out/klipper.bin /home/pi/printer_data/config/firmware_binaries/firmware-btt-skr-14-turbo.bin
chown pi:pi /home/pi/printer_data/config/firmware_binaries/firmware-btt-skr-14-turbo.bin

service klipper stop
if su -c "./scripts/flash-sdcard.sh /dev/btt-skr-14-turbo generic-lpc1769" pi -eq 0; then
    echo "Flashing successful!"
else
    echo "Flashing failed :("
    service klipper start
    popd || exit
    # Reset ownership
    chown pi:pi -R /home/pi/klipper
    exit 1
fi
# Reset ownership
chown pi:pi -R /home/pi/klipper
service klipper start
popd || exit
