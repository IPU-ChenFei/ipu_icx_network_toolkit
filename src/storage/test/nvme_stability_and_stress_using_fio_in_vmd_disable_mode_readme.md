TC: -["16013961309", "NVME-Stability and stress using FIO in VMD disable mode"]

Update content_config.xml tags as below: check from smartctl command get the model number and serial number in SUT
        <nvme_drive_name>
            <!-- NVME 1 drive for RAID creation -->
            <nvme_1>INTEL SSDSC2KB960G8 PHAL041200RP400JGN</nvme_1>
            <!-- NVME 2 drive for RAID creation -->
            <nvme_2>INTEL SSDSC2KB960G8 PHAL041200RK400JGN</nvme_2>
            <nvme_3>INTEL SSDSC2KB960G8 S55JNE0N800535</nvme_3>
            <nvme_4>INTEL SSDSC2KB960G8 S55JNE0N800437</nvme_4>
            <nvme_5>INTEL SSDSC2KB960G8 S55JNE0N800050</nvme_5>
            <nvme_6>INTEL SSDSC2KB960G8 S55LNG0NC00548</nvme_6>
            <nvme_7>INTEL SSDSC2KB960G8 S55JNE0N800594</nvme_7>
            <nvme_8>INTEL SSDSC2KB960G8 S55JNE0N800597</nvme_8>
        </nvme_drive_name>

        <nvme_disks_linux>/dev/nvme0n1,/dev/nvme3n1,/dev/nvme4n1,/dev/nvme5n1</nvme_disks_linux>:Upadte all 4 disks you want to run FIO 

<sata_m2_drive_name>INTEL SSDSC2KB960G8 BTLA805312DR128I</sata_m2_drive_name>: The M.2 Sata disk where the OS is booted from.