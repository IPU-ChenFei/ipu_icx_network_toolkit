 TC 16013819520 : U.2 NVME-FW update check  using Intel MAS tool With RAID Mode,
Pre requisites :
 1) VROC Key
 2) Four U.2 NVMe ( Gen3,Gen4 U.2 NVME)
 3) Pre installed Linux OS

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
Example :
non_raid_ssd_name = UEFI WDC WDS240G2G0A-00JH30 202290803367
