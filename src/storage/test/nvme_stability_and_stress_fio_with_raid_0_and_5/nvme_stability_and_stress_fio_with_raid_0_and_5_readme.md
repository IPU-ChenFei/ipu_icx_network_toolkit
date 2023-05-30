Test Case: ["16013957609", "NVME_Stability_and_Stress_FIO_with_RAID_0_and_5"]

1. Update the content_config tags for u.2 and pcie nvme

		<nvme_pcie_drive_name>
			<nvme_1>INTEL SSDPED1K015TA PHKS013300411P5CGN</nvme_1>
			<nvme_2>INTEL SSDPED1K015TA PHKS041100201P5CGN</nvme_2>
			<nvme_3>INTEL SSDPED1K015TA PHKS0133003E1P5CGN</nvme_3>
			<nvme_4>INTEL SSDPED1K015TA PHKS0133004S1P5CGN</nvme_4>
        </nvme_pcie_drive_name>
		
		<u2_nvme_drive_name>
            <nvme_1>INTEL SSDPF21Q400GB PHAL041200ZN400JGN</nvme_1>
            <nvme_2>INTEL SSDPF21Q400GB PHAL041200PS400JGN</nvme_2>
			<nvme_3>INTEL SSDPF21Q400GB PHAL041200N8400JGN</nvme_3>
			<nvme_4>INTEL SSDPF21Q400GB PHAL0412013G400JGN</nvme_4>
        </u2_nvme_drive_name>
        
2. Update the sut_inventory config with non_raid_ssd_name which has OS present in it
    
    non_raid_ssd_name = UEFI WDC WDS240G2G0A-00JH30 212816451813