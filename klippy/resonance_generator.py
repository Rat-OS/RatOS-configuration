# A utility class to test resonances of the printer
#
# Original resonance_tester by Dmitry Butyugin
# Copyright (C) 2020-2024  Dmitry Butyugin <dmbutyugin@google.com>
#
# Modified by Mikkel Schmidt to generate resonances at a static frequency 
#
# This file may be distributed under the terms of the GNU GPLv3 license.
from toolhead import ToolHead
from . import resonance_tester

class VibrationGenerator:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        tester_config = config.getsection('resonance_tester')
        self.accel_per_hz = tester_config.getfloat('accel_per_hz', 75., above=0.)
        # Resonate for 1 second by default
        self.time = 1

    def prepare_test(self, gcmd):
        self.freq = gcmd.get_float("FREQ", None, minval=1., maxval=300.)
        if self.freq is None:
            raise gcmd.error("FREQ parameter is required")

        self.time = gcmd.get_float("TIME", 1, minval=0.1, maxval=60.)

    def run_test(self, axis, gcmd):
        toolhead = self.printer.lookup_object('toolhead')
        if not isinstance(toolhead, ToolHead):
            raise gcmd.error("Toolhead is not available")
        X, Y, Z, E = toolhead.get_position()
        sign = 1.
        freq = self.freq
        # Override maximum acceleration and min cruise ratio 
        # based on the maximum test frequency
        systime = self.printer.get_reactor().monotonic()
        toolhead_info = toolhead.get_status(systime)
        old_max_accel = toolhead_info['max_accel']
        old_minimum_cruise_ratio = toolhead_info['minimum_cruise_ratio']
        max_accel = self.freq * self.accel_per_hz
        self.gcode.run_script_from_command(
                "SET_VELOCITY_LIMIT ACCEL=%.3f MINIMUM_CRUISE_RATIO=0" % (
                    max_accel))

        input_shaper = self.printer.lookup_object('input_shaper', None)
        if input_shaper is not None and not gcmd.get_int('INPUT_SHAPING', 0):
            input_shaper.disable_shaping()
            gcmd.respond_info("Disabled [input_shaper] for resonance generation")
        else:
            input_shaper = None

        run_time_seconds = 0.
        gcmd.respond_info("Testing frequency %.0f Hz" % (freq,))
        while run_time_seconds <= self.time:
            t_seg = .25 / freq
            accel = self.accel_per_hz * freq
            max_v = accel * t_seg
            toolhead.cmd_M204(self.gcode.create_gcode_command(
                "M204", "M204", {"S": accel}))
            L = .5 * accel * t_seg**2
            dX, dY = axis.get_point(L)
            nX = X + sign * dX
            nY = Y + sign * dY
            toolhead.move([nX, nY, Z, E], max_v)
            toolhead.move([X, Y, Z, E], max_v)
            sign = -sign
            run_time_seconds += 2. * t_seg

        # Restore the original acceleration values
        self.gcode.run_script_from_command(
                "SET_VELOCITY_LIMIT ACCEL=%.3f MINIMUM_CRUISE_RATIO=%.3f" % (
                    old_max_accel, old_minimum_cruise_ratio))

        # Restore input shaper if it was disabled for resonance testing
        if input_shaper is not None:
            input_shaper.enable_shaping()
            gcmd.respond_info("Re-enabled [input_shaper]")

class ResonanceGenerator:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.oscillator = VibrationGenerator(config)
        tester_config = config.getsection('resonance_tester')
        self.generator = resonance_tester.VibrationPulseTest(tester_config)

        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command("OSCILLATE",
                                    self.cmd_OSCILLATE,
                                    desc=self.cmd_OSCILLATE_help)
        self.gcode.register_command("GENERATE_RESONANCES",
                                    self.cmd_GENERATE_RESONANCES,
                                    desc=self.cmd_GENERATE_RESONANCES_help)

    def _oscillate(self, gcmd, axes):
        toolhead: ToolHead = self.printer.lookup_object('toolhead')
        if not isinstance(toolhead, ToolHead):
            raise gcmd.error("Toolhead is not available")

        self.oscillator.prepare_test(gcmd)

        gcmd.respond_info(
                "Generating oscillations at (%.3f, %.3f, %.3f)" % tuple(toolhead.get_position()[:3]))
        for axis in axes:
            if len(axes) > 1:
                gcmd.respond_info("Testing axis %s" % axis.get_name())

            # Generate moves
            self.oscillator.run_test(axis, gcmd)

    def _generate_resonances(self, gcmd, axes):
        toolhead: ToolHead = self.printer.lookup_object('toolhead')
        if not isinstance(toolhead, ToolHead):
            raise gcmd.error("Toolhead is not available")

        self.generator.prepare_test(gcmd)

        gcmd.respond_info(
                "Generating oscillations at (%.3f, %.3f, %.3f)" % tuple(toolhead.get_position()[:3]))
        for axis in axes:
            toolhead.wait_moves()
            toolhead.dwell(0.500)
            if len(axes) > 1:
                gcmd.respond_info("Testing axis %s" % axis.get_name())

            # Generate moves
            self.generator.run_test(axis, gcmd)

    def _get_max_calibration_freq(self):
        return 1.5 * self.generator.get_max_freq()

    cmd_OSCILLATE_help = ("Oscillate AXIS at the given FREQ for TIME amount of seconds.")
    def cmd_OSCILLATE(self, gcmd):
        # Parse parameters
        axis = resonance_tester._parse_axis(gcmd, gcmd.get("AXIS").lower())

        self._oscillate(
                gcmd, [axis])

        gcmd.respond_info(
                "Completed resonance generation for %s axis" % (axis.get_name()))


    cmd_GENERATE_RESONANCES_help = ("Generate resonances for AXIS from FREQ_START to FREQ_END hz.")
    def cmd_GENERATE_RESONANCES(self, gcmd):
        # Parse parameters
        axis = resonance_tester._parse_axis(gcmd, gcmd.get("AXIS").lower())

        self._generate_resonances(
                gcmd, [axis])

        gcmd.respond_info(
                "Completed resonance generation for %s axis" % (axis.get_name()))

def load_config(config):
    return ResonanceGenerator(config)
