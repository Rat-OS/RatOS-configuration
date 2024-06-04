# RatOS 2.1 with Beacon Contact 

## Prerequisites
- update RatOS 2.1 via mainsail
- read the official [beacon contact documentation](https://docs.beacon3d.com/contact/), but do not follow any installation instructions from there. 

## Initial calibration
We need to create a intial beacon model to be able to home the printer. **DO NOT USE** the `SET_CENTER_KINEMATIC_POSITION` command.
Run the following gcode commands to create the intial model. the `BEACON_AUTO_CALIBRATE` command can throw a tolerance error, in this case just repeat it until the command gets successfully executed. 

For safety and peace of mind, the LED will turn on as soon as the contact system determines it has a strong enough signal for detection. It should normally turn on up to 10mm in advance of the metal target, allowing enough time to manually estop the machine if necessary.

```
G28 X
G28 Y
BEACON_AUTO_CALIBRATE
```
Click `SAVE CONFIG` to save the model to your printer.cfg file.

## First test
Home your printer and then run 5 times `BEACON_POKE bottom=-0.6` from the mainsail console. Then check the console output, it should look like this: 
```
Overshoot: 35.625 um
Triggered at: z=0.07369 with latency=2
Armed at: z=4.76021
Poke test from 5.000 to -0.300, at 3.000 mm/s
```

We are interested in the latency value. Compare your results with the following list.

| Score	| Notes |
| :------------ |:--------------- |
| 0-1	| Extremely low noise, rarely achieved
| 2-3	| Excellent performance for a typical printer
| 4-6	| Acceptable performance, machine may have considerable cyclic axis noise
| 7-9	| Not ideal, may want to verify proper mounting or use thinner stackups
| 10-11	| Reason for concern, present setup may be risky to continue with

## Temperature expansion calibration
RatOS comes with a built in temperature expansion calibration and compensation.

- Unload filament from the nozzle
- Make sure the nozzle is clean and that no filament is leaking out of it. Make a cold pull for example.
- Let the machine cool down to ambient temperature
- Do NOT make this calibration on a smooth PEI sheet, in this case turn the sheet arround and make the calibration on the bare metall of it. 

**Single toolhead printer**
- run the macro `BEACON_CALIBRATE_NOZZLE_TEMP_OFFSET`. It will home your printer and run the calibration fully automated, this will take some minutes

**IDEX printer**
- Start VAOC
- Center both nozzles over the camera
- run the macro `_VAOC_CALIBRATE_TEMP_OFFSET`. This will calibrate both nozzles fully automated, this will take some minutes

It is recommended to repeat that process always when you change a nozzle and before loading any new filament into it.

After the test is finished check the console output, it should look like this typical result:
```
RatOS | Beacon: T0 expansion coefficient: 0.075000
```
This value is in mm and represents the thermal expansion for a temperature difference of 100°C. RatOS uses this value to calculate the needed offset and applies it automatically.

The result will be saved automatically to the configuration file, there is no user action required.


## RatOS configuration
The beacon contact feature is deactivated by default, enable it by copying this recommended configuration into your printer.cfg. 
```
#####
# Beacon probe configuration
#####
[gcode_macro RatOS]
variable_beacon_bed_mesh_scv: 25                         # square corner velocity for bed meshing with proximity method
variable_beacon_contact_z_homing: False                  # printer z-homing with contact method
variable_beacon_contact_z_calibration: True              # contact z-calibration before the print starts
                                                         # after changing this variable please run a recalibration before you use the printer  
                                                         # if you use a smooth PEI sheet turn this feature off
variable_beacon_contact_calibration_location: "center"   # center = center of the build plate
                                                         # front = front center
                                                         # corner = front corner
variable_beacon_contact_calibrate_margin_x: 30           # x-margin if calibrate in front corners
variable_beacon_contact_bed_mesh: False                  # bed mesh with contact method
variable_beacon_contact_bed_mesh_samples: 2              # probe samples for contact bed mesh
variable_beacon_contact_z_tilt_adjust: False             # z-tilt adjust with contact method
variable_beacon_contact_z_tilt_adjust_samples: 2         # probe samples for contact z-tilt adjust
variable_beacon_contact_prime_probing: True              # probe for priming with contact method
variable_beacon_contact_calibration_temp: 150            # nozzle temperature for auto calibration
variable_beacon_contact_expansion_compensation: True     # enables the nozzle thermal expansion compensation
variable_beacon_contact_expansion_multiplier: 1.0        # multiplier for the nozzle thermal expansion compensation
```

## First print and fine tuning
- Print a 50x50mm one layer thick square in the middle of the buildplate. 
- Use the `beacon_contact_expansion_multiplier` variable to fine tune your first layer squish. Higher value means less squish and lower value means more squish. 1.1 = a bit less squish, 0.9 = a bit more squish, ....

## Final calibration
For the scan method z-homing we should create a beacon model under real conditions. Run the following gcode commands to create the final beacon model. 
```
G28
G0 Z2 F1200
M104 S150
M190 S85                  # use your target bed temperature
M109 S150
G4 P90000
BEACON_AUTO_CALIBRATE
G0 Z15 F1200
M104 S0
M190 S0
```
Click `SAVE CONFIG` to save the model to your printer.cfg file.
