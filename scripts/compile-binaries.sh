#!/bin/bash

compile_octopus_pro_446() {
    echo "Compiling firmware for BTT Octopus Pro 446"
    cp -f /home/pi/klipper_config/config/boards/btt-octopus-pro-446/firmware.config /home/pi/klipper/.config
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-octopus-pro-446.bin
}

compile_octopus_pro_429() {
    echo "Compiling firmware for BTT Octopus Pro 429"
    cp -f /home/pi/klipper_config/config/boards/btt-octopus-pro-429/firmware.config /home/pi/klipper/.config
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-octopus-pro-429.bin
}

compile_btt_octopus_11() {
    echo "Compiling firmware for BTT Octopus v1.1"
    cp -f /home/pi/klipper_config/config/boards/btt-octopus-11/firmware.config /home/pi/klipper/.config
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-octopus-11.bin
}

compile_btt_octopus_11_407() {
    echo "Compiling firmware for BTT Octopus v1.1"
    cp -f /home/pi/klipper_config/config/boards/btt-octopus-11-407/firmware.config /home/pi/klipper/.config
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-octopus-11-407.bin
}

compile_fysetc_spider() {
    echo "Compiling firmware for Fysetc Spider v1.1"
    cp -f /home/pi/klipper_config/config/boards/fysetc-spider/firmware.config /home/pi/klipper/.config
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-fysetc-spider.bin
}

compile_skr_pro_12() {
    echo "Compiling firmware for SKR Pro 1.2"
    cp -f /home/pi/klipper_config/config/boards/btt-skr-pro-12/firmware.config /home/pi/klipper/.config
    make olddefconfig
    make clean
    make
    cp /home/pi/klipper/out/klipper.bin /home/pi/klipper_config/firmware_binaries/firmware-btt-skr-pro-12.bin
}

compile_skr_2_429() {
    echo "Compiling firmware for SKR 2 429"
    cp -f /home/pi/klipper_config/config/boards/btt-skr-2-429/firmware.config /home/pi/klipper/.config
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
compile_btt_octopus_11_407
compile_fysetc_spider
compile_skr_pro_12
compile_skr_2_429
chown pi:pi /home/pi/klipper_config/firmware_binaries/*.bin

popd
