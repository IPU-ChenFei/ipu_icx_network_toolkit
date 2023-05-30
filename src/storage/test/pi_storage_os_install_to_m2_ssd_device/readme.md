TC ID : H97917-PI_Storage_OS_Install_to_M.2_SSD_device_L

Prerequisite: 
	1. 1 SSD with RHEL installed
	2. NVME M.2 should be connected in the m.2 port.
	3. 1 USB
	
1. Create sut_inventory.cfg under C:\Inventory folder, refer this BKM on how to create [E2E_provisioning_One_liner.md](E2E_Provisioning_One_liner.md).
2. Update the above created file with your SATA or NVME device names, how it is shown in BIOS boot order list as per hardware connected on your system.

    example:
		[sut_information]
		mode = manual
		usb_name_1 = UEFI USB SanDisk 3.2Gen1 04015d5119abe6f416bc425b694f42f0f2862495151776ee3eaf08d5a42ba7bad5f200000000000000000000b4f0b67f000b811891558107b82951b4
		usb_size = 32
		nvme_ssd_name_rhel = UEFI Misc Device (the name of the nvme m.2 how it is shown in BIOS boot order list )

3. update the content_configuration.xml with the full name of NVME M.2 connected to the SUT.
   <storage>
	    <nvme_m2_drive_name>FULL NAME OF THE NVME M.2</nvme_m2_drive_name>
   </storage>
4. Download software package / os package from OWR repo (Artifactory)
5. After downloading, update the content_configuration.xml with software package / os package path in the tags accordingly.
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
	

6. Run the test case now.

Note: Make sure NVME M.2 is connected in the m.2 port of the SUT and the correct full name is given in the content_configuration.xml
file under the above mentioned tag(step No. 3)
