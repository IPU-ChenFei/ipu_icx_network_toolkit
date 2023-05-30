For the Test case : 16013802852-U.2 Nvme - Execute the commands of Nvme cli tool,
1) Need to connect the SUT with U.2 NVME Cards
 
2) We need to update the content_configuration.xml nvme_disks_linux tag by disk names separated by comma.
  Ex:
   <nvme_disks_linux>/dev/nvme0n1,/dev/nvme1n1</nvme_disks_linux>
3) Run the Test Case now
