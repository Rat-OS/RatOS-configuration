from math import fabs
from re import T

class RMMU:
	#####
	# Initialize
	#####
	def __init__(self, config):
		self.config = config
		self.name = config.get_name()
		self.printer = self.config.get_printer()
		self.reactor = self.printer.get_reactor()
		self.gcode = self.printer.lookup_object('gcode')

		self.load_settings()

		# get toolhead sensor endstop
		query_endstops = self.printer.load_object(self.config, 'query_endstops')
		for i in range(0, len(query_endstops.endstops)):
			if query_endstops.endstops[i][1] == "manual_stepper rmmu_pulley":
				self.toolhead_sensor_endstop = query_endstops.endstops[i][0]
				break

		# create parking endstop
		self.parking_sensor_endstop = None
		if self.parking_endstop_pin is not None:
			ppins = self.printer.lookup_object('pins')
			mcu_endstop = ppins.setup_pin('endstop', self.parking_endstop_pin)
			self.parking_sensor_endstop = mcu_endstop

		self.register_commands()
		self.register_handler()

	#####
	# Handler
	#####
	def register_handler(self):
		self.printer.register_event_handler("klippy:connect", self._connect)
		self.printer.register_event_handler("stepper_enable:motor_off", self._motor_off)

	def _connect(self):
		# get toolhead and extruder
		self.toolhead = self.printer.lookup_object('toolhead')
		self.extruder = self.printer.lookup_object('extruder')

		# get stepper
		self.rmmu_idler = self.printer.lookup_object("manual_stepper rmmu_idler")
		self.rmmu_pulley = self.printer.lookup_object("manual_stepper rmmu_pulley")

		# get filament sensors
		self.toolhead_filament_sensor_t0 = self.printer.lookup_object("filament_switch_sensor toolhead_filament_sensor_t0")

	def _motor_off(self, print_time):
		self.reset()
		self.gcode.run_script_from_command('_LED_MOTORS_OFF')

	#####
	# Settings
	#####
	def load_settings(self):
		# slicer profile settings
		self.travel_speed = 0
		self.travel_accel = 0
		self.wipe_accel = 0

		# mmu config
		self.tool_count = self.config.getint('tool_count', 4)
		self.reverse_bowden_length = self.config.getfloat('reverse_bowden_length', 400.0)
		self.toolhead_sensor_to_extruder_gears_distance = self.config.getfloat('toolhead_sensor_to_extruder_gears_distance', 10.0)
		self.extruder_gears_to_cooling_zone_distance = self.config.getfloat('extruder_gears_to_cooling_zone_distance', 40.0)
		self.parking_endstop_pin = None
		if self.config.get('parking_endstop_pin', None) is not None:
			self.parking_endstop_pin = self.config.get('parking_endstop_pin')

		# idler config
		self.idler_positions = [102,76,50,24]
		self.idler_speed = self.config.getfloat('idler_speed', 300.0)
		self.idler_accel = self.config.getfloat('idler_accel', 3000.0)
		self.idler_home_position = self.config.getfloat('idler_home_position', 0)
		self.idler_homing_speed = self.config.getfloat('idler_homing_speed', 40)
		self.idler_homing_accel = self.config.getfloat('idler_homing_accel', 200)

		# filament homing config
		self.filament_homing_speed = self.config.getfloat('filament_homing_speed', 250.0)
		self.filament_homing_accel = self.config.getfloat('filament_homing_accel', 2000.0)
		self.filament_homing_parking_distance = self.config.getfloat('filament_homing_parking_distance', 50.0)
		self.filament_cleaning_distance = self.config.getfloat('filament_cleaning_distance', 100.0)

		# filament parking config
		self.filament_parking_speed = self.config.getfloat('filament_parking_speed', 300.0)
		self.filament_parking_accel = self.config.getfloat('filament_parking_accel', 2000.0)
		self.filament_parking_distance = self.config.getfloat('filament_parking_distance', 50.0)

		# filament cooling zone config
		self.cooling_zone_loading_speed = self.config.getfloat('cooling_zone_loading_speed', 30.0)
		self.cooling_zone_loading_accel = self.config.getfloat('cooling_zone_loading_accel', 500)
		self.cooling_zone_unloading_speed = self.config.getfloat('cooling_zone_unloading_speed', 50.0)
		self.cooling_zone_unloading_accel = self.config.getfloat('cooling_zone_unloading_accel', 1000)
		self.cooling_zone_unloading_pause = self.config.getfloat('cooling_zone_unloading_pause', 1000.0)
		self.cooling_zone_unloading_distance = self.config.getfloat('cooling_zone_unloading_distance', 130.0)

	#####
	# Status
	#####
	is_homed = False
	filament_changes = 0
	selected_filament = -1

	def get_status(self, eventtime):
		return {'name': self.name,
		  'tool_count': self.tool_count,
		  'is_homed': self.is_homed,
		  'filament_changes': self.filament_changes,
		  'selected_filament': self.selected_filament}

	def reset(self):
		self.is_homed = False
		self.filament_changes = 0
		self.selected_filament = -1
		for i in range(0, self.tool_count):
			self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(i) + " VARIABLE=active VALUE=False")
			self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(i) + ' VARIABLE=color VALUE=\'"' + "FFFF00" + "\"\'")

	#####
	# G-Code Commands
	#####
	def register_commands(self):
		self.gcode.register_command('RMMU_ENABLE_PARKING_ENDSTOP', self.cmd_RMMU_ENABLE_PARKING_ENDSTOP, desc=("RMMU_ENABLE_PARKING_ENDSTOP"))
		self.gcode.register_command('RMMU_ENABLE_TOOLHEAD_ENDSTOP', self.cmd_RMMU_ENABLE_TOOLHEAD_ENDSTOP, desc=("RMMU_ENABLE_TOOLHEAD_ENDSTOP"))

		self.gcode.register_command('RMMU_HOME', self.cmd_RMMU_HOME, desc=("RMMU_HOME"))
		self.gcode.register_command('RMMU_RESET', self.cmd_RMMU_RESET, desc=("RMMU_RESET"))
		self.gcode.register_command('RMMU_LOAD_FILAMENT', self.cmd_RMMU_LOAD_FILAMENT, desc=("RMMU_LOAD_FILAMENT"))
		self.gcode.register_command('RMMU_SELECT_FILAMENT', self.cmd_RMMU_SELECT_FILAMENT, desc=("RMMU_SELECT_FILAMENT"))
		self.gcode.register_command('RMMU_UNLOAD_FILAMENT', self.cmd_RMMU_UNLOAD_FILAMENT, desc=("RMMU_UNLOAD_FILAMENT"))
		self.gcode.register_command('RMMU_EJECT_FILAMENT', self.cmd_RMMU_EJECT_FILAMENT, desc=("RMMU_EJECT_FILAMENT"))
		self.gcode.register_command('RMMU_CHANGE_FILAMENT', self.cmd_RMMU_CHANGE_FILAMENT, desc=("RMMU_CHANGE_FILAMENT"))
		self.gcode.register_command('RMMU_END_PRINT', self.cmd_RMMU_END_PRINT, desc=("RMMU_END_PRINT"))
		self.gcode.register_command('RMMU_START_PRINT', self.cmd_RMMU_START_PRINT, desc=("RMMU_START_PRINT"))
		self.gcode.register_command('RMMU_HOME_FILAMENT', self.cmd_RMMU_HOME_FILAMENT, desc=("RMMU_HOME_FILAMENT"))
		self.gcode.register_command('RMMU_TEST_FILAMENTS', self.cmd_RMMU_TEST_FILAMENTS, desc=("RMMU_TEST_FILAMENTS"))

	def cmd_RMMU_ENABLE_PARKING_ENDSTOP(self, param):
		self.set_pulley_endstop(self.parking_sensor_endstop)

	def cmd_RMMU_ENABLE_TOOLHEAD_ENDSTOP(self, param):
		self.set_pulley_endstop(self.toolhead_sensor_endstop)

	def cmd_RMMU_SELECT_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.tool_count)
		if not self.is_homed:
			self.home()
		self.select_idler(tool)

	def cmd_RMMU_LOAD_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=0, maxval=self.tool_count)
		if not self.is_homed:
			self.home()
		if not self.load_filament(tool):
			self.on_loading_error(tool)
			return
	
	def cmd_RMMU_UNLOAD_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.tool_count)
		if not self.is_homed:
			self.home()
		self.selected_filament = tool
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.unload_filament()

	def cmd_RMMU_EJECT_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.tool_count)
		if not self.is_homed:
			self.home()
		self.eject_filaments(tool)

	def cmd_RMMU_HOME(self, param):
		self.is_homed = False
		self.home()

	def cmd_RMMU_RESET(self, param):
		self.reset()

	def cmd_RMMU_CHANGE_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=0, maxval=self.tool_count)
		x = param.get_float('X', None, minval=-1, maxval=999)
		y = param.get_float('Y', None, minval=-1, maxval=999)
		if not self.change_filament(tool, x, y):
			self.on_loading_error(tool)

	def cmd_RMMU_END_PRINT(self, param):
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.unload_filament()
		self.select_filament(-1)
		self.reset()

	def cmd_RMMU_START_PRINT(self, param):
		self.travel_speed = param.get_int('TRAVEL_SPEED', None, minval=0, maxval=1000)
		self.travel_accel = param.get_int('TRAVEL_ACCEL', None, minval=0, maxval=100000)
		self.wipe_accel = param.get_int('WIPE_ACCEL', None, minval=0, maxval=100000)
		self.filament_changes = 0
		self.toolhead_filament_sensor_t0.runout_helper.sensor_enabled = False

	def cmd_RMMU_TEST_FILAMENTS(self, param):
		self.ratos_echo("Testing needed filaments...")
		if not self.is_homed:
			self.home()
		for i in range(0, self.tool_count):
			toolhead_used = param.get('T' + str(i), "true") 
			if toolhead_used == "true":
				if not self.home_filament(i):
					self.select_filament(-1)
					self.gcode.run_script_from_command('_RMMU_ON_START_PRINT_FILAMENT_TEST_FAILED TOOLHEAD=' + str(i))
					return
		self.select_filament(-1)
		self.ratos_echo("All needed filaments found!")

	def cmd_RMMU_HOME_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.tool_count)
		if not self.is_homed:
			self.home()
		self.home_filaments(tool)

	#####
	# Endstops
	#####
	def set_pulley_endstop(self, endstop):
		self._unregister_endstop()
		self._register_endstop(endstop)

	def _unregister_endstop(self):
		remove_id = -1
		query_endstops = self.printer.load_object(self.config, 'query_endstops')
		for i in range(0, len(query_endstops.endstops)):
			if query_endstops.endstops[i][1] == "manual_stepper rmmu_pulley":
				remove_id = i
				break
		if remove_id != -1:
			query_endstops.endstops.pop(remove_id)
			self.rmmu_pulley.rail.endstop_map = {}
			self.rmmu_pulley.rail.endstops.pop(0)

	def _register_endstop(self, endstop):
		query_endstops = self.printer.load_object(self.config, 'query_endstops')
		query_endstops.register_endstop(endstop, "manual_stepper rmmu_pulley")
		self.rmmu_pulley.rail.endstops.append((endstop, "manual_stepper rmmu_pulley"))
		endstop.add_stepper(self.rmmu_pulley.get_steppers()[0])

	#####
	# Home
	#####
	def home(self):
		self.ratos_echo("Homing RMMU...")
		self.reset()
		self.home_idler()
		self.is_homed = True
		self.selected_filament = -1
		self.ratos_echo("Hello RMMU!")

	def home_idler(self):
		self.rmmu_pulley.do_set_position(0.0)
		self.rmmu_idler.do_set_position(0.0)
		self.stepper_move(self.rmmu_idler, 2, True, self.idler_homing_speed, self.idler_homing_accel)
		self.stepper_homing_move(self.rmmu_idler, -300, self.idler_homing_speed, self.idler_homing_accel, 1)
		self.rmmu_idler.do_set_position(-1.0)
		self.stepper_move(self.rmmu_idler, self.idler_home_position, True, self.idler_homing_speed, self.idler_homing_accel)

	def home_filaments(self, tool):
		if tool >= 0:
			# update frontend
			self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(tool) + ' VARIABLE=color VALUE=\'"' + "FFFF00" + "\"\'")

			# home filament
			self.home_filament(tool)
			if self.parking_sensor_endstop != None:
				if self.is_endstop_triggered(self.parking_sensor_endstop):
					self.ratos_echo("Parking filament sensor isssue detected! Filament homing stopped!")
					self.gcode.run_script_from_command('MOVE_FILAMENT TOOLHEAD=' + str(i) + ' MOVE=-100 SPEED=150')
			else:
				if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
					self.ratos_echo("Toolhead filament sensor isssue detected! Filament homing stopped!")
					self.gcode.run_script_from_command('MOVE_FILAMENT TOOLHEAD=' + str(i) + ' MOVE=-100 SPEED=150')
		else:
			# update frontend
			for i in range(0, self.tool_count):
				self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(i) + ' VARIABLE=color VALUE=\'"' + "FFFF00" + "\"\'")

			# home all filaments
			for i in range(0, self.tool_count):
				self.home_filament(i)
				if self.parking_sensor_endstop != None:
					if self.is_endstop_triggered(self.parking_sensor_endstop):
						self.ratos_echo("Parking filament sensor isssue detected! Filament homing stopped!")
						self.select_filament(i)
						self.gcode.run_script_from_command('MOVE_FILAMENT TOOLHEAD=' + str(i) + ' MOVE=-100 SPEED=150')
						break
				else:
					if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
						self.ratos_echo("Toolhead filament sensor isssue detected! Filament homing stopped!")
						self.select_filament(i)
						self.gcode.run_script_from_command('MOVE_FILAMENT TOOLHEAD=' + str(i) + ' MOVE=-100 SPEED=150')
						break

		self.select_filament(-1)
		return True

	def home_filament(self, filament):
		# select filament
		self.select_filament(filament)

		if self.parking_sensor_endstop != None:
			# load filament into parking filament sensor 
			if not self.load_filament_from_parking_position_to_parking_sensor(filament):
				return False

			# park filament 
			if not self.unload_filament_from_parking_sensor_to_parking_position(filament):
				return False

		else:
			# load filament into toolhead filament sensor
			if not self.load_filament_from_reverse_bowden_to_toolhead_sensor(filament):
				self.ratos_echo("Filament T" + str(filament) + " not found!")
				self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(filament) + ' VARIABLE=color VALUE=\'"' + "FF0000" + "\"\'")
				return False
			else:
				self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(filament) + ' VARIABLE=color VALUE=\'"' + "00FF00" + "\"\'")

			# unload filament from toolhead filament sensor to reverse bowden 
			if not self.unload_filament_from_toolhead_sensor_to_reverse_bowden(filament):
				self.ratos_echo("Filament T" + str(filament) + " stucks in filament sensor!")
				self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(filament) + ' VARIABLE=color VALUE=\'"' + "FF0000" + "\"\'")
				return False

		# success
		self.ratos_echo("Filament T" + str(filament) + " found!")
		return True

	#####
	# Change Filament
	#####
	def change_filament(self, tool, x, y):
		if self.filament_changes > 0:
			self.gcode.run_script_from_command('_RMMU_BEFORE_FILAMENT_CHANGE TOOLHEAD=' + str(tool) + ' X=' + str(x) + ' Y=' + str(y) + ' TRAVEL_SPEED=' + str(self.travel_speed) + ' TRAVEL_ACCEL=' + str(self.travel_accel) + ' WIPE_ACCEL=' + str(self.wipe_accel))
			if not self.load_filament(tool, "change_filament"):
				return False
			self.gcode.run_script_from_command('_RMMU_AFTER_FILAMENT_CHANGE TOOLHEAD=' + str(tool))
			self.toolhead_filament_sensor_t0.runout_helper.sensor_enabled = False
		self.filament_changes = self.filament_changes + 1
		return True

	def load_filament(self, tool, origin = ""):
		# home if not homed yet
		if not self.is_homed:
			self.home()

		# toolhead filament sensor check
		self.toolhead_filament_sensor_t0.runout_helper.sensor_enabled = True
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			if not self.unload_filament():
				self.ratos_echo("Could not unload filament T" + str(tool) + "!")
				return False
		else:
			if origin == "change_filament":
				self.ratos_echo("Possible sensor failure!")
				self.ratos_echo("Filament sensor should be triggered but it isnt!")
				return False

		# load filament to toolhead sensor
		self.select_filament(tool)
		if self.parking_sensor_endstop != None:
			if not self.load_filament_from_parking_position_to_parking_sensor(tool):
				return False
			if not self.load_filament_from_parking_sensor_to_toolhead_sensor(tool):
				return False
		else:
			if not self.load_filament_from_reverse_bowden_to_toolhead_sensor(tool):
				self.ratos_echo("Could not load filament T" + str(tool) + "into sensor!")
				return False

		# load filament into hotend
		if not self.load_filament_from_toolhead_sensor_to_cooling_zone(tool):
			return False
		self.gcode.run_script_from_command('_LOAD_FILAMENT_FROM_COOLING_ZONE_TO_NOZZLE TOOLHEAD=0 PURGE=False')
		self.ratos_echo("Filament T" + str(tool) + " loaded.")

		# update frontend
		for i in range(0, self.tool_count):
			if tool == i:
				self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(i) + " VARIABLE=active VALUE=True")
			else:
				self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(i) + " VARIABLE=active VALUE=False")

		# send notification
		if self.filament_changes > 0:
			self.gcode.run_script_from_command('_RMMU_ON_FILAMENT_HAS_CHANGED TOOLHEAD=' + str(tool))

		# success 
		return True

	def unload_filament(self):

		# unload filament 
		self.gcode.run_script_from_command('_RMMU_UNLOAD_FILAMENT_FROM_NOZZLE_TO_COOLING_ZONE TOOLHEAD=' + str(self.selected_filament) + ' PAUSE=' + str(self.cooling_zone_unloading_pause))
		self.select_filament(self.selected_filament)
		if not self.unload_filament_from_cooling_zone_to_reverse_bowden(self.selected_filament):
			return False

		# park filament 
		if self.parking_sensor_endstop != None:
			if not self.unload_filament_from_reverse_bowden_to_parking_sensor(self.selected_filament):
				return False
			if not self.unload_filament_from_parking_sensor_to_parking_position(self.selected_filament):
				return False

		# success 
		self.select_idler(-1)
		self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(self.selected_filament) + " VARIABLE=active VALUE=False")
		self.ratos_echo("Filament T" + str(self.selected_filament) + " unloaded!")
		return True

	#####
	# Select Filament
	#####
	def select_filament(self, tool=-1):
		self.select_idler(tool)
		self.selected_filament = tool

	def select_idler(self, tool):
		if tool >= 0:
			self.stepper_move(self.rmmu_idler, self.idler_positions[tool], True, self.idler_speed, self.idler_accel)
		else:
			self.stepper_move(self.rmmu_idler, self.idler_home_position, True, self.idler_speed, self.idler_accel)

	#####
	# Load Filament
	#####
	def load_filament_from_parking_position_to_parking_sensor(self, tool):
		# enable parking sensor endstop
		self.set_pulley_endstop(self.parking_sensor_endstop)

		# homing move
		max_step_count = 5
		if not self.is_endstop_triggered(self.parking_sensor_endstop):
			for i in range(max_step_count):
				self.stepper_homing_move(self.rmmu_pulley, self.filament_parking_distance + 10, self.filament_homing_speed, self.filament_homing_accel, 2)
				if self.is_endstop_triggered(self.parking_sensor_endstop):
					break

		# check sensor and try to fix issues if needed
		if not self.is_endstop_triggered(self.parking_sensor_endstop):
			self.ratos_echo("Could not load filament T" + str(tool) + " into parking sensor!")
			try_count = 3
			move_distance = 30
			for i in range(1, try_count):
				self.ratos_echo("Retry " + str(i) + " ...")
				self.stepper_move(self.rmmu_pulley, move_distance, True, self.filament_homing_speed / i, self.filament_homing_accel / i)
				if self.is_endstop_triggered(self.parking_sensor_endstop):
					self.ratos_echo("Problem solved!")
					break

		# check sensor
		if not self.is_endstop_triggered(self.parking_sensor_endstop):
			self.ratos_echo("Could not load filament T" + str(tool) + " into parking sensor!")
			return False

		# success
		return True

	def load_filament_from_parking_sensor_to_toolhead_sensor(self, tool):
		# enable toolhead sensor endstop
		self.set_pulley_endstop(self.toolhead_sensor_endstop)

		# long homing move to toolhead sensor
		if not self.is_endstop_triggered(self.toolhead_sensor_endstop):
			self.stepper_homing_move(self.rmmu_pulley, self.reverse_bowden_length + 50, self.filament_homing_speed, self.filament_homing_accel, 2)

		# short homing moves in case long one wasnt successfull
		if not self.is_endstop_triggered(self.toolhead_sensor_endstop):
			step_distance = 20
			max_step_count = 10
			if not self.is_endstop_triggered(self.toolhead_sensor_endstop):
				for i in range(max_step_count):
					self.stepper_homing_move(self.rmmu_pulley, step_distance, self.filament_homing_speed, self.filament_homing_accel, 2)
					if self.is_endstop_triggered(self.toolhead_sensor_endstop):
						break

		# check sensor
		if not self.is_endstop_triggered(self.toolhead_sensor_endstop):
			self.ratos_echo("Could not load filament T" + str(tool) + " into parking sensor!")
			return False

		# success
		return True

	def load_filament_from_reverse_bowden_to_toolhead_sensor(self, tool):
		step_distance = 100
		max_step_count = int((self.reverse_bowden_length * 1.2) / step_distance)
		if not bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			for i in range(max_step_count):
				self.stepper_homing_move(self.rmmu_pulley, step_distance, self.filament_homing_speed, self.filament_homing_accel, 2)
				if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
					break
		if not bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.ratos_echo("Could not find toolhead filament sensor!")
			return False
		self.ratos_echo("Filament T" + str(self.selected_filament) + " found.")
		return True

	def load_filament_from_toolhead_sensor_to_cooling_zone(self, tool):
		for i in range(1, 3):
			if not self.push_and_pull_test(self.cooling_zone_loading_speed / i, self.cooling_zone_loading_accel / i):
				self.stepper_synced_move(-100, self.cooling_zone_loading_speed / i, self.cooling_zone_loading_accel / i)
				if not self.load_filament_from_reverse_bowden_to_toolhead_sensor(tool):
					self.stepper_synced_move(-100, self.cooling_zone_loading_speed / i, self.cooling_zone_loading_accel / i)
					self.select_idler(-1)
					return False
			else:
				self.stepper_synced_move(self.extruder_gears_to_cooling_zone_distance + self.toolhead_sensor_to_extruder_gears_distance / 2, self.cooling_zone_loading_speed / i, self.cooling_zone_loading_accel / i)
				self.select_idler(-1)
				return True
		self.stepper_synced_move(-100, self.cooling_zone_loading_speed, self.cooling_zone_loading_accel)
		self.select_idler(-1)
		return False

	def push_and_pull_test(self, loading_speed, loading_accel):
		self.ratos_echo("Push and pull test...")
		self.stepper_synced_move(self.extruder_gears_to_cooling_zone_distance + self.toolhead_sensor_to_extruder_gears_distance, loading_speed, loading_accel)
		self.stepper_synced_move(-(self.extruder_gears_to_cooling_zone_distance + self.toolhead_sensor_to_extruder_gears_distance / 2), loading_speed, loading_accel)
		return bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present)

	#####
	# Unload Filament
	#####
	def unload_filament_from_reverse_bowden_to_parking_sensor(self, tool):
		# enable parking sensor endstop
		self.set_pulley_endstop(self.parking_sensor_endstop)

		# long homing move to parking sensor
		self.stepper_homing_move(self.rmmu_pulley, -(self.reverse_bowden_length + 50), self.filament_homing_speed, self.filament_homing_accel, -2)

		# short homing moves in case long one wasnt successfull
		if not self.is_endstop_triggered(self.parking_sensor_endstop):
			step_distance = 20
			max_step_count = 10
			if self.is_endstop_triggered(self.parking_sensor_endstop):
				for i in range(max_step_count):
					self.stepper_homing_move(self.rmmu_pulley, step_distance, self.filament_homing_speed, self.filament_homing_accel, -2)
					if not self.is_endstop_triggered(self.parking_sensor_endstop):
						break

		# check sensor and try to fix issues if needed
		if self.is_endstop_triggered(self.parking_sensor_endstop):
			self.ratos_echo("Could not unload filament T" + str(tool) + " to parking sensor!")
			try_count = 5
			move_distance = 50
			for i in range(1, try_count):
				self.ratos_echo("Retry " + str(i) + " ...")
				self.stepper_move(self.rmmu_pulley, -move_distance, True, self.filament_homing_speed / i, self.filament_homing_accel / i)
				if not self.is_endstop_triggered(self.parking_sensor_endstop):
					self.ratos_echo("Problem solved!")
					break

		# check sensor
		if self.is_endstop_triggered(self.toolhead_sensor_endstop):
			self.ratos_echo("Could not unload filament T" + str(tool) + " to parking sensor!")
			return False

		# success
		return True

	def unload_filament_from_parking_sensor_to_parking_position(self, tool):
		# park filament
		self.rmmu_pulley.do_set_position(0.0)
		self.stepper_move(self.rmmu_pulley, -self.filament_parking_distance, True, self.filament_homing_speed, self.filament_homing_accel)

		# check sensor and try to fix issues if needed
		if self.is_endstop_triggered(self.parking_sensor_endstop):
			self.ratos_echo("Could not unload filament T" + str(tool) + " from parking sensor!")
			try_count = 3
			move_distance = 30
			for i in range(1, try_count):
				self.ratos_echo("Retry " + str(i) + " ...")
				self.stepper_move(self.rmmu_pulley, -move_distance, True, self.filament_homing_speed / i, self.filament_homing_accel / i)
				if not self.is_endstop_triggered(self.parking_sensor_endstop):
					self.ratos_echo("Problem solved!")
					break

		# check sensor
		if self.is_endstop_triggered(self.parking_sensor_endstop):
			self.ratos_echo("Could not unload filament T" + str(tool) + " from parking sensor!")
			return False

		# success
		return True

	def unload_filament_from_cooling_zone_to_reverse_bowden(self, tool):
		self.ratos_echo("Unload filament T" + str(tool) + " from cooling zone to reverse bowden...")
		self.stepper_synced_move(-(self.cooling_zone_unloading_distance), self.cooling_zone_unloading_speed, self.cooling_zone_unloading_accel)
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.ratos_echo("Could not unload filament T" + str(tool) + " from cooling zone to reverse bowden!")
			if self.filament_cleaning_distance > 0:
				self.ratos_echo("Trying to clean the toolhead filament sensor...")
				self.stepper_move(self.rmmu_pulley, self.filament_cleaning_distance, True, self.filament_homing_speed, self.filament_homing_accel)
				self.stepper_move(self.rmmu_pulley, -(self.filament_cleaning_distance * 2), True, self.filament_homing_speed, self.filament_homing_accel)
				if not bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
					self.ratos_echo("Toolhead filament sensor successfully cleaned!")
					return True
				self.ratos_echo("Could not clean toolhead filament sensor!")
			return False
		return True

	def unload_filament_from_toolhead_sensor_to_reverse_bowden(self, tool):
		self.select_idler(self.selected_filament)
		self.rmmu_pulley.do_set_position(0.0)
		self.stepper_move(self.rmmu_pulley, -self.filament_homing_parking_distance, True, self.filament_homing_speed, self.filament_homing_accel)
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.ratos_echo("Could not unload filament T" + str(tool) + " from toolhead sensor to reverse bowden!")
			return False
		return True

	#####
	# Eject Filament
	#####
	def eject_filaments(self, tool):
		if tool >= 0:
			self.eject_filament(tool)
		else:
			for i in range(0, self.tool_count):
				self.eject_filament(i)
		self.select_filament(-1)

	def eject_filament(self, tool):
		self.select_filament(tool)
		self.rmmu_pulley.do_set_position(0.0)
		self.stepper_move(self.rmmu_pulley, -(self.reverse_bowden_length + 100), True, self.filament_homing_speed, self.filament_homing_accel)

	#####
	# Evens
	#####
	def on_loading_error(self, tool):
		self.select_idler(-1)
		self.gcode.run_script_from_command("_RMMU_ON_FILAMENT_LOADING_ERROR TOOLHEAD=" + str(tool))

	#####
	# Helper
	#####
	def ratos_echo(self, msg):
		self.gcode.run_script_from_command("RATOS_ECHO PREFIX='RMMU' MSG='" + str(msg) + "'")

	def ratos_debug_echo(self, prefix, msg):
		self.gcode.run_script_from_command("DEBUG_ECHO PREFIX='" + str(prefix) + "' MSG='" + str(msg) + "'")

	def stepper_synced_move(self, move, speed, accel=-1):
		if accel == -1:
			accel = self.toolhead.max_accel
		self.gcode.run_script_from_command('G92 E0')
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 MOVE=' + str(move) + ' SPEED=' + str(speed) + ' ACCEL=' + str(accel) + ' SYNC=0')
		self.gcode.run_script_from_command('G0 E' + str(move) + ' F' + str(speed * 60))
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SYNC=1')
		self.rmmu_pulley.do_set_position(0.0)
		self.toolhead.wait_moves()      

	def stepper_move(self, stepper, dist, wait, speed, accel):
		stepper.do_move(dist, speed, accel, True)
		if wait:
			self.toolhead.wait_moves()      

	def stepper_homing_move(self, stepper, dist, speed, accel, homing_move):
		stepper.do_set_position(0.0)
		stepper.do_homing_move(dist, speed, accel, homing_move > 0, abs(homing_move) == 1)
		self.toolhead.wait_moves()      

	def is_endstop_triggered(self, endstop):
		return bool(endstop.query_endstop(self.printer.lookup_object('toolhead').get_last_move_time()))     

# -----------------------------------------------------------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------------------------------------------------------
def load_config(config):
	return RMMU(config)
