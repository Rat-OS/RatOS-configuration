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

		self.register_commands()
		self.register_handler()

	#####
	# Handler
	#####
	def register_handler(self):
		self.printer.register_event_handler("klippy:connect", self._connect)

	def _connect(self):
		self.toolhead = self.printer.lookup_object('toolhead')
		self.dual_carriage = self.printer.lookup_object("dual_carriage", None)
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

			# bowden filament sensors
			rmmu[1].bowdenfilament_sensors = []
			for i in range(start_tool_count, self.total_tool_count):
				for filament_sensor in self.printer.lookup_objects('filament_switch_sensor'):
					sensor_name = filament_sensor[1].runout_helper.name
					if sensor_name == 'bowdenfilament_sensor_t' + str(i):
						rmmu[1].bowdenfilament_sensors.append(filament_sensor[1])

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

	desc_RMMU_FILAMENT_INSERT = "Called from the RatOS bowden sensor insert detection."
	def cmd_RMMU_FILAMENT_INSERT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.total_tool_count)
		if tool >= self.rmmu[0].tool_count:
			self.rmmu[1].on_filament_insert(tool - self.rmmu[0].tool_count)
		else:
			self.rmmu[0].on_filament_insert(tool)

	desc_RMMU_FILAMENT_RUNOUT = "Called from the RatOS bowden sensor runout detection."
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
		  'total_tool_count': self.total_tool_count,
		  'mapping': self.mapping}

	#####
	# Start / End Print
	#####
	def start_print(self, param):
		# parameter
		self.start_print_param = param
		self.wipe_accel = param.get_int('WIPE_ACCEL', None, minval=0, maxval=100000)
		self.extruder_temp = param.get('EXTRUDER_TEMP').lower().split(",")
		self.extruder_temp = [float(item) for item in self.extruder_temp]
		logical_tools = []
		if param.get('USED_TOOLS', None) != None:
			try:
				logical_tools = [int(v.strip()) for v in str(param.get('USED_TOOLS', None)).split(',')]
			except:
				raise self.printer.command_error("Unable to parse START_PRINT parameter USED_TOOLS.")

		# idex mode
		idex_mode = ""
		act_idex_toolhead = -1
		if self.dual_carriage != None:
			idex_mode = self.dual_carriage.get_status(self.toolhead.get_last_move_time())['carriage_1'].lower()
			act_idex_toolhead = 1 if idex_mode == "primary" else 0

		# copy and mirror mmu mode
		if (idex_mode == "copy" or idex_mode == "mirror") and len(logical_tools) > 1:
			for logical_tool in logical_tools:
				if logical_tool > self.rmmu[0].tool_count:
					raise self.printer.command_error("Wrong slicer tool selection for copy and mirror mmu mode.")
			logical_tools_t1 = []
			for logical_tool in logical_tools:
				logical_tools_t1.append(logical_tool + self.rmmu[0].tool_count)
			logical_tools.extend(logical_tools_t1)

		# make sure the idlers are released when in non mmu copy and mirror mode
		if (idex_mode == "copy" or idex_mode == "mirror") and len(logical_tools) == 1:
			for rmmu in self.rmmu:
				if not rmmu.is_homed:
					rmmu.home()

		if not ((idex_mode == "copy" or idex_mode == "mirror") and len(logical_tools) == 1):

			# get used physical toolheads
			physical_toolheads = []
			for t in logical_tools:
				physical_toolhead = int(self.mapping[str(t)]["TOOLHEAD"])
				if physical_toolhead not in physical_toolheads:
					physical_toolheads.append(physical_toolhead)

			# home needed RMMUs
			for physical_toolhead in physical_toolheads:
				if not self.rmmu[physical_toolhead].is_homed:
					self.rmmu[physical_toolhead].home()

			# idex mode
			if idex_mode == "copy" or idex_mode == "mirror":
				default_toolhead = self.get_macro_variable("RatOS", "default_toolhead")
				parking_position = self.get_macro_variable("T" + str(default_toolhead), "parking_position")
				self.gcode.run_script_from_command('_IDEX_SINGLE X=' + str(parking_position))

			# unload / load filaments
			needs_cool_down = False
			for physical_toolhead in physical_toolheads:
				for t in logical_tools:
					if physical_toolhead == int(self.mapping[str(t)]["TOOLHEAD"]):
						self.rmmu[physical_toolhead].in_use = True
						self.rmmu[physical_toolhead].initial_filament = t
						break
				rmmu = self.rmmu[physical_toolhead]

				# handle toolhead mapping
				# initial_filament = self.get_remapped_toolhead(initial_filament)

				loaded_filament = rmmu.get_status(self.toolhead.get_last_move_time())['loaded_filament']
				loaded_filament_temp = rmmu.get_status(self.toolhead.get_last_move_time())['loaded_filament_temp']
				initial_filament = int(self.mapping[str(rmmu.initial_filament)]["FILAMENT"])

				# unload wrong filament if needed 
				if rmmu.is_sensor_triggered(rmmu.toolhead_filament_sensor):
					if loaded_filament != initial_filament:
						if loaded_filament_temp > rmmu.heater.min_extrude_temp and loaded_filament_temp < rmmu.heater.max_temp:
							needs_cool_down = True

							# unloaded the filament that is already loaded
							self.ratos_echo("Wrong filament detected in toolhead T" + str(physical_toolhead) + ".")
							self.ratos_echo("Unloading filament T" + str(loaded_filament) + "...")

							# start heating up extruder but dont wait for it so we can save some time
							self.ratos_echo("Preheating extruder to " + str(loaded_filament_temp) + "°C.")
							rmmu.extruder_set_temperature(loaded_filament_temp, False)

							# home printer if needed
							self.gcode.run_script_from_command('MAYBE_HOME')

							# park toolhead
							if idex_mode != "":
								self.gcode.run_script_from_command('PARK_TOOLHEAD')

							# handle dual carriage if needed
							if idex_mode != "":
								if act_idex_toolhead != physical_toolhead:
									self.gcode.run_script_from_command('SET_DUAL_CARRIAGE CARRIAGE=' + str(physical_toolhead) + ' MODE=PRIMARY')
									self.gcode.run_script_from_command('ACTIVATE_EXTRUDER EXTRUDER=extruder' + ('' if physical_toolhead == 0 else '1'))

							# move toolhead to its loading position
							self.gcode.run_script_from_command('_MOVE_TO_LOADING_POSITION TOOLHEAD=' + str(physical_toolhead))

							# wait for the extruder to heat up
							self.ratos_echo("Heating up extruder to " + str(loaded_filament_temp) + "°C! Please wait...")
							rmmu.extruder_set_temperature(loaded_filament_temp, True)					

							# unload wrong filament
							if not rmmu.unload_filament(loaded_filament, False):
								rmmu.extruder_set_temperature(0, False)					
								raise self.printer.command_error("Could not unload filament! Please unload the filament and restart the print.")

							# handle dual carriage if needed
							if idex_mode != "":
								if act_idex_toolhead != physical_toolhead:
									self.gcode.run_script_from_command('SET_DUAL_CARRIAGE CARRIAGE=' + str(act_idex_toolhead) + ' MODE=PRIMARY')
									self.gcode.run_script_from_command('ACTIVATE_EXTRUDER EXTRUDER=extruder' + ('' if act_idex_toolhead == 0 else '1'))
						else:
							raise self.printer.command_error("Unknown filament detected in toolhead! Please unload the filament and restart the print.")

				# load initial filament if needed
				if loaded_filament != initial_filament:
					needs_cool_down = True

					# start heating up extruder but dont wait for it so we can save some time
					self.ratos_echo("Preheating extruder to " + str(self.extruder_temp[physical_toolhead]) + "°C")
					rmmu.extruder_set_temperature(self.extruder_temp[physical_toolhead], False)

					# home printer if needed
					self.gcode.run_script_from_command('MAYBE_HOME')

					# handle dual carriage if needed
					if idex_mode != "":
						if act_idex_toolhead != physical_toolhead:
							self.gcode.run_script_from_command('SET_DUAL_CARRIAGE CARRIAGE=' + str(physical_toolhead) + ' MODE=PRIMARY')
							self.gcode.run_script_from_command('ACTIVATE_EXTRUDER EXTRUDER=extruder' + ('' if physical_toolhead == 0 else '1'))

					# move toolhead to its loading position
					self.gcode.run_script_from_command('_MOVE_TO_LOADING_POSITION TOOLHEAD=' + str(physical_toolhead))

					# wait for the extruder to heat up
					self.ratos_echo("Heating up extruder to " + str(self.extruder_temp[physical_toolhead]) + "°C...")
					rmmu.extruder_set_temperature(self.extruder_temp[physical_toolhead], True)					

					# load initial filament
					if not rmmu.load_filament(initial_filament):
						rmmu.extruder_set_temperature(0, False)					
						raise self.printer.command_error("Could not load filament! Please load filament T" + str(rmmu.initial_filament) + " and restart the print.")

					# purge filament
					toolchange_first_purge = self.get_macro_variable("RatOS", "toolchange_first_purge")
					self.ratos_echo("toolchange_first_purge: " + str(toolchange_first_purge))
					if toolchange_first_purge != None and toolchange_first_purge > 0:
						toolchange_first_purge_feedrate = self.get_macro_variable("RatOS", "toolchange_first_purge_feedrate")
						loading_position = self.get_macro_variable("T" + str(physical_toolhead), "loading_position")
						self.ratos_echo("physical_toolhead: " + str(physical_toolhead))
						self.ratos_echo("toolchange_first_purge_feedrate: " + str(toolchange_first_purge_feedrate))
						self.ratos_echo("loading_position: " + str(loading_position))
						if loading_position != None:
							self.ratos_echo("Initial puring...")
							self.gcode.run_script_from_command('_PURGE_FILAMENT	TOOLHEAD=' + str(physical_toolhead) + ' E=' + str(toolchange_first_purge) + ' F=' + str(toolchange_first_purge_feedrate))
							self.gcode.run_script_from_command('_CLEANING_MOVE TOOLHEAD=' + str(physical_toolhead))

					# handle dual carriage if needed
					if idex_mode != "":
						if act_idex_toolhead != physical_toolhead:
							self.gcode.run_script_from_command('SET_DUAL_CARRIAGE CARRIAGE=' + str(act_idex_toolhead) + ' MODE=PRIMARY')
							self.gcode.run_script_from_command('ACTIVATE_EXTRUDER EXTRUDER=extruder' + ('' if act_idex_toolhead == 0 else '1'))

					# cool down extruder, dont wait for it
					rmmu.extruder_set_temperature(0, False)					

				# disable toolhead filament sensor
				rmmu.toolhead_filament_sensor.runout_helper.sensor_enabled = False

			# cool toolhead down to standby temp if needed to avoid oozing on the build plate after loading filaments
			if needs_cool_down:
				preheat_extruder_temp = float(self.get_macro_variable("RatOS", "preheat_extruder_temp"))
				self.rmmu[0].extruder_set_temperature(0, False)
				self.ratos_echo("Waiting for extruder T0 to cool down to " + str(preheat_extruder_temp) + "°C...")
				self.gcode.run_script_from_command('TEMPERATURE_WAIT SENSOR="extruder" MINIMUM=0 MAXIMUM=' + str(preheat_extruder_temp))
				if self.dual_carriage != None:
					self.rmmu[1].extruder_set_temperature(0, False)
					self.ratos_echo("Waiting for extruder T1 to cool down to " + str(preheat_extruder_temp) + "°C...")
					self.gcode.run_script_from_command('TEMPERATURE_WAIT SENSOR="extruder1" MINIMUM=0 MAXIMUM=' + str(preheat_extruder_temp))

			# test if all demanded filaments are available and raises an error if not
			if len(self.rmmu[physical_toolhead].parking_t_sensor_endstop) == self.rmmu[physical_toolhead].tool_count:
				self.test_filaments(logical_tools)

			# restore idex mode
			if self.dual_carriage != None:
				act_idex_mode = self.dual_carriage.get_status(self.toolhead.get_last_move_time())['carriage_1'].lower()
				if idex_mode == "copy" and idex_mode != act_idex_mode:
					self.gcode.run_script_from_command('_IDEX_COPY DANCE=0')
				elif idex_mode == "mirror" and idex_mode != act_idex_mode:
					self.gcode.run_script_from_command('_IDEX_MIRROR DANCE=0')

		# call RatOS start print gcode macro
		self.gcode.run_script_from_command('START_PRINT ' + str(param.get_raw_command_parameters().strip()))

	#####
	# Filament presence check
 	#####
	def test_filaments(self, logical_tools):
		# echo
		self.ratos_echo("Testing needed filaments...")

		# test filaments
		for logical_tool in logical_tools:
			rmmu_filament = int(self.mapping[str(logical_tool)]["FILAMENT"])
			# filament = self.get_remapped_toolhead(filament)
			physical_toolhead = int(self.mapping[str(logical_tool)]["TOOLHEAD"])
			rmmu = self.rmmu[physical_toolhead]
			self.ratos_echo("Testing filament T" + str(logical_tool) + "...")
			if not rmmu.test_filament(rmmu_filament):
				self.ratos_echo("Filament T" + str(logical_tool) + " not found!")
				rmmu.select_filament(-1)
				raise self.printer.command_error("Can not start print because Filament T" + str(logical_tool) + " is not available!")

		# get used physical toolheads
		physical_toolheads = []
		for t in logical_tools:
			physical_toolhead = int(self.mapping[str(t)]["TOOLHEAD"])
			if physical_toolhead not in physical_toolheads:
				physical_toolheads.append(physical_toolhead)

		# release idler
		for physical_toolhead in physical_toolheads:
			physical_toolhead = int(self.mapping[str(logical_tool)]["TOOLHEAD"])
			if len(self.rmmu[physical_toolhead].parking_t_sensor_endstop) != self.rmmu[physical_toolhead].tool_count:
				self.rmmu[physical_toolhead].select_filament(-1)

		# echo
		self.ratos_echo("All needed filaments available!")

		# # testing spool join
		# if len(self.spool_joins) > 0:
		# 	self.ratos_echo("Validating spool join...")
		# 	for spool_join in self.spool_joins:
		# 		counter = 0
		# 		for spool in spool_join:
		# 			for i in range(0, self.tool_count):
		# 				if param.get('T' + str(i), "true") == "true":
		# 					if spool == i:
		# 						counter += 1
		# 		if counter > 1:
		# 			raise self.printer.command_error("Can not start print because joined spools are part of the print!")
		# 	self.ratos_echo("Spool join validated!")

	#####
	# Change Filament
	#####
	def change_filament(self, param):
		# parameter
		filament = param.get_int('FILAMENT', None, minval=0, maxval=self.total_tool_count)
		copy_mirror = True if param.get('COPY_MIRROR', 'False').lower() == "true" else False
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
		self.gcode.run_script_from_command('_RMMU_BEFORE_FILAMENT_CHANGE TOOLHEAD=' + str(physical_toolhead) + ' X=' + str(x) + ' Y=' + str(y) + ' WIPE_ACCEL=' + str(self.wipe_accel) + ' COPY_MIRROR=' + str(copy_mirror))

		# enable toolhead filament sensor
		rmmu.toolhead_filament_sensor.runout_helper.sensor_enabled = True

		# check toolhead filament sensor
		if rmmu.is_sensor_triggered(rmmu.toolhead_filament_sensor):
			# unload filament
			loaded_filament = rmmu.get_setting(rmmu.name.lower() + rmmu.VARS_LOADED_FILAMENT)
			if not rmmu.unload_filament(loaded_filament, True):
				rmmu.select_filament(-1)
				self.ratos_echo("Could not unload filament T" + str(loaded_filament) + "!")
				return
		else:
			# toolhead filament sensor false state detected
			self.ratos_echo("Possible sensor failure! Filament sensor should be triggered but it isnt.")
			return

		# load filament
		if not rmmu.load_filament(rmmu_filament, copy_mirror):
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
			rmmu.unload_filament(rmmu_filament, False)
		else:
			raise self.printer.command_error("Can not unload unknown filament!")

		# release idler
		rmmu.select_filament(-1)

	#####
	# Helper
	#####
	def ratos_echo(self, msg):
		self.gcode.run_script_from_command("RATOS_ECHO PREFIX='RMMU' MSG='" + str(msg) + "'")

	def ratos_debug_echo(self, msg):
		self.gcode.run_script_from_command("DEBUG_ECHO PREFIX='RMMU' MSG='" + str(msg) + "'")

	def get_macro_variable(self, macro, variable):
		self.gcode_macro = self.printer.lookup_object("gcode_macro " + macro, None)
		if self.gcode_macro != None:
			variables = self.gcode_macro.get_status(self.toolhead.get_last_move_time())
			if variable in variables:
				return variables[variable]
		return None

#####
# Loader
#####
def load_config(config):
	return RMMU_Hub(config)
