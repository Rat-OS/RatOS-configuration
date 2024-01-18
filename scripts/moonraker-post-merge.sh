#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "$(realpath -- "${BASH_SOURCE[0]}")" )" &> /dev/null && pwd )
# shellcheck source=./scripts/moonraker-update.sh
sudo "$SCRIPT_DIR"/moonraker-update.sh
