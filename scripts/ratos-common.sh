report_status()
{
    echo -e "\n\n###### $1"
}


install_hooks()
{
    report_status "Installing git hooks"
	if [[ ! -e /home/pi/klipper_config/config/.git/hooks/post-merge ]]
	then
 	   ln -s /home/pi/klipper_config/config/scripts/ratos-post-merge.sh /home/pi/klipper_config/config/.git/hooks/post-merge
	fi
	if [[ ! -e /home/pi/klipper/.git/hooks/post-merge ]]
	then
 	   ln -s /home/pi/klipper_config/config/scripts/klipper-post-merge.sh /home/pi/klipper/.git/hooks/post-merge
	fi
	if [[ ! -e /home/pi/moonraker/.git/hooks/post-merge ]]
	then
 	   ln -s /home/pi/klipper_config/config/scripts/moonraker-post-merge.sh /home/pi/moonraker/.git/hooks/post-merge
	fi
}

ensure_sudo_command_whitelisting()
{
	sudo="sudo"
	if [ "$1" = "root" ]
	then
		sudo=""
	fi
    report_status "Updating whitelisted commands"
	# Whitelist RatOS git hook scripts
	if [[ -e /etc/sudoers.d/030-ratos-githooks ]]
	then
		$sudo rm /etc/sudoers.d/030-ratos-githooks
	fi
	touch /tmp/030-ratos-githooks
	cat << '#EOF' > /tmp/030-ratos-githooks
pi  ALL=(ALL) NOPASSWD: /home/pi/klipper_config/config/scripts/ratos-update.sh
pi  ALL=(ALL) NOPASSWD: /home/pi/klipper_config/config/scripts/klipper-mcu-update.sh
pi  ALL=(ALL) NOPASSWD: /home/pi/klipper_config/config/scripts/moonraker-update.sh
#EOF

	$sudo chown root:root /tmp/030-ratos-githooks
	$sudo chmod 440 /tmp/030-ratos-githooks
	$sudo cp --preserve=mode /tmp/030-ratos-githooks /etc/sudoers.d/030-ratos-githooks

	# Whitelist change hostname script
	if [[ ! -e /etc/sudoers.d/031-ratos-change-hostname ]]
	then
		touch /tmp/031-ratos-change-hostname
		cat << '#EOF' > /tmp/031-ratos-change-hostname
pi  ALL=(ALL) NOPASSWD: /home/pi/klipper_config/config/scripts/change-hostname-as-root.sh
#EOF

		$sudo chown root:root /tmp/031-ratos-change-hostname
		$sudo chmod 440 /tmp/031-ratos-change-hostname
		$sudo cp --preserve=mode /tmp/031-ratos-change-hostname /etc/sudoers.d/031-ratos-change-hostname
	fi
}
