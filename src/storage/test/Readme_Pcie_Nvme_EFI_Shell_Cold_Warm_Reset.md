For Below Test Cases: 
16013537024 Pcie Nvme - EFI shell reset(cold)
16013537157 Pcie Nvme - EFI shell reset(cold)
16013536806 Pcie Nvme - EFI shell reset(warm)

Prerequisite: 
	1. Connect 8 pcie nvme to the pcie slots .
    2. Flash the latest IFWI and BMC.

Step 1:
     Update the below tags in content configuration file under <storage> tag,
     reset_count tag is for number of cycles of coldreset or warm reset to be executed,
     timeout_in_secs is for timeout in seconds to wait until the 100 cycles gets completed.
        ex: 
    <storage>
     <reset_count>100</reset_count>
     <timeout_in_secs>4000</timeout_in_secs>
    </storage>
step 2:
    update the nvme_drive_name tag with connected devies
    please refer below example to update the tag
    <nvme_drive_name>
			<nvme_3>INTEL SSDPF21Q400GB PHAL0412011J400JGN</nvme_3>
			<nvme_4>INTEL SSDPF21Q400GB PHAL0412010D400JGN</nvme_4>
			<nvme_5>INTEL SSDPF21Q400GB PHAL041200P0400JGN</nvme_5>
			<nvme_6>INTEL SSDPF21Q400GB PHAL041200FU400JGN</nvme_6>
			<nvme_7>INTEL SSDPF21Q400GB PHAL0412000B400JGN</nvme_7>
			<nvme_8>INTEL SSDPF21Q400GB PHAL0412012Z400JGN</nvme_8>
			<nvme_9>INTEL SSDPF21Q400GB PHAL0412018K400JGN</nvme_9>
    </nvme_drive_name>
step 3:
    Make Sure usb is connected to the SUT and Run the Test case now.
