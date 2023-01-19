#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

source /home/pi/printer_data/config/RatOS/scripts/ratos-common.sh
source /home/pi/printer_data/config/RatOS/scripts/moonraker-ensure-policykit-rules.sh

ensure_ownership() {
  chown pi:pi -R /home/pi/klipper
  chown pi:pi -R /home/pi/klipper_config
  chown pi:pi -R /home/pi/.KlipperScreen-env
}

update_symlinks()
{
  echo "Updating RatOS device symlinks.."
  rm /etc/udev/rules.d/98-*.rules
  ln -s /home/pi/printer_data/config/RatOS/boards/*/*.rules /etc/udev/rules.d/
}

restart_klipper()
{
  service klipper restart
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
symlink_klippy_extensions
symlink_moonraker_extensions
