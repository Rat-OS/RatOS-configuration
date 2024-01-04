#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: This script should be run as root"
  exit
fi

echo "##### Flashing connected MCU's"
ratos flash

echo "##### Symlinking registered extensions"
ratos extensions symlink klipper