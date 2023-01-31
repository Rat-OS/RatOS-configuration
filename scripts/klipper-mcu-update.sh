#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "ERROR: This script should be run as root"
  exit
fi

echo "##### Flashing connected MCU's"
flash_result=$(curl --fail --silent -X POST 'http://localhost:3000/configure/api/trpc/mcu.flash-all-connected' -H 'content-type: application/json')
configurator_success=$?
if [ $configurator_success -eq 0 ]
then
    echo $flash_result | jq -r '.result.data.json'
else
    echo "Failed to flash connected MCUs, is the configurator running?"
fi

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
