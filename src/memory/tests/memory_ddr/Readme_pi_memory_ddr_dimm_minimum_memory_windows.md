For test case H102739 - PI_Memory_DDR5_DIMMMinimumMemory_W, 
We need to use 1 DPC configuration as per the test case steps.
Operating system : Windows

In content_configuration.xml, we need to update
1) bios_post_memory_capacity tag, with the total memory connected in the SUT in GB to verify the memory 
in Bios and OS.
example :  <bios_post_memory_capacity>512</bios_post_memory_capacity>
2) ddr_frquency, under dpmo tag, with the DDR5 memory speed connected in the SUT.
   example : if the connected DDR5 speed is 4800 MT/s then tag will be <ddr_frquency>4800</ddr_frquency>
3) ITP should be connected.
4) serial cable should be connected.
