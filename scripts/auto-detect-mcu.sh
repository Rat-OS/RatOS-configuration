#!/usr/bin/env bash
CONFIG_PATH="/home/pi/klipper_config/v-core-3/mcu-detection.cfg"

id="$(ls /dev/serial/by-id/usb-Klipper_* | head -n1)"

# Make sure the file exists so there's no include error in klipper.
touch "$CONFIG_PATH"

if [[ -z "$id" ]]; then
    echo "$(date +"%Y-%m-%d %T"): MCU Detection Error: Cannot detect Klipper device" >> /tmp/klippy.log
    exit 1
fi

echo -e "[mcu]\nserial: $id" > "$CONFIG_PATH"
