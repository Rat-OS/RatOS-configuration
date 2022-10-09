#!/bin/bash
# NOTE: This script ONLY WORKS if there's no SD card in the board AND the 
# board has already been flashed with klipper via SD card.
# NEXT SECTION IS ONLY RELEVANT IF USING THE boot0 JUMPER (NOT RECOMMENDED)
# The first time the board is booted after the jumper has been installed
# the board needs to be flashed via the dfu vendor:device id. After that
# it can be flashed via the /dev/btt-manta-m8p path, but it then fails
# to exit dfu mode, and then one needs to flash it yet again with the
# vendor:device id. Then it correctly exits DFU mode. Except those times
# where it doesn't, for that we have a 3rd pass...

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

MCU=/dev/btt-manta-m8p
VENDORDEVICEID=0483:df11
cp -f /home/pi/klipper_config/config/boards/btt-manta-m8p/firmware.config /home/pi/klipper/.config
pushd /home/pi/klipper
make olddefconfig
make clean
make

if [ ! -d "/home/pi/klipper_config/firmware_binaries" ]
then
    mkdir /home/pi/klipper_config/firmware_binaries
    chown pi:pi /home/pi/klipper_config/firmware_binaries
fi
cp -f /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-manta-m8p.bin
chown pi:pi /home/pi/klipper_config/firmware_binaries/firmware-btt-manta-m8p.bin

# Reset ownership
chown pi:pi -R /home/pi/klipper

# echo "Unfortunately, unlike the Manta M8P cannot currently be flashed via DFU. The file firmware-btt-manta-m8p.bin has been compiled and is available in the firmware_binaries folder in Mainsail under the Machine tab. Use this to flash via SD Card." 
# echo "NOTE: Remember to rename the file to firmware.bin on the SD Card!"

service klipper stop
if [ -h $MCU ]; then
    echo "Flashing Manta M8P via path"
    make flash FLASH_DEVICE=$MCU
else
    echo "Flashing Manta M8P via vendor and device ids - 1st pass"
    make flash FLASH_DEVICE=$VENDORDEVICEID
fi
sleep 5
if [ -h $MCU ]; then
    echo "Flashing Successful!"
else
    echo "Flashing Manta M8P via vendor and device ids - 2nd pass"
    make flash FLASH_DEVICE=$VENDORDEVICEID

    sleep 5
    if [ -h $MCU ]; then
        echo "Flashing Successful!"
    else
        echo "Flashing Manta M8P via vendor and device ids - 3rd pass"
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
