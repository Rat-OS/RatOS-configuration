#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

source /home/pi/klipper_config/config/scripts/ratos-common.sh
source /home/pi/klipper_config/config/scripts/moonraker-ensure-policykit-rules.sh

ensure_ownership() {
  chown pi:pi -R /home/pi/klipper
  chown pi:pi -R /home/pi/klipper_config
  chown pi:pi -R /home/pi/.KlipperScreen-env
}

update_symlinks()
{
  echo "Updating RatOS device symlinks.."
  rm /etc/udev/rules.d/98-*.rules
  ln -s /home/pi/klipper_config/config/boards/*/*.rules /etc/udev/rules.d/
}

restart_klipper()
{
  service klipper restart
}

# Force script to exit if an error occurs
set -e

# Run update symlinks
update_symlinks
ensure_ownership
ensure_sudo_command_whitelisting
install_hooks
ensure_moonraker_policiykit_rules
restart_klipper
