#!/bin/bash

source /home/pi/printer_data/config/RatOS/scripts/moonraker-ensure-policykit-rules.sh
ensure_moonraker_policiykit_rules

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $SCRIPT_DIR/ratos-common.sh

ensure_service_permission

echo "##### Symlinking registered klippy extensions"
extensions_result=$(curl --fail --silent -X POST 'http://localhost:3000/configure/api/trpc/klippy-extensions.symlink' -H 'content-type: application/json')
extensions_success=$?
if [ $extensions_success -eq 0 ]
then
    echo $extensions_result | jq -r '.result.data.json'
else
    echo "Failed to symlink extensions, ignore this if not on RatOS 2.0 yet"
fi

echo "##### Symlinking moonraker extensions"
symlink_result=$(curl --fail --silent -X POST 'http://localhost:3000/configure/api/trpc/moonraker-extensions.symlink' -H 'content-type: application/json')
configurator_success=$?
if [ $configurator_success -eq 0 ]
then
    echo $symlink_result | jq -r '.result.data.json'
else
    echo "Failed to symlink moonraker extensions. Is the RatOS configurator running? Ignore this if not on RatOS 2.0 yet"
fi
