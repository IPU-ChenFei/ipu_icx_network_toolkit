FOR TC ID - H80019 - PI_Manageability_SPS_Tools_SPSManuf_O
----------------------------------------------------
Please add below mentioned configuration details in content_configuration.xml 
and run this TC on windows and Linux machine.

1) Place the sps tool in C:\Automation\BKC\Tools\ in the host and update the <path> tag
2) cd into c:\DPG_Automation\miv-mivsoftware\montana\nativemodules and run getdeviceid.py 
   the output should look something like below, update the <version></version> tag 
   with the Firmware Version Data:
   
+---------------------------+------------------------------------------+
| Field                     | Data                                     |
+---------------------------+------------------------------------------+
| Device ID                 | Intel(R) Management Engine (Intel(R) ME) |
| Region Name               | NM Operational Mode [image1]             |
| Firmware Version          | Unknown (0x06): 06.00.01.021.0           |
| Device Revision           | NM SKU                                   |
| IPMI Version              | 2.0                                      |
| Additional Device Support | 0x21                                     |
| Platform                  | Unknown                                  |
+---------------------------+------------------------------------------+

For Example :
<sps>
    <path>C:\Automation\BKC\Tools\SPS_Tools_4.2.97.398.zip</path>
    <version>6.0.1.21</version>
</sps>
