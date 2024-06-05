from math import fabs
from shutil import ReadError, copy2
from os import path, remove, getenv
import os, logging, io
import re, glob

#####
# RatOS
#####
class RatOS:

	#####
	# Initialize
	#####
	def __init__(self, config):
		self.config = config
		self.printer = config.get_printer()
		self.name = config.get_name()
		self.gcode = self.printer.lookup_object('gcode')
		self.reactor = self.printer.get_reactor()

		self.old_is_graph_files = []

		self.load_settings()
		self.register_commands()
		self.register_handler()

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
	# Settings
	#####
	def load_settings(self):
		self.enable_post_processing = True if self.config.get('enable_post_processing', "false").lower() == "true" else False 
		
	def get_status(self, eventtime):
		return {'name': self.name}

	#####
	# Gcode commands
	#####
	def register_commands(self):
		self.gcode.register_command('HELLO_RATOS', self.cmd_HELLO_RATOS, desc=(self.desc_HELLO_RATOS))
		self.gcode.register_command('CACHE_IS_GRAPH_FILES', self.cmd_CACHE_IS_GRAPH_FILES, desc=(self.desc_CACHE_IS_GRAPH_FILES))
		self.gcode.register_command('SHOW_IS_GRAPH_FILES', self.cmd_SHOW_IS_GRAPH_FILES, desc=(self.desc_SHOW_IS_GRAPH_FILES))
		self.gcode.register_command('CONSOLE_ECHO', self.cmd_CONSOLE_ECHO, desc=(self.desc_CONSOLE_ECHO))
		self.gcode.register_command('RATOS_LOG', self.cmd_RATOS_LOG, desc=(self.desc_RATOS_LOG))
		self.gcode.register_command('PROCESS_GCODE_FILE', self.cmd_PROCESS_GCODE_FILE, desc=(self.desc_PROCESS_GCODE_FILE))

	desc_HELLO_RATOS = "RatOS mainsail welcome message"
	def cmd_HELLO_RATOS(self, gcmd):
		url = "https://os.ratrig.com/"
		img = "../server/files/config/RatOS/Logo-white.png"
		_title = '<b><p style="font-weight-bold; margin:0; margin-bottom:8px; color:white">Welcome to RatOS V2.1.x</p></b>'
		_info = '\nClick image to open documentation.'
		_img = '<a href="' + url + '" target="_blank" ><img src="' + img + '" width="258px"></a>'
		self.gcode.respond_raw(_title + _img + _info)

	desc_CONSOLE_ECHO = "Multiline console output"
	def cmd_CONSOLE_ECHO(self, gcmd):
		title = gcmd.get('TITLE', '')
		msg = gcmd.get('MSG', '')
		type = gcmd.get('TYPE', '')

		color = "white" 
		if type == 'warning': color = "gold" 
		if type == 'alert': color = "red" 
		if type == 'result': color = "lime" 
		if type == 'info': color = "cyan" 

		_title = '<b><p style="font-weight-bold; margin:0; color:' + color + '">' + title + '</p></b>'
		_msg = '<p style="margin:0; color:' + color + '">' + msg.replace("_N_","\n") + '</p>'

		self.gcode.respond_raw(_title + _msg)

	desc_SHOW_IS_GRAPH_FILES = "Shows the last generated IS graph in the console"
	def cmd_SHOW_IS_GRAPH_FILES(self, gcmd):
		title = gcmd.get('TITLE', '')
		try:
			new_is_graph_files = self.get_is_graph_files()
			for file_path in new_is_graph_files:
				if file_path not in self.old_is_graph_files:
					file_name = file_path.replace("/home/pi/printer_data/config/input_shaper/", "")
					url = file_path.replace("/home/pi/printer_data", "../server/files")
					title = title + ': ' if title != '' else ''
					_title = '<b><p style="font-weight-bold; margin:0; color:white">' + title + file_name + '</p></b>'
					_link = 'Click image to download or right click for options.'
					_img = '<a href="' + url + '" target="_blank" ><img src="' + url + '" width="100%"></a>'
					self.gcode.respond_raw(_title + _link + _img)
			self.old_is_graph_files = []
		except Exception as exc:
			self.debug_echo("SHOW_IS_GRAPH_FILES", "Something went wrong. " + str(exc))

	desc_CACHE_IS_GRAPH_FILES = "Caches the current is graph files"
	def cmd_CACHE_IS_GRAPH_FILES(self, gcmd):
		self.old_is_graph_files = self.get_is_graph_files()

	desc_RATOS_LOG = "G-code logging command "
	def cmd_RATOS_LOG(self, gcmd):
		prefix = gcmd.get('PREFIX')
		msg = gcmd.get('MSG')
		logging.info(prefix + ": " + msg)

	desc_PROCESS_GCODE_FILE = "G-code post processor for IDEX and RMMU"
	def cmd_PROCESS_GCODE_FILE(self, gcmd):
		if (self.dual_carriage == None and self.rmmu_hub == None) or not self.enable_post_processing:
			self.v_sd.cmd_SDCARD_PRINT_FILE(gcmd)
		else:
			filename = gcmd.get('FILENAME', "")
			if filename[0] == '/':
				filename = filename[1:]
			if self.process_gode_file(filename):
				self.v_sd.cmd_SDCARD_PRINT_FILE(gcmd)
			else:
				raise self.printer.command_error("Could not process gcode file")

	#####
	# G-code post processor
	#####
	def process_gode_file(self, filename):
		echo_prefix = "POST_PROCESSOR"

		path = self.get_gcode_file_path(filename)
		lines = self.get_gcode_file_lines(path)

		if self.gcode_already_processed(path):
			return True

		self.ratos_echo(echo_prefix, "processing...")

		slicer = self.get_slicer_info(lines)

		if slicer["Name"] != "PrusaSlicer" and slicer["Name"] != "SuperSlicer" and slicer["Name"] != "OrcaSlicer":
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
		extruder_temps = []
		extruder_temps_line = 0
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

			# fix superslicer and orcaslicer other layer temperature bug
			if start_print_line > 0 and extruder_temps_line == 0:
				if slicer["Name"] == "SuperSlicer" or slicer["Name"] == "OrcaSlicer":
					if lines[line].rstrip().startswith("_ON_LAYER_CHANGE LAYER=2"):
						extruder_temps_line = line
						pattern = r"EXTRUDER_OTHER_LAYER_TEMP=([\d,]+)"
						matches = re.search(pattern, lines[start_print_line].rstrip())
						if matches:
							extruder_temps = matches.group(1).split(",")

			# fix orcaslicer set acceleration gcode command
			if start_print_line > 0 and slicer["Name"] == "OrcaSlicer":
				if lines[line].rstrip().startswith("SET_VELOCITY_LIMIT"):
					pattern = r"ACCEL=(\d+)"
					matches = re.search(pattern, lines[line].rstrip())
					if matches:
						accel = matches.group(1)
						lines[line] = 'M204 S' + str(accel) + ' ; Changed by RatOS post processor: ' + lines[line].rstrip() + '\n'

			# count toolshifts
			if start_print_line > 0:
				if lines[line].rstrip().startswith("T") and lines[line].rstrip()[1:].isdigit():
					if toolshift_count == 0:
						lines[line] = '; Removed by RatOS post processor: ' + lines[line].rstrip() + '\n' # remove first toolchange
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
								self.ratos_echo(echo_prefix, "Can not get first x coordinate. " + str(exc))
								return False
						if split[s].lower().startswith("y"):
							try:
								y = float(split[s].lower().replace("y", ""))
								if y > first_y:
									first_y = y
							except Exception as exc:
								self.ratos_echo(echo_prefix, "Can not get first y coordinate. " + str(exc))
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
								self.ratos_echo(echo_prefix, "Can not get x boundaries . " + str(exc))
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
							if slicer["Name"] == "PrusaSlicer" or slicer["Name"] == "SuperSlicer":
								if lines[line-i2].rstrip().startswith("; custom gcode: end_filament_gcode"):
									if lines[line-i2-1].rstrip().startswith("G1 Z"):
										split = lines[line-i2-1].rstrip().split(" ")
										if split[1].startswith("Z"):
											zhop = float(split[1].replace("Z", ""))
											if zhop > 0.0:
												zhop_line = line-i2-1
												break
							elif slicer["Name"] == "OrcaSlicer":
								if lines[line+i2].rstrip().startswith("G1 Z"):
									split = lines[line+i2].rstrip().split(" ")
									if split[1].startswith("Z"):
										zhop = float(split[1].replace("Z", ""))
										if zhop > 0.0:
											zhop_line = line+i2
											break

					# toolchange line
					toolchange_line = 0
					for i2 in range(20):
						if lines[line + i2].rstrip().startswith("T") and lines[line].rstrip()[1:].isdigit():
							toolchange_line = line + i2
							break

					# toolchange retraction
					retraction_line = 0
					if tower_line == 0 and toolchange_line > 0:
						for i2 in range(20):
							if slicer["Name"] == "PrusaSlicer" or slicer["Name"] == "SuperSlicer":
								if lines[toolchange_line + i2].rstrip().startswith("G1 E-"):
									retraction_line = toolchange_line + i2
									break
							elif slicer["Name"] == "OrcaSlicer":
								if lines[toolchange_line - i2].rstrip().startswith("G1 E-"):
									retraction_line = toolchange_line - i2
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
						if slicer["Name"] == "PrusaSlicer" or slicer["Name"] == "SuperSlicer":
							if lines[move_line + 1].rstrip().startswith("G1 Z"):
								zdrop_line = move_line + 1
							elif lines[move_line + 2].rstrip().startswith("G1 Z"):
								zdrop_line = move_line + 2
							if zdrop_line > 0:
								split = lines[zdrop_line].rstrip().split(" ")
								if split[1].startswith("Z"):
									move_z = split[1].rstrip()
						elif slicer["Name"] == "OrcaSlicer":
							if zhop_line > 0:
								for i in range(5):
									if lines[zhop_line+i].rstrip().startswith("G1 Z"):
										for i2 in range(5):
											if lines[zhop_line+i+i2].rstrip().startswith("G1 Z"):
												zdrop_line = zhop_line+i+i2
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
							lines[zhop_line] = '; Removed by RatOS post processor: ' + lines[zhop_line].rstrip() + '\n'
							if slicer["Name"] == "OrcaSlicer":
								for i in range(5):
									if lines[zhop_line+i].rstrip().startswith("G1 Z"):
										lines[zhop_line+i] = '; Removed by RatOS post processor: ' + lines[zhop_line+i].rstrip() + '\n'
										break
						if zdrop_line > 0:
							lines[zdrop_line] = '; Removed by RatOS post processor: ' + lines[zdrop_line].rstrip() + '\n'
						if self.rmmu_hub == None:
							new_toolchange_gcode = (lines[toolchange_line].rstrip() + ' ' + move_x + ' ' + move_y + ' ' + move_z).rstrip()
						else:
							new_toolchange_gcode = ('TOOL T=' + lines[toolchange_line].rstrip().replace("T", "") + ' ' + move_x.replace("X", "X=") + ' ' + move_y.replace("Y", "Y=") + ' ' + move_z.replace("Z", "Z=")).rstrip()
						lines[toolchange_line] = new_toolchange_gcode + '\n'
						lines[move_line] = '; Removed by RatOS post processor: ' + lines[move_line].rstrip().replace("  ", " ") + '\n'
						if retraction_line > 0 and extrusion_line > 0:
							lines[retraction_line] = '; Removed by RatOS post processor: ' + lines[retraction_line].rstrip() + '\n'
							lines[extrusion_line] = '; Removed by RatOS post processor: ' + lines[extrusion_line].rstrip() + '\n'

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
				# fix super slicer inactive toolhead other layer temperature bug
				if len(extruder_temps) > 0:
					for tool in used_tools:
						lines[extruder_temps_line] = lines[extruder_temps_line] + "M104 S" + str(extruder_temps[int(tool)]) + " T" + str(tool) + "\n"
					for i in range(10):
						if lines[extruder_temps_line + i].rstrip().startswith("M104 S"):
							lines[extruder_temps_line + i] = '; Removed by RatOS post processor: ' + lines[extruder_temps_line + i].rstrip() + '\n'
							break

			# console output 
			self.ratos_echo(echo_prefix, "USED TOOLS: " + ','.join(used_tools))
			self.ratos_echo(echo_prefix, "TOOLSHIFTS: " + str(0 if toolshift_count == 0 else toolshift_count - 1))
			self.ratos_echo(echo_prefix, "SLICER: " + slicer["Name"] + " " + slicer["Version"])

			# save file if it has changed 
			if file_has_changed:
				lines.append("; processed by RatOS\n")
				self.save_gcode_file(path, lines)

		self.ratos_echo(echo_prefix, "Done!")
		return True

	def gcode_already_processed(self, path):
		readfile = None
		try:
			with open(path, "r") as readfile:
				for line in readfile:
					pass
				return line.rstrip().lower().startswith("; processed by ratos")
		except:
			raise self.printer.command_error("Can not get processed state")
		finally:
			readfile.close()

	def get_slicer_info(self, lines):
		try:
			index = 0
			if not lines[0].rstrip().lower().startswith("; generated by"):
				if lines[1].rstrip().lower().startswith("; generated by"):
					index = 1
				else:
					return False
			line = lines[index].rstrip().replace("; generated by ", "")
			split = line.split(" on ")[0]
			return {"Name": split.split(" ")[0], "Version": split.split(" ")[1]}
		except:
			raise self.printer.command_error("Can not get slicer version")

	def get_gcode_file_path(self, filename):
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

	def get_gcode_file_lines(self, filepath):
		try:
			with open(filepath, "r", encoding='UTF-8') as readfile:
				return readfile.readlines()
		except:
			raise self.printer.command_error("Unable to open file")
		finally:
			readfile.close()

	def save_gcode_file(self, path, lines):
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
	def ratos_echo(self, prefix, msg):
		self.gcode.run_script_from_command("RATOS_ECHO PREFIX=" + str(prefix) + " MSG='" + str(msg) + "'")

	def debug_echo(self, prefix, msg):
		self.gcode.run_script_from_command("DEBUG_ECHO PREFIX=" + str(prefix) + " MSG='" + str(msg) + "'")

	def get_is_graph_files(self):
		try:
			folder_path = r"/home/pi/printer_data/config/input_shaper/"
			file_type = r"*.png"
			return glob.glob(os.path.join(folder_path, file_type))
		except Exception as exc:
			self.debug_echo("get_is_graph_files", "Something went wrong. " + str(exc))
		return None

#####
# Loader
#####
def load_config(config):
	return RatOS(config)
