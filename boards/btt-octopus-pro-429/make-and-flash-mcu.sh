#!/bin/bash
# NOTE: This script ONLY WORKS if there's no SD card in the board AND the 
# board has already been flashed with klipper via SD card.
# NEXT SECTION IS ONLY RELEVANT IF USING THE boot0 JUMPER (NOT RECOMMENDED)
# The first time the board is booted after the jumper has been installed
# the board needs to be flashed via the dfu vendor:device id. After that
# it can be flashed via the /dev/btt-octopus-pro-429 path, but it then fails
# to exit dfu mode, and then one needs to flash it yet again with the
# vendor:device id. Then it correctly exits DFU mode. Except those times
# where it doesn't, for that we have a 3rd pass...

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  exit
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

$SCRIPT_DIR/compile.sh

echo "Unfortunately, unlike the Octopus Pro 446, the Octopus Pro 429 cannot currently be flashed via DFU. The file firmware-btt-octopus-pro-429.bin has been compiled and is available in the firmware_binaries folder in Mainsail under the Machine tab. Use this to flash via SD Card." 
echo "NOTE: Remember to rename the file to firmware.bin on the SD Card!"
