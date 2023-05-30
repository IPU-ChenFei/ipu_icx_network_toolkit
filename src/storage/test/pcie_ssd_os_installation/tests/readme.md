### All PCIe OS installation test cases

1. Create sut_inventory.cfg under C:\Inventory folder, refer this BKM on how to create [E2E_provisioning_One_liner.md](E2E_Provisioning_One_liner.md).
2. Update the above created file with your PCIE device names, how it is shown in BIOS boot order list as per hardware connected on your system.
   example:
		[sut_information]
		mode = manual
		usb_name_1 = UEFI USB SanDisk 3.2Gen1 04015d5119abe6f416bc425b694f42f0f2862495151776ee3eaf08d5a42ba7bad5f200000000000000000000b4f0b67f000b811891558107b82951b4
		usb_size = 32
        pcie_ssd_name_rhel = UEFI ******* (target PCIe SSD name)
        non_raid_ssd_name = UEFI ****** (the SSD with preinstalled rhel)
		nvme_ssd_name_rhel = UEFI Misc Device
   		sata_ssd_name_rhel = UEFI ***********

3. Download software package / os package from OWR repo (Artifactory)
4. After downloading, update the content_configuration.xml with software package / os package path in the tags accordingly.
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
5. Run the test case now.

For Test Cases where VMD enabling is required :
	
	1.We need to update the content_configuration.xml, pcie_slots tags.

	The connected PCIe SSD slot location, we need no keep True and other slots with False. 
	Example : if PCIe SSD connected in mcio_s0_pxp4_pcieg_port2slot then we need to keep mcio_s0_pxp4_pcieg_port2 as True and remaining False.
	<pcie_slots>
            <!--Add True if the PCIe NVMe/SSD Card connected to the Particular PCIe Slot in the SUT else False -->
            <left_riser_bottom_slot>False</left_riser_bottom_slot>
            <left_riser_top_slot>False</left_riser_top_slot>
            <slot_b>False</slot_b>
            <right_riser_bottom_slot>False</right_riser_bottom_slot>
            <right_riser_top_slot>False</right_riser_top_slot>
            <slot_e>False</slot_e>
            <mcio_s0_pxp4_pcieg_port2>True</mcio_s0_pxp4_pcieg_port2>
        </pcie_slots>
	2. Update the sut_inventory.cfg    ###refer steps for above Pcie test case
	3. update the os_installation tag  ###refer steps for above Pcie test case
	4. Run the test case now.
	
	
	
