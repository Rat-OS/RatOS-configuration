#!/bin/bash

DISABLE_Y=0
DISABLE_X=0

if [ "$1" == "x" ]
then
	DISABLE_Y=1
fi
if [ "$1" == "y" ]
then
	DISABLE_X=1
fi

if [ ! -d "/home/pi/printer_data/config/input_shaper" ]
then
    mkdir /home/pi/printer_data/config/input_shaper
fi

T0=1
T1=1
T2=0

if [ "$2" == "0" ]
then
	T1=0
fi
if [ "$2" == "1" ]
then
	T0=0
fi
if [ "$2" == "2" ]
then
	T2=1
fi

DATE=$(date +'%Y-%m-%d-%H%M%S')
if [ $DISABLE_Y -eq 0 ]
then
	[ -e "/tmp/left_y_belt_tension.csv" ] && rm /tmp/left_y_belt_tension.csv
	[ -e "/tmp/right_y_belt_tension.csv" ] && rm /tmp/right_y_belt_tension.csv
	[ -e "/tmp/combined_y_belt_tension.csv" ] && rm /tmp/combined_y_belt_tension.csv

	if [ $T2 -eq 1 ]
	then
		if [ ! -e "/tmp/raw_data_y_toolboard_t2.csv" ]
		then
			echo "ERROR: No y data found for left toolhead (T0)"
			exit 1
		fi
		if [ ! -e "/tmp/raw_data_y_toolboardb_t2.csv" ]
		then
			echo "ERROR: No y data found for right toolhead (T1)"
			exit 1
		fi
		cp /tmp/raw_data_y_toolboard_t2.csv /tmp/left_y_belt_tension.csv
		cp /tmp/raw_data_y_toolboardb_t2.csv /tmp/right_y_belt_tension.csv
	fi

	if [ $T2 -eq 0 ]
	then
		if [ $T0 -eq 1 ]
		then
			if [ ! -e "/tmp/raw_data_y_toolboard_t0.csv" ]
			then
				echo "ERROR: No y data found for left toolhead (T0)"
				exit 1
			fi
			cp /tmp/raw_data_y_toolboard_t0.csv /tmp/left_y_belt_tension.csv
		fi

		if [ $T1 -eq 1 ]
		then
			if [ ! -e "/tmp/raw_data_y_toolboardb_t1.csv" ]
			then
				echo "ERROR: No y data found for right toolhead (T1)"
				exit 1
			fi
			cp /tmp/raw_data_y_toolboardb_t1.csv /tmp/right_y_belt_tension.csv
		fi
	fi

	/home/pi/klipper/scripts/graph_accelerometer.py -c /tmp/*_y_belt_tension.csv -o /home/pi/printer_data/config/input_shaper/y_tension_comparison_$DATE.png
fi
if [ $DISABLE_X -eq 0 ]
then
	[ -e "/tmp/left_x_belt_tension.csv" ] && rm /tmp/left_x_belt_tension.csv
	[ -e "/tmp/right_x_belt_tension.csv" ] && rm /tmp/right_x_belt_tension.csv

	if [ $T0 -eq 1 ]
	then
		if [ ! -e "/tmp/raw_data_x_toolboard_t0.csv" ]
		then
			echo "ERROR: No x data found for the left toolhead (T0)"
			exit 1
		fi
		cp /tmp/raw_data_x_toolboard_t0.csv /tmp/left_x_belt_tension.csv
	fi

	if [ $T1 -eq 1 ]
	then
		if [ ! -e "/tmp/raw_data_x_toolboardb_t1.csv" ]
		then
			echo "ERROR: No x data found for right toolhbead (T1)"
			exit 1
		fi
		cp /tmp/raw_data_x_toolboardb_t1.csv /tmp/right_x_belt_tension.csv
	fi

	/home/pi/klipper/scripts/graph_accelerometer.py -c /tmp/*_x_belt_tension.csv -o /home/pi/printer_data/config/input_shaper/x_tension_comparison_$DATE.png
fi