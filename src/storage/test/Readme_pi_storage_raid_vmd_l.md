For the Test case : H80241 - pi_storage_raid_vmd_l,
1) Need to connect the SUT with 2 PCIE NVME Cards
   
2) We need to update the content_configuration.xml, pcie_slots tags.

The connected PCIe NVMe slot location, we need no keep True and other slots with False. 
Example : if PCIe NVMe connected in right riser top slot then we need to keep right_riser_top_slot as True and remaining False.
<pcie_slots>
            <left_riser_bottom_slot>False</left_riser_bottom_slot>
            <left_riser_top_slot>True</left_riser_top_slot>
            <slot_b>True</slot_b>
            <right_riser_bottom_slot>False</right_riser_bottom_slot>
            <right_riser_top_slot>False</right_riser_top_slot>
            <slot_e>False</slot_e>
</pcie_slots>

