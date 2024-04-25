#!/bin/bash
# This script install additional dependencies
# for the v-core 3 klipper setup.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# shellcheck source=./scripts/ratos-common.sh
source "$SCRIPT_DIR"/ratos-common.sh

verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit 1
    fi
}

symlink_extensions()
{
	report_status "Symlinking klippy extensions"
	ratos extensions symlink
	configurator_success=$?
	if [ ! $configurator_success -eq 0 ]
	then
		echo "Failed to symlink klippy extensions. Is the RatOS configurator running?"
		exit 1
	fi
}

# Force script to exit if an error occurs
set -xe

verify_ready
disable_modem_manager
patch_klipperscreen_service_restarts
symlink_extensions
