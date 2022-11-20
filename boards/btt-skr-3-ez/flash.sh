#!/bin/bash

MCU=/dev/btt-skr-3-ez
if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
FLASH_SCRIPT=$(realpath "$SCRIPT_DIR/../../scripts/flash-path.sh")
$FLASH_SCRIPT $MCU
