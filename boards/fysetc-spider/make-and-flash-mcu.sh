#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

VENDORDEVICEID=0483:df11
MCU=/dev/fysetc-spider
cp -f /home/pi/klipper_config/config/boards/fysetc-spider/firmware.config /home/pi/klipper/.config
pushd /home/pi/klipper
make olddefconfig
make clean
make

if [ ! -d "/home/pi/klipper_config/firmware_binaries" ]
then
    mkdir /home/pi/klipper_config/firmware_binaries
    chown pi:pi /home/pi/klipper_config/firmware_binaries
fi
cp -f /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-fysetc-spider.bin

service klipper stop
if [ -e $MCU ]; then
    echo "Flashing Spider via path"
    make flash FLASH_DEVICE=$MCU
    tstat=$?
else
    echo "No USB connection found, trying DFU id"
    make flash FLASH_DEVICE=$VENDORDEVICEID
    tstat=$?
fi
sleep 5
if [ "$tstat" -eq 0 ]; then
    echo "Flashing successful!"
else
    echo "Flashing failed trying again"
    if [ -e $MCU ]; then
        echo "Flashing Spider via path"
        make flash FLASH_DEVICE=$MCU
        secondtstat=$?
    else
        echo "No USB connection found, trying DFU id"
        make flash FLASH_DEVICE=$VENDORDEVICEID
        secondtstat=$?
    fi

    if [ "$secondtstat" -eq 0 ]; then
        echo "Flashing successful!"
    else
        service klipper start
        popd
        exit 1
    fi
fi
# Reset ownership
chown pi:pi -R /home/pi/klipper
service klipper start
popd