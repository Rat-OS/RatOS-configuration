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
install_numpy