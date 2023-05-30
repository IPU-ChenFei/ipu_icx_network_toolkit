Need to create 8 VMs and each VM will have max 16VFs allocated from different PFs (each of the 8 PFs will give 2 VF to each VM)

This test case is similar to 
https://hsdes.intel.com/appstore/article/#/16013374004
Virtualization - Vmware Esxi - QAT_SRIOV_Single_VM_Multi_PF_Data_Movement_L

=============================================================================================================================
1. Prerequisites  for VMware QAT driver tests

ESXi host should have enabled SSH. WebUI should be accessible.

For all PI_SPR_ESXi_QAT_SRIOV_* tests SR-IOV should been enabled for all 4 QAT endpoints per socket with at least 6 VFs per PF
Create/Clone 2 VMs per socket. VMs should have BKC OS (RHEL or ClearLinux) installed, same as the one used by Linux QAT BKC validation team.
BKC version of Linux VF driver should be used inside VMs.
1.1 Pass-through the VF PCI Device to VM

Follow this instruction to passthru VF to VM:

Connect to the target ESXi host via Web User Interface (UI).
In the left pane, click on VMs.
In the center pane, click on the desired Virtual Machine. Ensure that the VM is powered off.
Click on the "Edit" button to edit the virtual machines settings. A pop-up window with the VM settings will appear.
Click on "Add other Device" and select "PCI device". The new PCI device will be added. By default it selects the first VF in the system, but it may not be a QAT VF since there could be other PCI devices present in the system. To select QAT VF, click the drop-down list and choose desired PCI device with "QAT VF" in name. The BDFs listed here will match with the output of the "lspci -vn | grep 4941" command. Additional VFs can be added by repeating this step.
Click "Save".
Also, ESXi require to pin all memory for VM with passthru device(s), to do that follow next steps:

Click on the "Edit" button to edit the virtual machines settings. A pop-up window with the VM settings will appear.
Expand “Memory” setting.
Click on “Reserve all guest memory (All locked)” checkbox to make it enabled.
Click “Save”.
1.2 Prerequisites for test execution inside VM

1.2.1 VF driver installation

1.2.1.1 RHEL

The following packages must be installed prior to QAT driver build:

yum install -y gcc-toolset-9  zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel xxhash-devel elfutils-libelf-devel zlib-devel libnl3-devel boost-devel systemd-devel yasm openssl-devel

The following may be required prior to build if system is not configured to use gcc-9 by default

scl enable gcc-toolset-9 bash 

The driver can then be installed via:

tar -xvf ./<QAT_package.tar.gz>

./configure –enable-icp-sriov=guest && make uninstall

 make -s -j install  or make install



1.2.1.2 ClearLinux

The following packages must be installed prior to QAT driver build:

swupd bundle-add wget

swupd bundle-add  dev-utils-dev

swupd bundle-add devpkg-libnl

swupd bundle-add devpkg-openssl

swupd bundle-add devpkg-lz4

swupd bundle-add  dev-utils

swupd bundle-add  devpkg-boost

swupd bundle-add devpkg-libgudev

swupd bundle-add devpkg-systemd

The driver can then be installed via:

export EXTRA_CXXFLAGS=-Wno-stringop-truncation 

echo "/usr/local/lib" | sudo tee -a /etc/ld.so.conf

mkdir -p /etc/default

mkdir -p /etc/udev/rules.d/

mkdir -p /etc/ld.so.conf.d/

tar -xvf ./<QAT_package.tar.gz>

./configure –enable-icp-sriov=guest && make uninstall

make -s -j install or make install

1.2.2 Sample code compilation

After driver installation cpa_sample_code application should be built and installed:

make -s -j samples

2. Tests

2.1 Device_enumeration

Search PCI system for CPM2.0 devices, expectation is the there should be 4 devices returned for each socket in system:

lspci -p | grep 8086:4940

Example output - format only as Segment:Bus:Device.Function, actual SBDF could be different from system to system:

> lspci -p | grep 8086:4940

0000:e9:00.0 8086:4940 8086:0000                V

0000:ee:00.0 8086:4940 8086:0000                V

0000:f3:00.0 8086:4940 8086:0000                V

0000:f8:00.0 8086:4940 8086:0000                V

0001:e9:00.0 8086:4940 8086:0000                V

0001:ee:00.0 8086:4940 8086:0000                V

0001:f3:00.0 8086:4940 8086:0000                V

0001:f8:00.0 8086:4940 8086:0000                V

2.2 ESXi_QAT_Driver_Installation_L

By default driver will be loaded with default service configuration - “sym;dc”.

Copy the component bundle to the ESXi server.    Technically, you can place the file anywhere that is accessible to the ESXi console shell, but for these instructions, we'll assume the location is in '/tmp' folder.

Extract the package, set required acceptance level and install the component bundle:

tar -xzf QAT20_SRIOV.VMW*.tar.gz

tar -xzf QAT20_SRIOV.VMW*.tar.gz

 

esxcli software component apply --no-sig-check -d /tmp/VMW-esx-7.0.0-Intel-qat-2.*.zip

System should indicate successful installation, for example:

> esxcli software component remove -n Intel_qat

Installation Result

   Components Installed: Intel-qat_2.0.0-44832007

   Components Removed:

   Components Skipped:

   Message: Operation finished successfully.

   Reboot Required: false

Reboot host to complete installation

 

2.3 ESXi_QAT_Driver_Presence_L

This test is targeted to make sure that QAT driver was properly installed and attached to HW correctly.

QAT driver should be loaded:

vmkload_mod --list | grep qat

Example output:

> vmkload_mod --list | grep qat

qat_dvx                    9     4024

And attached to corresponding devices that could be checked by lspci:

lspci -p | grep 8086:4940

Example output:

> lspci -p | grep 8086:4940

0000:e9:00.0 8086:4940 8086:0000                V qat

0000:ee:00.0 8086:4940 8086:0000                V qat

0000:f3:00.0 8086:4940 8086:0000                V qat

0000:f8:00.0 8086:4940 8086:0000                V qat

0001:e9:00.0 8086:4940 8086:0000                V qat

0001:ee:00.0 8086:4940 8086:0000                V qat

0001:f3:00.0 8086:4940 8086:0000                V qat

0001:f8:00.0 8086:4940 8086:0000                V qat

2.4 ESXi_QAT_SRIOV_Enabling_L

Configure SR-IOV on the ESXi host via Web UI by following next steps:

Login to the target ESXi host Web User Interface (UI).
In the left pane, expand Host and click on "Manage" section.
In the center pane, choose "Hardware" tab and "PCI Devices" sub-tab.
Find devices with "Intel Corporation QAT" text in "Description" and click on "Configure SR-IOV" button.
In dialog window change "Enabled" param to "Yes" and enter the desired number of VF in the range between 1 and maximum indicated in window. Test recommendation to try next number of VFs: 1,16,8,9
Click "Save" and ESXi will reconfigure device with requested number of VFs.
Now the Intel® QAT VFs are enabled in the system. You can verify this by running the 'lspci' command in ESXi shell. Example output:
    > lspci -vn | grep 4941

    0000:e9:00.1 Class 0b40: 8086:4941 [PF_0.233.0_VF_0]

    0000:e9:00.2 Class 0b40: 8086:4941 [PF_0.233.0_VF_1]

    0000:e9:00.3 Class 0b40: 8086:4941 [PF_0.233.0_VF_2]

    0000:e9:00.4 Class 0b40: 8086:4941 [PF_0.233.0_VF_3]

    0000:e9:00.5 Class 0b40: 8086:4941 [PF_0.233.0_VF_4]

    0000:e9:00.6 Class 0b40: 8086:4941 [PF_0.233.0_VF_5]

    0000:e9:00.7 Class 0b40: 8086:4941 [PF_0.233.0_VF_6]

    0000:e9:01.0 Class 0b40: 8086:4941 [PF_0.233.0_VF_7]

    0000:e9:01.1 Class 0b40: 8086:4941 [PF_0.233.0_VF_8]

    0000:e9:01.2 Class 0b40: 8086:4941 [PF_0.233.0_VF_9]

    0000:e9:01.3 Class 0b40: 8086:4941 [PF_0.233.0_VF_10]

    0000:e9:01.4 Class 0b40: 8086:4941 [PF_0.233.0_VF_11]

    0000:e9:01.5 Class 0b40: 8086:4941 [PF_0.233.0_VF_12]

    0000:e9:01.6 Class 0b40: 8086:4941 [PF_0.233.0_VF_13]

    0000:e9:01.7 Class 0b40: 8086:4941 [PF_0.233.0_VF_14]

    0000:e9:02.0 Class 0b40: 8086:4941 [PF_0.233.0_VF_15]

2.5 ESXi_QAT_SRIOV_Single_VM_signOfLifeTests_UserSpace_L

One VF should be attached to VM. This test will allow to check QAT functionality with minimum traffic (should be executed from folder with VF driver sources and build folder):

Yum command from top:

 

yum install -y gcc-toolset-9  zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel zlib-devel libnl3-devel boost-devel systemd-devel yasm openssl-devel

 

 

export EXTRA_CXXFLAGS=-Wno-stringop-truncation 

echo "/usr/local/lib" | sudo tee -a /etc/ld.so.conf

mkdir -p /etc/default

mkdir -p /etc/udev/rules.d/

mkdir -p /etc/ld.so.conf.d/

 

./configure --enable-icp-sriov=guest && make uninstall

make -s -j install 

make -s -j samples-install

 

Cd build 

./build/cpa_sample_code signOfLife=1

Example output:

> ./build/cpa_sample_code signOfLife=1

qaeMemInit started

icp_sal_userStartMultiProcess("SSL") started

*** QA version information ***

device ID               = 0

software                = 0.5.3

*** END QA version information ***

Warning! Skipping RSA tests as they are not supported on Instance

runTests=125                                                  

Warning! Skipping DSA tests as they are not supported on Instance

runTests=121

Warning! Skipping ECDSA tests as they are not supported on Instance

runTests=113

Warning! Skipping DH tests as they are not supported on Instance

runTests=97

Warning! Skipping Kasumi wireless algorithm tests as they are not supported on Instance

includeWirelessAlgs = 0

Inst 0, Affin: 1, Dev: 0, Accel 0, EE 0, BDF 13:00:00

Inst 1, Affin: 2, Dev: 0, Accel 0, EE 0, BDF 13:00:00

Warning we have reached core limit resetting core to 0

---------------------------------------

Cipher AES128-CBC

Direction             Encrypt

API                   Traditional

Packet Size           64

Number of Threads     2

Total Submissions     40

Total Responses       40

Total Retries         0

---------------------------------------

 

Inst 0, Affin: 1, Dev: 0, Accel 0, EE 0, BDF 13:00:00

Inst 1, Affin: 2, Dev: 0, Accel 0, EE 0, BDF 13:00:00

Warning we have reached core limit resetting core to 0

---------------------------------------

Cipher AES128-CBC

Direction             Encrypt

API                   Traditional

Packet Size           128

Number of Threads     2

Total Submissions     40

Total Responses       40

Total Retries         0

---------------------------------------

2.6 ESXi_QAT_SRIOV_Single_VM_Data_Movement_L

One VF should be attached to VM. This is higher throughput version of PI_SPR_ESXi_QAT_SRIOV_Single_VM_signOfLifeTests_UserSpace_L test, it also prints performance metrics for every algorithm executed (should be executed from folder with VF driver sources and build folder):

./build/cpa_sample_code

Example output:

> ./build/cpa_sample_code

qaeMemInit started

icp_sal_userStartMultiProcess("SSL") started

*** QA version information ***

device ID               = 0

software                = 0.5.3

*** END QA version information ***

Warning! Skipping RSA tests as they are not supported on Instance

runTests=125

Warning! Skipping DSA tests as they are not supported on Instance

runTests=121

Warning! Skipping ECDSA tests as they are not supported on Instance

runTests=113

Warning! Skipping DH tests as they are not supported on Instance

runTests=97

Warning! Skipping Kasumi wireless algorithm tests as they are not supported on Instance

includeWirelessAlgs = 0

Inst 0, Affin: 1, Dev: 0, Accel 0, EE 0, BDF 13:00:00

Inst 1, Affin: 2, Dev: 0, Accel 0, EE 0, BDF 13:00:00

Warning we have reached core limit resetting core to 0

---------------------------------------

Cipher AES128-CBC

Direction             Encrypt

API                   Traditional

Packet Size           64

Number of Threads     2

Total Submissions     200000

Total Responses       200000

Total Retries         391

CPU Frequency(kHz)    2200126

Throughput(Mbps)      1163

---------------------------------------

 

 

 