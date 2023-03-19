# Run user defined actions in place of a normal G28 homing command
# This is a combination of safe_z_home and homing_override
#
# Does not support set_position_* variables
# instead supports z_hop and z_hop_speed
#
# Copyright (C) 2018  Kevin O'Connor <kevin@koconnor.net>
# Modified by Mikkel Schmidt <mikkel.schmidt@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

class RatOSHoming:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.z_hop = config.getfloat("z_hop", default=0.0)
        self.z_hop_speed = config.getfloat('z_hop_speed', 15., above=0.)
        self.axes = config.get('axes', 'XYZ').upper()
        gcode_macro = self.printer.load_object(config, 'gcode_macro')
        self.template = gcode_macro.load_template(config, 'gcode')
        self.in_script = False
        self.printer.load_object(config, 'homing')
        self.gcode = self.printer.lookup_object('gcode')
        self.prev_G28 = self.gcode.register_command("G28", None)
        self.gcode.register_command("G28", self.cmd_G28)
    def cmd_G28(self, gcmd):
        if self.in_script:
            # Was called recursively - invoke the real G28 command
            self.prev_G28(gcmd)
            return

        # Perform Z Hop if necessary
        if self.z_hop != 0.0:
            # Check if Z axis is homed and its last known position
            toolhead = self.printer.lookup_object('toolhead')
            curtime = self.printer.get_reactor().monotonic()
            kin_status = toolhead.get_kinematics().get_status(curtime)
            pos = toolhead.get_position()

            if 'z' not in kin_status['homed_axes']:
                # Always perform the z_hop if the Z axis is not homed
                pos[2] = 0
                toolhead.set_position(pos, homing_axes=[2])
                toolhead.manual_move([None, None, self.z_hop],
                                     self.z_hop_speed)
                if hasattr(toolhead.get_kinematics(), "note_z_not_homed"):
                    toolhead.get_kinematics().note_z_not_homed()
            elif pos[2] < self.z_hop:
                # If the Z axis is homed, and below z_hop, lift it to z_hop
                toolhead.manual_move([None, None, self.z_hop],
                                     self.z_hop_speed)

        # if no axis is given as parameter we assume the override
        no_axis = True
        for axis in 'XYZ':
            if gcmd.get(axis, None) is not None:
                no_axis = False
                break

        if no_axis:
            override = True
        else:
            # check if we home an axis which needs the override
            override = False
            for axis in self.axes:
                if gcmd.get(axis, None) is not None:
                    override = True

        if not override:
            self.prev_G28(gcmd)
            return

        # Perform homing
        context = self.template.create_template_context()
        context['params'] = gcmd.get_command_parameters()
        try:
            self.in_script = True
            self.template.run_gcode_from_command(context)
        finally:
            self.in_script = False

def load_config(config):
    return RatOSHoming(config)