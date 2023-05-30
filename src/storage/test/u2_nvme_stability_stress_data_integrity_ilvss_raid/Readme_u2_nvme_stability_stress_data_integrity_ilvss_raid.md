TC: - ["16013942532", "U.2NVME-Stability and Stress- Data integrity - ILVSS in RAID Mode"]

Pre requisites :
 1) VROC Key
 2) U.2 NVMe 
 3) Pre-installed OS

Update ilvss information in content_config.xml as below,

Example:
<ilvss>
    <!-- ilvss tool run time in minutes -->
    <ilvss_run_time>10</ilvss_run_time>
    <!-- ilvss file name -->
    <ilvss_file_name>ilvss-3.6.25.man</ilvss_file_name>
    <!-- ilvss licence key file name -->
    <ilvss_licence_key>VSS_Site_12-01-2022_license.key</ilvss_licence_key>
</ilvss>

In content_configuration.xml, update NVMe drive details like below,
<nvme_drive_name>
    <!-- NVME 1 drive for RAID creation -->
    <nvme_1>INTEL SSDPF21Q400GB PHAL041200N8400JGN</nvme_1>
    <!-- NVME 2 drive for RAID creation -->
    <nvme_2>INTEL SSDPF21Q400GB PHAL0412013G400JGN</nvme_2>
    <nvme_3>INTEL SSDPF21Q400GB PHAL041200VL400JGN</nvme_3>
    <nvme_4>INTEL SSDPF21Q800GB PHAL04120050800LGN</nvme_4>
</nvme_drive_name>

In C:\Inventory, sut_inventory.cfg file,
update non_raid_ssd_name with the SSD name where we have OS.
Example :  non_raid_ssd_name = UEFI WDC WDS240G2G0A-00JH30 202290803367
