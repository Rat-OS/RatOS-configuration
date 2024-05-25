#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi
<<<<<<<< HEAD:boards/fysetc-spider-22/compile.sh

cp -f /home/pi/printer_data/config/RatOS/boards/fysetc-spider-22/firmware.config /home/pi/klipper/.config
========
cp -f /home/pi/printer_data/config/RatOS/boards/btt-sb-2209-10-rp2040/firmware.config /home/pi/klipper/.config
>>>>>>>> 58371553e9472dd20465e3dbada6dd5427ca7016:boards/btt-sb-2209-10-rp2040/compile.sh
pushd /home/pi/klipper || exit
make olddefconfig
make clean
make

if [ ! -d "/home/pi/printer_data/config/firmware_binaries" ]
then
    mkdir /home/pi/printer_data/config/firmware_binaries
    chown pi:pi /home/pi/printer_data/config/firmware_binaries
fi
<<<<<<<< HEAD:boards/fysetc-spider-22/compile.sh
cp -f /home/pi/klipper/out/klipper.bin /home/pi/printer_data/config/firmware_binaries/firmware-fysetc-spider-22.bin
chown pi:pi /home/pi/printer_data/config/firmware_binaries/firmware-fysetc-spider-22.bin

========
cp -f /home/pi/klipper/out/klipper.bin /home/pi/printer_data/config/firmware_binaries/firmware-btt-sb-2209-10-rp.uf2
chown pi:pi /home/pi/printer_data/config/firmware_binaries/firmware-btt-sb-2209-10-rp.uf2
>>>>>>>> 58371553e9472dd20465e3dbada6dd5427ca7016:boards/btt-sb-2209-10-rp2040/compile.sh
popd || exit
