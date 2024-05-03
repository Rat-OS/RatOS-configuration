# RatOS IDEX and RMMU Gcode Post Processor
#
# Copyright (C) 2024 Helge Magnus Keck <helgekeck@hotmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
from math import fabs
from shutil import ReadError, copy2
from os import path, remove, getenv
import os, logging, io
import re

#####
# RatOS Gcode Post Processor
#####
class RatOS_Post_Processor:

	#####
	# Initialize
	#####
	def __init__(self, config):
		self.printer = config.get_printer()
		self.name = config.get_name()
		self.gcode = self.printer.lookup_object('gcode')
		self.reactor = self.printer.get_reactor()

		self.register_commands()
		self.register_handler()

	def get_status(self, eventtime):
		return {'name': self.name}

	#####
	# Handler
	#####
	def register_handler(self):
		self.printer.register_event_handler("klippy:connect", self._connect)

	def _connect(self):
		self.v_sd = self.printer.lookup_object('virtual_sdcard', None)
		self.sdcard_dirname = self.v_sd.sdcard_dirname
		self.dual_carriage = self.printer.lookup_object("dual_carriage", None)
		self.rmmu_hub = self.printer.lookup_object("rmmu_hub", None)

	#####
	# Gcode commands
	#####
	def register_commands(self):
		self.gcode.register_command('RATOS_POST_PROCESSOR', self.cmd_RATOS_POST_PROCESSOR, desc=(self.desc_RATOS_POST_PROCESSOR))

	desc_RATOS_POST_PROCESSOR = ""
	def cmd_RATOS_POST_PROCESSOR(self, gcmd):
		if self.dual_carriage == None and self.rmmu_hub == None:
			self.v_sd.cmd_SDCARD_PRINT_FILE(gcmd)
		else:
			filename = gcmd.get('FILENAME', "")
			if filename[0] == '/':
				filename = filename[1:]
			if self.process_file(filename):
				self.v_sd.cmd_SDCARD_PRINT_FILE(gcmd)
			else:
				raise self.printer.command_error("Could not process gcode file")

	#####
	# Post Processor
	#####
	def process_file(self, filename):
		path = self.get_file_path(filename)
		lines = self.get_file_lines(path)

		if self.already_processed(path):
			return True

		self.ratos_echo("processing...")

		slicer = self.get_slicer(lines[0].rstrip())

		if slicer["Name"] != "PrusaSlicer" and slicer["Name"] != "SuperSlicer":
			raise self.printer.command_error("Unsupported Slicer")

		min_x = 1000
		max_x = 0
		first_x = -1
		first_y = -1
		toolshift_count = 0
		tower_line = -1
		start_print_line = 0
		file_has_changed = False
		wipe_accel = 0
		used_tools = []
		pause_counter = 0
		other_layer_temp_bug_fixed = slicer["Name"] == "PrusaSlicer" 
		for line in range(len(lines)):
			# give the cpu some time
			pause_counter += 1
			if pause_counter == 1000:
				pause_counter = 0
				self.reactor.pause(.001)

			# get slicer profile settings
			if slicer["Name"] == "PrusaSlicer":
				if wipe_accel == 0:
					if lines[line].rstrip().startswith("; wipe_tower_acceleration = "):
						wipe_accel = int(lines[line].rstrip().replace("; wipe_tower_acceleration = ", ""))

			# get the start_print line number
			if start_print_line == 0:
				if lines[line].rstrip().startswith("START_PRINT") or lines[line].rstrip().startswith("RMMU_START_PRINT"):
					lines[line] = lines[line].replace("#", "") # fix color variable format
					start_print_line = line

			# fix superslicer other layer temperature bug
			if start_print_line > 0:
				if not other_layer_temp_bug_fixed:
					if lines[line].rstrip().startswith(";LAYER_CHANGE"):
						layer_number += 1
						if layer_number == 2:
							pattern = r"EXTRUDER_OTHER_LAYER_TEMP=(\d+) EXTRUDER_OTHER_LAYER_TEMP_1=(\d+)"
							matches = re.search(pattern, lines[start_print_line].rstrip())
							if matches:
								extruder_temp = int(matches.group(1))
								extruder_temp_1 = int(matches.group(2))
								lines[line] = lines[line] + "M104 S" + str(extruder_temp) + " T0\nM104 S" + str(extruder_temp_1) + " T1\n"
							other_layer_temp_bug_fixed = True

			# count toolshifts
			if start_print_line > 0:
				if lines[line].rstrip().startswith("T") and lines[line].rstrip()[1:].isdigit():
					if toolshift_count == 0:
						lines[line] = '' # remove first toolchange
					toolshift_count += 1

			# get first tools usage in order
			if start_print_line > 0:
				if len(used_tools) == 0:
					index = lines[start_print_line].rstrip().find("INITIAL_TOOL=")
					if index != -1:
						used_tools.append(lines[start_print_line].rstrip()[index + len("INITIAL_TOOL="):].split()[0])
				if lines[line].rstrip().startswith("T") and lines[line].rstrip()[1:].isdigit():
					# add tool to the list if not already added
					t = lines[line].rstrip()[1:]
					if t not in used_tools:
						used_tools.append(t)

			# get first XY coordinates
			if start_print_line > 0 and first_x < 0 and first_y < 0:
				if lines[line].rstrip().startswith("G1") or lines[line].rstrip().startswith("G0"):
					split = lines[line].rstrip().replace("  ", " ").split(" ")
					for s in range(len(split)):
						if split[s].lower().startswith("x"):
							try:
								x = float(split[s].lower().replace("x", ""))
								if x > first_x:
									first_x = x
							except Exception as exc:
								self.ratos_echo("Can not get first x coordinate. " + str(exc))
								return False
						if split[s].lower().startswith("y"):
							try:
								y = float(split[s].lower().replace("y", ""))
								if y > first_y:
									first_y = y
							except Exception as exc:
								self.ratos_echo("Can not get first y coordinate. " + str(exc))
								return False

			# get x boundaries 
			if start_print_line > 0:
				if lines[line].rstrip().startswith("G1") or lines[line].rstrip().startswith("G0"):
					split = lines[line].rstrip().replace("  ", " ").split(" ")
					for s in range(len(split)):
						if split[s].lower().startswith("x"):
							try:
								x = float(split[s].lower().replace("x", ""))
								if x < min_x:
									min_x = x
								if x > max_x:
									max_x = x
							except Exception as exc:
								self.ratos_echo("Can not get x boundaries . " + str(exc))
								return False

			# toolshift processing
			if start_print_line > 0:
				if lines[line].rstrip().startswith("T") and lines[line].rstrip()[1:].isdigit():

					# purge tower
					if tower_line == -1:
						tower_line = 0
						for i2 in range(20):
							if lines[line-i2].rstrip().startswith("; CP TOOLCHANGE START"):
								tower_line = line-i2
								break

					# z-hop before toolchange
					zhop = 0
					zhop_line = 0
					if tower_line == 0:
						for i2 in range(20):
							if lines[line-i2].rstrip().startswith("; custom gcode: end_filament_gcode"):
								if lines[line-i2-1].rstrip().startswith("G1 Z"):
									split = lines[line-i2-1].rstrip().split(" ")
									if split[1].startswith("Z"):
										zhop = float(split[1].replace("Z", ""))
										if zhop > 0.0:
											zhop_line = line-i2-1

					# toolchange line
					toolchange_line = 0
					for i2 in range(20):
						if lines[line + i2].rstrip().startswith("T") and lines[line].rstrip()[1:].isdigit():
							toolchange_line = line + i2
							break

					# retraction after toolchange
					retraction_line = 0
					if tower_line == 0 and toolchange_line > 0:
						for i2 in range(20):
							if lines[toolchange_line + i2].rstrip().startswith("G1 E-"):
								retraction_line = toolchange_line + i2
								break

					# move after toolchange
					move_x = ''
					move_y = ''
					move_line = 0
					if toolchange_line > 0:
						for i2 in range(20):
							if lines[toolchange_line + i2].rstrip().replace("  ", " ").startswith("G1 X"):
								splittedstring = lines[toolchange_line + i2].rstrip().replace("  ", " ").split(" ")
								if splittedstring[1].startswith("X"):
									if splittedstring[2].startswith("Y"):
										move_x = splittedstring[1].rstrip()
										move_y = splittedstring[2].rstrip()
										move_line = toolchange_line + i2
										break

					# z-drop after toolchange
					move_z = ''
					zdrop_line = 0
					if tower_line == 0:
						if lines[move_line + 1].rstrip().startswith("G1 Z"):
							zdrop_line = move_line + 1
						elif lines[move_line + 2].rstrip().startswith("G1 Z"):
							zdrop_line = move_line + 2
						if zdrop_line > 0:
							split = lines[zdrop_line].rstrip().split(" ")
							if split[1].startswith("Z"):
								move_z = split[1].rstrip()

					# extrusion after move
					extrusion_line = 0
					if tower_line == 0 and move_line > 0:
						for i2 in range(5):
							if lines[move_line + i2].rstrip().startswith("G1 E"):
								extrusion_line = move_line + i2
								break

					# make toolshift changes
					if toolshift_count > 0 and toolchange_line > 0 and move_line > 0:
						file_has_changed = True
						if zhop_line > 0:
							lines[zhop_line] = '; Removed by RatOS Postprocessor: ' + lines[zhop_line].rstrip() + '\n'
						if zdrop_line > 0:
							lines[zdrop_line] = '; Removed by RatOS Postprocessor: ' + lines[zdrop_line].rstrip() + '\n'
						if self.rmmu_hub == None:
							new_toolchange_gcode = (lines[toolchange_line].rstrip() + ' ' + move_x + ' ' + move_y + ' ' + move_z).rstrip()
						else:
							new_toolchange_gcode = ('TOOL T=' + lines[toolchange_line].rstrip().replace("T", "") + ' ' + move_x.replace("X", "X=") + ' ' + move_y.replace("Y", "Y=") + ' ' + move_z.replace("Z", "Z=")).rstrip()
						lines[toolchange_line] = new_toolchange_gcode + '\n'
						lines[move_line] = '; Removed by RatOS Postprocessor: ' + lines[move_line].rstrip().replace("  ", " ") + '\n'
						if retraction_line > 0 and extrusion_line > 0:
							lines[retraction_line] = '; Removed by RatOS Postprocessor: ' + lines[retraction_line].rstrip() + '\n'
							lines[extrusion_line] = '; Removed by RatOS Postprocessor: ' + lines[extrusion_line].rstrip() + '\n'

		# add START_PRINT parameters 
		if start_print_line > 0:
			if toolshift_count > 0:
				file_has_changed = True
				lines[start_print_line] = lines[start_print_line].rstrip() + ' TOTAL_TOOLSHIFTS=' + str(toolshift_count - 1) + '\n'
			if first_x >= 0 and first_y >= 0:
				file_has_changed = True
				lines[start_print_line] = lines[start_print_line].rstrip() + ' FIRST_X=' + str(first_x) + ' FIRST_Y=' + str(first_y) + '\n'
			if min_x < 1000:
				file_has_changed = True
				lines[start_print_line] = lines[start_print_line].rstrip() + ' MIN_X=' + str(min_x) + ' MAX_X=' + str(max_x) + '\n'
			if len(used_tools) > 0:
				file_has_changed = True
				lines[start_print_line] = lines[start_print_line].rstrip() + ' USED_TOOLS=' + ','.join(used_tools) + '\n'
				lines[start_print_line] = lines[start_print_line].rstrip() + ' WIPE_ACCEL=' + str(wipe_accel) + '\n'

			# console output 
			self.ratos_echo("USED TOOLS: " + ','.join(used_tools))
			self.ratos_echo("TOOLSHIFTS: " + str(0 if toolshift_count == 0 else toolshift_count - 1))
			self.ratos_echo("SLICER: " + slicer["Name"] + " " + slicer["Version"])

			# save file if it has changed 
			if file_has_changed:
				lines[1] = lines[1].rstrip()+ "; processed by RatOS\n"
				self.save_file(path, lines)

		self.ratos_echo("Done!")
		return True

	def already_processed(self, path):
		readfile = None
		try:
			i = 0
			with open(path, 'r', encoding='utf-8') as readfile:
				for line in readfile:
					i += 1
					if i == 2:
						return line.rstrip().lower().startswith("; processed by ratos")
		except:
			raise self.printer.command_error("Can not get processed state")
		finally:
			readfile.close()

	def get_slicer(self, line):
		try:
			line = line.rstrip().replace("; generated by ", "")
			split = line.split(" on ")[0]
			return {"Name": split.split(" ")[0], "Version": split.split(" ")[1]}
		except:
			raise self.printer.command_error("Can not get slicer version")

	def get_file_path(self, filename):
		files = self.v_sd.get_file_list(True)
		flist = [f[0] for f in files]
		files_by_lower = { filepath.lower(): filepath for filepath, fsize in files }
		filepath = filename
		try:
			if filepath not in flist:
				filepath = files_by_lower[filepath.lower()]
			return os.path.join(self.sdcard_dirname, filepath)
		except:
			raise self.printer.command_error("Can not get path for file " + filename)

	def get_file_lines(self, filepath):
		try:
			with open(filepath, "r", encoding='UTF-8') as readfile:
				return readfile.readlines()
		except:
			raise self.printer.command_error("Unable to open file")
		finally:
			readfile.close()

	def save_file(self, path, lines):
		writefile = None
		try:
			pause_counter = 0
			with open(path, "w", newline='\n', encoding='UTF-8') as writefile:
				for i, strline in enumerate(lines):
					pause_counter += 1
					if pause_counter == 1000:
						pause_counter = 0
						self.reactor.pause(.001)
					writefile.write(strline)
		except Exception as exc:
			raise self.printer.command_error("FileWriteError: " + str(exc))
		finally:
			writefile.close()

	#####
	# Helper
	#####
	def ratos_echo(self, msg):
		self.gcode.run_script_from_command("RATOS_ECHO PREFIX='POST_PROCESSOR' MSG='" + str(msg) + "'")

	def ratos_debug_echo(self, msg):
		self.gcode.run_script_from_command("DEBUG_ECHO PREFIX='POST_PROCESSOR' MSG='" + str(msg) + "'")

#####
# Loader
#####
def load_config(config):
	return RatOS_Post_Processor(config)
