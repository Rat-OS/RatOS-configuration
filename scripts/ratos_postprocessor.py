# /usr/bin/python3

####################################################################
# THIS FILE WORKS ONLY WITH THE NEWEST RatOS V2.1 DEVELOPMENT BRANCH
# IT DOES NOT WORK WITH THE OLD V-CORE IDEX REPO FROM HELGE KECK
# MANDATORY SLICER SETTINGS ARE AT THE END OF THIS FILE
####################################################################

import sys
import re
import argparse
from shutil import ReadError, copy2
from os import path, remove, getenv

POST_PROCESSOR_VERSION=2

def argumentparser():
	parser = argparse.ArgumentParser(
		prog=path.basename(__file__),
		description='** RatOS Gcode Postprocessor ** \n\r',
		epilog='Result: Makes the GCode IDEX and RMMU ready.')

	parser.add_argument('parameters', metavar='gcode-files', type=str, nargs='+',
		help='One GCode file to be processed')

	try:
		args = parser.parse_args()
		return args
	except IOError as msg:
		parser.error(str(msg))

def main(args):
	if "RMMU" in args.parameters:
		sourcefile = args.parameters[1]
	else:
		sourcefile = args.parameters[0]

	if path.exists(sourcefile):
		process_file(args, sourcefile, "RMMU" in args.parameters)
	else:
		print("File not found!\n")

def process_file(args, sourcefile, rmmu):
	# read file into memory
	try:
		with open(sourcefile, "r", encoding='UTF-8') as readfile:
			lines = readfile.readlines()
	except ReadError as exc:
		print('FileReadError: ' + str(exc))
		sys.exit(1)
	finally:
		readfile.close()

	slicer = ""
	if "prusaslicer" in lines[0].rstrip().lower():
		slicer = "prusaslicer"
	elif "superslicer" in lines[0].rstrip().lower():
		slicer = "superslicer"
	elif "orcaslicer" in lines[1].rstrip().lower():
		slicer = "orcaslicer"
	
	if slicer == "prusaslicer" or slicer == "superslicer" or slicer == "orcaslicer":
		# START_PRINT parameter and toolshift processing
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
		extruder_temps = []
		extruder_temps_line = 0
		for line in range(len(lines)):

			# get slicer profile settings
			if slicer == "prusaslicer":
				if wipe_accel == 0:
					if lines[line].rstrip().startswith("; wipe_tower_acceleration = "):
						wipe_accel = int(lines[line].rstrip().replace("; wipe_tower_acceleration = ", ""))

			# get the start_print line number and fix color variable format
			if start_print_line == 0:
				if lines[line].rstrip().startswith("START_PRINT") or lines[line].rstrip().startswith("RMMU_START_PRINT"):
					start_print_line = line
					lines[line] = lines[line].replace("#", "") # fix color variable format

			# fix superslicer and orcaslicer other layer temperature bug
			if start_print_line > 0 and extruder_temps_line == 0:
				if slicer == "superslicer" or slicer == "orcaslicer":
					if lines[line].rstrip().startswith("_ON_LAYER_CHANGE LAYER=2"):
						extruder_temps_line = line
						pattern = r"EXTRUDER_OTHER_LAYER_TEMP=([\d,]+)"
						matches = re.search(pattern, lines[start_print_line].rstrip())
						if matches:
							extruder_temps = matches.group(1).split(",")

			# fix orcaslicer set acceleration gcode command
			if start_print_line > 0 and slicer == "orcaslicer":
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
								print("Cant get first x coordinate. " + str(exc) + "\n")
								print("line:" + lines[line].rstrip())
								sys.exit(1)
						if split[s].lower().startswith("y"):
							try:
								y = float(split[s].lower().replace("y", ""))
								if y > first_y:
									first_y = y
							except Exception as exc:
								print("Cant get first y coordinate. " + str(exc) + "\n")
								print("line:" + lines[line].rstrip())
								sys.exit(1)

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
								print("Oops! Something went wrong. " + str(exc) + "\n")
								print("line:" + lines[line].rstrip())
								sys.exit(1)

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
							if slicer == "prusaslicer" or slicer == "superslicer":
								if lines[line-i2].rstrip().startswith("; custom gcode: end_filament_gcode"):
									if lines[line-i2-1].rstrip().startswith("G1 Z"):
										split = lines[line-i2-1].rstrip().split(" ")
										if split[1].startswith("Z"):
											zhop = float(split[1].replace("Z", ""))
											if zhop > 0.0:
												zhop_line = line-i2-1
												break
							elif slicer == "orcaslicer":
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
						if lines[line + i2].rstrip().startswith("T") and lines[line + i2].rstrip()[1:].isdigit():
							toolchange_line = line + i2
							break

					# toolchange retraction
					retraction_line = 0
					if tower_line == 0 and toolchange_line > 0:
						for i2 in range(20):
							if slicer == "prusaslicer" or slicer == "superslicer":
								if lines[toolchange_line + i2].rstrip().startswith("G1 E-"):
									retraction_line = toolchange_line + i2
									break
							elif slicer == "orcaslicer":
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
						if slicer == "prusaslicer" or slicer == "superslicer":
							if lines[move_line + 1].rstrip().startswith("G1 Z"):
								zdrop_line = move_line + 1
							elif lines[move_line + 2].rstrip().startswith("G1 Z"):
								zdrop_line = move_line + 2
							if zdrop_line > 0:
								split = lines[zdrop_line].rstrip().split(" ")
								if split[1].startswith("Z"):
									move_z = split[1].rstrip()
						elif slicer == "orcaslicer":
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
					if toolshift_count > 1 and toolchange_line > 0 and move_line > 0:
						file_has_changed = True

						if zhop_line > 0:
							print("Z-Hop removed               " + lines[zhop_line].rstrip())
							lines[zhop_line] = '; Removed by RatOS post processor: ' + lines[zhop_line].rstrip() + '\n'
							if slicer == "orcaslicer":
								for i in range(5):
									if lines[zhop_line+i].rstrip().startswith("G1 Z"):
										lines[zhop_line+i] = '; Removed by RatOS post processor: ' + lines[zhop_line+i].rstrip() + '\n'
										break

						if zdrop_line > 0:
							print("Z-Drop removed              " + lines[zdrop_line].rstrip())
							lines[zdrop_line] = '; Removed by RatOS post processor: ' + lines[zdrop_line].rstrip() + '\n'
						if not rmmu:
							new_toolchange_gcode = (lines[toolchange_line].rstrip() + ' ' + move_x + ' ' + move_y + ' ' + move_z).rstrip()
						else:
							new_toolchange_gcode = ('TOOL T=' + lines[toolchange_line].rstrip().replace("T", "") + ' ' + move_x.replace("X", "X=") + ' ' + move_y.replace("Y", "Y=") + ' ' + move_z.replace("Z", "Z=")).rstrip()
						print('parameter added             ' + new_toolchange_gcode)
						lines[toolchange_line] = new_toolchange_gcode + '\n'
						print('Horizontal move removed     ' + lines[move_line].rstrip().replace("  ", " "))
						lines[move_line] = '; Removed by RatOS post processor: ' + lines[move_line].rstrip().replace("  ", " ") + '\n'

						if retraction_line > 0 and extrusion_line > 0:
							print("Retraction removed          " + lines[retraction_line].rstrip())
							lines[retraction_line] = '; Removed by RatOS post processor: ' + lines[retraction_line].rstrip() + '\n'
							print("Deretraction removed        " + lines[extrusion_line].rstrip())
							lines[extrusion_line] = '; Removed by RatOS post processor: ' + lines[extrusion_line].rstrip() + '\n'

						print("\n")

		# add START_PRINT parameters 
		if start_print_line > 0:
			lines[start_print_line] = lines[start_print_line].rstrip() + ' POST_PROCESSOR_VERSION=' + str(POST_PROCESSOR_VERSION) + '\n'
			if toolshift_count > 0 :
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

		# save file if it has changed 
		if file_has_changed:
			writefile = None
			try:
				lines.append("; processed by RatOS\n")
				with open(sourcefile, "w", newline='\n', encoding='UTF-8') as writefile:
					for i, strline in enumerate(lines):
						writefile.write(strline)
			except Exception as exc:
				print("FileWriteError: " + str(exc) + "\n")
				sys.exit(1)
			finally:
				writefile.close()

ARGS = argumentparser()

main(ARGS)
