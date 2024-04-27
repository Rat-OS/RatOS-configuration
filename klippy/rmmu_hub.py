# Support for controlling the RMMU multi material device under RatOS
#
# Copyright (C) 2024 Helge Magnus Keck <helgekeck@hotmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
from math import fabs
import re

#####
# RMMU Hub
#####
class RMMU_Hub:

	#####
	# Initialize
	#####
	def __init__(self, config):
		self.printer = config.get_printer()
		self.name = config.get_name()
		self.gcode = self.printer.lookup_object('gcode')

		self.rmmu = []
		self.mapping = {}
		self.mode = "multi"
		self.total_tool_count = 0
		self.initial_filament = 0

		self.register_commands()
		self.register_handler()

	#####
	# Handler
	#####
	def register_handler(self):
		self.printer.register_event_handler("klippy:connect", self._connect)

	def _connect(self):
		self.toolhead = self.printer.lookup_object('toolhead')
		self.rmmu = []
		self.mapping = {}
		start_tool_count = 0
		for rmmu in self.printer.lookup_objects('rmmu'):
			# rmmu device
			self.total_tool_count += rmmu[1].tool_count
			self.rmmu.append(rmmu[1])

			# rmmu mapping
			for tool in range(start_tool_count, self.total_tool_count):
				self.mapping[str(tool)] = {"TOOLHEAD": rmmu[1].name.lower().replace("rmmu_t", ""), "FILAMENT": tool - start_tool_count}

			# feeder filament sensors
			rmmu[1].feeder_filament_sensors = []
			for i in range(start_tool_count, self.total_tool_count):
				for filament_sensor in self.printer.lookup_objects('filament_switch_sensor'):
					sensor_name = filament_sensor[1].runout_helper.name
					if sensor_name == 'feeder_filament_sensor_t' + str(i):
						rmmu[1].feeder_filament_sensors.append(filament_sensor[1])

			start_tool_count = self.total_tool_count

	#####
	# Gcode commands
	#####
	def register_commands(self):
		self.gcode.register_command('RMMU_HOME', self.cmd_RMMU_HOME, desc=(self.desc_RMMU_HOME))
		self.gcode.register_command('RMMU_RESET', self.cmd_RMMU_RESET, desc=(self.desc_RMMU_RESET))
		self.gcode.register_command('RMMU_CHANGE_FILAMENT', self.cmd_RMMU_CHANGE_FILAMENT, desc=(self.desc_RMMU_CHANGE_FILAMENT))
		self.gcode.register_command('RMMU_LOAD_FILAMENT', self.cmd_RMMU_LOAD_FILAMENT, desc=(self.desc_RMMU_LOAD_FILAMENT))
		self.gcode.register_command('RMMU_UNLOAD_FILAMENT', self.cmd_RMMU_UNLOAD_FILAMENT, desc=(self.desc_RMMU_UNLOAD_FILAMENT))
		self.gcode.register_command('RMMU_START_PRINT', self.cmd_RMMU_START_PRINT, desc=(self.desc_RMMU_START_PRINT))
		self.gcode.register_command('RMMU_END_PRINT', self.cmd_RMMU_END_PRINT, desc=(self.desc_RMMU_END_PRINT))
		self.gcode.register_command('RMMU_HOME_FILAMENT', self.cmd_RMMU_HOME_FILAMENT, desc=(self.desc_RMMU_HOME_FILAMENT))
		self.gcode.register_command('RMMU_MOVE_FILAMENT', self.cmd_RMMU_MOVE_FILAMENT, desc=(self.desc_RMMU_MOVE_FILAMENT))
		self.gcode.register_command('RMMU_EJECT_FILAMENT', self.cmd_RMMU_EJECT_FILAMENT, desc=(self.desc_RMMU_EJECT_FILAMENT))
		self.gcode.register_command('RMMU_FILAMENT_INSERT', self.cmd_RMMU_FILAMENT_INSERT, desc=(self.desc_RMMU_FILAMENT_INSERT))
		self.gcode.register_command('RMMU_FILAMENT_RUNOUT', self.cmd_RMMU_FILAMENT_RUNOUT, desc=(self.desc_RMMU_FILAMENT_RUNOUT))

	desc_RMMU_HOME = "Homes the RMMU idler."
	def cmd_RMMU_HOME(self, param):
		for rmmu in self.rmmu:
			rmmu.home()

	desc_RMMU_RESET = "Resets the RMMU device."
	def cmd_RMMU_RESET(self, param):
		for rmmu in self.rmmu:
			rmmu.reset()

	desc_RMMU_HOME_FILAMENT = "Homes one or all filaments to their homing positions."
	def cmd_RMMU_HOME_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.total_tool_count)
		if tool == -1:
			for rmmu in self.rmmu:
				rmmu.home_filaments(-1)
		else:
			if tool >= self.rmmu[0].tool_count:
				self.rmmu[1].home_filaments(tool- self.rmmu[0].tool_count)
			else:
				self.rmmu[0].home_filaments(tool)

	desc_RMMU_MOVE_FILAMENT = "Moves a filament with or without extruder sync."
	def cmd_RMMU_MOVE_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=0, maxval=self.total_tool_count)
		move = param.get_int('MOVE', 50)
		speed = param.get_int('SPEED', 10)
		accel = param.get_int('ACCEL', 100)
		sync = param.get_int('SYNC_EXTRUDER', None, minval=0, maxval=1)
		if tool >= self.rmmu[0].tool_count:
			self.rmmu[1].move_filament(tool - self.rmmu[0].tool_count, move, speed, accel, sync)
		else:
			self.rmmu[0].move_filament(tool, move, speed, accel, sync)

	desc_RMMU_EJECT_FILAMENT = "Ejects one or all filament(s) from the RMMU device."
	def cmd_RMMU_EJECT_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.total_tool_count)
		if tool == -1:
			for rmmu in self.rmmu:
				rmmu.eject_filaments(-1)
		else:
			if tool >= self.rmmu[0].tool_count:
				self.rmmu[1].eject_filaments(tool - self.rmmu[0].tool_count)
			else:
				self.rmmu[0].eject_filaments(tool)

	desc_RMMU_CHANGE_FILAMENT = "Called during the print to switch to another filament. Do not call it manually!"
	def cmd_RMMU_CHANGE_FILAMENT(self, param):
		self.change_filament(param)

	desc_RMMU_LOAD_FILAMENT = "Loads a filament form its parking position into the hotend."
	def cmd_RMMU_LOAD_FILAMENT(self, param):
		self.cmd_load_filament(param)

	desc_RMMU_UNLOAD_FILAMENT = "Unloads a filament from the hotend to its parking position."
	def cmd_RMMU_UNLOAD_FILAMENT(self, param):
		self.cmd_unload_filament(param)

	desc_RMMU_FILAMENT_INSERT = "Called from the RatOS feeder sensor insert detection."
	def cmd_RMMU_FILAMENT_INSERT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.total_tool_count)
		if tool >= self.rmmu[0].tool_count:
			self.rmmu[1].on_filament_insert(tool - self.rmmu[0].tool_count)
		else:
			self.rmmu[0].on_filament_insert(tool)

	desc_RMMU_FILAMENT_RUNOUT = "Called from the RatOS feeder sensor runout detection."
	def cmd_RMMU_FILAMENT_RUNOUT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.total_tool_count)
		clogged = param.get_int('CLOGGED', "true")
		if tool >= self.rmmu[0].tool_count:
			self.rmmu[1].on_filament_runout(tool - self.rmmu[0].tool_count, clogged)
		else:
			self.rmmu[0].on_filament_runout(tool, clogged)

	desc_RMMU_START_PRINT = "RMMU_START_PRINT gcode macro. Calls the RatOS START_PRINT macro if there are no errors."
	def cmd_RMMU_START_PRINT(self, param):
		self.start_print(param)

	desc_RMMU_END_PRINT = "Called from the END_PRINT gcode macro. Unloads the filament and resets the RMMU device."
	def cmd_RMMU_END_PRINT(self, param):
		for rmmu in self.rmmu:
			rmmu.end_print()

	#####
	# Status
	#####
	def get_status(self, eventtime):
		return {'name': self.name,
		  'mode': self.mode,
		  'initial_filament': self.initial_filament,
		  'total_tool_count': self.total_tool_count,
		  'mapping': self.mapping}

	#####
	# Start / End Print
	#####
	def start_print(self, param):
		# parameter
		self.initial_filament = param.get_int('INITIAL_TOOL', None, minval=0, maxval=self.total_tool_count)
		self.wipe_accel = param.get_int('WIPE_ACCEL', None, minval=0, maxval=100000)
		self.start_print_param = param

		# handle toolhead mapping
		# self.initial_filament = self.get_remapped_toolhead(self.initial_filament)

		# home RMMUs
		for rmmu in self.rmmu:
			rmmu.home()

		# # get used physical toolheads
		# used_toolheads = []
		# for t in range(0, self.total_tool_count):
		# 	if param.get('T' + str(t), "true") == "true":
		# 		if not t in used_toolheads:
		# 			used_toolheads.append(t)
		# self.ratos_echo("used_toolheads: " + str(used_toolheads))

		# get initial RMMU and tool
		rmmu = self.rmmu[0]
		rmmu_tool = self.initial_filament
		if rmmu_tool >= self.rmmu[0].tool_count:
			rmmu = self.rmmu[1]
			rmmu_tool = rmmu_tool - self.rmmu[0].tool_count

		# check for filament in hotend
		rmmu.needs_initial_purging = True
		if rmmu.is_sensor_triggered(rmmu.toolhead_filament_sensor):
			loaded_filament = rmmu.get_status(self.toolhead.get_last_move_time())['loaded_filament']
			loaded_filament_temp = rmmu.get_status(self.toolhead.get_last_move_time())['loaded_filament_temp']
			if loaded_filament >=0 and loaded_filament <= self.total_tool_count:
				if loaded_filament != rmmu_tool:
					if loaded_filament_temp > rmmu.heater.min_extrude_temp and loaded_filament_temp < rmmu.heater.max_temp:
						# unloaded the filament that is already loaded
						self.ratos_echo("Wrong filament detected in hotend!")
						self.ratos_echo("Unloading filament T" + str(loaded_filament) + "! Please wait...")

						# start heating up extruder but dont wait for it so we can save some time
						self.ratos_echo("Preheating extruder to " + str(loaded_filament_temp) + "°C.")
						rmmu.extruder_set_temperature(loaded_filament_temp, False)

						# home printer if needed and move toolhead to its parking position
						self.gcode.run_script_from_command('MAYBE_HOME')
						if rmmu_tool >= self.rmmu[0].tool_count:
							self.gcode.run_script_from_command('_MOVE_TO_LOADING_POSITION TOOLHEAD=1')
						else:
							self.gcode.run_script_from_command('_MOVE_TO_LOADING_POSITION TOOLHEAD=0')

						# wait for the extruder to heat up
						self.ratos_echo("Heating up extruder to " + str(loaded_filament_temp) + "°C! Please wait...")
						rmmu.extruder_set_temperature(loaded_filament_temp, True)					

						# unload filament
						if not rmmu.unload_filament(loaded_filament):
							rmmu.extruder_set_temperature(0, False)					
							raise self.printer.command_error("Could not unload filament! Please unload the filament and restart the print.")

						# cool down extruder, dont wait for it
						rmmu.extruder_set_temperature(0, False)					
					else:
						raise self.printer.command_error("Unknown filament detected in toolhead! Please unload the filament and restart the print.")
				else:
					# tell RatOS that initial purging is not needed
					rmmu.needs_initial_purging = False
			else:
				raise self.printer.command_error("Unknown filament detected in toolhead! Please unload the filament and restart the print.")

		# # test if all demanded filaments are available and raises an error if not
		# rmmu.test_filaments(param)

		# disable toolhead filament sensor
		rmmu.toolhead_filament_sensor.runout_helper.sensor_enabled = False

		# call RatOS start print gcode macro
		self.gcode.run_script_from_command('START_PRINT ' + str(param.get_raw_command_parameters().strip()))

	#####
	# Change Filament
	#####
	def change_filament(self, param):
		# parameter
		filament = param.get_int('FILAMENT', None, minval=0, maxval=self.total_tool_count)
		x = param.get_float('X', None, minval=-1, maxval=999)
		y = param.get_float('Y', None, minval=-1, maxval=999)

		# rmmu instance
		physical_toolhead = int(self.mapping[str(filament)]["TOOLHEAD"])
		rmmu_filament = int(self.mapping[str(filament)]["FILAMENT"])
		rmmu = self.rmmu[physical_toolhead]

		# # handle toolhead mapping
		# rmmu_filament = self.get_remapped_toolhead(rmmu_filament)

		# # handle spool mapping
		# rmmu_filament = self.get_remapped_spool(rmmu_filament)

		# run before filament change gcode macro
		self.gcode.run_script_from_command('_RMMU_BEFORE_FILAMENT_CHANGE TOOLHEAD=' + str(physical_toolhead) + ' X=' + str(x) + ' Y=' + str(y) + ' WIPE_ACCEL=' + str(self.wipe_accel))

		# enable toolhead filament sensor
		rmmu.toolhead_filament_sensor.runout_helper.sensor_enabled = True

		# check toolhead filament sensor
		if rmmu.is_sensor_triggered(rmmu.toolhead_filament_sensor):
			# unload filament
			loaded_filament = rmmu.get_setting(rmmu.name.lower() + rmmu.VARS_LOADED_FILAMENT)
			if not rmmu.unload_filament(loaded_filament, "change_filament"):
				rmmu.select_filament(-1)
				self.ratos_echo("Could not unload filament T" + str(loaded_filament) + "!")
				return
		else:
			# toolhead filament sensor false state detected
			self.ratos_echo("Possible sensor failure! Filament sensor should be triggered but it isnt.")
			return

		# load filament
		if not rmmu.load_filament(rmmu_filament):
			rmmu.on_loading_error(rmmu_filament)

		# disable toolhead filament sensor
		rmmu.toolhead_filament_sensor.runout_helper.sensor_enabled = False

	#####
	# Load Filament
	#####
	def cmd_load_filament(self, param):
		# parameter
		filament = param.get_int('FILAMENT', None, minval=0, maxval=self.total_tool_count)

		# rmmu instance
		physical_toolhead = int(self.mapping[str(filament)]["TOOLHEAD"])
		rmmu_filament = int(self.mapping[str(filament)]["FILAMENT"])
		rmmu = self.rmmu[physical_toolhead]

		# check toolhead filament sensor
		if rmmu.is_sensor_triggered(rmmu.toolhead_filament_sensor):
			raise self.printer.command_error("Can not load filament! Another one is already loaded.")

		# home if needed
		if not rmmu.is_homed:
			rmmu.home()

		# load filament
		if not rmmu.load_filament(rmmu_filament):
			rmmu.on_loading_error(rmmu_filament)
			return

	#####
	# Unload Filament
	#####
	def cmd_unload_filament(self, param):
		# parameter
		filament = param.get_int('FILAMENT', None, minval=-1, maxval=self.total_tool_count)

		# rmmu instance
		physical_toolhead = int(self.mapping[str(filament)]["TOOLHEAD"])
		rmmu_filament = int(self.mapping[str(filament)]["FILAMENT"])
		rmmu = self.rmmu[physical_toolhead]

		# check toolhead filament sensor
		if not rmmu.is_sensor_triggered(rmmu.toolhead_filament_sensor):
			raise self.printer.command_error("No filament loaded!")

		# home if needed
		if not rmmu.is_homed:
			rmmu.home()

		# unload filament
		loaded_filament = rmmu.get_setting(rmmu.name.lower() + rmmu.VARS_LOADED_FILAMENT)
		rmmu_filament = rmmu_filament if rmmu_filament > -1 else loaded_filament
		if rmmu_filament > -1 and rmmu_filament < rmmu.tool_count:
			rmmu.unload_filament(rmmu_filament)
		else:
			raise self.printer.command_error("Can not unload unknown filament!")

		# release idler
		rmmu.select_filament(-1)

	#####
	# Helper
	#####
	def ratos_echo(self, msg):
		self.gcode.run_script_from_command("RATOS_ECHO PREFIX='" + str(self.name) + "' MSG='" + str(msg) + "'")

	def ratos_debug_echo(self, msg):
		self.gcode.run_script_from_command("DEBUG_ECHO PREFIX='" + str(self.name) + "' MSG='" + str(msg) + "'")

#####
# Loader
#####
def load_config(config):
	return RMMU_Hub(config)
