#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

pushd /home/pi/klipper || exit
service klipper stop

if [ "$(su -c './scripts/flash-sdcard.sh /dev/btt-skr-14 generic-lpc1768' pi)" -eq 0 ]; then
    echo "Flashing successful!"
else
    echo "Flashing failed :("
    service klipper start
    # Reset ownership
    chown pi:pi -R /home/pi/klipper
    popd || exit 1
    exit 1
fi
# Reset ownership
chown pi:pi -R /home/pi/klipper
service klipper start
popd || exit
