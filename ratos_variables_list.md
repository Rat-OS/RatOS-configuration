## Common
```
[gcode_macro RatOS]
variable_relative_extrusion: False        # True|False = enable relative extrusion mode
variable_force_absolute_position: False   # True|False = force absolute positioning before the print starts
variable_preheat_extruder: True           # True|False = enable preheating for inductive probes
variable_preheat_extruder_temp: 150       # int = the preheating nozzle temperature
variable_end_print_motors_off: True       # True|False = Keeps the motors on after a print ends
variable_macro_travel_speed: 150          # int = xy macro travel move speed  
variable_macro_travel_accel: 2000         # int = xy macro travel move acceleration
variable_macro_z_speed: 15                # int = z macro travel move speed
variable_bed_margin_x: [0, 0]             # [float, float] = left and right bed margin
variable_bed_margin_y: [0, 0]             # [float, float] = front and back bed margin
variable_printable_x_min: 0               # internal use only. Do not touch!
variable_printable_x_max: 0               # internal use only. Do not touch!
variable_printable_y_min: 0               # internal use only. Do not touch!
variable_printable_y_max: 0               # internal use only. Do not touch!
variable_status_color_ok: "00FF00"        # internal use only. Do not touch!
variable_status_color_error: "FF0000"     # internal use only. Do not touch!
variable_status_color_unknown: "FFFF00"   # internal use only. Do not touch!
```

## Homing
```
[gcode_macro RatOS]
variable_homing: "endstops"                    # endstops|sensorless = axis homing method
variable_z_probe: "static"                     # static|stowable = z-probe type
variable_safe_home_x: "middle"                 # float|middle = z-homing x location
variable_safe_home_y: "middle"                 # float|middle = z-homing y location
variable_driver_type_x: "tmc2209"              # tmc2209|tmc2130|tmc5160 = stepper driver type for sensorless homing
variable_driver_type_y: "tmc2209"              # tmc2209|tmc2130|tmc5160 = stepper driver type for sensorless homing
variable_sensorless_x_current: 0.4             # float = stepper driver run current for sensorless x-homing
variable_sensorless_y_current: 0.4             # float = stepper driver run current for sensorless y-homing
variable_stowable_probe_stop_on_error: False   # internal use only. Do not touch! 
```

## Mesh
```
[gcode_macro RatOS]
variable_calibrate_bed_mesh: True                # True|False = enable bed meshing
variable_adaptive_mesh: True                     # True|False = enable adaptive bed meshing
variable_probe_for_priming_result: None          # internal use only. Do not touch!
variable_probe_for_priming_result_t1: None       # internal use only. Do not touch!
variable_probe_for_priming_end_result: None      # internal use only. Do not touch!
variable_probe_for_priming_end_result_t1: None   # internal use only. Do not touch!
variable_adaptive_prime_offset_threshold: -1.0   # float = threshold value used for probing sanity checks
```

## Parking 
```
[gcode_macro RatOS]
variable_start_print_park_in: "back"              # back|front|center = gantry parking position before the print starts
variable_start_print_park_z_height: 50            # float = toolhead parking z-position before the print starts
variable_start_print_heat_chamber_bed_temp: 115   # int
variable_end_print_park_in: "back"                # back|front|center
variable_pause_print_park_in: "back"              # back|front|center 
variable_end_print_park_z_hop: 20                 # float
```

## Priming 
```
[gcode_macro RatOS]
variable_nozzle_priming: "primeblob"      # primeblob|false
variable_nozzle_prime_start_x: "max"      # non IDEX priming x position = min|max|float
variable_nozzle_prime_start_y: "min"      # non IDEX priming y position = min|max|float
variable_nozzle_prime_direction: "auto"   # non IDEX priming y direction = auto|forwards|backwards
variable_nozzle_prime_bridge_fan: 102     # priming fan speed = 0-255
variable_last_z_offset: None              # internal use only. Do not touch!
```

## IDEX 
```
[gcode_macro RatOS]
variable_auto_center_subject: False        # True|False
variable_toolchange_zhop: 2.0              # float
variable_toolchange_zspeed: 25             # int
variable_toolchange_sync_fans: False       # True|False
variable_toolchange_combined_zhop: False   # True|False
variable_toolchange_travel_speed: 300      # int
variable_toolchange_travel_accel: 5000     # int
variable_toolchange_extrusion: 2.0         # float
variable_toolchange_retraction: 2.0        # float
variable_toolchange_feedrate: 7200         # int
variable_toolchange_prepurging_timer: 0    # int
variable_toolchange_standby_temp: -1       # int
variable_toolchange_purge: 25              # float
variable_toolchange_first_purge: 50        # float
```

## Stowable Probes
```
[gcode_macro RatOS]
variable_stowable_probe_position_preflight: [30, 60]    # x,y coordinates = [float, float]
variable_stowable_probe_position_side:      [13, 60]    # x,y coordinates = [float, float]
variable_stowable_probe_position_dock:      [13, 6.5]   # x,y coordinates = [float, float]
variable_stowable_probe_position_exit:      [60, 6.5]   # x,y coordinates = [float, float]
variable_stowable_probe_batch_mode_enabled: False       # internal use only. Do not touch!
variable_stowable_probe_state: None                     # internal use only. Do not touch!
```

## Beacon 
```
[gcode_macro RatOS]
variable_beacon_bed_mesh_scv: 25                         # int
variable_beacon_contact_z_homing: False                  # True|False
variable_beacon_contact_z_calibration: False             # True|False
variable_beacon_contact_calibration_location: "center"   # center|front|corner
variable_beacon_contact_calibrate_margin_x: 30           # float
variable_beacon_contact_bed_mesh: False                  # True|False
variable_beacon_contact_bed_mesh_samples: 2              # int
variable_beacon_contact_z_tilt_adjust: False             # True|False
variable_beacon_contact_z_tilt_adjust_samples: 2         # int
variable_beacon_contact_prime_probing: False             # True|False
variable_beacon_contact_calibration_temp: 170            # int
```

## Toolhead variables
```
[gcode_macro T0]
variable_active: True                                     # internal use only. Do not touch!
variable_standby: False                                   # internal use only. Do not touch!
variable_color: "7bff33"                                  # internal use only. Do not touch!
variable_hotend_type: "UHF"                               # SF|HF|UHF
variable_has_cht_nozzle: False                            # True|False
variable_cooling_position_to_nozzle_distance: 40          # float
variable_tooolhead_sensor_to_extruder_gear_distance: 15   # flaot
variable_extruder_gear_to_cooling_position_distance: 30   # float
variable_filament_loading_nozzle_offset: -5               # float
variable_filament_grabbing_length: 5                      # float
variable_filament_grabbing_speed: 1                       # int
variable_enable_insert_detection: True                    # True|False
variable_enable_runout_detection: True                    # True|False
variable_enable_clog_detection: True                      # True|False
variable_unload_after_runout: True                        # True|False
variable_resume_after_insert: True                        # True|False
variable_purge_after_load: 0                              # float
variable_purge_before_unload: 0                           # float
variable_extruder_load_speed: 60                          # int
variable_filament_load_speed: 10                          # int
variable_temperature_offset: 0                            # int
variable_has_oozeguard: False                             # True|False
variable_has_front_arm_nozzle_wiper: False                # True|False
variable_loading_position: -30                            # float
variable_parking_position: -55                            # float
```

## VAOC variables
```
[gcode_macro _VAOC]
variable_is_fixed: False                       # True|False
variable_additional_safe_distance: 50          # float
variable_safe_z: 60                            # float
variable_auto_z_offset_calibration: True       # True|False
variable_enable_camera_cooling: True           # True|False
variable_camera_cooling_temperature: 50        # int
variable_camera_cooling_fan_speed: 0.3         # float
variable_is_started: False                     # True|False
variable_toolchange_travel_speed: 300          # int
variable_toolchange_travel_accel: 5000         # int
variable_cache_toolchange_travel_speed: 300    # internal use only. Do not touch!
variable_cache_toolchange_travel_accel: 5000   # internal use only. Do not touch!
variable_cache_toolchange_zhop: 1.0            # float
```
