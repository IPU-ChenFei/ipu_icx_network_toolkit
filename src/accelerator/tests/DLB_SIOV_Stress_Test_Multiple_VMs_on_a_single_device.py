# Tool Version [0.2.11]
CASE_DESC = [
    "it is a python script generated from validation language"
]

from dtaf_core.lib.tklib.basic.testcase import Result
from dtaf_core.lib.tklib.steps_lib.vl.vltcd import *
from dtaf_core.lib.tklib.steps_lib.uefi_scene import UefiShell, BIOS_Menu
from dtaf_core.lib.tklib.steps_lib.os_scene import GenericOS
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from plat_feature_config import *


def test_steps(tcd):
    sut = tcd.sut
    sutos = tcd.sut.sutos
    assert (issubclass(sutos, GenericOS))
    hostos = tcd.hostos
    tools = get_tool(tcd.sut)
    bmc = get_bmc_info()

    if tcd.prepare("boot to OS"):
        boot_to(sut, sut.default_os)


    # Tool Version [0.2.11]
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15011259333
    #TITLE: DLB_SIOV_Stress_Test_Multiple_VMs_on_a_single_device
    #DOMAIN: accelerator
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        
        ### Call TCDB accel.path_import Start
        sutos.execute_cmd(sut, f'rm -rf $HOME/.bashrc')
        sutos.execute_cmd(sut, f'cp /home/acce_tools/.bashrc $HOME/.bashrc')
        sutos.execute_cmd(sut, f'echo export API_SCRIPT={sutos.bkc_root_path}/accelerator_inband >> $HOME/.bashrc  #according to the handover instruction')
        sutos.execute_cmd(sut, f'python3 {sutos.bkc_root_path}/accelerator_inband/constant.py')
        sutos.execute_cmd(sut, f'source $HOME/.bashrc')
        
        #Execute Command: echo export ACCEL_CONFIG_PKG={sutos.bkc_root_path}/domains/acce_tools >> $HOME/.bashrc
        #Execute Command: echo export SUT_TOOLS=/home/acce_tools >> $HOME/.bashrc
        #Execute Command: echo export Accelerator_REMOTE_TOOL_PATH={sutos.bkc_root_path}/domains/acce_tools >> $HOME/.bashrc
        #Execute Command: echo export ACCE_RANDOM_CONFIG_NAME=$SUT_TOOLS/accel-random-config-and-test-main.zip >> $HOME/.bashrc
        #Execute Command: echo export ACCE_RANDOM_CONFIG_PATH_L=$Accelerator_REMOTE_TOOL_PATH/acce_random_config >> $HOME/.bashrc
        #Execute Command: echo export DSA_NAME=$SUT_TOOLS/idxd-config-accel-config*.zip >> $HOME/.bashrc
        #Execute Command: echo export DSA_PATH_L=$Accelerator_REMOTE_TOOL_PATH/DSA >> $HOME/.bashrc
        ### Call TCDB accel.path_import End
        
        
        ## Boot to Linux
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        sutos.execute_cmd(sut, f'unzip -o $DPDK_DRIVER_ZIP_NAME', timeout=10*60)
        # Configuration:
        # https://hsdes.intel.com/appstore/article/#/15010469226
        # 1.Enable SRIOV and VT-D
        # EDKII->Socket Configuration -> IIO Configuration -> Intel  VT For Directed I/O (VT-d) - Intel  VT For Directed I/O Enable
        # EDKII->Platform Configuration -> Miscellaneous Configuration -> SR-IOV Support Enable
        ## Set BIOS knob: VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/yum_install_packages.py', timeout=10*60)
        # 2.Please Download DLB driver from BKC release and copy it to /root/dlb
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH/dlb')
        sutos.execute_cmd(sut, f'\cp $DLB_DRIVER_NAME $Accelerator_REMOTE_TOOL_PATH/dlb')
        # 3.Please Download dpdk package from https://fast.dpdk.org/rel/ and copy it to /root/dlb
        # Note: The version must match the patch in DLB
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH/dlb/dpdk-main')
        sutos.execute_cmd(sut, f'tar xfJ $DPDK_DRIVER_NAME -C $Accelerator_REMOTE_TOOL_PATH/dlb/dpdk-main')
        # 4.Download 5.15 Kernel rpms to /root/ from BKC releaseKERNEL-PACKAGES-SPR-BKC-PC-6.13-0
        # 5.VM test need copy OVMF.fd and img files to system.
        # wget https://ubit-artifactory-or.intel.com/artifactory/linuxmvpstacks-or-local/linux-stack-bkc/2022ww17/internal-images/spr-bkc-pc-centos-stream-8-coreserver-5.12.0.img.xz to /home/
        # OVMF file copy to /home/OVMF.fd
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_img_copy.py -d \'dlb\' -s \'16\' -g \'1\' -p \'1\' -f $CENTOS_IMG_NAME', timeout=60*60)
        sutos.execute_cmd(sut, f'\cp $OVMF_NAME /home/')
        # 6.Download shell scripts : accelerators_interop_multi_vm_scripts-master.zip to /root
        # https://gitlab.devtools.intel.com/ryakkati/accelerators_interop_multi_vm_scripts/
        # Note:System memory must be large enough
        #Execute Command: \cp $ACC_INTEROP_SCRIPT_NAME $Accelerator_REMOTE_TOOL_PATH/dlb
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Insert intel_iommu=on into the grub file"):
        # Insert intel_iommu=on into the grub file
        #grubby --update-kernel=/boot/vmlinuz-'uname-r' --args="intel_iommu=on,sm_on iommu=on"
        #reboot
        # Note:'uname -r' means the kernel which you used now.
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on iommu=on\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on iommu=on\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("check args insert success after reboot.")
        tcd.log("# cat /proc/cmdline")
        tcd.log("BOOT_IMAGE=(hd0,gpt2)/vmlinuz-5.12.0-0507.intel_next.09_15_po.39.x86_64+server root=/dev/mapper/cl-r oot ro crashkernel=auto resume=/dev/mapper/cl-swap rd.lvm.lv=cl/root rd.lvm.lv=cl/swap rhgb quiet co nsole=ttyS0,115200 loglevel=7 console=tty0 intel_iommu=on,sm_on")
        ### Notes ###
        # Note : for RHEL OS
        # cd /etc/default/grub (intel_iommu=on,sm_on iommu=on)
        # GRUB_TIMEOUT=5
        # GRUB_DISTRIBUTOR="$(sed 's, release .*$,,g' /etc/system-release)"
        # GRUB_DEFAULT=saved
        # GRUB_DISABLE_SUBMENU=true
        # GRUB_TERMINAL_OUTPUT="console"
        # GRUB_CMDLINE_LINUX="crashkernel=auto resume=/dev/mapper/cl00-swap rd.lvm.lv=cl00/root rd.lvm.lv=cl00/swap console=ttyS0,115200n8 console=tty0 intel_iommu=on,sm_on iommu=on"
        # GRUB_DISABLE_RECOVERY="true"
        # GRUB_ENABLE_BLSCFG=true
        # Run the command : grub2-mkconfig -o /boot/efi/EFI/centos/grub.cfg
        ##################
        
        
    ## 2
    if tcd.step("Install the DLB driver on Host machine"):
        # Install the DLB driver on Host machine
        #cd /root/dlb
        #unzip release_ver_7.5.2.zip
        #cd /root/dlb/driver/dlb2
        #make
        #insmod ./dlb2.ko
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dlb_install.py -c "False"', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Driver installation is successful.")
        ### Notes ###
        # If you are use intel next kernel , please rmmod dlb2 driver first .
        # #rmmod dlb2
        ##################
        
        
    ## 3
    if tcd.step("Start VM using QEMU:"):
        # Start VM using QEMU:
        # dnf update --allowerasing --nobest
        # dnf install qemu-kvm -y --allowerasing
        # /usr/libexec/qemu-kvm -name guestVM1 -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 4096 -cpu host -drive format=raw,file=/home/home/spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img -bios /home/OVMF.fd -smp 8 -nic user,hostfwd=tcp::2202-:22 -nographic
        
        sutos.execute_cmd(sut, f'dnf update --allowerasing --nobest -y', timeout=60*60)
        sutos.execute_cmd(sut, f'dnf install qemu-kvm -y --allowerasing', timeout=60*60)
        sutos.execute_cmd(sut, f'pip3 install setuptools_rust paramiko scp', timeout=60*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/resource_config_login.py -d \'dlb\' -s \'16\' -g \'1\' -p \'1\'', timeout=60*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_config.py', timeout=60*60)
        ### Notes ###
        # If kernel is 5.15+, use /usr/libexec/qemu-kvm to replace qemu-system-x86_64
        ##################
        
        
    ## 4
    if tcd.step("Set password and Copy the DLB and DPDK package and kernel rpms inside the VM"):
        # Set password and Copy the DLB and DPDK package and kernel rpms inside the VM
        # Set password for VM
        # passwd
        
        #cd /root
        #mkdir dlb
        # sftp host_ip_address
        # > get /root/dlb/release_ver_7.5.2.zip
        # > get /root/dlb/dpdk-20.11.3.tar.xz
        # > get /root/kernel-spr-bkc-pc-devel-6.13-0.el8.x86_64.rpm
        # > get /root/accelerators_interop_multi_vm_scripts-master/accelerators_guest_script.sh
        # > bye
        
        # mv release_ver_7.5.2.zip dpdk-20.11.3.tar.xz /root/dlb
        # Install dependencies
        # rpm -Uvh *.rpm --force --nodeps
        # yum install make gcc
        
        # Load DLB driver.
        # cd /root/dlb
        # unzip release_ver_7.5.2.zip
        # cd /root/dlb/driver/dlb2/
        # make
        # insmod ./dlb2.ko
        # cd /root/dlb/libdlb/
        # make
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $Accelerator_REMOTE_TOOL_PATH/dlb"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $SUT_TOOLS"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$DPDK_DRIVER_NAME" -d "$SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$DLB_DRIVER_NAME" -d "$SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$KERNEL_PKG" -d "$SUT_TOOLS"', timeout=10*60)
        #Execute Command: timeout=10*60, cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$ACC_INTEROP_SCRIPT_NAME" -d "$Accelerator_REMOTE_TOOL_PATH/dlb"
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $SUT_TOOLS && unzip -o kernel-packages-spr-bkc-pc-*.zip -d $Accelerator_REMOTE_TOOL_PATH/dlb"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $Accelerator_REMOTE_TOOL_PATH/dlb && rpm -Uvh *.rpm --force --nodeps"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $Accelerator_REMOTE_TOOL_PATH/dlb && yum install make gcc -y"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/dlb_install.py -c \'False\'"', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# passwd")
        tcd.log("Changing password for user root.")
        tcd.log("New password:")
        tcd.log("BAD PASSWORD: The password fails the dictionary check - it is based on a dictionary word")
        tcd.log("Retype new password:")
        tcd.log("passwd: all authentication tokens updated successfully.")
        ### Notes ###
        # If you are use intel next kernel , please rmmod dlb2 driver first .
        # #rmmod dlb2
        ##################
        
        
    ## 5
    if tcd.step("DLB - Tests - Inside VM"):
        # DLB - Tests - Inside VM
        # DPDK Installation
        # cd /root/dlb/
        # tar xfJ dpdk-<DPDK version>.tar.xz
        # cd dpdk-<DPDK version> (This is the $DPDK_DIR path used in steps
        # ahead)
        # yum install patch
        # patch -Np1 < /root/dlb/dpdk/<DPDK patch name>.patch
        
        # DPDK build:
        # export DPDK_DIR=/root/dlb/dpdk-<DPDK version>/
        # export RTE_SDK=$DPDK_DIR
        # export RTE_TARGET=installdir
        # yum install meson
        # meson setup --prefix $RTE_SDK/$RTE_TARGET builddir
        # ninja -C builddir
        
        # Shutdown the virtual machine
        # shutdown now
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/run_dpdk.py"', timeout=30*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# patch -Np1 < /root/dlb/dpdk/<DPDK patch name>.patch")
        tcd.log("(Stripping trailing CRs from patch; use --binary to disable.)")
        tcd.log("patching file app/dlb_monitor/main.c")
        tcd.log("(Stripping trailing CRs from patch; use --binary to disable.)")
        tcd.log("...")
        tcd.log("...")
        tcd.log("(Stripping trailing CRs from patch; use --binary to disable.)")
        tcd.log("patching file app/meson.build")
        tcd.log("# meson setup --prefix $RTE_SDK/$RTE_TARGET builddir")
        tcd.log("builddir")
        tcd.log("The Meson build system")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Build targets in project: 975")
        tcd.log("Found ninja-1.8.2 at /usr/bin/ninja")
        tcd.log("# ninja -C builddir")
        tcd.log("...")
        tcd.log("...")
        tcd.log("[2420/2420] Linking target app/test/dpdk-test")
        ##################
        
        
    ## 6
    if tcd.step("Repeat the Step 4,5,6 and 7 to launch Multiple VMs. The max MDEVs that can be created on single DLB device is 16."):
        # Repeat the Step 4,5,6 and 7 to launch Multiple VMs. The max MDEVs that can be created on single DLB device is 16.
        
        # Try to crate maximum possible number of VMs to utilize all the MDEVs that can be created on a single DLB device.
        
        # E.g. Create 16 VMs with 1 DLB MDEVs each
        
        
        # 1.Config VM_IMAGE and VM_BIOS path in config.sh
        # cd /root/accelerators_interop_multi_vm_scripts-master
        #vi config.sh
        # VM_IMAGE="/home/spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img" # location of VM guest image
        # VM_BIOS="/home/OVMF.fd" # location of VM guest BIOS
        
        # 2.Start VM using launch script
        # ./Accelerators_SIOV_Multi_VM.sh -n 16 -H -m 1 -c 8 -i gva
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# cat config.sh")
        tcd.log("# configurables. Modify this file for your specific configuration")
        tcd.log("DSA_CONFIG_PATH=/sys/bus/dsa/devices")
        tcd.log("QAT_PATH=/root/qat/build/")
        tcd.log("MDEV_DIR=/sys/bus/mdev/devices/")
        tcd.log("VM_IMAGE=\"/home/spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img\" #Location of VM guest image")
        tcd.log("VM_BIOS=\"/home/OVMF.fd\" # location of VM guest BIOS")
        tcd.log("VM_MEMORY=2048 # Memory allocation for VM (MiB)")
        tcd.log("NIC_DEVICE_LIST=(\"ens5f0\" \"ens5f1\") #List of NIC Devices for Network Virtualization.")
        tcd.log("# ./Accelerators_SIOV_Multi_VM.sh -n 16 -H -m 1 -c 8 -i gva")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Checking for Acceleratlor devices.")
        tcd.log("Executing lspci on VM using port 2001...")
        tcd.log("root@localhost\'s password:")
        tcd.log("00:00.0 Host bridge: Intel Corporation 82G33/G31/P35/P31 Express DRAM Controller")
        tcd.log("00:01.0 VGA compatible controller: Device 1234:1111 (rev 02)")
        tcd.log("00:02.0 Ethernet controller: Red Hat, Inc. Virtio network device")
        tcd.log("00:03.0 Co-processor: Intel Corporation Device 2711")
        tcd.log("00:1f.0 ISA bridge: Intel Corporation 82801IB (ICH9) LPC Interface Controller (rev 02)")
        tcd.log("00:1f.2 SATA controller: Intel Corporation 82801IR/IO/IH (ICH9R/DO/DH) 6 port SATA Controller [AHCI mode] (rev 02)")
        tcd.log("00:1f.3 SMBus: Intel Corporation 82801I (ICH9 Family) SMBus Controller (rev 02)")
        tcd.log("...")
        tcd.log("...")
        tcd.log("### VM SSH Connection Info ###")
        tcd.log("VM running on port 2001...")
        tcd.log("to connect to VM: ssh -p 2001 localhost")
        tcd.log("VM running on port 2002...")
        tcd.log("to connect to VM: ssh -p 2002 localhost")
        tcd.log("VM running on port 2003...")
        tcd.log("to connect to VM: ssh -p 2003 localhost")
        tcd.log("...")
        tcd.log("...")
        ### Notes ###
        # You can use shell scripts to launch Multiple VMs. Inorder to do so, The VM img has to be setup with required configuration and install all accelerator tools and drivers in the img file.
        # Scripts: https://gitlab.devtools.intel.com/ryakkati/accelerators_interop_multi_vm_scripts/
        # Usage: ./Accelerators_SIOV_Multi_VM.sh <options>
        # Options:
        # -h      Show Help.
        # -s      Shutdown running VMs.
        # -t      Shutdown running VMs and Remove all the MDEVS
        # -r       "<command>"            Command to run on VMs.
        # Configuration Options:
        # -n       <VMs>          Number of VMs to create on a device.
        # -a       <All Devices>  Creats -n number of  VMs on each Accelerator devices available.
        # Eg: In a 2S System, 8 - devices are present, Hence 8*n Number of VMs will be Launched.
        # -Q       <QAT>          Enables Assignment of QAT MDEVs to VM.
        # Provide Mdev type. Avaliable Mdev types: sym asym dc
        # -H       <DLB>          Enables Assignment of DLB MDEVs to VM.
        # -D       <DSA>          Enables Assignment of DSA MDEVs to VM.
        # Provide Mdev type. Avaliable Mdev types: 1swq 1dwq
        # -I       <IAX>          Enables Assignment of IAX MDEVs to VM.
        # Provide Mdev type. Avaliable Mdev types: 1swq 1dwq
        # -S       <SGX>          Enables SGX Feature to VM.
        # -d       <Device>       Device Number on which VMs to be created. Default: 0
        # -c       <cores>        Number of CPU cores. Default: 1
        # -m       <MDEVS>        Max number MDEV devices per VM. Actual number may be limited by config Default: 1
        # -i "<IOMMU CONFIG>"     QEMU IOMMU device configuration. Default gpa
        # Available IOMMU config options: gpa giova gva
        # Command to launch 16 VMs on a device and 1 MDEVs per VM(on 2S : 8 devices * 16 VMs per device = 128VMs)  with DLB MDEVs
        # # ./Accelerators_SIOV_Multi_VM.sh -n 16 -H -m 1 -c 8 -i gva
        # To run DLB worklaod in all VMs concurently for a given time: (given that accelerator_guest_script.sh is copied into VMs and drivers and workloads installed in all VMs )
        # # ./Accelerators_SIOV_Multi_VM.sh -r "./accelerator_guest_script.sh -H -t 43200"
        #
        # Usage: ./accelerators_guest_script.sh <options>
        # Options:
        # -h      Show Help.
        # -Q       <QAT>          Runs QAT Workload.
        # -H       <DLB>          Runs DLB Workload.
        # -D       <DSA>          Runs DSA Workload.
        # -I       <IAX>          Runs IAX Workload.
        # -M       <DMA>          Runs DMA Workload.
        # -P       <IAX>          Passthrough Mode.
        # -t       <Runtime>              Runs Workload for -t seconds.
        ##################
        
        
    ## 7
    if tcd.step("Reload dlb2 and running DPDK test-event-dev Application on all VMs Concurrently"):
        # Reload dlb2 and running DPDK test-event-dev Application on all VMs Concurrently
        # cd /root/dlb/driver/dlb2/
        # insmod ./dlb2.ko
        # mkdir -p /mnt/hugepages
        # mount -t hugetlbfs nodev /mnt/hugepages
        # echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
        # cd /root/dlb/dpdk-<DPDK-Version>/builddir/app/
        
        # ./dpdk-test-eventdev -c 0xf --vdev=dlb2_event -- --test=order_queue --plcores=1 --wlcore=2,3 --nb_flows=64
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c \'cd $DPDK_DRIVER_PATH_L/dpdk-*/builddir/app &&  ./dpdk-test-eventdev -c 0xf --vdev=dlb2_event -- --test=order_queue --plcores=1 --wlcore=2,3 --nb_flows=64\' -m \'keyword\' -l \'Success\'"', timeout=30*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# ./dpdk-test-eventdev --vdev=dlb2_event -- --test=order_queue --plcores=3 --wlcore=4,5 --nb_flows=64 --nb_pkts=100000000")
        tcd.log("EAL: Detected 8 lcore(s)")
        tcd.log("EAL: Detected 1 NUMA nodes")
        tcd.log("EAL: Detected static linkage of DPDK")
        tcd.log("EAL: Multi-process socket /var/run/dpdk/rte/mp_socket")
        tcd.log("EAL: Selected IOVA mode \'PA\'")
        tcd.log("EAL: No available hugepages reported in hugepages-1048576kB")
        tcd.log("EAL: Probing VFIO support...")
        tcd.log("EAL: VFIO support initialized")
        tcd.log("PMD: Initialising DLB2 dlb2_event on NUMA node 0")
        tcd.log("EAL: No legacy callbacks, legacy socket not created")
        tcd.log("driver               : dlb2_event")
        tcd.log("test                 : order_queue")
        tcd.log("dev                  : 0")
        tcd.log("verbose_level        : 1")
        tcd.log("socket_id            : -1")
        tcd.log("pool_sz              : 16384")
        tcd.log("main lcore           : 0")
        tcd.log("nb_pkts              : 100000000")
        tcd.log("nb_timers            : 100000000")
        tcd.log("available lcores     : {0 1 2 3 4 5 6 7 }")
        tcd.log("nb_flows             : 64")
        tcd.log("worker deq depth     : 16")
        tcd.log("producer lcores      : {3 }")
        tcd.log("nb_wrker_lcores      : 2")
        tcd.log("worker lcores        : {4 5 }")
        tcd.log("nb_evdev_ports       : 3")
        tcd.log("nb_evdev_queues      : 2")
        tcd.log("Result: Success")
        ##################
        
        
    ## 8
    if tcd.step("To run DLB worklaod(Available Workload types: ldb ordered perf"):
        # To run DLB worklaod(Available Workload types: ldb ordered perf
        # ) in all VMs concurently for a given time
        # Change the terminal to host
        # 1.dlb_workload
        # ./Accelerators_SIOV_Multi_VM.sh -r "./accelerators_guest_script.sh -H ldb -t 43200"
        
        # 2.dlb_dpdk_oq_workload
        # ./Accelerators_SIOV_Multi_VM.sh -r "./accelerators_guest_script.sh -H ordered -t 43200"
        
        # 3.dlb_dpdk_pq_workload
        #./Accelerators_SIOV_Multi_VM.sh -r "./accelerators_guest_script.sh -H perf -t 43200"
        
        # Check the log
        # cd logs/Acc_RuncmCmd-*****/
        # cat run_cmd-vm-20**.log
        
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/accelerators_guest_script.py -d \'dlb\' -m \'all\' -t \'43200\'"', timeout=20*60)
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on iommu=on\'')
        sutos.execute_cmd(sut, f'cd /home/ && rm -rf vm*.qcow2 && rm -rf vm*.img', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS && rm -rf vm*.qcow2', timeout=20*60)
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# ./Accelerators_SIOV_Multi_VM.sh -r \"./accelerators_guest_script.sh -H ldb -t 43200\"")
        tcd.log("Executing command \"./accelerators_guest_script.sh -H ldb -t 300\" on VM using port 2001...")
        tcd.log("Check log /root/accelerators_interop_multi_vm_scripts-master/logs/Acc_RunCmd-20220527-084145/run_cmd-vm-2001.log")
        tcd.log("Executing command \"./accelerators_guest_script.sh -H ldb -t 300\" on VM using port 2002...")
        tcd.log("Check log /root/accelerators_interop_multi_vm_scripts-master/logs/Acc_RunCmd-20220527-084145/run_cmd-vm-2002.log")
        tcd.log("Waiting for Command to Complete...")
        tcd.log("root@localhost\'s password:")
        tcd.log("root@localhost\'s password:")
        tcd.log("password")
        tcd.log("Workloads run successfully of 2 VMs")
        tcd.log("No error in logs")
        tcd.log("# cat run_cmd-vm-2001.log")
        tcd.log("Found 1 DLB devices.")
        tcd.log("dlb2                  360448  0")
        tcd.log("Running DLB ldb_traffic in Loop - 1...")
        tcd.log("...")
        tcd.log("...")
        tcd.log("[tx_traffic()] Sent 1000000 events")
        tcd.log("[rx_traffic()] Received 1000000 events")
        tcd.log("[rx_traffic()] Received 1000000 events")
        tcd.log("DLB Workload ran successfully: Pass in Loop - 265")
        ### Notes ###
        # The number of times to enter password depends on the number of VMS
        ##################
        
        


def clean_up(sut):
    pass


def test_main():
    tcd = TestCase(globals(), locals())
    try:
        tcd.start(CASE_DESC)
        test_steps(tcd)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        tcd.end()
        clean_up(tcd)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
