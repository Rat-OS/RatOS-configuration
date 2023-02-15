#!/bin/bash

tail -n +2 /home/pi/printer_data/config/RatOS/templates/voron-v24-printer.template.cfg > /home/pi/printer_data/config/printer.cfg

#on rasbian get the board name
function get_sbc  {
    cat /etc/board-release | grep BOARD_NAME | cut -d '=' -f2 | cut -d '"' -f2
}

#change the mainsail interface to use the correct board name
if [ -e /etc/board-release ]
then
  git -C /home/pi/printer_data/config/RatOS update-index --assume-unchanged /home/pi/printer_data/config/RatOS/printers/sbc.cfg
  sed -i s"/raspberry_pi/$(get_sbc)/g" /home/pi/printer_data/config/RatOS/printers/sbc.cfg
fi