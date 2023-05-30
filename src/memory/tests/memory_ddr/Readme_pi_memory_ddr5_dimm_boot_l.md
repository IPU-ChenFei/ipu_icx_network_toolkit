For test case H102744 - PI_Memory_DDR5_DIMM_BOOT_L, 
We need to use 2 DPC memory configuration as per the test case steps.
Operating system : Linux

In content_configuration.xml, we need to update
1) supported_highest_capacity_dimms, under SPR(according to family) tag, capacity tag with the maximum Size
 supported by the platform.
2) bios_post_memory_capacity tag, with the total memory connected in the SUT in GB to verify the memory 
in Bios and OS.
example :  <bios_post_memory_capacity>512</bios_post_memory_capacity>

3) ITP should be connected.
4) Serial cable should be connected.
