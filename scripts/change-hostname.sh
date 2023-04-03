#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
sudo "$SCRIPT_DIR"/change-hostname-as-root.sh "$1"
