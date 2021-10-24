#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

MCU=/dev/fysetc-spider
cp -f /home/pi/klipper_config/config/boards/fysetc-spider/firmware.config /home/pi/klipper/.config
pushd /home/pi/klipper
make olddefconfig
make clean
make
service klipper stop
if [ -e $MCU ]; then
    echo "Flashing Spider via path"
    make flash FLASH_DEVICE=$MCU
    tstat=$?
else
    echo "No USB connection found"
    service klipper start
    popd
    exit 1
fi
sleep 5
if [ "$tstat" -eq 0 ]; then
    echo "Flashing successful!"
else
    echo "Flashing failed :("
    service klipper start
    popd
    exit 1
fi
service klipper start
popd