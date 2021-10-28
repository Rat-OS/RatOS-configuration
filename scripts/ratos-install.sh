#!/bin/bash
# This script install additional dependencies
# for the v-core 3 klipper setup.

SYSTEMDDIR="/etc/systemd/system"

report_status()
{
    echo -e "\n\n###### $1"
}

install_printer_config()
{
    report_status "Copying printer configuration"
    PRINTER_CFG = /home/pi/klipper_config/printer.cfg
    tail -n +2 /home/pi/klipper_config/config/templates/v-core-3-printer.template.cfg > $PRINTER_CFG
}

install_udev_rules()
{
    report_status "Installing udev rules"
    sudo ln -s /home/pi/klipper_config/config/boards/*/*.rules /etc/udev/rules.d/
}

install_hooks()
{
    ln -s /home/pi/klipper_config/config/scripts/ratos-post-merge.sh /home/pi/klipper_config/config/.git/hooks/post-merge
    ln -s /home/pi/klipper_config/config/scripts/klipper-post-merge.sh /home/pi/klipper/.git/hooks/post-merge
}

verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
}

# Force script to exit if an error occurs
set -e

verify_ready
install_printer_config
install_udev_rules
install_hooks