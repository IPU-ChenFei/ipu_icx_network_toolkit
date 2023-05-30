TC "16013871985", "U2_nvme_stability_cross_socket_stress_fio"

1. RHEL OS to be installed in SATA SSD
2. update the content config file with the details of Nvme drive 
           <nvme_drive_name>
               <!-- NVME 1 drive for RAID creation -->
               <nvme_1>INTEL SSDPF21Q400GB PHAL041200N8400JGN</nvme_1>
               <!-- NVME 2 drive for RAID creation -->
               <nvme_2>INTEL SSDPF21Q400GB PHAL0412013G400JGN</nvme_2>
               <nvme_3>INTEL SSDPF21Q400GB PHAL041200VL400JGN</nvme_3>
               <nvme_4>INTEL SSDPF21Q800GB PHAL04120050800LGN</nvme_4>
           </nvme_drive_name>
3. Update the content config file for how long you want to run FIO 
   <fio>
      <!-- FIO app test tool configuration -->
      <fio_runtime>60</fio_runtime> <!-- give time in seconds -->