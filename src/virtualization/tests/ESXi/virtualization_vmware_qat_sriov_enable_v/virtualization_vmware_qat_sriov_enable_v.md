Prerequisites  for VMware QAT driver tests
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

Sample code compilation
After driver installation cpa_sample_code application should be built and installed:
make -s -j samples