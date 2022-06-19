#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

$SCRIPT_DIR/compile.sh

echo "The SKR 2 cannot currently be flashed via DFU. The file firmware-btt-skr-2-429.bin has been compiled and is available in the firmware_binaries folder in Mainsail under the Machine tab. Use this to flash via SD Card."
echo "NOTE: Remember to rename the file to firmware.bin on the SD Card!"
