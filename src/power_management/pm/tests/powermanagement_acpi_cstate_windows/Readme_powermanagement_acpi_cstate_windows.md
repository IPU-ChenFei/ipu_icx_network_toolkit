For the test case H87939 - PI_Power Management - ACPI C-States on Windows,
1) Need to download the PTU tool exe file.
2) Zip the exe file name to Intel_Power_Thermal_Utility.zip.
3) In content_configuration.xml, we need to update the tag, under ptu--> windows.
Example:
   <ptu>
        <windows>C:\Automation\BKC\Tools\windows\Intel_Power_Thermal_Utility.zip</windows>
   </ptu>

