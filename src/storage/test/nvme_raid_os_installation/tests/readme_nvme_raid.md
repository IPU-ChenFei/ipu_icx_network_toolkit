TC: H80250 - PI_Storage_VROC_NVMe_RAID0_L
TC ID : H80239

Prerequisite: 
	1. 2 empty PCIE SSDs
	2. 1 SATA SSD with RHEL installed
	3. 1 USB
	4. Connect Premium VROC key
	Note : We have connected the above Hard ware to ports in this order 2 empty PCIE SSDs to Slot B, Left riser top slot
	and SATA SSD with RHEl to port3

After RAID creation: the  empty SSD names will appear in boot page as UEFI Misc Device(is RAID)
After RAID deletion: the two empty SSD names will appear in boot page as UEFI Misc Device and UEFI Misc Device 2
	
1. Create sut_inventory.cfg under C:\Inventory folder, refer this BKM on how to create [E2E_provisioning_One_liner.md](E2E_Provisioning_One_liner.md).
2. Update the above created file with your SATA or NVME device names, how it is shown in BIOS boot order list as per hardware connected on your system.

    example:
		[sut_information]
		mode = manual
		usb_name_1 = UEFI USB SanDisk 3.2Gen1 04015d5119abe6f416bc425b694f42f0f2862495151776ee3eaf08d5a42ba7bad5f200000000000000000000b4f0b67f000b811891558107b82951b4
		usb_size = 32
        non_raid_ssd_name = UEFI ****** (the SSD with preinstalled rhel)
		nvme_ssd_name_rhel = UEFI Misc Device

3. update the content_configuration.xml with the PCIe slot information where the PCIe SSDs are connected.
	<pcie_slots>
            <!--Add True if the PCIe NVMe Card connected to the Particular PCIe Slot in the SUT else False -->
            <left_riser_bottom_slot>False</left_riser_bottom_slot>
            <left_riser_top_slot>True</left_riser_top_slot>
            <slot_b>True</slot_b>
            <right_riser_bottom_slot>False</right_riser_bottom_slot>
            <right_riser_top_slot>False</right_riser_top_slot>
            <slot_e>False</slot_e>
   </pcie_slots>

4. Download software package / os package from OWR repo (Artifactory)
5. After downloading, update the content_configuration.xml with software package / os package path in the tags accordingly.
   	<mark>
    <os_installation>
        <win>
            <os_pkg_path>C:\os_package\WIN2022.20344_FRE_IA-64_EGS-SRV-WIN2022-21.35.6.6F.wim</os_pkg_path>
            <sft_pkg_path>None</sft_pkg_path>
            <atf_iso_path>None</atf_iso_path>
            <cfg_file_name>None</cfg_file_name>
        </win>
        <rhel>
			<os_pkg_path>C:\os_package\rhel-8.4.0-20210503.1-x86_64-dvd1_auto_v3_FRE_IA-64_EGS-SRV-RHEL-21.38.3.161B.zip</os_pkg_path>
			<sft_pkg_path>C:\os_package\EGS-SRV-RHEL-21.38.3.161B_SWpackage.zip</sft_pkg_path>
            <cfg_file_name>rh8.4-uefi-raid.cfg</cfg_file_name>
            <atf_iso_path>None</atf_iso_path>
        </rhel>
        <centos>
            <os_pkg_path>None</os_pkg_path>
            <sft_pkg_path>None</sft_pkg_path>
            <atf_iso_path>https://ubit-artifactory-ba.intel.com/artifactory/dcg-dea-srvplat-local/Automation_Tools/SPR/CentOS_8_4_v3.iso</atf_iso_path>
            <cfg_file_name>None</cfg_file_name>
        </centos>
    </os_installation>
   </mark>
   <nvme_drive_name>
            <!-- NVME 1 drive name for RAID creation -->
            <nvme_1>WDC WDS480G2G0A-00JH30 20504V803188</nvme_1>
            <!-- NVME 2 drive name for RAID creation -->
            <nvme_2>CT480BX500SSD1 2020E3FB3A95</nvme_2>
   </nvme_drive_name>
6. Run the test case now.

For Test Case: 16013612118 - Pcie SSD - Check Data Raid for Pcie ssd between VMD controllers
Prerequisite: 
	1. minimum 4  empty PCIE SSDs and maximum is max supported
	2. 1 SATA SSD with RHEL installed
	3. Connect Premium VROC key
step 1:
    update the content_configuration.xml with the PCIe slot information where the PCIe SSDs are connected.
    please refer pcie_slots tag above

step  2:
    update the nvme_drive_name tag with connected devies
    please refer above to update the tag
step 3:
    Run the Test case now.


