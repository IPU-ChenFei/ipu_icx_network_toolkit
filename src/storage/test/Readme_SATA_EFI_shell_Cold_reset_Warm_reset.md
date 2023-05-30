For TC ID: 16013535852 : SATA - EFI shell reset(cold)
For TC ID: 16013535757 : SATA - EFi Shell reset(warm)

 1. Connect 8 sata ssd to hsbp and Flash the latest IFWI , BMC and HSBP FW .
 2. Update the below tags in content configuration file under <storage> tag,
     reset_count tag is for number of cycles of coldreset or warm reset to be executed,
     timeout_in_secs is for timeout in seconds to wait until the 100 cycles gets completed.
        ex: 
     <reset_count>100</reset_count>
     <timeout_in_secs>4000</timeout_in_secs>
    </storage>

For Below Test Cases: 
1509355093 : SATA- U.2 and M.2 EFI shell reset(warm)

Prerequisite:
   1. Connect 8 SATA SSD to the hsbp. 
   2. Connect M.2 SATA SSD to the SUT 
   3. Flash the latest IFWI , BMC and hsbp FW.

Step 1:
     Update the below tags in content configuration file under <storage> tag,
     reset_count tag is for number of cycles of warm reset to be executed,
     timeout_in_secs is for timeout in seconds to wait until the 100 cycles gets completed.
        ex: 
    <storage>
     <reset_count>100</reset_count>
     <timeout_in_secs>4000</timeout_in_secs>
    </storage>
step 2:
    update the sata_drive_name tag with connected devies
    please refer below example to update the tag
    <sata_drive_name>
        <!-- SATA 1 drive name for RAID creation -->
        <sata_1>CT480BX500SSD1 2020E3FB3A95</sata_1>
        <!-- SATA 2 drive name for RAID creation -->
        <sata_2>KINGSTON SA400S37480G 50026B76844A6EE8</sata_2>
    </sata_drive_name>
step 3:
    Make Sure usb is connected to the SUT and Run the Test case now.
