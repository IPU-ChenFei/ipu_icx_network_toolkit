For the Test case : 16013579805 - U.2 NVME Check Software RAID creation in VMD Enable with RAID
1) Need to connect the SUT with U.2 NVME Cards
 
2) We need to update the content_configuration.xml nvme_disks_linux tag by disk names separated by comma.
  Ex:
   <nvme_disks_linux>/dev/nvme0n1,/dev/nvme1n1,/dev/nvme2n1, /dev/nvme3n1</nvme_disks_linux>

3) We need to update the content_configuration.xml, pcie_slots tags.

The connected U.2 NVMe slot location, we need to keep True and other slots with False. 
Example : if U.2 NVMe connected in mcio_s1_pxp4_pcieg_port0 slot then we need to keep mcio_s1_pxp4_pcieg_port0 as True 
<pcie_slots>
            <left_riser_bottom_slot>False</left_riser_bottom_slot>
            <left_riser_top_slot>False</left_riser_top_slot>
            <slot_b>Flase</slot_b>
            <right_riser_bottom_slot>False</right_riser_bottom_slot>
            <right_riser_top_slot>False</right_riser_top_slot>
            <slot_e>False</slot_e>
            <mcio_s1_pxp4_pcieg_port0>True</mcio_s1_pxp4_pcieg_port0>
            <mcio_s1_pxp4_pcieg_port1>True</mcio_s1_pxp4_pcieg_port1>
			<mcio_s1_pxp4_pcieg_port3>True</mcio_s1_pxp4_pcieg_port3>
			<mcio_s1_pxp5_pcieg_port3>True</mcio_s1_pxp5_pcieg_port3>
</pcie_slots>

4) Run the Test Case now
