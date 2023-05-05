#!/bin/bash

pushd /home/pi/klipper
service klipper stop
make flash
# Reset ownership
chown pi:pi -R /home/pi/klipper

service klipper start
popd
