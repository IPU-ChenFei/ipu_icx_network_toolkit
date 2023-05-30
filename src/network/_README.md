#### Networking Validation Setup Guide

###### 0. Test Environment Setup
![](../../../_imgsrc/network/nic_conn_demo.png)
```text
1. In above topology, shows 2 "Testing Set", each contains "HOST <-> SUT" pair
2. Left "Testing Set" works as "Testing Server/Target", right one works as "Testing Client"
3. Right "Testing Set" must be "power on to OS" before running scripts (Act as a test client)
4. Each nic config is built on <network connection>, it's representation of "network packet flow"
5. All networking scripts use the "Pre-Defined" connections in "config.nic_config() in steps_lib/domains/network/config.py"
```

```text
Execution Preparation
1. Executors check and modify nic connection based on below table
2. Preparing network env for two SUT
    a. Connecting two SUT to IT Network
    b. Running src/sample_content/_utils/platform_domain_valtools.py --platform=bhs/egs --domain=network --cred=username:password
    c. For Windows OS, when it show you the GUI windows for tool install, please manual install the tool.
3. Running scripts ...
```

###### 1. Test NIC Configuration
![](../../../_imgsrc/network/nic_cfg.png)

###### 2. Test Case Requirement
<details>
<summary>Windows List</summary>

| **Test Case** | **NIC Connection Requirement** | **Tool Requirement on SUT** | **Tool Link Reference** |
| --- | --- | --- | --- |
| PI_Networking_Springville_TCPStress_W | spr_conn_v4 | ||
| PI_Networking_Columbiaville_InternetProtocolv6_W & PI_Networking_Columbiaville_PCIe_InternetProtocolv6_W | col_conn_v6 |||
| PI_Networking_Columbiaville_VMDQ_W & PI_Networking_Columbiaville_PCIe_VMDQ_W | col_conn_v4 |||
| PI_Networking_Columbiaville_SRIOV_W & PI_Networking_Columbiaville_PCIe_SRIOV_W | col_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/windows/WIN.vhdx |
| PI_Networking_Columbiaville_TCPStress_W & PI_Networking_Columbiaville_PCIe_TCPStress_W & PI_Networking_Columbiaville_OCP_TCPStress_W | col_conn_v4 | ||
| PI_Networking_Columbiaville_PCIe_NVMUpgrade_W & PI_Networking_Columbiaville_OCP_NVMUpgrade_W | col_conn_v4 | ||
| PI_Networking_Columbiaville_PCIe_IPv4_W | col_conn_v4 | ||
| PI_Networking_Columbiaville_PCIe_ConnectivityReboot_W | col_conn_v4 | ||
| PI_Networking_Columbiaville_PCIe_ConnectivityShutdown_W | col_conn_v4 | ||
| PI_Networking_Carlsville_IPv4_W | car_conn_v4 ||
| PI_Networking_Carlsville_NVMUpgrade_W | car_conn_v4 ||10.239.115.67: /localdisk/test_tools/network/windows/700Series_NVMUpdatePackage_v8_30_Windows.zip or https://www.intel.com/content/www/us/en/support/detect.html |
| PI_Networking_Carlsville_SRIOV_W | car_conn_v4 ||10.239.115.67: /localdisk/test_tools/network/windows/WIN.vhdx |
| PI_Networking_Carlsville_TCPStress_W | car_conn_v4 | ||
| PI_Networking_Fortville_IPv4_W | for_conn_v4 |||
| PI_Networking_Fortville_InternetProtocolv6_W | for_conn_v6 |||
| PI_Networking_Fortville_ConnectivityReboot_W | for_conn_v4 |||
| PI_Networking_Fortville_ConnectivityShutdown_W | for_conn_v4 |||
| PI_Networking_Fortville_NVMUpgrade_W | for_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/windows/700Series_NVMUpdatePackage_v8_30_Windows.zip or https://www.intel.com/content/www/us/en/support/detect.html |
| PI_Networking_Fortville_SRIOV_W | for_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/windows/WIN.vhdx |
| PI_Networking_Fortville_TCPStress_W | for_conn_v4 | ||
| PI_Networking_Jacksonville_WakeMagicPacket_W | jac_conn_v4 |||
| PI_Networking_Jacksonville_TCPStress_W | jac_conn_v4 | ||
| PI_Networking_Foxville_WakeMagicPacket_W | fox_conn_v4 |||
| PI_Networking_Foxville_TCPStress_W | fox_conn_v4 | ||
| DV_Infiniband_FirmwareUpdate_W | mel_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/linux/fw-ConnectX5-rel-16_31_1014-MCX516A-BDA_Ax_Bx-UEFI-14.24.13-FlexBoot-3.6.403.zip  |
| DV_Infiniband_ConnectionSpeed_W | mel_conn_v4 | mannual install MLNX_WinOF2-2_70_51000_All_x64.exe | 10.239.115.67: /localdisk/test_tools/network/windows/MLNX_WinOF2-2_70_51000_All_x64.exe |
| DV_Infiniband_IOStress_W | mel_conn_v4 | C:\\iwVSS\\Whitley\\Whitley_NoBMC.pkx | 10.239.115.67: /localdisk/test_tools/network/windows/iwvss |
| DV_Infiniband_RDMAPerformance_W | mel_conn_v4 |||
| DV_Infiniband_RoCEEthernetPerformance_W | mel_conn_v4 |||
| DV_Infiniband_Ethernet_Mode_W | mel_conn_v4 | C:\\WinMFT | 10.239.115.67: /localdisk/test_tools/network/windows/MLNX_WinOF2-2_70_51000_All_x64.exe |
| DV_Infiniband_LOM_IOBWChecks_W | spr_conn_v4 | C:\\iwVSS\\Whitley\\Whitley_NoBMC.pkx | 10.239.115.67: /localdisk/test_tools/network/windows/iwvss |
| DV_LOM_DataIntegrityJumboFrame_W | spr_conn_v4 | C:\\iwVSS\\Whitley\\Whitley_NoBMC.pkx | 10.239.115.67: /localdisk/test_tools/network/windows/iwvss |
| DV_LOM_Diagnostic_W.py | spr_conn_v4 |||
| DV_LOM_Internet_Protocol_W.py | spr_conn_v4 |||
| DV_LOM_InternetProtocolv6_W.py | spr_conn_v4 |||
| DV_LOM_WakeMagicPacket_W.py | spr_conn_v4 |||
</details>

<details>
<summary>Redhat List</summary>

| **Test Case** | **NIC Connection Requirement** | **Tool Requirement on SUT** | **Tool Link Reference** |
| --- | --- | --- | --- |
| PI_Networking_Springville_TCPStress_L | spr_conn_v4 |||
| PI_Networking_Springville_PXE_L | spr_conn_v4 |||
| PI_Networking_Columbiaville_IPv4_L & PI_Networking_Columbiaville_PCIe_IPv4_L |col_conn_v4 |||
| PI_Networking_Columbiaville_ConnectivityReboot_L & PI_Networking_Columbiaville_PCIe_ConnectivityReboot_L | col_conn_v4 ||||
| PI_Networking_Columbiaville_ConnectivityShutdown_L & PI_Networking_Columbiaville_PCIe_ConnectivityShutdown_L | col_conn_v4 ||||
| PI_Networking_Columbiaville_PXE_L & PI_Networking_Columbiaville_PCIe_PXE_L | col_conn_v4 |||
| PI_Networking_Columbiaville_TCPStress_L & PI_Networking_Columbiaville_PCIe_TCPStress_L & PI_Networking_Columbiaville_OCP_TCPStress_L | col_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/linux/iperf3-3.1.3-1.fc24.x86_64.rpm or https://iperf.fr/iperf-download.php|
| PI_Networking_Columbiaville_BondingFaultTolerance_L & PI_Networking_Columbiaville_PCIe_BondingFaultTolerance_L | col_conn_v4 |||
| PI_Networking_Columbiaville_PCIe_NVMUpgrade_L | col_conn_v4 |||
| PI_Networking_Columbiaville_PCIe_SRIOVCheckDevice_L | col_conn_v4 |||
| PI_Networking_Carlsville_IPv4_L | car_conn_v4 |||
| PI_Networking_Carlsville_TCPStress_L | car_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/linux/iperf3-3.1.3-1.fc24.x86_64.rpm or https://iperf.fr/iperf-download.php|
| PI_Networking_Carlsville_BondingFaultTolerance_L | car_conn_v4 |||
| PI_Networking_Carlsville_PXE_L | car_conn_v4 |||
| PI_Networking_Fortville_IPv4_L | for_conn_v4 |||
| PI_Networking_Fortville_ConnectivityReboot_L | for_conn_v4 |||
| PI_Networking_Fortville_ConnectivityShutdown_L | for_conn_v4 |||
| PI_Networking_Fortville_PXE_L | for_conn_v4 |||
| PI_Networking_Fortville_TCPStress_L | for_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/linux/iperf3-3.1.3-1.fc24.x86_64.rpm or https://iperf.fr/iperf-download.php |
| PI_Networking_Fortville_NVMUpgrade_L | for_conn_v4 ||10.239.115.67: /localdisk/test_tools/network/windows/700Series_NVMUpdatePackage_v8_30_Windows.zip or https://www.intel.com/content/www/us/en/support/detect.html |
| PI_Networking_Fortville_SRIOVCheckDevice_L | for_conn_v4 |||
| PI_Networking_Jacksonville_WakeMagicPacket_L | jac_conn_v4 |||
| PI_Networking_Jacksonville_PXE_L | jac_conn_v4 | |||
| PI_Networking_Foxville_WakeMagicPacket_L | fox_conn_v4 |||
| PI_Networking_Foxville_PXE_L | fox_conn_v4 |||
| DV_Infiniband_FirmwareUpdate_L | mel_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/linux/fw-ConnectX5-rel-16_31_1014-MCX516A-BDA_Ax_Bx-UEFI-14.24.13-FlexBoot-3.6.403.zip |
| DV_Infiniband_ConnectionSpeed_L | mel_conn_v4 |||
| DV_Infiniband_PCIeLinkSpeedWidth_L | mel_conn_v4 |||
| DV_Infiniband_Ethernet_Mode_L | mel_conn_v4 |||
| DV_Infiniband_IOStress_L | mel_conn_v4 | RHEL(SUT1)+WINDOWS(SUT2) | 10.239.115.67: /localdisk/test_tools/network/linux/ilvss-3.6.23.tar.gz |
| DV_LOM_DataIntegrityJumboFrame_L | mel_conn_v4 | RHEL(SUT1)+WINDOWS(SUT2) | 10.239.115.67: /localdisk/test_tools/network/linux/ilvss-3.6.23.tar.gz |
| DV_Infiniband_Bit_Error_Rate_L | mel_conn_v4 |||
| DV_Infiniband_Basic_Function_Check_L | mel_conn_v4 ||| 
| DV_Infiniband_RDMA_Performance_L | mel_conn_v4 ||| 
| DV_Infiniband_RoCE_Ethernet_Performance_L.py | mel_conn_v4 |||
| DV_Infiniband_SRIOV_L.py | mel_conn_v4 |||
| DV_Infiniband_SRIOV_Stress_ilVSS_L.py | mel_conn_v4 |||
</details>

<details>
<summary>CentOS List</summary>

| **Test Case** | **NIC Connection Requirement** | **Tool Requirement on SUT** | **Tool Link Reference** |
| --- | --- | --- | --- |
| PI_Networking_Columbiaville_NVMUpgrade_L |col_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/linux/E810_NVMUpdatePackage_v3_00_Linux.tar.gz or https://www.intel.com/content/www/us/en/support/detect.html |
| PI_Networking_Columbiaville_IPv4_L |col_conn_v4 |||
| PI_Networking_Columbiaville_ConnectivityReboot_L | col_conn_v4 ||||
| PI_Networking_Columbiaville_ConnectivityShutdown_L | col_conn_v4 ||||
| PI_Networking_Columbiaville_PXE_L | col_conn_v4 |||
| PI_Networking_Columbiaville_TCPStress_L | col_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/linux/iperf3-3.1.3-1.fc24.x86_64.rpm or https://iperf.fr/iperf-download.php |
| PI_Networking_Columbiaville_BondingFaultTolerance_L | col_conn_v4 & col_conn_v4_02 |||
| PI_Networking_Carlsville_IPv4_L | car_conn_v4 |||
| PI_Networking_Carlsville_TCPStress_L | car_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/linux/iperf3-3.1.3-1.fc24.x86_64.rpm or https://iperf.fr/iperf-download.php |
| PI_Networking_Carlsville_BondingFaultTolerance_L | car_conn_v4 & car_conn_v4_02 |||
| PI_Networking_Fortville_IPv4_L | for_conn_v4 |||
| PI_Networking_Fortville_ConnectivityReboot_L | for_conn_v4 |||
| PI_Networking_Fortville_ConnectivityShutdown_L | for_conn_v4 |||
| PI_Networking_Fortville_PXE_L | for_conn_v4 |||
| PI_Networking_Fortville_TCPStress_L | for_conn_v4 || 10.239.115.67: /localdisk/test_tools/network/linux/iperf3-3.1.3-1.fc24.x86_64.rpm or https://iperf.fr/iperf-download.php |
| PI_Networking_Fortville_NVMUpgrade_L | for_conn_v4 | 700Series_NVMUpdatePackage_v8_30_Linux.tar.gz |  or https://www.intel.com/content/www/us/en/support/detect.html |
| PI_Networking_Foxville_PXE_L | fox_conn_v4 |||
</details>
