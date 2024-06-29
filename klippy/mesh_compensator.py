from math import fabs
from shutil import ReadError, copy2
from os import path, remove, getenv
import os, logging, io, collections
import re, glob, math
from . import manual_probe as ManualProbe, bed_mesh as BedMesh

#####
# RatOS
#####
class MeshCompensator:

	#####
	# Initialize
	#####
	def __init__(self, config):
		self.config = config
		self.printer = config.get_printer()
		self.name = config.get_name()
		self.gcode = self.printer.lookup_object('gcode')
		self.reactor = self.printer.get_reactor()

		self.contact_mesh = None
		self.pmgr = ProfileManager(self.config, self)

		self.enable_compensation = False

		self.load_settings()
		self.register_commands()
		self.register_handler()

	#####
	# Handler
	#####
	def register_handler(self):
		self.printer.register_event_handler("klippy:connect", self._connect)
		# self.printer.register_event_handler("probe:update_results",
		# 									self._update_z_compensation_value)

	def _connect(self):
		self.bed_mesh = self.printer.lookup_object('bed_mesh')
		if "Contact" in self.pmgr.get_profiles():
			self.contact_mesh = self.pmgr.load_profile("Contact")

	# def _update_z_compensation_value(self, pos):
	# 	if not self.enable_compensation or not self.contact_mesh:
	# 		return

	# 	x_coord = pos[0]

	# 	z_compensations = self.z_compensations
	# 	sample_count = len(z_compensations)
	# 	spacing = ((self.calibrate_end_x - self.calibrate_start_x)
	# 				/ (sample_count - 1))

	# 	interpolate_t = (x_coord - self.calibrate_start_x) / spacing
	# 	interpolate_i = int(math.floor(interpolate_t))
	# 	interpolate_i = BedMesh.constrain(interpolate_i, 0, sample_count - 2)
	# 	interpolate_t -= interpolate_i
	# 	interpolated_z_compensation = BedMesh.lerp(
	# 		interpolate_t, z_compensations[interpolate_i],
	# 		z_compensations[interpolate_i + 1])
	# 	pos[2] += interpolated_z_compensation

	def clear_compensations(self):
		self.z_compensations = []

	#####
	# Settings
	#####
	def load_settings(self):
		self.enable_compensation = True if self.config.get('enable_compensation', "false").lower() == "true" else False 
		
	def get_status(self, eventtime):
		return {'name': self.name}

	#####
	# Gcode commands
	#####
	def register_commands(self):
		self.gcode.register_command('COMPENSATE_BED_MESH', self.cmd_COMPENSATE_BED_MESH, desc=(self.desc_COMPENSATE_BED_MESH))

	desc_COMPENSATE_BED_MESH = "COMPENSATE_BED_MESH"
	def cmd_COMPENSATE_BED_MESH(self, gcmd):
		if self.contact_mesh:
			systime = self.printer.get_reactor().monotonic()
			if self.bed_mesh.z_mesh:
				profile_name = self.bed_mesh.z_mesh.get_profile_name()
				if profile_name != "Contact":
					points = self.bed_mesh.get_status(systime)["profiles"][profile_name]["points"]

					params = self.bed_mesh.z_mesh.get_mesh_params()

					min_x = params["min_x"]
					min_y = params["min_y"]
					max_x = params["max_x"]
					max_y = params["max_y"]
					x_count = params["y_count"]
					y_count = params["x_count"]
					x_step = ((max_x - min_x) / (x_count - 1))
					y_step = ((max_y - min_y) / (y_count - 1))

					line = ""
					for y in range(y_count):
						for x in range(x_count):
							x_pos = min_x + x * x_step
							y_pos = min_y + y * y_step
							z_val = points[y][x]
							contact_z = self.contact_mesh.calc_z(x_pos, y_pos)
							new_z = z_val - contact_z
							line += str(str(float("{:.6f}".format(new_z)))) + ", "
						line += "\n"
					self.gcode.respond_raw(str(line))

class ProfileManager:
    def __init__(self, config, bedmesh):
        self.name = "bed_mesh"
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.bedmesh = bedmesh
        self.profiles = {}
        self.incompatible_profiles = []
        # Fetch stored profiles from Config
        stored_profs = config.get_prefix_sections(self.name)
        stored_profs = [s for s in stored_profs
                        if s.get_name() != self.name]
        for profile in stored_profs:
            name = profile.get_name().split(' ', 1)[1]
            version = profile.getint('version', 0)
            if version != BedMesh.PROFILE_VERSION:
                logging.info(
                    "bed_mesh: Profile [%s] not compatible with this version\n"
                    "of bed_mesh.  Profile Version: %d Current Version: %d "
                    % (name, version, BedMesh.PROFILE_VERSION))
                self.incompatible_profiles.append(name)
                continue
            self.profiles[name] = {}
            zvals = profile.getlists('points', seps=(',', '\n'), parser=float)
            self.profiles[name]['points'] = zvals
            self.profiles[name]['mesh_params'] = params = \
                collections.OrderedDict()
            for key, t in BedMesh.PROFILE_OPTIONS.items():
                if t is int:
                    params[key] = profile.getint(key)
                elif t is float:
                    params[key] = profile.getfloat(key)
                elif t is str:
                    params[key] = profile.get(key)
    def get_profiles(self):
        return self.profiles
    def load_profile(self, prof_name):
        profile = self.profiles.get(prof_name, None)
        if profile is None:
            return None
        probed_matrix = profile['points']
        mesh_params = profile['mesh_params']
        z_mesh = BedMesh.ZMesh(mesh_params, prof_name)
        try:
            z_mesh.build_mesh(probed_matrix)
        except BedMesh.BedMeshError as e:
            raise self.gcode.error(str(e))
        return z_mesh

#####
# Loader
#####
def load_config(config):
	return MeshCompensator(config)

#*#
#*# [bed_mesh Compensated]
#*# version = 1
#*# points =
#*# 	  0.049299, 0.050602, 0.074538, 0.051765, 0.034003, 0.04896, 0.091433, 0.052442, 0.082208, 0.104516
#*# 	  0.071503, 0.064134, 0.061717, 0.070617, 0.05007, 0.041172, 0.044418, 0.082746, 0.075901, 0.084298
#*# 	  0.073075, 0.066455, 0.068403, 0.066999, 0.06886, 0.060599, 0.074887, 0.081621, 0.088664, 0.080353
#*# 	  0.027264, 0.011738, 0.039861, 0.03247, 0.029208, 0.026635, 0.044098, 0.053829, 0.041679, 0.06048
#*# 	  0.02881, 0.034162, 0.035481, 0.039168, 0.027192, 0.02403, 0.055014, 0.051521, 0.043291, 0.062064
#*# 	  0.047747, 0.045715, 0.044548, 0.060817, 0.05201, 0.045912, 0.057426, 0.068299, 0.072304, 0.088487
#*# 	  0.03689, 0.044175, 0.039799, 0.037837, 0.044899, 0.05148, 0.050739, 0.067673, 0.058155, 0.076391
#*# 	  0.048509, 0.051292, 0.059823, 0.054822, 0.055669, 0.06791, 0.081129, 0.087779, 0.081107, 0.084253
#*# 	  0.020016, 0.015955, 0.023242, 0.017478, 0.043919, 0.028951, 0.051093, 0.056721, 0.05995, 0.057432
#*# 	  0.039893, 0.024619, 0.030596, 0.019875, 0.042219, 0.02419, 0.052301, 0.061301, 0.06316, 0.06544
#*# x_count = 10
#*# y_count = 10
#*# mesh_x_pps = 2
#*# mesh_y_pps = 2
#*# algo = bicubic
#*# tension = 0.2
#*# min_x = 35.0
#*# max_x = 265.0
#*# min_y = 35.0
#*# max_y = 265.0
