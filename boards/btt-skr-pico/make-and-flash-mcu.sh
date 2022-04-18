#!/bin/bash

#TODO: How to have USB and GPIO configs

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

cp -f /home/pi/klipper_config/config/boards/btt-skr-pico/firmware.config /home/pi/klipper/.config
pushd /home/pi/klipper
make olddefconfig
make clean
make

if [ ! -d "/home/pi/klipper_config/firmware_binaries" ]
then
    mkdir /home/pi/klipper_config/firmware_binaries
    chown pi:pi /home/pi/klipper_config/firmware_binaries
fi
cp -f /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-skr-pico.bin
chown pi:pi /home/pi/klipper_config/firmware_binaries/firmware-btt-skr-pico.bin

# TODO: We can build for pico, need workout how to copy.
exit

#service klipper stop
#su -c "./scripts/flash-sdcard.sh /dev/btt-skr-pro-12 btt-skr-pro-v1.2" pi
#if [ $? -eq 0 ]; then
#    echo "Flashing successful!"
#else
#    echo "Flashing failed :("
#    service klipper start
#    popd
    # Reset ownership
#    chown pi:pi -R /home/pi/klipper
#    exit 1
#fi
# Reset ownership
#chown pi:pi -R /home/pi/klipper
#service klipper start
#popd
