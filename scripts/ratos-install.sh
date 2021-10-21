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
    cp -f /home/pi/klipper_config/config/templates/v-core-3-printer.template.cfg /home/pi/klipper_config/printer.cfg
}

install_udev_rules()
{
    report_status "Installing udev rules"
    sudo ln -s /home/pi/klipper_config/config/boards/*/*.rules /etc/udev/rules.d/
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