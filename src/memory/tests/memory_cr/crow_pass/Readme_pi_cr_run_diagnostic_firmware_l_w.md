For the test cases, H101118: PI_CR_RunDiagnosticFirmware_L, H101163 : PI_CR_RunDiagnosticFirmware_W,

Before running the test case, make sure Firmware version on the CPS should be same.
Command to check firmware version on CPS is : ipmctl show -firmware 
Example:
ipmctl show -firmware
 DimmID | ActiveFWVersion | StagedFWVersion
============================================
 0x0001 | 03.01.00.2506   | N/A
 0x0011 | 03.01.00.2506   | N/A
 0x0101 | 03.01.00.2506   | N/A
 0x0111 | 03.01.00.2506   | N/A
 0x0201 | 03.01.00.2506   | N/A
 0x0211 | 03.01.00.2506   | N/A
 0x0301 | 03.01.00.2506   | N/A
 0x0311 | 03.01.00.2506   | N/A
 0x1001 | 03.01.00.2506   | N/A
 0x1011 | 03.01.00.2506   | N/A
 0x1101 | 03.01.00.2506   | N/A
 0x1111 | 03.01.00.2506   | N/A
 0x1201 | 03.01.00.2506   | N/A
 0x1211 | 03.01.00.2506   | N/A
 0x1301 | 03.01.00.2506   | N/A
 0x1311 | 03.01.00.2506   | N/A

if any one of the CPS firmware version is different:
Please update the CPS firmware.

Steps to update CPS firmware:
1)After downloading the <*.bin> firmware image file to the target system, ensure the firmware image is valid and
 supported, using the examine option.
ipmctl load -source (firmware file) -examine -dimm

2)Then update the firmware image with following command. It is recommended that all firmware in the system have same
 versions, although updating the firmware on individual modules is supported.
ipmctl load -source (firmware file) -dimm

3)Verify Staged FW Version is according to update.
ipmctl show -dimm -firmware

4)Power cycle the server and confirm the Active FW Version is the latest version.
ipmctl show -dimm -firmware
