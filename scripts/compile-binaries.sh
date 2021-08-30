# Octopus
cp -f /home/pi/klipper_config/config/boards/btt-octopus-11/firmware.config /home/pi/klipper/.config
cd /home/pi/klipper
make olddefconfig
make clean
make
cp /home/pi/klipper/out/klipper.bin ~/firmware-btt-octopus-11.bin

# SKR Pro
cp -f /home/pi/klipper_config/config/boards/btt-skr-pro-12/firmware.config /home/pi/klipper/.config
cd /home/pi/klipper
make olddefconfig
make clean
make
cp /home/pi/klipper/out/klipper.bin ~/firmware-btt-skr-pro-12.bin

# Spider
cp -f /home/pi/klipper_config/config/boards/fysetc-spider/firmware.config /home/pi/klipper/.config
cd /home/pi/klipper
make olddefconfig
make clean
make
cp /home/pi/klipper/out/klipper.bin ~/firmware-fysetc-spider.bin
