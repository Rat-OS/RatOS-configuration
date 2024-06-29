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

	def _connect(self):
		self.bed_mesh = self.printer.lookup_object('bed_mesh')
		if "Contact" in self.pmgr.get_profiles():
			self.contact_mesh = self.pmgr.load_profile("Contact")

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
					new_points = []
					for y in range(y_count):
						new_points.append([])
						for x in range(x_count):
							x_pos = min_x + x * x_step
							y_pos = min_y + y * y_step
							z_val = points[y][x]
							contact_z = self.contact_mesh.calc_z(x_pos, y_pos)
							new_z = z_val - (z_val - contact_z)
							new_points[y].append(new_z)
					self.bed_mesh.z_mesh.build_mesh(new_points)
					self.bed_mesh.save_profile(profile_name)

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
