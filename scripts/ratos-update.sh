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

fix_klipperscreen_forcepush()
{
  [ -f /home/pi/.klipperscreenforcepushfixed ] && return
  pushd /home/pi/KlipperScreen
  git fetch
  git merge-base --is-ancestor origin/master master
  if [ $? -ne 0 ]; then
    git reset --hard origin/master~1
    chown -R pi /home/pi/KlipperScreen
    # curl -X GET "http://localhost/machine/update/status?refresh=true"
    # curl -X POST "http://localhost/machine/update/client?name=KlipperScreen"
    touch /home/pi/.klipperscreenforcepushfixed 
  fi
  popd
}

fix_klipperscreen_permissions()
{
  chown -R pi /home/pi/KlipperScreen
}

symlink_klippy_extensions()
{
	report_status "Symlinking klippy extensions"
	symlink_result=$(curl --fail --silent -X POST 'http://localhost:3000/configure/api/trpc/klippy-extensions.symlink' -H 'content-type: application/json')
	configurator_success=$?
	if [ $configurator_success -eq 0 ]
	then
		echo $symlink_result | jq -r '.result.data.json'
	else
		echo "Failed to symlink klippy extensions. Is the RatOS configurator running? Ignore this if not on RatOS 2.0 yet"
	fi
}

symlink_moonraker_extensions()
{
	report_status "Symlinking moonraker extensions"
	symlink_result=$(curl --fail --silent -X POST 'http://localhost:3000/configure/api/trpc/moonraker-extensions.symlink' -H 'content-type: application/json')
	configurator_success=$?
	if [ $configurator_success -eq 0 ]
	then
		echo $symlink_result | jq -r '.result.data.json'
	else
		echo "Failed to symlink moonraker extensions. Is the RatOS configurator running? Ignore this if not on RatOS 2.0 yet"
	fi
}
# Run update symlinks
update_symlinks
ensure_ownership
ensure_sudo_command_whitelisting
install_hooks
ensure_moonraker_policiykit_rules
[ $? -eq 1 ] && echo "Policykit rules have changed. You will have to manually restart moonraker. Power cycling the raspberry pi will also do the trick."
fix_klipperscreen_forcepush
fix_klipperscreen_permissions
symlink_klippy_extensions
symlink_moonraker_extensions
disable_modem_manager
