For test case H102740 - PI_Memory_DDR5_DIMMMaximumMemory_W, 
We need to use 2 DPC memory configuration as per the test case steps.
Operating system : Windows

In content_configuration.xml, we need to update
1) supported_highest_capacity_dimms, under SPR(according to family) tag, capacity tag with the maximum Size
 supported by the platform.
2) bios_post_memory_capacity tag, with the total memory connected in the SUT in GB to verify the memory 
in Bios and OS.
example :  <bios_post_memory_capacity>512</bios_post_memory_capacity>
3) ddr_frquency, under dpmo tag, with the DDR5 memory speed connected in the SUT.
   example : if the connected DDR5 speed is 4800 MT/s also tag will be <ddr_frquency>4400</ddr_frquency>.
   For 2DPC DDR frequency supports upto 4400 MT/s

4) ITP should be connected.
5) Serial cable should be connected.
