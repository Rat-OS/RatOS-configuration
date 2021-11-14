#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

ensure_ownership() {
  chown pi:pi -R /home/pi/klipper
  chown pi:pi -R /home/pi/klipper_config
}

update_symlinks()
{
    echo "Updating RatOS device symlinks.."
    rm /etc/udev/rules.d/98-*.rules
    ln -s /home/pi/klipper_config/config/boards/*/*.rules /etc/udev/rules.d/
}

# Force script to exit if an error occurs
set -e

# Run update symlinks
update_symlinks
ensure_ownership
