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

		# config
		self.tool_count = self.config.getint('tool_count', 2)
		self.extruder_push_and_pull_test = self.config.getfloat('extruder_push_and_pull_test', 1) == 1
		self.nozzle_loading_speed_mms = self.config.getfloat('nozzle_loading_speed_mms', 10.0)
		self.toolhead_sensor_to_bowden_cache_mm = self.config.getfloat('toolhead_sensor_to_bowden_cache_mm', 50.0)
		self.reverse_bowden_length = self.config.getfloat('reverse_bowden_length', 100.0)
		self.toolhead_sensor_to_extruder_gear_mm = self.config.getfloat('toolhead_sensor_to_extruder_gear_mm', 10.0)
		self.extruder_gear_to_parking_position_mm = self.config.getfloat('extruder_gear_to_parking_position_mm', 40.0)
		self.parking_position_to_nozzle_mm = self.config.getfloat('parking_position_to_nozzle_mm', 55.0)

		# idler config
		self.idler_speed = self.config.getfloat('idler_speed', 250.0)
		self.idler_accel = self.config.getfloat('idler_accel', 1000.0)
		self.idler_home_position = self.config.getfloat('idler_home_position', 0)
		self.idler_homeing_speed = self.config.getfloat('idler_homeing_speed', 40)
		self.idler_homeing_accel = self.config.getfloat('idler_homeing_accel', 200)
		self.idler_positions = [102,76,50,24]

		# filament config
		self.filament_homing_speed = self.config.getfloat('filament_homing_speed', 150.0)
		self.filament_homing_accel = self.config.getfloat('filament_homing_accel', 500.0)
		self.filament_parking_speed_mms = self.config.getfloat('filament_parking_speed_mms', 50.0)
		self.filament_parking_accel = self.config.getfloat('filament_parking_accel', 500)

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
		self.gcode.register_command('RMMU_LOAD_TOOL', self.cmd_RMMU_LOAD_TOOL, desc=("RMMU_LOAD_TOOL"))
		self.gcode.register_command('RMMU_SELECT_TOOL', self.cmd_RMMU_SELECT_TOOL, desc=("RMMU_SELECT_TOOL"))
		self.gcode.register_command('RMMU_UNLOAD_TOOL', self.cmd_RMMU_UNLOAD_TOOL, desc=("RMMU_UNLOAD_TOOL"))
		self.gcode.register_command('RMMU_EJECT_FILAMENT', self.cmd_RMMU_EJECT_FILAMENT, desc=("RMMU_EJECT_FILAMENT"))
		self.gcode.register_command('RMMU_CHANGE_TOOL', self.cmd_RMMU_CHANGE_TOOL, desc=("RMMU_CHANGE_TOOL"))
		self.gcode.register_command('RMMU_END_PRINT', self.cmd_RMMU_END_PRINT, desc=("RMMU_END_PRINT"))
		self.gcode.register_command('RMMU_START_PRINT', self.cmd_RMMU_START_PRINT, desc=("RMMU_START_PRINT"))
		self.gcode.register_command('RMMU_HOME_FILAMENT', self.cmd_RMMU_HOME_FILAMENT, desc=("RMMU_HOME_FILAMENT"))

	def cmd_RMMU_SELECT_TOOL(self, param):
		tool = param.get_int('TOOL', None, minval=-1, maxval=self.tool_count)
		self.select_tool(tool)

	def cmd_RMMU_LOAD_TOOL(self, param):
		self.cmd_origin = "gcode"
		tool = param.get_int('TOOL', None, minval=0, maxval=self.tool_count)
		temp = param.get_int('TEMP', None, minval=-1, maxval=self.heater.max_temp)
		if not self.load_tool(tool, temp):
			self.pause_rmmu()
			return
	
	def cmd_RMMU_UNLOAD_TOOL(self, param):
		self.cmd_origin = "gcode"
		tool = param.get_int('TOOL', None, minval=-1, maxval=self.tool_count)
		temp = param.get_int('TEMP', None, minval=-1, maxval=self.heater.max_temp)
		if temp > 0:
			self.set_hotend_temperature(temp)
		self.Selected_Filament = tool
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.unload_tool()

	def cmd_RMMU_EJECT_FILAMENT(self, param):
		tool = param.get_int('TOOL', None, minval=-1, maxval=self.tool_count)
		if not self.is_homed:
			if not self.home():
				return
		self.eject_filaments(tool)

	def cmd_RMMU_HOME(self, param):
		self.is_homed = False
		if not self.home():
			self.gcode.respond_raw("Can not home RMMU!")

	def cmd_RMMU_CHANGE_TOOL(self, param):
		tool = param.get_int('TOOL', None, minval=0, maxval=self.tool_count)
		if not self.change_tool(tool):
			self.pause_rmmu()

	def cmd_RMMU_END_PRINT(self, param):
		self.cmd_origin = "gcode"
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			self.unload_tool()
		self.select_tool(-1)
		self.reset()

	def cmd_RMMU_START_PRINT(self, param):
		self.cmd_origin = "rmmu"
		self.mode = "native"
		self.filament_changes = 0
		self.exchange_old_position = None

		cooling_tube_retraction = param.get_float('COOLING_TUBE_RETRACTION', None, minval=0, maxval=999) 
		cooling_tube_length = param.get_float('COOLING_TUBE_LENGTH', None, minval=0, maxval=999) 
		parking_pos_retraction = param.get_float('PARKING_POS_RETRACTION', None, minval=0, maxval=999) 
		extra_loading_move = param.get_float('EXTRA_LOADING_MOVE', None, minval=-999, maxval=999) 
		if cooling_tube_retraction == 0 and cooling_tube_length == 0 and parking_pos_retraction == 0 and extra_loading_move == 0:
			self.mode = "native"
		else:
			self.mode = "slicer"
		
		for i in range(0, self.tool_count):
			filament_color = param.get('COLOR' + ("" if i == 0 else "_" + str(i)), None) 
			if filament_color != "":
				self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(i) + ' VARIABLE=color VALUE=\'"' + str(filament_color) + "\"\'")

		self.toolhead_filament_sensor_t0.runout_helper.sensor_enabled = False

	def cmd_RMMU_HOME_FILAMENT(self, param):
		tool = param.get_int('TOOL', None, minval=-1, maxval=self.tool_count)
		if not self.is_homed:
			if not self.home():
				return 
		self.home_filaments(tool)

	# -----------------------------------------------------------------------------------------------------------------------------
	# Home
	# -----------------------------------------------------------------------------------------------------------------------------
	is_homed = False

	def reset(self):
		self.is_homed = False
		for i in range(0, self.tool_count):
			self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(i) + ' VARIABLE=color VALUE=\'"' + "FFFF00" + "\"\'")

	def home(self):
		self.gcode.respond_raw("Homing RMMU...")
		self.reset()
		if not self.can_home():
			return False
		self.home_idler()
		self.is_homed = True
		self.Selected_Filament = -1
		self.gcode.respond_raw("Hello RMMU!")
		return True

	def can_home(self):
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			# check hotend temperature
			if not self.extruder_can_extrude():
				self.gcode.respond_raw("Preheat Nozzle to " + str(self.heater.min_extrude_temp + 10))
				self.extruder_set_temperature(self.heater.min_extrude_temp + 10, True)
			# unload filament from nozzle
			if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
				if not self.unload_tool():
					self.gcode.respond_raw("Can not unload from nozzle!")
					return False
			# turn off hotend heater
			self.extruder_set_temperature(0, False)
			# check filament sensor
			if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
				self.gcode.respond_raw("Filament stuck in extruder!")
				return False
		return True

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
				self.gcode.respond_raw("Toolhead filament sensor isssue detected! Filament homing stopped!")
				self.gcode.run_script_from_command('MOVE_FILAMENT TOOLHEAD=' + str(i) + ' MOVE=-100 SPEED=150')
		else:
			for i in range(0, self.tool_count):
				self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(i) + ' VARIABLE=color VALUE=\'"' + "FFFF00" + "\"\'")
			for i in range(0, self.tool_count):
				self.home_filament(i)
				if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
					self.gcode.respond_raw("Toolhead filament sensor isssue detected! Filament homing stopped!")
					self.select_tool(i)
					self.gcode.run_script_from_command('MOVE_FILAMENT TOOLHEAD=' + str(i) + ' MOVE=-100 SPEED=150')
					break
		self.select_tool(-1)
		return True

	def home_filament(self, filament):
		self.select_tool(filament)
		if not self.load_filament_from_reverse_bowden_to_toolhead_sensor():
			self.gcode.respond_raw("Filament " + str(filament) + " not found!")
			self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(filament) + ' VARIABLE=color VALUE=\'"' + "FF0000" + "\"\'")
			return False
		else:
			self.gcode.run_script_from_command('SET_GCODE_VARIABLE MACRO=T' + str(filament) + ' VARIABLE=color VALUE=\'"' + "00FF00" + "\"\'")
		if not self.unload_filament_from_toolhead_sensor():
			self.gcode.respond_raw("Filament " + str(filament) + " stucks in filament sensor!")
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

	# -----------------------------------------------------------------------------------------------------------------------------
	# Change Tool
	# -----------------------------------------------------------------------------------------------------------------------------
	mode = "native"
	cmd_origin = "rmmu"

	filament_changes = 0
	exchange_old_position = None

	def change_tool(self, tool):
		self.cmd_origin = "rmmu"
		if self.filament_changes > 0:
			self.before_change()
			if not self.load_tool(tool, -1):
				return False
			self.toolhead_filament_sensor_t0.runout_helper.sensor_enabled = False
		self.filament_changes = self.filament_changes + 1
		return True

	def load_tool(self, tool, temp):
		# set hotend temperature
		if temp > 0:
			self.set_hotend_temperature(temp)

		# home if not homed yet
		if not self.is_homed:
			if not self.home():
				return False

		# set temp if configured and wait for it
		if temp > 0:
			self.gcode.respond_raw("Waiting for heater...")
			self.extruder_set_temperature(temp, True)

		# check hotend temperature
		if not self.extruder_can_extrude():
			self.gcode.respond_raw("Heat up nozzle to " + str(self.heater.min_extrude_temp))
			self.extruder_set_temperature(self.heater.min_extrude_temp, True)

		# enable filament sensor
		self.toolhead_filament_sensor_t0.runout_helper.sensor_enabled = True

		# load filament
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			if not self.unload_tool():
				self.gcode.respond_raw("could not unload tool!")
				return False
		else:
			if self.cmd_origin == "rmmu":
				self.gcode.respond_raw("Possible sensor failure!")
				self.gcode.respond_raw("Filament sensor should be triggered but it isnt!")
				return False

		self.select_tool(tool)
		if not self.load_filament_from_reverse_bowden_to_toolhead_sensor():
			self.gcode.respond_raw("could not load tool to sensor!")
			return False
		if not self.load_filament_from_toolhead_sensor_to_parking_position():
			return False
		if self.mode != "slicer" or self.filament_changes == 0:
			if not self.load_filament_from_parking_position_to_nozzle():
				self.gcode.respond_raw("could not load into nozzle!")
				return False

		# success
		self.gcode.respond_raw("tool " + str(tool) + " loaded")

		# send notification
		self.gcode.run_script_from_command('_RMMU_ON_TOOL_HAS_CHANGED T=' + str(tool))

		return True

	def unload_tool(self):
		if self.mode != "slicer":
			if not self.unload_filament_from_nozzle_to_parking_position():
				return False
		self.select_tool(self.Selected_Filament)
		if not self.unload_filament_from_parking_position_to_toolhead_sensor():
			return False
		if not self.unload_filament_from_toolhead_sensor():
			return False
		self.select_idler(-1)
		return True

	def before_change(self):
		if self.mode == "native":
			self.gcode.run_script_from_command('SAVE_GCODE_STATE NAME=PAUSE_state')
			self.exchange_old_position = self.toolhead.get_position()
			self.extruder_move(-2, 60)
			self.gcode.run_script_from_command('M400')
		elif self.mode == "slicer":
			self.gcode.run_script_from_command('SAVE_GCODE_STATE NAME=PAUSE_state')
			self.exchange_old_position = self.toolhead.get_position()

	# -----------------------------------------------------------------------------------------------------------------------------
	# Select Tool
	# -----------------------------------------------------------------------------------------------------------------------------
	Selected_Filament = -1
	MMU_Synced = False

	def select_tool(self, tool=-1):
		self.select_idler(tool)
		self.Selected_Filament = tool

	def select_idler(self, tool):
		if tool >= 0:
			self.MMU_Synced = True
			self.stepper_move(self.rmmu_idler, self.idler_positions[tool], True, self.idler_speed, self.idler_accel)
			for i in range(0, self.tool_count):
				if tool == i:
					self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(i) + " VARIABLE=active VALUE=True")
				else:
					self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(i) + " VARIABLE=active VALUE=False")
		else:
			self.MMU_Synced = False
			self.stepper_move(self.rmmu_idler, self.idler_home_position, True, self.idler_speed, self.idler_accel)
			for i in range(0, self.tool_count):
				self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=T" + str(i) + " VARIABLE=active VALUE=False")

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
			self.gcode.respond_raw("Could not find filament sensor!")
			return False
		self.gcode.respond_raw("Filament " + str(self.Selected_Filament) + " found!")
		return True

	def load_filament_from_toolhead_sensor_to_parking_position(self):
		self.extruder_move(self.toolhead_sensor_to_extruder_gear_mm + self.extruder_gear_to_parking_position_mm, self.filament_parking_speed_mms)
		self.gcode.run_script_from_command('M400')
		if self.extruder_push_and_pull_test:
			push_and_pull_offset = 10
			self.extruder_move(-(self.toolhead_sensor_to_extruder_gear_mm + self.extruder_gear_to_parking_position_mm - push_and_pull_offset), self.filament_parking_speed_mms)
			self.gcode.run_script_from_command('M400')
			if not bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
				self.gcode.respond_raw("could not load filament into extruder!")
				return False
			self.extruder_move(self.toolhead_sensor_to_extruder_gear_mm + self.extruder_gear_to_parking_position_mm - push_and_pull_offset, self.filament_parking_speed_mms)
			self.gcode.run_script_from_command('M400')
		self.select_idler(-1)
		return True

	def load_filament_from_parking_position_to_nozzle(self):
		self.gcode.run_script_from_command('G92 E0')
		self.gcode.run_script_from_command('G0 E' + str(self.parking_position_to_nozzle_mm) + ' F' + str(self.nozzle_loading_speed_mms * 60))
		self.gcode.run_script_from_command('G4 P1000')
		self.gcode.run_script_from_command('G92 E0')
		self.gcode.run_script_from_command('M400')
		return True

	# -----------------------------------------------------------------------------------------------------------------------------
	# Unload Filament
	# -----------------------------------------------------------------------------------------------------------------------------

	def unload_filament_from_nozzle_to_parking_position(self):
		self.gcode.run_script_from_command('_RMMU_UNLOAD_FILAMENT_FROM_NOZZLE_TO_COOLING_POSITION')
		return True

	def unload_filament_from_parking_position_to_toolhead_sensor(self):
		self.gcode.run_script_from_command('M400')
		self.extruder_move(-(self.extruder_gear_to_parking_position_mm + 50), self.filament_parking_speed_mms)
		self.gcode.run_script_from_command('M400')
		self.select_idler(self.Selected_Filament)
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 MOVE=-' + str(self.toolhead_sensor_to_extruder_gear_mm * 2) + ' SPEED=' + str(self.filament_parking_speed_mms) + ' ACCEL=' + str(self.filament_parking_accel) + ' STOP_ON_ENDSTOP=-2')
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 MOVE=-5 SPEED=' + str(self.filament_parking_speed_mms) + ' ACCEL=' + str(self.filament_parking_accel))
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			return False
		return True

	def unload_filament_from_toolhead_sensor(self):
		self.select_idler(self.Selected_Filament)
		self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 MOVE=-' + str(self.toolhead_sensor_to_bowden_cache_mm) + ' SPEED=' + str(self.filament_homing_speed) + ' ACCEL=' + str(self.filament_homing_accel))
		self.gcode.run_script_from_command('M400')
		if bool(self.toolhead_filament_sensor_t0.runout_helper.filament_present):
			return False
		return True

	# -----------------------------------------------------------------------------------------------------------------------------
	# Pause
	# -----------------------------------------------------------------------------------------------------------------------------
	def pause_rmmu(self):
		self.gcode.run_script_from_command("_PAUSE_RMMU")

	def resume_rmmu(self):
		if self.exchange_old_position != None:
			self.gcode.run_script_from_command('G0 Z' + str(self.exchange_old_position[2] + 2) + ' F3600')
			self.gcode.run_script_from_command('G0 X' + str(self.exchange_old_position[0]) + ' Y' + str(self.exchange_old_position[1]) + ' F3600')
			self.gcode.run_script_from_command('M400')
		self.toolhead_filament_sensor_t0.runout_helper.sensor_enabled = False
		self.gcode.run_script_from_command("_RESUME_RMMU")

	# -----------------------------------------------------------------------------------------------------------------------------
	# Helper
	# -----------------------------------------------------------------------------------------------------------------------------
	def extruder_move(self, e, f):
		self.gcode.run_script_from_command('G92 E0')
		if self.MMU_Synced:
			self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0 MOVE=' + str(e) + ' SPEED=' + str(f) + ' ACCEL=' + str(self.toolhead.max_accel) + ' SYNC=0')
			self.gcode.run_script_from_command('G0 E' + str(e) + ' F' + str(f * 60))
			self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SYNC=1')
			self.gcode.run_script_from_command('MANUAL_STEPPER STEPPER=rmmu_pulley SET_POSITION=0')
		else:
			self.gcode.run_script_from_command('G0 E' + str(e) + ' F' + str(f * 60))

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
			self.gcode.respond_raw("Selected temperature " + str(temp) + " too low, must be above " + str(self.heater.min_temp))
			return False
		if temp > self.heater.max_temp:
			self.gcode.respond_raw("Selected temperature " + str(temp) + "too high, must be below " + str(self.heater.max_temp))
			return False
		if temp < self.heater.min_extrude_temp:
			self.gcode.respond_raw("Selected temperature " + str(temp) + " below minimum extrusion temperature " + str(self.heater.min_extrude_temp))
			return False
		self.gcode.respond_raw("Heat up nozzle to " + str(temp))
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
