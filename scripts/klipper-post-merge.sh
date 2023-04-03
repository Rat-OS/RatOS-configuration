#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# shellcheck source=./klipper-mcu-update.sh
sudo "$SCRIPT_DIR"/klipper-mcu-update.sh
