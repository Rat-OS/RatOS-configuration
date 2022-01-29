#!/bin/bash

POLKIT_LEGACY_DIR="/etc/polkit-1/localauthority/50-local.d"
POLKIT_DIR="/etc/polkit-1/rules.d"
POLKIT_USR_DIR="/usr/share/polkit-1/rules.d"
MOONRAKER_UNIT="/etc/systemd/system/moonraker.service"

ensure_moonraker_policiykit_rules() {
	if [[ -e ${POLKIT_USR_DIR}/moonraker.rules ]]
	then
		echo -e "\n\n###### Moonraker policy exists, skipping policykit script."
		return
	fi
	if [[ -e ${POLKIT_DIR}/moonraker.rules ]]
	then
		echo -e "\n\n###### Moonraker policy exists, skipping policykit script."
		return
	fi
	if [[ -e ${POLKIT_LEGACY_DIR}/10-moonraker.pkla ]]
	then
		echo -e "\n\n###### Moonraker legacy policy exists, skipping policykit script."
		return
	fi
	if [[ -e /home/pi/moonraker/scripts/set-policykit-rules.sh ]]
	then
		echo -e "\n\n###### Moonraker policy not found, running moonraker policykit script..."
		if [ "$EUID" -eq 0 ]; then
			# This feels wrong, but...
			OLDUSER=$USER
			USER=pi
			/home/pi/moonraker/scripts/set-policykit-rules.sh
			USER=$OLDUSER
		else
			/home/pi/moonraker/scripts/set-policykit-rules.sh
		fi
	fi
}