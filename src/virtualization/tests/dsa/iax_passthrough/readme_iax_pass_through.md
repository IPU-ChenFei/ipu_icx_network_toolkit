===========================================================================================
This TC requires below settings to be enabled on the SUT
===========================================================================================
Current TC Status: Not working as Manually it is not passing, to be updated once Steps are provided.

1.Verify the following BIOS settings. 

EDKII Menu > Socket Configuration > IIO configuration > PCIe ENQCMD > ENQCMDS = enabled 
EDKII Menu > Socket Configuraiton > IIO Configuration >IOAT configuration >socket <n> IOAT configure > DSA = enabled 
EDKII Menu > Socket Configuraiton > IIO Configuration > VT-d = enabled 
EDKII Menu > Socket Configuration > Processor Configuration > VMX = enabled

2.Download latest centos installer from BKC:
  ex:https://emb-pub.ostc.intel.com/overlay/centos/8/202109221317/images/centos-8.4.2105-embargo-installer-202109221317.iso

3.Copy above downloaded file to location "C:\Automation\BKC\VM_DETAILS\IMAGE"
4. updtate the content configuration file tag "os_iso_location_on_host"
virtualization>
        
        <linux>
            <!-- Put the free MAC id which is registered in IT portal
            example: <mac_address>52:54:00:83:CE:82,52:54:00:BA:84:11</mac_address>-->
            <mac_address11>52:54:00:49:f2:f9,52:54:00:9a:1e:e2,52:54:00:96:70:dd,52:54:00:15:da:b3,52:54:00:04:87:94,52:54:00:9a:1e:e2,52:54:00:96:70:dd,52:54:00:15:da:b3,52:54:00:04:87:94,52:54:00:96:70:dd</mac_address11>
            <mac_address>00:15:5D:58:37:60,00:15:5D:58:37:61,00:15:5D:58:37:62,00:15:5D:58:37:63,00:15:5D:58:37:50,00:15:5D:58:37:51,00:15:5D:58:37:52,00:15:5D:58:37:53,00:15:5D:58:37:54,00:15:5D:58:37:55,00:15:5D:58:37:56,00:15:5D:58:37:57,00:15:5D:58:37:58,00:15:5D:58:37:59,00:15:5D:58:37:5A,00:15:5D:58:37:5B,00:15:5D:58:37:5C,00:15:5D:58:37:5D,00:15:5D:58:37:5E,00:15:5D:58:37:5F</mac_address>
            
            <CENTOS>
                <ISO>
					<memory_size>4098</memory_size>
					<num_of_cpus>2</num_of_cpus>
					<disk_space_in_gb>20</disk_space_in_gb>
					<os_variant>8</os_variant>
					<kernel_version>4.18</kernel_version>
					<os_iso_location_on_host>C:\Automation\BKC\VM_DETAILS\IMAGE\centos-8.4.2105-embargo-installer-202109221317.iso</os_iso_location_on_host>
					<yum_repos_location_on_host>C:\Automation\BKC\Tools\RHEL_REPOS.zip</yum_repos_location_on_host>
                    <!-- Put the free MAC id which is registered in IT portal
                    -->

                </ISO>
            </CENTOS>

      </linux>
  </virtualization>
5.Run the TC now

