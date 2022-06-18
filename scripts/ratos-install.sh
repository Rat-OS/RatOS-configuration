#!/bin/bash
# This script install additional dependencies
# for the v-core 3 klipper setup.

SYSTEMDDIR="/etc/systemd/system"
PKGLIST="python3-numpy python3-matplotlib"

source /home/pi/klipper_config/config/scripts/ratos-common.sh

install_dependencies()
{
    report_status "Installing RatOS dependencies"
    sudo apt-get update && sudo apt-get install -y $PKGLIST
}

install_printer_config()
{
    report_status "Copying printer configuration"
    PRINTER_CFG="/home/pi/klipper_config/printer.cfg"
    tail -n +2 /home/pi/klipper_config/config/templates/initial-printer.template.cfg > $PRINTER_CFG
}

install_udev_rules()
{
    report_status "Installing udev rules"
    sudo ln -s /home/pi/klipper_config/config/boards/*/*.rules /etc/udev/rules.d/
}
compile_binaries()
{
    report_status "Compiling firmware binaries"
    sudo /home/pi/klipper_config/config/scripts/compile-binaries.sh
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
install_dependencies
ensure_sudo_command_whitelisting
compile_binaries
