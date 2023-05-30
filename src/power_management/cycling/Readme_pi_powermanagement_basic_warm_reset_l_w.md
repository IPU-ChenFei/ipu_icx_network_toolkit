For the test cases H92918 - PI_Powermanagement_Basic_Warm_Reset_W, 
H92919 - PI_Powermanagement_Basic_Warm_Reset_L 
 
1) In content_configuration.xml, need to update tag, reboot_cycles, under power_management.
if we need to run for 10 cycles then example is <reboot_cycles>10</reboot_cycles>
2) and need to update the tag, machine_check under power_management-->dpmo-->machine_check
