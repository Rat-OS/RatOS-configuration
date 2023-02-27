#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source /home/pi/printer_data/config/RatOS/scripts/ratos-common.sh
source /home/pi/printer_data/config/RatOS/scripts/moonraker-ensure-policykit-rules.sh

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

register_ratos_homing()
{
    EXT_NAME="ratos_homing_extension"
    EXT_PATH=$(realpath $SCRIPT_DIR/../klippy)
    EXT_FILE="ratos_homing.py"
	# Don't error if extension is already registered
    register_klippy_extension $EXT_NAME $EXT_PATH $EXT_FILE "false"
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
ensure_sudo_command_whitelisting
install_hooks
register_ratos_homing
symlink_klippy_extensions
symlink_moonraker_extensions
ensure_service_permission