from math import fabs
from re import T

class RMMU:

	# -----------------------------------------------------------------------------------------------------------------------------
	# Initialize
	# -----------------------------------------------------------------------------------------------------------------------------
	def __init__(self, config):
		self.config = config
		self.name = config.get_name()
		self.printer = self.config.get_printer()
		self.reactor = self.printer.get_reactor()
		self.gcode = self.printer.lookup_object('gcode')
		self.toolhead_filament_sensor_t0 = self.printer.lookup_object("filament_switch_sensor toolhead_filament_sensor_t0")

		self.load_settings()
		self.register_commands()
		self.register_handle_connect()

	def load_settings(self):
		self.rmmu_idler = None

		# mmu config
		self.tool_count = self.config.getint('tool_count', 4)
		self.reverse_bowden_length = self.config.getfloat('reverse_bowden_length', 400.0)
		self.toolhead_sensor_to_extruder_gears_distance = self.config.getfloat('toolhead_sensor_to_extruder_gears_distance', 10.0)
		self.extruder_gears_to_cooling_zone_distance = self.config.getfloat('extruder_gears_to_cooling_zone_distance', 40.0)

		# idler config
		self.idler_positions = [102,76,50,24]
		self.idler_speed = self.config.getfloat('idler_speed', 300.0)
		self.idler_accel = self.config.getfloat('idler_accel', 3000.0)
		self.idler_home_position = self.config.getfloat('idler_home_position', 0)
		self.idler_homeing_speed = self.config.getfloat('idler_homeing_speed', 40)
		self.idler_homeing_accel = self.config.getfloat('idler_homeing_accel', 200)

		# filament homing config
		self.filament_homing_speed = self.config.getfloat('filament_homing_speed', 250.0)
		self.filament_homing_accel = self.config.getfloat('filament_homing_accel', 2000.0)
		self.filament_homing_parking_distance = self.config.getfloat('filament_homing_parking_distance', 50.0)

		# filament cooling zone config
		self.cooling_zone_loading_speed = self.config.getfloat('cooling_zone_loading_speed', 50.0)
		self.cooling_zone_loading_accel = self.config.getfloat('cooling_zone_loading_accel', 500)
		self.cooling_zone_parking_distance = self.config.getfloat('cooling_zone_parking_distance', 130.0)

	def register_handle_connect(self):
		self.printer.register_event_handler("klippy:connect", self.execute_handle_connect)

	def execute_handle_connect(self):
		self.toolhead = self.printer.lookup_object('toolhead')
		self.extruder = self.printer.lookup_object('extruder')
		self.pheaters = self.printer.lookup_object('heaters')
		self.heater = self.extruder.get_heater()

		self.rmmu_idler = None
		for manual_stepper in self.printer.lookup_objects('manual_stepper'):
			rail_name = manual_stepper[1].get_steppers()[0].get_name()
			if rail_name == 'manual_stepper rmmu_idler':
				self.rmmu_idler = manual_stepper[1]

	def get_status(self, eventtime):
		return {'name': self.name,
		  'tool_count': self.tool_count,
			'is_homed': self.is_homed,
			'filament_changes': self.filament_changes}

	# -----------------------------------------------------------------------------------------------------------------------------
	# G-Code Registration
	# -----------------------------------------------------------------------------------------------------------------------------
	def register_commands(self):
		self.gcode.register_command('RMMU_HOME', self.cmd_RMMU_HOME, desc=("RMMU_HOME"))
		self.gcode.register_command('RMMU_RESET', self.cmd_RMMU_RESET, desc=("RMMU_RESET"))
		self.gcode.register_command('RMMU_LOAD_TOOL', self.cmd_RMMU_LOAD_TOOL, desc=("RMMU_LOAD_TOOL"))
		self.gcode.register_command('RMMU_SELECT_TOOL', self.cmd_RMMU_SELECT_TOOL, desc=("RMMU_SELECT_TOOL"))
		self.gcode.register_command('RMMU_UNLOAD_TOOL', self.cmd_RMMU_UNLOAD_TOOL, desc=("RMMU_UNLOAD_TOOL"))
		self.gcode.register_command('RMMU_EJECT_FILAMENT', self.cmd_RMMU_EJECT_FILAMENT, desc=("RMMU_EJECT_FILAMENT"))
		self.gcode.register_command('RMMU_CHANGE_TOOL', self.cmd_RMMU_CHANGE_TOOL, desc=("RMMU_CHANGE_TOOL"))
		self.gcode.register_command('RMMU_END_PRINT', self.cmd_RMMU_END_PRINT, desc=("RMMU_END_PRINT"))
		self.gcode.register_command('RMMU_START_PRINT', self.cmd_RMMU_START_PRINT, desc=("RMMU_START_PRINT"))
		self.gcode.register_command('RMMU_HOME_FILAMENT', self.cmd_RMMU_HOME_FILAMENT, desc=("RMMU_HOME_FILAMENT"))
		self.gcode.register_command('RMMU_TEST_FILAMENTS', self.cmd_RMMU_TEST_FILAMENTS, desc=("RMMU_TEST_FILAMENTS"))

	def cmd_RMMU_SELECT_TOOL(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.tool_count)
		if not self.is_homed:
			self.home()
		self.select_tool(tool)

	def cmd_RMMU_LOAD_TOOL(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=0, maxval=self.tool_count)
		temp = param.get_int('TEMP', None, minval=-1, maxval=self.heater.max_temp)
		if not self.is_homed:
			self.home()
		if not self.load_tool(tool, temp):
			self.on_loading_error(tool)
			return
	
	def cmd_RMMU_UNLOAD_TOOL(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.tool_count)
		temp = param.get_int('TEMP', None, minval=-1, maxval=self.heater.max_temp)
		if not self.is_homed:
			self.home()
		if temp > 0:
			self.set_hotend_temperature(temp)
		self.selected_filament = tool
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.unload_tool()

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

	def cmd_RMMU_CHANGE_TOOL(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=0, maxval=self.tool_count)
		if not self.change_tool(tool):
			self.on_loading_error(tool)

	def cmd_RMMU_END_PRINT(self, param):
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.unload_tool()
		self.select_tool(-1)
		self.reset()

	def cmd_RMMU_START_PRINT(self, param):
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
					self.gcode.run_script_from_command('_RMMU_ON_START_PRINT_FILAMENT_TEST_FAILED TOOLHEAD=' + str(i))
					return
		self.ratos_echo("All needed filaments found!")

	def cmd_RMMU_HOME_FILAMENT(self, param):
		tool = param.get_int('TOOLHEAD', None, minval=-1, maxval=self.tool_count)
		if not self.is_homed:
			self.home()
		self.home_filaments(tool)

	# -----------------------------------------------------------------------------------------------------------------------------
	# Home
	# -----------------------------------------------------------------------------------------------------------------------------
	is_homed = False

	def reset(self):
		self.is_homed = False
		self.filament_changes = 0
		self.selected_filament = -1

	def home(self):
		self.ratos_echo("Homing RMMU...")
		self.reset()
		self.home_idler()
		self.is_homed = True
		self.selected_filament = -1
		self.ratos_echo("Hello RMMU!")

	def home_idler(self):
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 ENABLE=1')
		self.rmmu_idler.do_set_position(0.0)
		self.stepper_move(self.rmmu_idler, 2, True, self.idler_homeing_speed, self.idler_homeing_accel)
		self.stepper_homing_move(self.rmmu_idler, -300, True, self.idler_homeing_speed, self.idler_homeing_accel, 1)
		self.rmmu_idler.do_set_position(-1.0)
		self.stepper_move(self.rmmu_idler, self.idler_home_position, True, self.idler_homeing_speed, self.idler_homeing_accel)

	def home_filaments(self, tool):
		if tool >= 0:
			self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(tool) + ' VARIABLE=color VALUE=\'"' + "FFFF00" + "\"\'")
			self.home_filament(tool)
			if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
				self.ratos_echo("Toolhead filament sensor isssue detected! Filament homing stopped!")
				self.gcode.run_script_from_command('MOVE_FILAMENT TOOLHEAD=' + str(i) + ' MOVE=-100 SPEED=150')
		else:
			for i in range(0, self.tool_count):
				self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(i) + ' VARIABLE=color VALUE=\'"' + "FFFF00" + "\"\'")
			for i in range(0, self.tool_count):
				self.home_filament(i)
				if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
					self.ratos_echo("Toolhead filament sensor isssue detected! Filament homing stopped!")
					self.select_tool(i)
					self.gcode.run_script_from_command('MOVE_FILAMENT TOOLHEAD=' + str(i) + ' MOVE=-100 SPEED=150')
					break
		self.select_tool(-1)
		return True

	def home_filament(self, filament):
		# select filament
		self.select_tool(filament)

		# load filament into toolhead filament sensor
		if not self.load_filament_from_reverse_bowden_to_toolhead_sensor():
			self.ratos_echo("Filament " + str(filament) + " not found!")
			self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(filament) + ' VARIABLE=color VALUE=\'"' + "FF0000" + "\"\'")
			return False
		else:
			self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(filament) + ' VARIABLE=color VALUE=\'"' + "00FF00" + "\"\'")

		# unload filament from toolhead filament sensor to reverse bowden 
		if not self.unload_filament_from_toolhead_sensor_to_reverse_bowden():
			self.ratos_echo("Filament " + str(filament) + " stucks in filament sensor!")
			self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(filament) + ' VARIABLE=color VALUE=\'"' + "FF0000" + "\"\'")
			return False
		return True

	# -----------------------------------------------------------------------------------------------------------------------------
	# Autoload
	# -----------------------------------------------------------------------------------------------------------------------------
	def eject_filaments(self, tool):
		if tool >= 0:
			self.eject_filament(tool)
		else:
			for i in range(0, self.tool_count):
				self.eject_filament(i)
		self.select_tool(-1)

	def eject_filament(self, tool):
		self.select_tool(tool)
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 MOVE=-' + str(self.reverse_bowden_length + 100) + ' SPEED=' + str(self.filament_homing_speed) + ' ACCEL=' + str(self.filament_homing_accel))
		self.gcode.run_script_from_command('M400')

	# -----------------------------------------------------------------------------------------------------------------------------
	# Change Tool
	# -----------------------------------------------------------------------------------------------------------------------------
	filament_changes = 0

	def change_tool(self, tool):
		if self.filament_changes > 0:
			self.gcode.run_script_from_command('_RMMU_BEFORE_TOOL_CHANGE TOOLHEAD=' + str(tool))
			if not self.load_tool(tool, -1, "change_tool"):
				return False
			self.gcode.run_script_from_command('_RMMU_AFTER_TOOL_CHANGE TOOLHEAD=' + str(tool))
			self.toolhead_filament_sensor_t0.runout_helper.sensor_enabled = False
		self.filament_changes = self.filament_changes + 1
		return True

	def load_tool(self, tool, temp, origin = ""):
		# set hotend temperature
		if temp > 0:
			self.set_hotend_temperature(temp)

		# home if not homed yet
		if not self.is_homed:
			self.home()

		# set temp if configured and wait for it
		if temp > 0:
			self.ratos_echo("Waiting for heater...")
			self.extruder_set_temperature(temp, True)

		# check hotend temperature
		if not self.extruder_can_extrude():
			self.ratos_echo("Heat up nozzle to " + str(self.heater.min_extrude_temp))
			self.extruder_set_temperature(self.heater.min_extrude_temp, True)

		# enable filament sensor
		self.toolhead_filament_sensor_t0.runout_helper.sensor_enabled = True

		# load filament
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			if not self.unload_tool():
				self.ratos_echo("could not unload tool!")
				return False
		else:
			if origin == "change_tool":
				self.ratos_echo("Possible sensor failure!")
				self.ratos_echo("Filament sensor should be triggered but it isnt!")
				return False

		self.select_tool(tool)
		if not self.load_filament_from_reverse_bowden_to_toolhead_sensor():
			self.ratos_echo("could not load tool to sensor!")
			return False
		if not self.load_filament_from_toolhead_sensor_to_cooling_zone():
			return False
		self.gcode.run_script_from_command('_LOAD_FILAMENT_FROM_COOLING_ZONE_TO_NOZZLE TOOLHEAD=0')

		# success
		self.ratos_echo("Filament " + str(tool) + " loaded.")

		# update frontend
		for i in range(0, self.tool_count):
			if tool == i:
				self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(i) + " VARIABLE=active VALUE=True")
			else:
				self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(i) + " VARIABLE=active VALUE=False")

		# send notification
		if self.filament_changes > 0:
			self.gcode.run_script_from_command('_RMMU_ON_TOOL_HAS_CHANGED TOOLHEAD=' + str(tool))

		return True

	def unload_tool(self):
		self.gcode.run_script_from_command('_RMMU_UNLOAD_FILAMENT_FROM_NOZZLE_TO_COOLING_ZONE TOOLHEAD=' + str(self.selected_filament))
		self.select_tool(self.selected_filament)
		if not self.unload_filament_from_cooling_zone_to_reverse_bowden():
			return False
		self.select_idler(-1)

		# update frontend
		self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(self.selected_filament) + " VARIABLE=active VALUE=False")

		return True

	# -----------------------------------------------------------------------------------------------------------------------------
	# Select Tool
	# -----------------------------------------------------------------------------------------------------------------------------
	selected_filament = -1

	def select_tool(self, tool=-1):
		self.select_idler(tool)
		self.selected_filament = tool

	def select_idler(self, tool):
		if tool >= 0:
			self.stepper_move(self.rmmu_idler, self.idler_positions[tool], True, self.idler_speed, self.idler_accel)
		else:
			self.stepper_move(self.rmmu_idler, self.idler_home_position, True, self.idler_speed, self.idler_accel)

	# -----------------------------------------------------------------------------------------------------------------------------
	# Load Filament
	# -----------------------------------------------------------------------------------------------------------------------------
	def load_filament_from_reverse_bowden_to_toolhead_sensor(self):
		step_distance = 100
		max_step_count = int((self.reverse_bowden_length * 1.2) / step_distance)
		if not bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			for i in range(max_step_count):
				self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 MOVE=' + str(step_distance) + ' SPEED=' + str(self.filament_homing_speed) + ' ACCEL=' + str(self.filament_homing_accel) + ' STOP_ON_ENDSTOP=2')
				if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
					break
		if not bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.ratos_echo("Could not find toolhead filament sensor!")
			return False
		self.ratos_echo("Filament T" + str(self.selected_filament) + " found.")
		return True

	def load_filament_from_toolhead_sensor_to_cooling_zone(self):
		self.synced_move(self.toolhead_sensor_to_extruder_gears_distance + self.extruder_gears_to_cooling_zone_distance, self.cooling_zone_loading_speed, self.cooling_zone_loading_accel)
		push_and_pull_offset = 10
		self.synced_move(-(self.toolhead_sensor_to_extruder_gears_distance + self.extruder_gears_to_cooling_zone_distance - push_and_pull_offset), self.cooling_zone_loading_speed, self.cooling_zone_loading_accel)
		if not bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.ratos_echo("could not load filament into extruder!")
			return False
		self.synced_move(self.toolhead_sensor_to_extruder_gears_distance + self.extruder_gears_to_cooling_zone_distance - push_and_pull_offset, self.cooling_zone_loading_speed, self.cooling_zone_loading_accel)
		self.select_idler(-1)
		return True

	# -----------------------------------------------------------------------------------------------------------------------------
	# Unload Filament
	# -----------------------------------------------------------------------------------------------------------------------------
	def unload_filament_from_cooling_zone_to_reverse_bowden(self):
		self.synced_move(-(self.cooling_zone_parking_distance), self.cooling_zone_loading_speed, self.cooling_zone_loading_accel)
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			return False
		return True

	def unload_filament_from_toolhead_sensor_to_reverse_bowden(self):
		self.select_idler(self.selected_filament)
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 MOVE=-' + str(self.filament_homing_parking_distance) + ' SPEED=' + str(self.filament_homing_speed) + ' ACCEL=' + str(self.filament_homing_accel))
		self.gcode.run_script_from_command('M400')
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			return False
		return True

	# -----------------------------------------------------------------------------------------------------------------------------
	# Evens
	# -----------------------------------------------------------------------------------------------------------------------------
	def on_loading_error(self, tool):
		self.select_idler(-1)
		self.gcode.run_script_from_command("_RMMU_ON_TOOL_LOADING_ERROR TOOLHEAD=" + str(tool))

	# -----------------------------------------------------------------------------------------------------------------------------
	# Helper
	# -----------------------------------------------------------------------------------------------------------------------------
	def ratos_echo(self, msg):
		self.gcode.run_script_from_command("RATOS_ECHO PREFIX='RMMU' MSG='" + str(msg) + "'")

	def ratos_debug_echo(self, prefix, msg):
		self.gcode.run_script_from_command("DEBUG_ECHO PREFIX='" + str(prefix) + "' MSG='" + str(msg) + "'")

	def synced_move(self, move, speed, accel=-1):
		if accel == -1:
			accel = self.toolhead.max_accel
		self.gcode.run_script_from_command('G92 E0')
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 MOVE=' + str(move) + ' SPEED=' + str(speed) + ' ACCEL=' + str(accel) + ' SYNC=0')
		self.gcode.run_script_from_command('G0 E' + str(move) + ' F' + str(speed * 60))
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SYNC=1')
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0')
		self.gcode.run_script_from_command('M400')

	def stepper_move(self, stepper, dist, wait, speed, accel):
		stepper.do_move(dist, speed, accel, True)
		if wait:
			self.toolhead.wait_moves()      

	def stepper_homing_move(self, stepper, dist, wait, speed, accel, homing_move):
		stepper.do_homing_move(dist, speed, accel, homing_move > 0, abs(homing_move) == 1)
		if wait:
			self.toolhead.wait_moves()      

	def set_hotend_temperature(self, temp):
		if temp < self.heater.min_temp:
			self.ratos_echo("Selected temperature " + str(temp) + " too low, must be above " + str(self.heater.min_temp))
			return False
		if temp > self.heater.max_temp:
			self.ratos_echo("Selected temperature " + str(temp) + "too high, must be below " + str(self.heater.max_temp))
			return False
		if temp < self.heater.min_extrude_temp:
			self.ratos_echo("Selected temperature " + str(temp) + " below minimum extrusion temperature " + str(self.heater.min_extrude_temp))
			return False
		self.ratos_echo("Heat up nozzle to " + str(temp))
		self.extruder_set_temperature(temp, False)

	def extruder_set_temperature(self, temperature, wait):
		self.pheaters.set_temperature(self.heater, temperature, wait)

	def extruder_can_extrude(self):
		status = self.extruder.get_status(self.toolhead.get_last_move_time())
		result = status['can_extrude'] 
		return result

# -----------------------------------------------------------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------------------------------------------------------
def load_config(config):
	return RMMU(config)
