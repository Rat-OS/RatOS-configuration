#!/bin/bash
if [ -d "/home/pi/printer_data" ]; then
  echo "Deleting printer data config, database, gcodes and logs directories.."
  rm -rf /home/pi/printer_data/config
  rm -rf /home/pi/printer_data/database
  rm -rf /home/pi/printer_data/gcodes
  rm -rf /home/pi/printer_data/logs
else
  mkdir /home/pi/printer_data
fi

echo "Restoring printer data config, database, gcodes and logs directories.."
ln -s /home/pi/klipper_config /home/pi/printer_data/config
ln -s /home/pi/.moonraker_database /home/pi/printer_data/database
ln -s /home/pi/gcode_files /home/pi/printer_data/gcodes
ln -s /home/pi/klipper_logs /home/pi/printer_data/logs
