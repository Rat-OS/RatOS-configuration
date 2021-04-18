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


install_mcu_detection_script()
{
# Create systemd service file
    SERVICE_FILE="${SYSTEMDDIR}/vcore3.service"
    [ -f $SERVICE_FILE ] && [ $FORCE_DEFAULTS = "n" ] && return
    report_status "Installing vcore3 mcu detection script..."
    sudo /bin/sh -c "cat > ${SERVICE_FILE}" << EOF
#Systemd service file for the v-core 3 MCU detection script
[Unit]
Description=Automatically detects klipper MCU
After=network.target
Before=moonraker.service

[Service]
ExecStart=/usr/bin/env bash /home/pi/klipper_config/v-core-3/scripts/auto-detect-mcu.sh
WorkingDirectory=/home/pi/klipper_config/v-core-3/scripts
StandardOutput=inherit
StandardError=inherit
Restart=no
User=pi

[Install]
WantedBy=multi-user.target
EOF
# Use systemctl to enable the vcore3 systemd service script
	sudo systemctl enable vcore3.service
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
install_mcu_detection_script