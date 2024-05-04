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
  report_status "Restarting configurator..."
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


update_beacon_fw()
{
	report_status "Updating beacon firmware..."
	KLIPPER_DIR="/home/pi/klipper"
	KLIPPER_ENV="/home/pi/klippy-env"
	BEACON_DIR="/home/pi/beacon"
    report_status "Installing beacon module..."

	if [ ! -d "$BEACON_DIR" ] || [ ! -e "$KLIPPER_DIR/klippy/extras/beacon.py" ]; then
		echo "beacon: beacon isn't installed, skipping..."
		return
	fi

	if [ ! -d "$KLIPPER_DIR" ] || [ ! -d "$KLIPPER_ENV" ]; then
		echo "beacon: klipper or klippy env doesn't exist"
		return
	fi

	if [ ! -e "$BEACON_DIR/update-firmware.py" ]; then
		echo "beacon: beacon firmware updater script doesn't exist, skipping..."
		return
	fi
	$KLIPPER_ENV/bin/python $BEACON_DIR/update-firmware.py update all --no-sudo
}

# Run update symlinks
update_symlinks
ensure_sudo_command_whitelisting root
ensure_service_permission
install_beacon
update_beacon_fw
install_hooks
ensure_node_18
patch_klipperscreen_service_restarts
register_z_offset_probe
register_ratos_post_processor
register_rmmu
register_rmmu_hub
register_resonance_generator
symlink_extensions
restart_configurator
