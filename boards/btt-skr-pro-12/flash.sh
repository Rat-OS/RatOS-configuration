#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

pushd /home/pi/klipper || exit
service klipper stop

if su -c "./scripts/flash-sdcard.sh /dev/btt-skr-pro-12 btt-skr-pro-v1.2" pi -eq 0; then
    echo "Flashing successful!"
else
    echo "Flashing failed :("
    service klipper start
    popd || exit
    # Reset ownership
    chown pi:pi -R /home/pi/klipper
    exit 1
fi
# Reset ownership
chown pi:pi -R /home/pi/klipper
service klipper start
popd || exit
