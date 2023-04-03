#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
NEWX=$(find /tmp -name "resonances_x_*.csv" -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")
DATE=$(date +'%Y-%m-%d-%H%M%S')
if [ ! -d "$SCRIPT_DIR/../../input_shaper" ]
then
    mkdir "$SCRIPT_DIR"/../../input_shaper
    chown pi:pi "$SCRIPT_DIR"/../../input_shaper
fi

~/klipper/scripts/calibrate_shaper.py "$NEWX" -o "$SCRIPT_DIR"/../../input_shaper/resonances_x_"$DATE".png
