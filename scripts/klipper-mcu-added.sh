#!/bin/sh
logfile="/var/log/vcore.log"

echo "RESTART" > /tmp/klipper
touch "$logfile"
chmod 664 "$logfile"
echo "$(date +"%Y-%m-%d %T"): MCU Detected" >> "$logfile"
