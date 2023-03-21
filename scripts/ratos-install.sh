#!/bin/bash
# This script install additional dependencies
# for the v-core 3 klipper setup.

SYSTEMDDIR="/etc/systemd/system"
PKGLIST="python3-numpy python3-matplotlib jq curl"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $SCRIPT_DIR/ratos-common.sh

install_dependencies()
{
    report_status "Installing RatOS dependencies"
    sudo apt-get update && sudo apt-get install -y $PKGLIST
}

install_printer_config()
{
    report_status "Copying printer configuration"
    PRINTER_CFG="/home/pi/printer_data/config/printer.cfg"
    tail -n +2 /home/pi/printer_data/config/RatOS/templates/initial-printer.template.cfg > $PRINTER_CFG
}

install_udev_rules()
{
    report_status "Installing udev rules"
    sudo ln -s /home/pi/printer_data/config/RatOS/boards/*/*.rules /etc/udev/rules.d/
}

verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
}

# Force script to exit if an error occurs
set -xe

verify_ready
install_printer_config
install_udev_rules
install_hooks
install_dependencies
ensure_sudo_command_whitelisting
register_gcode_shell_command
register_ratos_homing