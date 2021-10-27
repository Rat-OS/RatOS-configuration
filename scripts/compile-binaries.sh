#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

compile_octopus_pro_446() {
    cp -f /home/pi/klipper_config/config/boards/btt-octopus-pro-446/firmware.config /home/pi/klipper/.config
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-octopus-pro-446.bin
}

compile_octopus_pro_429() {
    cp -f /home/pi/klipper_config/config/boards/btt-octopus-pro-429/firmware.config /home/pi/klipper/.config
    pushd /home/pi/klipper
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-octopus-pro-429.bin
}

compile_btt_octopus_11() {
    cp -f /home/pi/klipper_config/config/boards/btt-octopus-11/firmware.config /home/pi/klipper/.config
    pushd /home/pi/klipper
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-octopus-11.bin
}

compile_fysetc_spider() {
    cp -f /home/pi/klipper_config/config/boards/fysetc-spider/firmware.config /home/pi/klipper/.config
    pushd /home/pi/klipper
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-fysetc-spider.bin
}

compile_skr_pro_12() {
    cp -f /home/pi/klipper_config/config/boards/btt-skr-pro-12/firmware.config /home/pi/klipper/.config
    pushd /home/pi/klipper
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-skr-pro-12.bin
}

compile_skr_2_429() {
    cp -f /home/pi/klipper_config/config/boards/btt-skr-2-429/firmware.config /home/pi/klipper/.config
    pushd /home/pi/klipper
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-skr-2-429.bin
}

# Force script to exit if an error occurs
set -e

if [ ! -d "/home/pi/klipper_config/firmware_binaries" ]
then
    mkdir /home/pi/klipper_config/firmware_binaries
    chown pi:pi /home/pi/klipper_config/firmware_binaries
fi


pushd /home/pi/klipper

# Run make scripts for the supported boards.
compile_octopus_pro_446
compile_octopus_pro_429
compile_btt_octopus_11
compile_fysetc_spider
compile_skr_pro_12
compile_skr_2_429

popd