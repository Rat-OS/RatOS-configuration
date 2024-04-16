# /usr/bin/python3

import sys
import argparse
from shutil import ReadError, copy2
from os import path, remove, getenv

def argumentparser():
	parser = argparse.ArgumentParser(
		prog=path.basename(__file__),
		description='** RatOS RMMU Postprocessor ** \n\r',
		epilog='Result: Makes the GCode RMMU ready.')

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
		first_x = -1
		first_y = -1
		start_print_line = 0
		file_has_changed = False
		first_layer_override_done = False
		travel_speed = 0
		travel_accel = 0
		wipe_accel = 0

		for line in range(len(lines)):

			# get slicer profile settings
			if travel_speed == 0:
				if lines[line].rstrip().startswith("; travel_speed = "):
					travel_speed = int(lines[line].rstrip().replace("; travel_speed = ", ""))
			if travel_accel == 0:
				if lines[line].rstrip().startswith("; travel_acceleration = "):
					travel_accel = int(lines[line].rstrip().replace("; travel_acceleration = ", ""))
			if wipe_accel == 0:
				if lines[line].rstrip().startswith("; wipe_tower_acceleration = "):
					wipe_accel = int(lines[line].rstrip().replace("; wipe_tower_acceleration = ", ""))

			# get the start_print line number and fix color variable format
			if start_print_line == 0:
				if lines[line].rstrip().startswith("START_PRINT") or lines[line].rstrip().startswith("RMMU_START_PRINT"):
					start_print_line = line
					# fix color variable format
					if "#" in lines[start_print_line].rstrip():
						file_has_changed = True
						lines[start_print_line] = lines[start_print_line].rstrip().replace("#", "") + '\n'

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

			# get wiper tower XY toolchange coordinates
			if start_print_line > 0:
				# find toolchange unload line
				if lines[line].rstrip().startswith("; CP TOOLCHANGE UNLOAD"):

					toolchange_tx_line = 0
					wipe_tower_xy_line = 0
					toolchange_unload_line_g1xy = 0
					toolchange_unload_line_g1yf = 0
					wipe_tower_x = 0
					wipe_tower_y = 0

					# find toolchange g1 lines
					if toolchange_unload_line_g1xy == 0 and toolchange_unload_line_g1yf == 0:
						for i in range(20):
							if lines[line + i].rstrip().startswith("G1"):
								if "X" in lines[line + i].rstrip() and "Y" in lines[line + i].rstrip():
									toolchange_unload_line_g1xy = line + i
								if "Y" in lines[line + i].rstrip() and "F" in lines[line + i].rstrip():
									toolchange_unload_line_g1yf = line + i
									break

					# find Tx line						
					if toolchange_unload_line_g1xy > 0 and toolchange_unload_line_g1yf > 0 and toolchange_tx_line == 0:
						for i in range(20):
							if lines[toolchange_unload_line_g1yf + i].rstrip().startswith("; Filament-specific end gcode"):
								for i in range(20):
									if len(lines[toolchange_unload_line_g1yf + i].rstrip()) == 2 and lines[toolchange_unload_line_g1yf + i].rstrip().startswith("T"):
										toolchange_tx_line = toolchange_unload_line_g1yf + i
										break

					# find wipe tower xy line
					if toolchange_tx_line > 0:
						for i in range(20):
							if lines[toolchange_tx_line + i].rstrip().startswith("G1"):
								if "X" in lines[toolchange_tx_line + i].rstrip() and "Y" in lines[toolchange_tx_line + i].rstrip():
									wipe_tower_xy_line = toolchange_tx_line + i
									break

					# get wipe tower xy coordinates
					if wipe_tower_xy_line > 0:
						split = lines[wipe_tower_xy_line].rstrip().replace("  ", " ").split(" ")
						for s in range(len(split)):
							if split[s].lower().startswith("x"):
								try:
									wipe_tower_x = float(split[s].lower().replace("x", ""))
								except Exception as exc:
									print("Cant get wipe tower x coordinate. " + str(exc) + "\n")
									print("line:" + lines[wipe_tower_xy_line].rstrip())
									sys.exit(1)
							if split[s].lower().startswith("y"):
								try:
									wipe_tower_y = float(split[s].lower().replace("y", ""))
								except Exception as exc:
									print("Cant get wipe tower y coordinate. " + str(exc) + "\n")
									print("line:" + lines[wipe_tower_xy_line].rstrip())
									sys.exit(1)

					# remove gcode junk
					if wipe_tower_x > 0 and wipe_tower_y > 0:
						lines[toolchange_unload_line_g1xy] = "; Removed by RMMU -> " + lines[toolchange_unload_line_g1xy]
						lines[toolchange_unload_line_g1yf] = "; Removed by RMMU -> " + lines[toolchange_unload_line_g1yf]
						for i in range(20):
							if lines[line - i].rstrip().startswith("G1 E"):
								lines[line - i] = "; Removed by RMMU -> " + lines[line - i]
							if lines[line - i].rstrip().startswith("G1 Z"):
								lines[line - i] = "; Removed by RMMU -> " + lines[line - i]
							if lines[line - i].rstrip().startswith("G1 X"):
								lines[line - i] = "; Removed by RMMU -> " + lines[line - i]
								break
						for i in range(20):
							if lines[toolchange_tx_line - i].rstrip().startswith("G1 E"):
								lines[toolchange_tx_line - i] = "; Removed by RMMU -> " + lines[toolchange_tx_line - i]
								break

					# add wipe tower xy coordinates to toolchange parameter
					if wipe_tower_x > 0 and wipe_tower_y > 0:
						lines[toolchange_tx_line] = lines[toolchange_tx_line].rstrip() + " X" + str(wipe_tower_x) + " Y" + str(wipe_tower_y) + "\n"

			# remove wipe tower speed override for the first layer to ensure first layer adhesion
			if slicer == "superslicer":
				if start_print_line > 0 and not first_layer_override_done:
					if lines[line].rstrip().startswith("; CP TOOLCHANGE WIPE"):
						lines[line] = 'M220 S100 ' + lines[line]
						first_layer_override_done = True

		# add START_PRINT parameters 
		if start_print_line > 0:
			if first_x >= 0 and first_y >= 0:
				file_has_changed = True
				lines[start_print_line] = lines[start_print_line].rstrip() + ' FIRST_X=' + str(first_x) + ' FIRST_Y=' + str(first_y) + ' TRAVEL_SPEED=' + str(travel_speed) + ' TRAVEL_ACCEL=' + str(travel_accel) + ' WIPE_ACCEL=' + str(wipe_accel) + '\n'

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
