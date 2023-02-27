#!/bin/bash

source /home/pi/printer_data/config/RatOS/scripts/moonraker-ensure-policykit-rules.sh
ensure_moonraker_policiykit_rules

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $SCRIPT_DIR/ratos-common.sh

ensure_service_permission
