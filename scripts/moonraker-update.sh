#!/bin/bash

source /home/pi/printer_data/config/RatOS/scripts/moonraker-ensure-policykit-rules.sh
ensure_moonraker_policiykit_rules

ensure_service_permission()
{
	report_status "Updating service permissions"
	if ! cat /home/pi/printer_data/moonraker.asvc | grep "ratos-configurator" &>/dev/null; then
		printf '\nratos-configurator' >> /home/pi/printer_data/moonraker.asvc
		report_status "Configurator added to moonraker service permissions"
	fi
}

ensure_service_permission
