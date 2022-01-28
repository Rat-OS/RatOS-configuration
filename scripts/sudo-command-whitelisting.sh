#!/bin/bash
ensure_sudo_command_whitelisting()
{
	# Whitelist RatOS git hook scripts
	if [[ ! -e /etc/sudoers.d/030-ratos-githooks ]]
	then
		touch /tmp/030-ratos-githooks
		cat << '#EOF' > /tmp/030-ratos-githooks
pi  ALL=(ALL) NOPASSWD: /home/pi/klipper_config/config/scripts/ratos-update.sh
pi  ALL=(ALL) NOPASSWD: /home/pi/klipper_config/config/scripts/klipper-mcu-update.sh
#EOF

		sudo chown root:root /tmp/030-ratos-githooks
		sudo chmod 440 /tmp/030-ratos-githooks
		sudo cp --preserve=mode /tmp/030-ratos-githooks /etc/sudoers.d/030-ratos-githooks
	fi

	# Whitelist change hostname script
	if [[ ! -e /etc/sudoers.d/031-ratos-change-hostname ]]
	then
		touch /tmp/031-ratos-change-hostname
		cat << '#EOF' > /tmp/031-ratos-change-hostname
pi  ALL=(ALL) NOPASSWD: /home/pi/klipper_config/config/scripts/change-hostname-as-root.sh
#EOF

		sudo chown root:root /tmp/031-ratos-change-hostname
		sudo chmod 440 /tmp/031-ratos-change-hostname
		sudo cp --preserve=mode /tmp/031-ratos-change-hostname /etc/sudoers.d/031-ratos-change-hostname
	fi
}
