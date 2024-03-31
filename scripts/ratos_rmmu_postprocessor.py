# /usr/bin/python3

import sys
import re
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
		found_m220 = False
		found_layerchange = False

		for line in range(len(lines)):

			# get the start_print line number and fix color variable format
			if start_print_line == 0:
				if lines[line].rstrip().startswith("START_PRINT"):
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

			# remove wipe tower speed override for the first layer
			if start_print_line > 0 and not found_m220:
				if not found_layerchange:
					if lines[line].rstrip().startswith(";LAYER_CHANGE"):
						found_layerchange = True

				if found_layerchange:
					if lines[line].rstrip().startswith("M220 S"):
						file_has_changed = True
						found_m220 = True
						lines[line] = 'M220 S100\n'

		# add START_PRINT parameters 
		if start_print_line > 0:
			if first_x >= 0 and first_y >= 0:
				file_has_changed = True
				lines[start_print_line] = lines[start_print_line].rstrip() + ' FIRST_X=' + str(first_x) + ' FIRST_Y=' + str(first_y) + '\n'

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
