#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# shellcheck source=./scripts/ratos-common.sh
source "$SCRIPT_DIR"/ratos-common.sh
# shellcheck source=./scripts/moonraker-ensure-policykit-rules.sh
source "$SCRIPT_DIR"/moonraker-ensure-policykit-rules.sh

update_symlinks()
{
  echo "Updating RatOS device symlinks.."
  rm /etc/udev/rules.d/98-*.rules
  ln -s /home/pi/printer_data/config/RatOS/boards/*/*.rules /etc/udev/rules.d/
}

ensure_node_18()
{
	node -v | grep "^v18" > /dev/null
	isinstalled=$?
	if [ $isinstalled -eq 0 ]
	then
		echo "Node 18 already installed"
	else
		echo "Installing Node 18"
		sed -i 's/node_16\.x/node_18\.x/g' /etc/apt/sources.list.d/nodesource.list
		apt-get update
		apt-get install -y nodejs
	fi
}

restart_configurator()
{
  systemctl restart ratos-configurator
}

symlink_extensions()
{
	report_status "Symlinking klippy extensions"
	ratos extensions symlink
	configurator_success=$?
	if [ ! $configurator_success -eq 0 ]
	then
		echo "Failed to symlink klippy extensions. Is the RatOS configurator running?"
		exit 1
	fi
}
# Run update symlinks
update_symlinks
ensure_sudo_command_whitelisting root
ensure_service_permission
install_beacon
install_hooks
ensure_node_18
register_ratos_homing
symlink_extensions
# regenerate_config # moonraker now restarts the configurator which results in a regen