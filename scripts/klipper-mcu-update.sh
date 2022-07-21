#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: This script should be run as root"
  exit
fi

update_rpi() {
    echo "Updating RPi"
    /home/pi/klipper_config/config/boards/rpi/make-and-flash-mcu.sh
}

update_octopus_pro_446() {
    if [[ -h "/dev/btt-octopus-pro-446" ]]
    then
        echo "Octopus Pro 446 detected"
        /home/pi/klipper_config/config/boards/btt-octopus-pro-446/make-and-flash-mcu.sh
    fi
}

update_octopus_pro_429() {
    if [[ -h "/dev/btt-octopus-pro-429" ]]
    then
        echo "Octopus Pro 429 detected"
        /home/pi/klipper_config/config/boards/btt-octopus-pro-429/make-and-flash-mcu.sh
    fi
}

update_btt_octopus_11() {
    if [[ -h "/dev/btt-octopus-11" ]]
    then
        echo "Octopus v1.1 detected"
        /home/pi/klipper_config/config/boards/btt-octopus-11/make-and-flash-mcu.sh
    fi
}

update_fysetc_spider() {
    if [[ -h "/dev/fysetc-spider" ]]
    then
        echo "Fysetc Spider v1.1 detected"
        /home/pi/klipper_config/config/boards/fysetc-spider/make-and-flash-mcu.sh
    fi
}

update_skr_pro_12() {
    if [[ -h "/dev/btt-skr-pro-12" ]]
    then
        echo "SKR Pro v1.2 detected"
        /home/pi/klipper_config/config/boards/btt-skr-pro-12/make-and-flash-mcu.sh
    fi
}

update_skr_2_429() {
    if [[ -h "/dev/btt-skr-2-429" ]]
    then
        echo "SKR 2 W/ STM32F429 detected"
        /home/pi/klipper_config/config/boards/btt-skr-2-429/make-and-flash-mcu.sh
    fi
}

update_btt_ebb42_11() {
    if [[ -h "/dev/btt-ebb42-11" ]]
    then
        echo "BTT EBB42 v1.1 detected"
        /home/pi/klipper_config/config/boards/btt-skr-2-429/make-and-flash-mcu.sh
    fi
}

update_mellow_fly_sht_42() {
    if [[ -h "/dev/mellow-fly-sht-42" ]]
    then
        echo "Mellow FLY-SHT42 detected"
        /home/pi/klipper_config/config/boards/mellow-fly-sht-42/make-and-flash-mcu.sh
    fi
}

update_btt_skr_mini_e3_30() {
    if [[ -h "/dev/btt-skr-mini-e3-30" ]]
    then
        echo "BTT SKR Mini E3 V3.0 detected"
        /home/pi/klipper_config/config/boards/btt-skr-mini-e3-30/make-and-flash-mcu.sh
    fi
}

# Force script to exit if an error occurs
set -e

# Run make scripts for the supported boards.
update_rpi
update_octopus_pro_446
update_octopus_pro_429
update_btt_octopus_11
update_fysetc_spider
update_skr_pro_12
update_skr_2_429
update_btt_ebb42_11
update_mellow_fly_sht_42
update_btt_skr_mini_e3_30
