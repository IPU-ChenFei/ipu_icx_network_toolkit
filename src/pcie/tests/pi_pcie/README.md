Content_configuration Update.

Test Case:- "G16400", "PCI_Express_PCIe_Subsytem_IO_Bus_Check" 
Test Case:- "G10473", "PCI_Express_PCIe_Adapter_IO_Bus_Check"
Test Case:- "H92895", "PI_PCIE_All_Slot_Populated_Reset_W"
Test Case:- "H89962", "PI_PCIe_Endpoint_LTSSM_Testing_Gen4_L"
Test Case:- "H89963", "PI_PCIe_Link_training_and_Initialization_Overnight_AC_cycling_Gen4_W"
Test Case:- "H102286", "G10527", "PI_PCIe_Endpoint_LTSSM_Testing_Gen5_W"
Test Case:- "H89967", "PI_PCH_SlotC_LTSSM_Endpoint_Testing_L"

Above Test Cases should follow below mention configuration changes.

PCIe Slot which is needed to Test.
For example if we need to test "right_riser_bottom,right_riser_top,left_riser_top" slot then we should keep these slot under "select_slot" tag, eg: below: 

<select_slot>left_riser_bottom,left_riser_top,slot_e</select_slot>
and: 
Note: For All slot, <select_slot>All_Slot</select_slot>

Now Fill the info of PCIe devices of all slot which we have selected above under your selected tag example.
<left_riser_bottom>
      <Pcie_Device_Name>ETHERNET NETWORK ADAPTER - X710-T2L</Pcie_Device_Name>
      <pcie_device_speed_in_gt_sec>8</pcie_device_speed_in_gt_sec>
      <pcie_device_width>x8</pcie_device_width>
</left_riser_bottom>
<left_riser_top>
       <Pcie_Device_Name>ETHERNET NETWORK ADAPTER - X710-T2L</Pcie_Device_Name>
       <pcie_device_speed_in_gt_sec>8</pcie_device_speed_in_gt_sec>
       <pcie_device_width>x8</pcie_device_width>
</left_riser_top>
<slot_e>
       <Pcie_Device_Name>ETHERNET NETWORK ADAPTER - X710-T2L</Pcie_Device_Name>
       <pcie_device_speed_in_gt_sec>8</pcie_device_speed_in_gt_sec>
       <pcie_device_width>x8</pcie_device_width>
</slot_e>

Below Changes also require for PCI Cycling Test Case:
TC:
PI_PCIe_Link_training_and_Initialization_Overnight_AC_cycling_Gen4_W
PI_PCIe_Link_training_and_Initialization_Overnight_AC_cycling_Gen4_L

<pcie>
    <cycling_time>43200</cycling_time>
</pcie>


Test Case:- "G10526", "PCI_Express_PCIe_Gen1_Link_Width_Verification"
Test Case:- "G10525", "PCI_Express_PCIe_Gen2_Link_Width_Verification"
Test Case:- "G29886", "PCI_Express_PCIe_Gen3_Link_Width_Verification"

For the above Test Cases should follow below mention configuration changes.

PCIe Slot which is needed to Test.
For example if we need to test "left_riser_top" slot then we should keep these slot under "select_slot" tag, eg: below: 

    <select_slot>left_riser_top</select_slot>
Now fill the details of Populated slot:
<!-- All Slot -->
<pcie_device_population>
    <SPR>
        <left_riser_top>
            <Pcie_Device_Name>INTEL® GIGABIT CT DESKTOP ADAPTER - X710</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>2.5</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x1</pcie_device_width>
        </left_riser_top>
    </SPR>
</pcie_device_population>


"G56023", "PCI_Express_Adapter_power_state_cycling_using_driver_unloads_loads_Linux"

For the above Test Case should follow below mention configuration changes.

<pcie>
    <number_of_cycle_to_load_unload_driver>500</number_of_cycle_to_load_unload_driver>
</pcie>

"H102286", "G10527", "PI_PCIe_Endpoint_LTSSM_Testing_Gen5_W"
For the above Test Case you should follow below mentioned configuration changes.

<pcie_disable>False</pcie_disable>
<pcie_disable_cards_device_id_list>mlx5_ib,mlx5_core,i40iw,i40e</pcie_disable_cards_device_id_list>

Test Case:- "H89967", "PI_PCH_SlotC_LTSSM_Endpoint_Testing_L"

For the above Test Case should follow below mention configuration changes.

Suggested to use SLOT C Rework system

prferreded to use gen3 cards:
		Intel Corporation Ethernet Network Adapter X710-T2L   
		Intel® Corporation Ethernet Network Adapter XXV710-DA2T


We need to update the content configuration bus id,speed, width, device name for connected ethernet

<pcie_device_population>
            <SPR>
                
                <slot_c>
                    <Pcie_Device_Name>Intel Corporation Ethernet Controller XXV710 for 25GbE SFP28</Pcie_Device_Name>
                    <pcie_device_speed_in_gt_sec>8</pcie_device_speed_in_gt_sec>
                    <pcie_device_width>x1</pcie_device_width>
                    <bus>04</bus>
                </slot_c>
</pcie_device_population>
        
Now Run the TC.



