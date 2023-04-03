#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# shellcheck source=./ratos-update.sh
sudo "$SCRIPT_DIR"/ratos-update.sh
