#!/bin/bash
# This script install additional dependencies
# for the v-core 3 klipper setup.

SYSTEMDDIR="/etc/systemd/system"

report_status()
{
    echo -e "\n\n###### $1"
}

install_numpy()
{
    report_status "Installing numpy and related packages..."
    KLIPPER_PYTHON_DIR="${HOME}/klippy-env"
    ${KLIPPER_PYTHON_DIR}/bin/pip install -v numpy
    sudo apt-get update
    sudo apt-get install --yes python-numpy python-matplotlib
}

install_printer_config()
{
    report_status "Copying printer configuration"
    cp /home/pi/klipper_config/RatOS/templates/v-core-3-printer.template.cfg /home/pi/klipper_config/printer.cfg
}

install_udev_rules()
{
    report_status "Installing udev rules"
    sudo ln -s /home/pi/klipper_config/v-core-3/boards/*/*.rules /etc/udev/rules.d/
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
install_numpy