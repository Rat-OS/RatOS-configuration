#!/bin/bash

pushd /home/pi/klipper || exit
systemctl stop klipper
make flash
# Reset ownership
chown pi:pi -R /home/pi/klipper

systemctl start klipper
systemctl restart klipper_mcu
popd || exit
