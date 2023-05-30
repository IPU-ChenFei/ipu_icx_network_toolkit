For test case H80034 - PI_Memory_DDR5_DIMMMinimumMemory_L, 
We need to use 1 DPC configuration as per the test case steps.
In content_configuration.xml, we need to update 
1) bios_post_memory_capacity tag, with the total memory connected in the SUT in GB to verify the memory 
in Bios and OS.
example :  <bios_post_memory_capacity>512</bios_post_memory_capacity>
2) stress_test_execute_time tag, The time which needs to run the stressapptest in seconds.
3) ITP should be connected.
4) serial cable should be connected.

