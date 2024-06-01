# RatOS 2.1 Prusa slicer settings

**START GCODE**
```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[0]} EXTRUDER_OTHER_LAYER_TEMP={temperature[0]} BED_TEMP=[first_layer_bed_temperature] TOTAL_LAYER_COUNT={total_layer_count} X0={first_layer_print_min[0]} Y0={first_layer_print_min[1]} X1={first_layer_print_max[0]} Y1={first_layer_print_max[1]}
```

**IDEX START GCODE**
```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[0]},{first_layer_temperature[1]} EXTRUDER_OTHER_LAYER_TEMP={temperature[0]},{temperature[1]} BED_TEMP=[first_layer_bed_temperature] INITIAL_TOOL={initial_tool} TOTAL_LAYER_COUNT={total_layer_count} X0={first_layer_print_min[0]} Y0={first_layer_print_min[1]} X1={first_layer_print_max[0]} Y1={first_layer_print_max[1]}
```

**END GCODE**
```
END_PRINT
```

**BEFORE LAYER CHANGE GCODE**
```
;BEFORE_LAYER_CHANGE
;[layer_z]
```

**AFTER LAYER CHANGE GCODE**
```
;AFTER_LAYER_CHANGE
;[layer_z]
G92 E0
_ON_LAYER_CHANGE LAYER={layer_num + 1}
```

**TOOL CHANGE GCODE**
*only for IDEX*
```
T[next_extruder]
```

**BETWEEN OBJECTS GCODE**
```
;BETWEEN_OBJECTS
G92 E0
```

**FILAMENT START GCODE**
```
; Filament gcode
SET_PRESSURE_ADVANCE ADVANCE=0.05
```

# RatOS 2.1 Super slicer settings

**START GCODE**
```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[0]} EXTRUDER_OTHER_LAYER_TEMP={temperature[0]} BED_TEMP=[first_layer_bed_temperature] TOTAL_LAYER_COUNT={total_layer_count} X0={first_layer_print_min[0]} Y0={first_layer_print_min[1]} X1={first_layer_print_max[0]} Y1={first_layer_print_max[1]}
```

**IDEX START GCODE**
```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[0]},{first_layer_temperature[1]} EXTRUDER_OTHER_LAYER_TEMP={temperature[0]},{temperature[1]} BED_TEMP=[first_layer_bed_temperature] INITIAL_TOOL={initial_tool} TOTAL_LAYER_COUNT={total_layer_count} X0={first_layer_print_min[0]} Y0={first_layer_print_min[1]} X1={first_layer_print_max[0]} Y1={first_layer_print_max[1]}
```

**END GCODE**
```
END_PRINT
```

**BEFORE LAYER CHANGE GCODE**
```
;BEFORE_LAYER_CHANGE
;[layer_z]
```

**AFTER LAYER CHANGE GCODE**
```
;AFTER_LAYER_CHANGE
;[layer_z]
G92 E0
_ON_LAYER_CHANGE LAYER={layer_num + 1}
```

**TOOL CHANGE GCODE**
*only for IDEX*
```
T[next_extruder]
```

**BETWEEN OBJECTS GCODE**
```
;BETWEEN_OBJECTS
G92 E0
```

**FILAMENT START GCODE**
```
; Filament gcode
SET_PRESSURE_ADVANCE ADVANCE=0.05
```

# RatOS 2.1 Orca slicer settings

**START GCODE**
```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[0]} EXTRUDER_OTHER_LAYER_TEMP={nozzle_temperature[0]} BED_TEMP=[bed_temperature_initial_layer_single] TOTAL_LAYER_COUNT={total_layer_count} X0={adaptive_bed_mesh_min[0]} Y0={adaptive_bed_mesh_min[1]} X1={adaptive_bed_mesh_max[0]} Y1={adaptive_bed_mesh_max[1]}
```

**IDEX START GCODE**
```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[0]},{first_layer_temperature[1]} EXTRUDER_OTHER_LAYER_TEMP={nozzle_temperature[0]},{nozzle_temperature[1]} BED_TEMP=[bed_temperature_initial_layer_single] INITIAL_TOOL={initial_tool} TOTAL_LAYER_COUNT={total_layer_count} X0={adaptive_bed_mesh_min[0]} Y0={adaptive_bed_mesh_min[1]} X1={adaptive_bed_mesh_max[0]} Y1={adaptive_bed_mesh_max[1]}
```

**END GCODE**
```
END_PRINT
```

**BEFORE LAYER CHANGE GCODE**
```
;BEFORE_LAYER_CHANGE
;[layer_z]
```

**LAYER CHANGE GCODE**
```
;AFTER_LAYER_CHANGE
;[layer_z]
G92 E0
_ON_LAYER_CHANGE LAYER={layer_num + 1}
```

**CHANGE FILAMENT GCODE**
*only for IDEX*
```
T{next_extruder}
```

**PRINTING BY OBJECT GCODE**
```
;BETWEEN_OBJECTS
G92 E0
```

**FILAMENT START GCODE**
```
; Filament gcode
```
