#!/bin/bash

NEWX=$(find /tmp -name "resonances_x_*.csv" -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")
DATE=$(date +'%Y-%m-%d-%H%M%S')
if [ ! -d "/home/pi/printer_data/config/input_shaper" ]
then
    mkdir /home/pi/printer_data/config/input_shaper
    chown pi:pi /home/pi/printer_data/config/input_shaper
fi

~/klipper/scripts/calibrate_shaper.py "$NEWX" -o /home/pi/printer_data/config/input_shaper/resonances_x_"$DATE".png
