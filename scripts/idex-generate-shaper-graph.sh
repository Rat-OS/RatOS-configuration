#!/bin/bash

DISABLE_Y=0
DISABLE_X=0

if [ "$1" = "x" ]
then
	DISABLE_Y=1
fi
if [ "$1" = "y" ]
then
	DISABLE_X=1
fi

if [ ! -d "/home/pi/printer_data/config/input_shaper" ]
then
    mkdir /home/pi/printer_data/config/input_shaper
fi

T0=1
T1=1
IDEX=0

if [ "$2" == "0" ]
then
	T1=0
fi
if [ "$2" == "1" ]
then
	T0=0
fi
if [ "$3" == "1" ]
then
	IDEX=1
fi
if [ "$3" == "2" ]
then
	IDEX=2
fi

DATE=$(date +'%Y-%m-%d-%H%M%S')
if [ $DISABLE_Y -eq 0 ]
then
	[ -e "/tmp/t0_y.csv" ] && rm /tmp/t0_y.csv
	[ -e "/tmp/t1_y.csv" ] && rm /tmp/t1_y.csv
	[ -e "/tmp/t0_copy_y.csv" ] && rm /tmp/t0_copy_y.csv
	[ -e "/tmp/t1_copy_y.csv" ] && rm /tmp/t1_copy_y.csv
	[ -e "/tmp/t0_mirror_y.csv" ] && rm /tmp/t0_mirror_y.csv
	[ -e "/tmp/t1_mirror_y.csv" ] && rm /tmp/t1_mirror_y.csv

	if [ $IDEX -eq 0 ]
	then
		if [ $T0 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_y_"$4"_"$5"_"$6"_t0.csv" ]
			then
				echo "ERROR: No y data found for T0"
				exit 1
			fi
			cp /tmp/resonances_y_"$4"_"$5"_"$6"_t0.csv /tmp/t0_y.csv
			echo "please wait..."
			/home/pi/klipper/scripts/calibrate_shaper.py /tmp/t0_y.csv -o /home/pi/printer_data/config/input_shaper/t0_resonances_y_$DATE.png
			rm /tmp/resonances_y_"$4"_"$5"_"$6"_t0.csv
		fi

		if [ $T1 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_y_"$4"_"$5"_"$6"_t1.csv" ]
			then
				echo "ERROR: No y data found for T1"
				exit 1
			fi
			cp /tmp/resonances_y_"$4"_"$5"_"$6"_t1.csv /tmp/t1_y.csv
			echo "please wait..."
			/home/pi/klipper/scripts/calibrate_shaper.py /tmp/t1_y.csv -o /home/pi/printer_data/config/input_shaper/t1_resonances_y_$DATE.png
			rm /tmp/resonances_y_"$4"_"$5"_"$6"_t1.csv
		fi
	fi

	if [ $IDEX -eq 1 ]
	then
		if [ $T0 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_y_"$4"_"$5"_"$6"_t0_copy.csv" ]
			then
				echo "ERROR: No y data found for T0 copy mode"
				exit 1
			fi
			echo "please wait..."
			cp /tmp/resonances_y_"$4"_"$5"_"$6"_t0_copy.csv /tmp/t0_copy_y.csv
			[ -e "/tmp/t0_copy_y.csv" ] && /home/pi/klipper/scripts/calibrate_shaper.py /tmp/t0_copy_y.csv -o /home/pi/printer_data/config/input_shaper/t0_copy_resonances_y_$DATE.png
			rm /tmp/resonances_y_"$4"_"$5"_"$6"_t0_copy.csv
		fi
		if [ $T1 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_y_"$4"_"$5"_"$6"_t1_copy.csv" ]
			then
				echo "ERROR: No y data found for T1 copy mode"
				exit 1
			fi
			echo "please wait..."
			cp /tmp/resonances_y_"$4"_"$5"_"$6"_t1_copy.csv /tmp/t1_copy_y.csv
			[ -e "/tmp/t1_copy_y.csv" ] && /home/pi/klipper/scripts/calibrate_shaper.py /tmp/t1_copy_y.csv -o /home/pi/printer_data/config/input_shaper/t1_copy_resonances_y_$DATE.png
			rm /tmp/resonances_y_"$4"_"$5"_"$6"_t1_copy.csv
		fi
	fi

	if [ $IDEX -eq 2 ]
	then
		if [ $T0 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_y_"$4"_"$5"_"$6"_t0_mirror.csv" ]
			then
				echo "ERROR: No y data found for T0 mirror mode"
				exit 1
			fi
			echo "please wait..."
			cp /tmp/resonances_y_"$4"_"$5"_"$6"_t0_mirror.csv /tmp/t0_mirror_y.csv
			[ -e "/tmp/t0_mirror_y.csv" ] && /home/pi/klipper/scripts/calibrate_shaper.py /tmp/t0_mirror_y.csv -o /home/pi/printer_data/config/input_shaper/t0_mirror_resonances_y_$DATE.png
			rm /tmp/resonances_y_"$4"_"$5"_"$6"_t0_mirror.csv
		fi
		if [ $T1 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_y_"$4"_"$5"_"$6"_t1_mirror.csv" ]
			then
				echo "ERROR: No y data found for T1 mirror mode"
				exit 1
			fi
			echo "please wait..."
			cp /tmp/resonances_y_"$4"_"$5"_"$6"_t1_mirror.csv /tmp/t1_mirror_y.csv
			[ -e "/tmp/t1_mirror_y.csv" ] && /home/pi/klipper/scripts/calibrate_shaper.py /tmp/t1_mirror_y.csv -o /home/pi/printer_data/config/input_shaper/t1_mirror_resonances_y_$DATE.png
			rm /tmp/resonances_y_"$4"_"$5"_"$6"_t1_mirror.csv
		fi
	fi
fi

if [ $DISABLE_X -eq 0 ]
then
	[ -e "/tmp/t0_x.csv" ] && rm /tmp/t0_x.csv
	[ -e "/tmp/t1_x.csv" ] && rm /tmp/t1_x.csv
	[ -e "/tmp/t0_copy_x.csv" ] && rm /tmp/t0_copy_x.csv
	[ -e "/tmp/t1_copy_x.csv" ] && rm /tmp/t1_copy_x.csv
	[ -e "/tmp/t0_mirror_x.csv" ] && rm /tmp/t0_mirror_x.csv
	[ -e "/tmp/t1_mirror_x.csv" ] && rm /tmp/t1_mirror_x.csv

	if [ $IDEX -eq 0 ]
	then
		if [ $T0 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_x_"$4"_"$5"_"$6"_t0.csv" ]
			then
				echo "ERROR: resonances_x_"$4"_"$5"_"$6"_t0.csv"
				echo "ERROR: No x data found for T0"
				exit 1
			fi
			cp /tmp/resonances_x_"$4"_"$5"_"$6"_t0.csv /tmp/t0_x.csv
			echo "please wait..."
			/home/pi/klipper/scripts/calibrate_shaper.py /tmp/t0_x.csv -o /home/pi/printer_data/config/input_shaper/t0_resonances_x_$DATE.png
			rm /tmp/resonances_x_"$4"_"$5"_"$6"_t0.csv
		fi

		if [ $T1 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_x_"$4"_"$5"_"$6"_t1.csv" ]
			then
				echo "ERROR: No x data found for T1"
				exit 1
			fi
			cp /tmp/resonances_x_"$4"_"$5"_"$6"_t1.csv /tmp/t1_x.csv
			echo "please wait..."
			/home/pi/klipper/scripts/calibrate_shaper.py /tmp/t1_x.csv -o /home/pi/printer_data/config/input_shaper/t1_resonances_x_$DATE.png
			rm /tmp/resonances_x_"$4"_"$5"_"$6"_t1.csv
		fi
	fi

	if [ $IDEX -eq 1 ]
	then
		if [ $T0 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_x_"$4"_"$5"_"$6"_t0_copy.csv" ]
			then
				echo "ERROR: No x data found for T0 copy mode"
				exit 1
			fi
			echo "please wait..."
			cp /tmp/resonances_x_"$4"_"$5"_"$6"_t0_copy.csv /tmp/t0_copy_x.csv
			[ -e "/tmp/t0_copy_x.csv" ] && /home/pi/klipper/scripts/calibrate_shaper.py /tmp/t0_copy_x.csv -o /home/pi/printer_data/config/input_shaper/t0_copy_resonances_x_$DATE.png
			rm /tmp/resonances_x_"$4"_"$5"_"$6"_t0_copy.csv
		fi
		if [ $T1 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_x_"$4"_"$5"_"$6"_t1_copy.csv" ]
			then
				echo "ERROR: No x data found for T1 copy mode"
				exit 1
			fi
			echo "please wait..."
			cp /tmp/resonances_x_"$4"_"$5"_"$6"_t1_copy.csv /tmp/t1_copy_x.csv
			[ -e "/tmp/t1_copy_x.csv" ] && /home/pi/klipper/scripts/calibrate_shaper.py /tmp/t1_copy_x.csv -o /home/pi/printer_data/config/input_shaper/t1_copy_resonances_x_$DATE.png
			rm /tmp/resonances_x_"$4"_"$5"_"$6"_t1_copy.csv
		fi
	fi

	if [ $IDEX -eq 2 ]
	then
		if [ $T0 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_x_"$4"_"$5"_"$6"_t0_mirror.csv" ]
			then
				echo "ERROR: No x data found for T0 mirror mode"
				exit 1
			fi
			echo "please wait..."
			cp /tmp/resonances_x_"$4"_"$5"_"$6"_t0_mirror.csv /tmp/t0_mirror_x.csv
			[ -e "/tmp/t0_mirror_x.csv" ] && /home/pi/klipper/scripts/calibrate_shaper.py /tmp/t0_mirror_x.csv -o /home/pi/printer_data/config/input_shaper/t0_mirror_resonances_x_$DATE.png
			rm /tmp/resonances_x_"$4"_"$5"_"$6"_t0_mirror.csv
		fi
		if [ $T1 -eq 1 ]
		then
			if [ ! -e "/tmp/resonances_x_"$4"_"$5"_"$6"_t1_mirror.csv" ]
			then
				echo "ERROR: No x data found for T1 mirror mode"
				exit 1
			fi
			echo "please wait..."
			cp /tmp/resonances_x_"$4"_"$5"_"$6"_t1_mirror.csv /tmp/t1_mirror_x.csv
			[ -e "/tmp/t1_mirror_x.csv" ] && /home/pi/klipper/scripts/calibrate_shaper.py /tmp/t1_mirror_x.csv -o /home/pi/printer_data/config/input_shaper/t1_mirror_resonances_x_$DATE.png
			rm /tmp/resonances_x_"$4"_"$5"_"$6"_t1_mirror.csv
		fi
	fi
fi