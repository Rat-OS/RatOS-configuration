#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "##### Running beacon firmware update script"
# shellcheck source=./scripts/ratos-common.sh
source "$SCRIPT_DIR"/ratos-common.sh
update_beacon_fw