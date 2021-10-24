#!/bin/bash
# NOTE: UNTESTED

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

MCU=/dev/btt-skr-2-429
VENDORDEVICEID=0483:df11
cp -f /home/pi/klipper_config/config/boards/btt-skr-2-429/firmware.config /home/pi/klipper/.config
pushd /home/pi/klipper
make olddefconfig
make clean
make
service klipper stop
if [ -h $MCU ]; then
    echo "Flashing SKR 2 via path"
    make flash FLASH_DEVICE=$MCU
else
    echo "Flashing SKR 2 via vendor and device ids - 1st pass"
    make flash FLASH_DEVICE=$VENDORDEVICEID
fi
sleep 5
if [ -h $MCU ]; then
    echo "Flashing Successful!"
else
    echo "Flashing SKR 2 via vendor and device ids - 2nd pass"
    make flash FLASH_DEVICE=$VENDORDEVICEID

    sleep 5
    if [ -h $MCU ]; then
        echo "Flashing Successful!"
    else
        echo "Flashing SKR 2 via vendor and device ids - 3rd pass"
        make flash FLASH_DEVICE=$VENDORDEVICEID
        if [ $? -e 0 ]; then
            echo "Flashing successful!"
        else
            echo "Flashing failed :("
            service klipper start
            popd
            exit 1
        fi
    fi
fi
service klipper start
popd