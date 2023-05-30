## Menu Bar
* Setting
  * Open different config file for user setting
* Tool
  * File Transfer: Panel for transfer file between host & sut
  * Utilities Setup: Panel for setup validation tools to system (get tools/uncomparess/install/..., i.e. convert tools solution to gui operation for users)
* Help
  * Help Page


## High Level Step Panel
* usage flow: click button -> pop up sub panel ->
click/input data -> then directly execute related apis (import these api from toolkit lib) ->
output generated python logs to "DryRun Log"
* specific for "Set Feature"
  * bios knobs are defined in pvl.xlsx (including biosmenu + xmlcli), so need to extract apis from vl_translator.py (refer to plvltk/generated_step.py/__l2py_translate_file())
  * or, need to parse pvl.xlsx, then collect all values for xmlcli and bios menu, and call toolkit lib api to set it correctly

## Low Level Step Panel
* same as above

## DryRun Log


## Generated Step
* Record generated HLS/LLS steps
* Add save/load/run widget for running existing steps


## BIOS Log
* output bios logs in real time with toolkit lib api
* should provide start/stop funciton for bios log


## System Monitor
* continuously monitor power status, post code
* each monitor should provide start/stop function


## Common Requirement
* Each text widget should provide popup window: Copy/Cut/Paste/Clear/Save As
* Development Flow in parallel
  1. Module Function Definition (format: module->class->function)
      * menubar
      * vlstep
      * textwidget (used for: dryrunlog/bioslog/generatedsteps)
      * bioslog
      * monitor
      * utils
  2. Window/Panel Layout
     * main_window + "layout package"
  3. Module API Implementation & Verification
  4. Function Integration with widgets


## Reference GUI
* reference/dryrun_box1.rp
* plvltk/plvl2.py
* plvltk/plvl.py