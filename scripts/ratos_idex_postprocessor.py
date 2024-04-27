# /usr/bin/python3

import sys
import re
import argparse
from shutil import ReadError, copy2
from os import path, remove, getenv

def argumentparser():
	parser = argparse.ArgumentParser(
		prog=path.basename(__file__),
		description='** RatOS IDEX Postprocessor ** \n\r',
		epilog='Result: Makes the GCode IDEX ready and removes GCode junk to enable faster toolshifts.')

	parser.add_argument('input_file', metavar='gcode-files', type=str, nargs='+',
		help='One or more GCode file(s) to be processed '
		'- at least one is required.')

	try:
		args = parser.parse_args()
		return args
	except IOError as msg:
		parser.error(str(msg))


def main(args):
	for sourcefile in args.input_file:
		if path.exists(sourcefile):
			process_file(args, sourcefile)
		else:
			print("File not found!\n")


def process_file(args, sourcefile):

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
	
	if slicer == "prusaslicer" or slicer == "superslicer":
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
		for line in range(len(lines)):

			# get slicer profile settings
			if wipe_accel == 0:
				if lines[line].rstrip().startswith("; wipe_tower_acceleration = "):
					wipe_accel = int(lines[line].rstrip().replace("; wipe_tower_acceleration = ", ""))

			# get the start_print line number
			if start_print_line == 0:
				if lines[line].rstrip().startswith("START_PRINT") or lines[line].rstrip().startswith("RMMU_START_PRINT"):
					start_print_line = line

			# count toolshifts
			if start_print_line > 0:
				if lines[line].rstrip().startswith("T") and lines[line].rstrip()[1:].isdigit():
					if toolshift_count == 0:
						# remove first toolchange
						lines[line] = ''
					toolshift_count += 1

			# get first tools usage in order
			if start_print_line > 0:
				if lines[line].rstrip().startswith("T") and lines[line].rstrip()[1:].isdigit():
					# add initial tool to the list if not already added
					if len(used_tools) == 0:
						index = lines[start_print_line].rstrip().find("INITIAL_TOOL=")
						if index != -1:
							used_tools.append(lines[start_print_line].rstrip()[index + len("INITIAL_TOOL="):].split()[0])
					# add Tx to the list if not already added
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
							print("Z-Hop removed            " + lines[zhop_line].rstrip())
							lines[zhop_line] = '; Z-Hop removed by RatOS IDEX Postprocessor: ' + lines[zhop_line].rstrip() + '\n'

						if zdrop_line > 0:
							print("Z-Drop removed           " + lines[zdrop_line].rstrip())
							lines[zdrop_line] = '; Z-Drop removed by RatOS IDEX Postprocessor: ' + lines[zdrop_line].rstrip() + '\n'

						new_toolchange_gcode = ('TOOL T=' + lines[toolchange_line].rstrip().replace("T", "") + ' ' + move_x.replace("X", "X=") + ' ' + move_y.replace("Y", "Y=") + ' ' + move_z.replace("Z", "Z=")).rstrip()
						print('parameter added          ' + new_toolchange_gcode)
						lines[toolchange_line] = new_toolchange_gcode + '\n'
						print('Horizontal move removed  ' + lines[move_line].rstrip().replace("  ", " "))
						lines[move_line] = '; Horizontal move removed by RatOS IDEX Postprocessor: ' + lines[move_line].rstrip().replace("  ", " ") + '\n'

						if retraction_line > 0 and extrusion_line > 0:
							print("Retraction move removed  " + lines[retraction_line].rstrip())
							lines[retraction_line] = '; Retraction removed by RatOS IDEX Postprocessor: ' + lines[retraction_line].rstrip() + '\n'
							print("Deretraction move removed   " + lines[extrusion_line].rstrip())
							lines[extrusion_line] = '; Deretraction removed by RatOS IDEX Postprocessor: ' + lines[extrusion_line].rstrip() + '\n'

						print("\n")

		# add START_PRINT parameters 
		if start_print_line > 0:
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

		# save file if it has changed 
		if file_has_changed:
			writefile = None
			try:
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
