#!/bin/bash

NEWY = ${ls -Art /tmp/resonances_y_*.csv | tail -n 1}
if [ ! -d "/home/pi/klipper_config/input_shaper" ]
then
    mkdir /home/pi/klipper_config/input_shaper
    chown pi:pi /home/pi/klipper_config/input_shaper
fi

~/klipper/scripts/calibrate_shaper.py ${NEWY} -o /home/pi/klipper_config/resonances_y_${date + '%Y-%m-%d-%H%M%S'}.png