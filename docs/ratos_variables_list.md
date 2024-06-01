## Common
```
[gcode_macro RatOS]
variable_relative_extrusion: False                # True|False = enable relative extrusion mode
variable_force_absolute_position: False           # True|False = force absolute positioning before the print starts
variable_preheat_extruder: True                   # True|False = enable preheating for inductive probes
variable_preheat_extruder_temp: 150               # int = the preheating nozzle temperature
variable_end_print_motors_off: True               # True|False = Keeps the motors for none IDEX printer on after a print ends
variable_macro_travel_speed: 150                  # int = xy macro travel move speed  
variable_macro_travel_accel: 2000                 # int = xy macro travel move acceleration
variable_macro_z_speed: 15                        # int = z macro travel move speed
variable_bed_margin_x: [0, 0]                     # [float, float] = left and right bed margin
variable_bed_margin_y: [0, 0]                     # [float, float] = front and back bed margin
variable_printable_x_min: 0                       # internal use only. Do not touch!
variable_printable_x_max: 0                       # internal use only. Do not touch!
variable_printable_y_min: 0                       # internal use only. Do not touch!
variable_printable_y_max: 0                       # internal use only. Do not touch!
variable_status_color_ok: "00FF00"                # internal use only. Do not touch!
variable_status_color_error: "FF0000"             # internal use only. Do not touch!
variable_status_color_unknown: "FFFF00"           # internal use only. Do not touch!
variable_start_print_heat_chamber_bed_temp: 115   # int = bed temperature during chamber preheating
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
variable_start_print_park_in: "back"     # back|front|center = gantry parking position before the print starts
variable_start_print_park_z_height: 50   # float = toolhead parking z-position before the print starts
variable_end_print_park_in: "back"       # back|front|center = gantry parking position after the print has finished
variable_pause_print_park_in: "back"     # back|front|center = gantry parking position if the print has paused
variable_end_print_park_z_hop: 20        # float = toolhead z-hop after the print has finished
```

## Priming 
```
[gcode_macro RatOS]
variable_nozzle_priming: "primeblob"             # primeblob|false = To prime, or not to prime, that is the question.
variable_nozzle_prime_start_x: "max"             # min|max|float = non IDEX priming x-location
variable_nozzle_prime_start_y: "min"             # min|max|float = non IDEX priming y-location
variable_nozzle_prime_direction: "auto"          # auto|forwards|backwards = non IDEX priming y-direction
variable_nozzle_prime_bridge_fan: 102            # int = priming fan speed 0-255
variable_probe_for_priming_result: None          # internal use only. Do not touch!
variable_probe_for_priming_end_result: None      # internal use only. Do not touch!
variable_probe_for_priming_result_t1: None       # internal use only. Do not touch!
variable_probe_for_priming_end_result_t1: None   # internal use only. Do not touch!
variable_last_z_offset: None                     # internal use only. Do not touch!
```

## Prime blob 
```
[gcode_macro PRIME_BLOB]
variable_x_offset: 5   # the prime blob x-margin 
```

## IDEX 
```
[gcode_macro RatOS]
variable_auto_center_subject: False        # True|False = Experimental auto centering subject on build plate for copy and mirror mode
variable_toolchange_zhop: 2.0              # float = toolshifts z-hop
variable_toolchange_zspeed: 25             # int = toolshifts z-hop speed
variable_toolchange_sync_fans: False       # True|False = synchronizes fan speeds while printing.
variable_toolchange_combined_zhop: False   # True|False = combines z-hop and retract/deretract moves for toolshifts
variable_toolchange_travel_speed: 300      # int = toolshift travel speed
variable_toolchange_travel_accel: 5000     # int = toolshift travel acceleration
variable_toolchange_extrusion: 2.0         # float = toolshift deretraction
variable_toolchange_retraction: 2.0        # float = toolshift retraction
variable_toolchange_feedrate: 7200         # int = extruder feedrate for retract/deretract moves for toolshifts
variable_toolchange_prepurging_timer: 0    # int = prepurge some filament before going back to the buildplate after X seconds of inactivity
variable_toolchange_purge: 25              # float = mm of filament that gets prepruged in case the timer has been configured
variable_toolchange_standby_temp: -1       # int = if configured the toolheads are going into standby mode when parked 
variable_toolchange_first_purge: 50        # float = mm of filament that gets purged before a toolheads first use
```

## IDEX join spools 
```
[gcode_macro _IDEX_JOIN_SPOOLS]
variable_enabled: False   # internal use only. Do not touch!
```

## IDEX remap toolheads 
```
[gcode_macro _IDEX_REMAP_TOOLHEADS]
variable_enabled: False   # internal use only. Do not touch! 
```

## IDEX select tool 
```
[gcode_macro _SELECT_TOOL]
variable_last_timestamp: 0   # internal use only. Do not touch! 
```

## IDEX toolchange 
```
[gcode_macro _TOOLCHANGE]
variable_toolshift_count: 0   # internal use only. Do not touch! 
```

## Stowable Probes
```
[gcode_macro RatOS]
variable_stowable_probe_position_preflight: [30, 60]    # [float, float] = x,y preflight coordinates
variable_stowable_probe_position_side:      [13, 60]    # [float, float] = x,y side coordinates
variable_stowable_probe_position_dock:      [13, 6.5]   # [float, float] = x,y dock coordinates
variable_stowable_probe_position_exit:      [60, 6.5]   # [float, float] = x,y exit coordinates
variable_stowable_probe_batch_mode_enabled: False       # internal use only. Do not touch!
variable_stowable_probe_state: None                     # internal use only. Do not touch!
```

## Beacon 
```
[gcode_macro RatOS]
variable_beacon_bed_mesh_scv: 25                         # int = square corner velocity for beacon proximity bed meshing
variable_beacon_contact_z_homing: False                  # True|False = use beacon contact for z-homing
variable_beacon_contact_z_calibration: False             # True|False = use beacon contact z-calibration
variable_beacon_contact_calibration_location: "center"   # center|front|corner = beacon contact z-calibration location
variable_beacon_contact_calibrate_margin_x: 30           # float = use beacon contact z-calibration x-margin 
variable_beacon_contact_bed_mesh: False                  # True|False = use beacon contact for bed meshing
variable_beacon_contact_bed_mesh_samples: 2              # int = beacon contact bed mesh probe samples
variable_beacon_contact_z_tilt_adjust: False             # True|False = use beacon contact for z-tilting
variable_beacon_contact_z_tilt_adjust_samples: 2         # int = beacon contact z-tilt probe samples
variable_beacon_contact_prime_probing: False             # True|False = use beacon contact to probe for prime blobs
variable_beacon_contact_calibration_temp: 150            # int = beacon contact z-calibration nozzle temperature
variable_beacon_contact_expansion_compensation: False    # True|False = use nozzle thermal expansion compensation
variable_beacon_contact_expansion_multiplier: 1.0        # float = multiplier for the nozzle thermal expansion compensation
```

## Toolhead variables
```
[gcode_macro T0]
variable_active: True                                     # internal use only. Do not touch!
variable_standby: False                                   # internal use only. Do not touch!
variable_color: "7bff33"                                  # internal use only. Do not touch!
variable_hotend_type: "UHF"                               # SF|HF|UHF = nozzle type. used for loading/unloading macros
variable_has_cht_nozzle: False                            # True|False = nozzle type. used for loading/unloading macros
variable_cooling_position_to_nozzle_distance: 40          # float = mm from the cooling position to the nozzles melting zone
variable_tooolhead_sensor_to_extruder_gear_distance: 15   # flaot = mm from the toolhead filament sensor trigger point to the extruder gears
variable_extruder_gear_to_cooling_position_distance: 30   # float = mm from the extruder gears to the cooling zone
variable_filament_loading_nozzle_offset: -5               # float = mm loading offset for fine tuning
variable_filament_grabbing_length: 5                      # float = mm filament grabbing length when inserting filament into the extruder
variable_filament_grabbing_speed: 1                       # int = filament grabbing speed
variable_enable_insert_detection: True                    # True|False = enable the filament sensor insert detection
variable_enable_runout_detection: True                    # True|False = enable the filament sensor runout detection
variable_enable_clog_detection: True                      # True|False = enable the filament sensor clog detection
variable_unload_after_runout: True                        # True|False = unload filament from toolhead after if runout has been detected
variable_resume_after_insert: True                        # True|False = auto resume a paused print after runout and insert
variable_purge_after_load: 0                              # float = purge x mm after the filament has been loaded to the nozzle tip
variable_purge_before_unload: 0                           # float = purge x mm before the filament unloads
variable_extruder_load_speed: 60                          # int = extruder/cooling zone loading speed
variable_filament_load_speed: 10                          # int = filament nozzle loading speed
variable_temperature_offset: 0                            # int = adds a positive or negative offset to the nozzle temperature
variable_has_oozeguard: False                             # True|False = toolhead has a oozeguard
variable_has_front_arm_nozzle_wiper: False                # True|False = toolhead has a front arm nozzle wiper
variable_loading_position: -30                            # float = x-position for filament loading/unloading actions
variable_parking_position: -55                            # float = toolhead parking x-position
```

## VAOC variables
```
[gcode_macro _VAOC]
variable_is_fixed: False                       # True|False = vaoc is installed on a fix position
variable_is_started: False                     # internal use only. Do not touch!
variable_additional_safe_distance: 50          # internal use only. Do not touch!
variable_safe_z: 60                            # float = safe z-height for xy travel moves
variable_auto_z_offset_calibration: True       # True|False = performs a auto z-offset calibration before the print starts if needed
variable_enable_camera_cooling: True           # True|False = enables the part cooling fan of the currently loaded toolhead
variable_camera_cooling_fan_speed: 0.3         # float = part cooling fan speed of the currently loaded toolhead
variable_camera_cooling_temperature: 50        # int = enables the integrated VAOC fan at the configured bed temperature 
variable_is_started: False                     # internal use only. Do not touch!
variable_toolchange_travel_speed: 300          # int = xy travel move speeds
variable_toolchange_travel_accel: 5000         # int = xy travel move sccelerations
variable_cache_toolchange_travel_speed: 300    # internal use only. Do not touch!
variable_cache_toolchange_travel_accel: 5000   # internal use only. Do not touch!
variable_cache_toolchange_zhop: 1.0            # internal use only. Do not touch!
variable_t0_toolhead_sensor_enabled: 0         # internal use only. Do not touch!
variable_t1_toolhead_sensor_enabled: 0         # internal use only. Do not touch!
variable_t0_bowden_sensor_enabled: 0           # internal use only. Do not touch!
variable_t1_bowden_sensor_enabled: 0           # internal use only. Do not touch!
```

## VAOC calibrate nozzle temp offset
```
[gcode_macro _VAOC_CALIBRATE_NOZZLE_TEMP_OFFSET]
variable_reference_z: 0.0   # internal use only. Do not touch!
touch!
```

## PAUSE
```
[gcode_macro PAUSE]
variable_extrude: 1.5           # extrusion in mm when resuming the print
variable_retract: 1.5           # retraction in mm when print is paused
variable_fan_speed: 0           # internal use only. Do not touch!
variable_idex_mode: ""          # internal use only. Do not touch!
variable_idex_toolhead: 0       # internal use only. Do not touch!
variable_idex_toolhead_x: 0.0   # internal use only. Do not touch!
variable_idex_toolhead_y: 0.0   # internal use only. Do not touch!
variable_idex_toolhead_z: 0.0   # internal use only. Do not touch!
```

## START_PRINT
```
[gcode_macro START_PRINT]
variable_post_processor_version: 2       # internal use only. Do not touch!
variable_is_printing_gcode: False        # internal use only. Do not touch!
variable_both_toolheads: True            # internal use only. Do not touch!
variable_object_xoffset: 0               # internal use only. Do not touch!
variable_first_x: -1                     # internal use only. Do not touch!
variable_first_y: -1                     # internal use only. Do not touch!
variable_total_toolshifts: 0             # internal use only. Do not touch!
variable_initial_tool: 0                 # internal use only. Do not touch!
variable_extruder_first_layer_temp: ""   # internal use only. Do not touch!
variable_extruder_other_layer_temp: ""   # internal use only. Do not touch!
```

## ratos_homing
```
[ratos_homing]
z_hop: 15         # homing z-hop distance
z_hop_speed: 15   # homing z-hop speed
```

## SET_PRESSURE_ADVANCE
```
[gcode_macro SET_PRESSURE_ADVANCE]
variable_snyc_toolheads: False   # internal use only. Do not touch!
```

## _ON_LAYER_CHANGE
```
[gcode_macro _ON_LAYER_CHANGE]
variable_layer_number: 0   # internal use only. Do not touch!
```

## END_FEATURE
```
[gcode_macro END_FEATURE]
variable_scv: 5         # internal use only. Do not touch!
variable_accel: 10000   # internal use only. Do not touch!
variable_ratio: 0.5     # internal use only. Do not touch!
```

## DEBUG_ECHO
```
[gcode_macro DEBUG_ECHO]
variable_enabled: False      # internal use only. Do not touch!
variable_prefix_filter: ''   # internal use only. Do not touch!
```

## CACHE_TOOLHEAD_SETTINGS
```
[gcode_macro CACHE_TOOLHEAD_SETTINGS]
variable_cache: {"global": {"accel": 1000, "ratio": 0.5, "speed": 50, "scv": 5}}   # internal use only. Do not touch!
```
