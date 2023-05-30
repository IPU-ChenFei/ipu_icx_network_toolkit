Common precondition:

1. Config your system following the test plan including HW config and SW config. 

2. Make sure ITP was connected to your system. Make sure pythonsv has updated to the latest and works well on the host.

3. Connect Bios Serial cable to system. Open putty or taraterm for logging the log.

4. Connect BMC Serial cable to system. Use cmdtool to enable BMC console login account. Open putty or taraterm for logging the log.

5. Connect SUT to the network.

6. List each storage device model, serial number and which slot each inserts for future check.



Tools and Devices(HW --- SW)

1. SF100/SF600 --- Dediprog : For updating Bios and BMC firmware.

2. Blaster --- Quartus : For updating CPLD.

3. ITP --- Pythonsv : For save the log.

4. cmdtool : For enabling BMC console account.



HW - ITP required, Pythonsv/Cscript should be working fine
For other tool, please refer to HSD for detail.
