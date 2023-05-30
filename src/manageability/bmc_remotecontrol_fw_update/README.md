BMC Flashing using Redfish for SPR platform:
------------------------------------------------------
Following information has to be populated for performing the flashing via redfish api
1. user need to keep the bin file of BMC firmware in the host which is associated with the current version from 
   latest BKC mail in below location
<current_bmc_fw_file>C:\Automation\BKC\Tools\OBMC-egs-0.30-0-g42d189-8fc454f-pfr-oob.bin</current_bmc_fw_file>
            
2. user need to keep the bin file of BMC firmware in the host which is associated with the  
   previous version from latest BKC mail in below location
<previous_bmc_fw_file>C:\Automation\BKC\Tools\OBMC-egs-0.29-0-g971e3d-8fc454f-pfr-oob.bin</previous_bmc_fw_file>
   

Testcase execution method is same as other DTAF testcases provided the system is Configured with BMC.

System configuration Details:
------------------------------------------------------
Following information has to be populated in system_configuration.xml file inside <sut><silicon> tag before executing 
the testcases:
<bmc>
    <ip>10.219.165.77</ip>    [BMC IP of the system]
    <credentials user="debuguser" password="0penBmc1"/>
</bmc>

Add the test as event in BKC execution


