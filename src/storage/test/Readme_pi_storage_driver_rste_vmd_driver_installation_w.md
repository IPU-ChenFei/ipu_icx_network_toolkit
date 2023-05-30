For the Test case : H80275 - PI_Storage_Driver_RSTeVMDDriver_Installation_W,
1) we need to update the content_configuration.xml, pcie_slots tags.

The connected PCIe NVMe slot location, we need no keep True and other slots with False. 
Example : if PCIe NVMe connected in right riser top slot then we need to keep right_riser_top_slot as True and remaining False.
<pcie_slots>
            <left_riser_bottom_slot>False</left_riser_bottom_slot>
            <left_riser_top_slot>False</left_riser_top_slot>
            <slot_b>False</slot_b>
            <right_riser_bottom_slot>False</right_riser_bottom_slot>
            <right_riser_top_slot>True</right_riser_top_slot>
            <slot_e>False</slot_e>
</pcie_slots>
2) Driver Intel_VROC has to download from the BKC mail under category DRIVER.
The path has to update in content_configuration.xml, under tag vroc_tool --> windows. 
   Example :
   <vroc_tool>
            <linux>C:\Automation\BKC\Tools\linux\vroc.zip</linux>

            <windows>C:\Automation\BKC\Tools\windows\vroc.zip</windows>
   </vroc_tool>
