TC ID : H97917-PI_Storage_OS_Install_to_M.2_SSD_device_L

Prerequisite: 
	1. 1 SSD with RHEL installed
	2. 1 PCI NVME should be connected in the slot C.

	
Please put correct  Pcie_Device_Name  and get from bios menu page -- Ex:create RAID on CPU->it will list all devices
and do not remove SPR tag in below else test case fail

	<pcie_device_population>
            <SPR>

                <slot_c>
                    <Pcie_Device_Name>INTEL SSDPED1K015TA SN:PHKS126000011P5CGN</Pcie_Device_Name>
                    <pcie_device_speed_in_gt_sec>8</pcie_device_speed_in_gt_sec>
                    <pcie_device_width>x1</pcie_device_width>
                    <bus>04</bus>
            </SPR>

  </pcie_device_population>

2. Maintain SUT inventory config file for Non raid disk where RHEL installed in SSD as below
	[sut_information]
	mode = manual
	non_raid_ssd_name = UEFI Samsung SSD 870 EVO 500GB S6PXNJ0R611521Y

3.For nvme storeage devices info maintain as in below <storage> tag
	 <storage>
		  <nvme_drive_name>
				<!-- NVME 1 drive for RAID creation -->
				<nvme_1>INTEL SSDPED1K015TA PHKS126000011P5CGN 1</nvme_1>
				<!-- NVME 2 drive for RAID creation -->
				<nvme_2>INTEL SSDPED1K015TA PHKS0230003W1P5CGN 1</nvme_2>
		  </nvme_drive_name>

	 </storage>

