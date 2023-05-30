For Below Test Cases: 
16013539771 U.2 NVMe-EFI shell reset(Cold)
16013539880 U.2 NVMe-EFI shell reset(Warm)

 1. Connect 16 U.2 nvme to hsbp and Flash the latest IFWI , BMC and HSBP FW .
 2. Update the below tags in content configuration file under <storage> tag,
     reset_count tag is for number of cycles of coldreset or warm reset to be executed,
     timeout_in_secs is for timeout in seconds to wait until the 100 cycles gets completed.
        ex: 
     <reset_count>100</reset_count>
     <timeout_in_secs>4000</timeout_in_secs>
    </storage>