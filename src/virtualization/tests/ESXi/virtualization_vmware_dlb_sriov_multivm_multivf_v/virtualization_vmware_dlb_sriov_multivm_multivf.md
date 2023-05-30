virtualization_vmware_dlb_sriov_multivm_multivf_v
The purpose of this test case is to create multiple VMs and assign multiple VFs from different PFs. Then run the dlb test.
eg : create 8 VMs and assign 2VFs from each PF to each VM.  

Note: TC is not doable  with the scenario-"create 8 VMs and assign 2VFs from each PF to each VM", as the workload runs in only 1 VM and fails in rest all VMs.
Scenario : "2vfs(vf1,vf2) from dlb0,dlb1,dlb2--dlb7 to VM1,
            2vfs(vf3,vf4) from dlb0,dlb1--dlb7 to VM2,
            2vfs(vf5,vf6) from dlb0,dlb1--dlb7 to VM3"
HSDES: https://hsdes.intel.com/appstore/article/#/16014302844

========================================================================================================================
Prerequisites 
1.       ESXi host should have SSH enabled. vSphere Web Client should be accessible.
2.       Enable 5 DLB VFs per each PF. Assign every 5 DLB VFs group per created/cloned VM.
3.       VMs should use BKC OSes (RHEL or CentOS) supported by BKC Linux DLB driver installed.
4.       BKC version of DLB Linux Driver (with VF support) should be used inside VMs.
5.       Same tests as provided by BKC version of DLB Linux Driver needs to be run inside VMs.

Pass-through the VF PCI Device to VM
1.       Login to the vSphere Web Client on the target ESXi host.
2.       In the left pane, expand "Virtual Machines" and select desired VM. Ensure that the VM is powered off.
3.       Click on the "Edit" button to edit VM settings. A pop-up window will appear.
4.       Click on "Add other device" and select "PCI device". The new PCI device will be added. The first VF in the system is selected by default but it could be not a DLB one. To select DLB VF, click the drop-down list and choose desired PCI device with "INTEL DLB VF" in name (appear after reboot only) or by BDFs. The listed BDFs need to match with the output of the "lspci -vn | grep 2711". See example above. Additional VFs can be added by repeating this step.
5.       Click "Save".

Also, ESXi require to pin all memory for VM with pass-through device(s), to do that follow next steps:
1.       Click on the "Edit" button to edit the virtual machines settings. A pop-up window with the VM settings will appear.
2.       Expand “Memory” setting.
3.       Click on “Reserve all guest memory (All locked)” checkbox to make it enabled.
4.       Click “Save”.

Prerequisites for test execution inside VM
Follow instructions provided by BKC Linux DLB driver.

Linux OSes installation
Install Linux OSes (RHEL and CentOS) supported by BKC Linux DLB driver with all required packages.

VF driver compilation
MDEV support needs to be disabled to build VF Linux driver instead of SIOV one

> cd $TOP/driver/dlb2
> make CONFIG_VFIO_MDEV=n

DLB Library compilation
> cd $TOP/user/libdlb
> make

DLB Library test
> insmod $TOP/driver/dlb2/dlb2.ko
> export LD_LIBRARY_PATH=$TOP/user/libdlb/
> $TOP/user/libdlb/examples/ldb_traffic -n 1024 -w poll
> rmmod dlb2

DLB's available resources:
Domains: 32
LDB queues: 32
LDB ports: 64
DIR ports: 64
ES entries: 2048
Contig ES entries: 2048
LDB credits: 8192
Contig LDB cred: 8192
DIR credits: 2048
Contig DIR cred: 2048
LDB credit pls: 64
DIR credit pls: 64
[tx_traffic()] Sent 1024 events
[rx_traffic()] Received 1024 events

SPR_ESXi_DLB_PCIe_Device_Enumeration
Search PCI system for DLB 2.0 devices, expectation is the there should be 4 devices returned for each socket in system (actual SBDF in the output could be different from system to system)

> lspci -p | grep 8086:2710
0000:6d:00.0 8086:2710 8086:0000                V
0000:72:00.0 8086:2710 8086:0000                V
0000:77:00.0 8086:2710 8086:0000                V
0000:7c:00.0 8086:2710 8086:0000                V


SPR_ ESXi_DLB_Driver_Installation
1.       Open a SSH connection to the target ESXi host (SSH needs to be enabled).
2.       Copy the driver package to the ESXi (assume here and further that the target location is in '/tmp' folder and "scp" utility is used to copy the file to the target ESXi at 10.10.10.10)
> scp dlb_vmw_ext_rel_bin_*.tar.gz root@10.10.10.10:/tmp
3.       Extract the driver package
> cd /tmp
> tar -xzf dlb_vmw_ext_rel_bin_*.tar.gz
4.       Install the driver from the component
> esxcli software component apply --no-sig-check \
  -d /tmp/VMW-esx-7.0.0-Intel-dlb-*.zip
Installation Result
     Components Installed: Intel-dlb_0.5.0.14-15525992
     Components Removed:
     Components Skipped:
     Message: Operation finished successfully.
     Reboot Required: false
1.       Configure module parameters. Out of scope now. Default parameters are used.
2.       Load driver
> kill -HUP $(cat /var/run/vmware/vmkdevmgr.pid)

SPR_ESXi_DLB_Driver_Presence
This test is targeted to make sure that DLB driver was properly installed and attached to HW correctly (actual output could have differences but “dlb” should be presented)

> esxcfg-module -l | grep dlb
  dlb                      8    184
> lspci -p | grep 2710
0000:eb:00.0 8086:2710 8086:0000 V dlb
0000:f0:00.0 8086:2710 8086:0000 V dlb
0000:f5:00.0 8086:2710 8086:0000 V dlb
0000:fa:00.0 8086:2710 8086:0000 V dlb

SPR_ESXi_DLB_SRIOV_Enabling
1.       Login to the vSphere Web Client on the target ESXi host.
2.       In the left pane, expand "Host" and select "Manage".
3.       In the center pane, on the "Hardware" tab, select "PCI devices".
4.       Find devices with "Intel Corporation INTEL DLB PF" text in "Description" and click on "Configure SR-IOV" button.
5.       In dialog window change "Enabled" param to "Yes" and enter the number of VFs in the range between 1 and maximum indicated in the window. Test 1, 16 and 5 VFs for at least one PF from the socket.
6.       Verify DLB VFs have been enabled finding them in "Description" by text "Intel Corporation INTEL DLB VF" (appear after reboot only) or by BDFs. The listed BDFs need to match with the output of the "lspci". Example:

> lspci -vn | grep 2711

0000:6d:00.1 Class 0b40: 8086:2711 [PF_0.109.0_VF_0]
0000:6d:00.2 Class 0b40: 8086:2711 [PF_0.109.0_VF_1]
0000:6d:00.3 Class 0b40: 8086:2711 [PF_0.109.0_VF_2]
0000:6d:00.4 Class 0b40: 8086:2711 [PF_0.109.0_VF_3]
0000:6d:00.5 Class 0b40: 8086:2711 [PF_0.109.0_VF_4]

1.Finally, set 5 VFs for every PF to be used further inside VMs. It is required now to use 5 VFs due to Linux SW limitations. Swap VF1 and VF3 as described on the picture to have zero DLB device ID inside Linux VM (this ID is used by default by Linux tests). Click "Save" to reconfigure DLB PF device with requested number of VFs.
make CONFIG_VFIO_MDEV=n
