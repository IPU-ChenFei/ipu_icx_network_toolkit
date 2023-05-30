For CPS test cases, 

1) need to update the tag : bios_total_dcpmm_memory_capacity in content_configuration.xml with the amount of CPS
 connected in the SUT. 
   ex : if 1024 GB CPS connected to SUT then <bios_total_dcpmm_memory_capacity>1024</bios_total_dcpmm_memory_capacity> 

2) need to update the tag : bios_post_memory_capacity in content_configuration.xml with the amount of DDR connected in SUT  
   ex: if 512 GB DDR connected to SUT then <bios_post_memory_capacity>512</bios_post_memory_capacity><bios_post_memory_capacity>16</bios_post_memory_capacity>

3) need to update the tag : intel_optane_pmem_mgmt_file_name : with ipmctl tool path in Host. 
ipmctl tool need to download from the BKC mail based on OS. Please rename zip file with underscores ( _ )

After downloading, for SPR : keep the tool under,
if linux : C:\Automation\Tools\SPR\Linux
if windows : C:\Automation\Tools\SPR\Windows
and we need to keep zip file name in tag intel_optane_pmem_mgmt_file_name
ex: <intel_optane_pmem_mgmt_file_name>cr_mgmt_03.00.00.0329_centos_8.2.zip</intel_optane_pmem_mgmt_file_name> 

4) Need to update the tag : cr_ddr_population with population of DDR and CR in the system 
Value can only be one of these -> 8_plus_1/8_plus_4/8_plus_8/4_plus_4

ex : <cr_ddr_population>8_plus_8</cr_ddr_population>
