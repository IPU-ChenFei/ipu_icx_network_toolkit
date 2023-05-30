TC: -["16014320191", "M_2_SATA_Stability_and_Stress_FIO"]

OS : RHEL
M.2 should be connected in SUT

Update content_config.xml tags as below: check from smartctl command get the model number and serial number in SUT
       fio>
            <!-- FIO app test tool configuration -->
            <fio_runtime>300</fio_runtime> <!-- give time in seconds -->
            <!-- Give ssd details in below format : seperated. Ignore OS SSD -->
            <file_name> /dev/sdf</file_name>
        </fio>
update fio_runtime and file_name should be M.2 SATA SSD device name connected in the SUT.