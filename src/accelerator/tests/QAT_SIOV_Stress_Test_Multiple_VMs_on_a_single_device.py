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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15011258466
    #TITLE: QAT_SIOV_Stress_Test_Multiple_VMs_on_a_single_device
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
        
        #1.Enable SRIOV and VT-D
        #EDKII->Socket Configuration -> IIO Configuration -> Intel  VT For Directed I/O (VT-d) - Intel  VT For Directed I/O Enable
        #EDKII->Platform Configuration -> Miscellaneous Configuration -> SR-IOV Support Enable
        ## Set BIOS knob: VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        #2. CentOS_QAT_Dependency_need to install:
        # yum -y install zlib-devel.x86_64
        # yum -y install yasm
        # yum -y install systemd-devel
        # yum -y install boost-devel.x86_64
        # yum -y install openssl-devel
        # yum -y install libnl3-devel
        # yum -y install gcc
        # yum -y install gcc-c++
        # yum -y install libgudev.x86_64
        # yum -y install libgudev-devel.x86_64
        # yum -y install systemd*
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH/QAT')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH/QAT && python3 $API_SCRIPT/qat_dependency_setup.py', timeout=10*60)
        #3.VM test need copy OVMF.fd and img files to system.
        #wget https://ubit-artifactory-or.intel.com/artifactory/linuxmvpstacks-or-local/linux-stack-bkc/2022ww19/internal-images/spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img.xz to /home
        #OVMF file copy to /home/OVMF.fd
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_img_copy.py -d \'qat\' -s \'64\' -g \'2\' -p \'1\' -f $CENTOS_IMG_NAME', timeout=30*60)
        sutos.execute_cmd(sut, f'\cp $OVMF_NAME /home/')
        #4. Please Download QAT driver and kernel-spr-bkc-pc-devel-6.13-0.el8.x86_64.rpm from BKC release and copy it to /root/QAT
        sutos.execute_cmd(sut, f'\cp $QAT_DRIVER_NAME $Accelerator_REMOTE_TOOL_PATH/QAT')
        #5. Download shell scripts:accelerators_interop_multi_vm_scripts-master.zip to /root
        #https://gitlab.devtools.intel.com/ryakkati/accelerators_interop_multi_vm_scripts/
        #Note:System memory must be large enough
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Make sure to set kernel command line parameter intel_iommu=on,sm_on"):
        # Make sure to set kernel command line parameter intel_iommu=on,sm_on
        #grubby --update-kernel=/boot/vmlinuz-'uname-r' --args="intel_iommu=on,sm_on"
        #reboot
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("check args insert success after reboot.")
        tcd.log("# cat /proc/cmdline")
        tcd.log("BOOT_IMAGE=(hd0,gpt2)/vmlinuz-5.12.0-0507.intel_next.09_15_po.39.x86_64+server root=/dev/mapper/cl-r oot ro crashkernel=auto resume=/dev/mapper/cl-swap rd.lvm.lv=cl/root rd.lvm.lv=cl/swap rhgb quiet co nsole=ttyS0,115200 loglevel=7 console=tty0 intel_iommu=on,sm_on")
        ##################
        
        
    ## 2
    if tcd.step("Extract QAT package and build driver:"):
        # Extract QAT package and build driver:
        #cd /root/QAT
        #unzip qat20.l.0.5.6-00008.zip
        #tar -zxvf QAT20.L.0.5.6-00008.tar.gz
        #./configure --help
        #./configure --enable-icp-sriov=host --enable-icp-sym-only
        #make install
        
        
        # Check if the QAT service is running correctly.
        # command :
        # service qat_service status
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_install.py -i True -w \'host --enable-icp-sym-only\'', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -m "no_found" -c \'service qat_service status\' -l \'down\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("#./configure --help")
        tcd.log("...")
        tcd.log("...")
        tcd.log("--enable-icp-sym-only")
        tcd.log("Enables driver to support Symmetric Crypto services only.")
        tcd.log("...")
        tcd.log("...")
        tcd.log("#make install")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Checking status of all devices.")
        tcd.log("There is 136 QAT acceleration device(s) in the system:")
        tcd.log("qat_dev0 - type: 4xxx,  inst_id: 0,  node_id: 0,  bsf: 0000:6b:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("...")
        tcd.log("...")
        ##################
        
        
    ## 3
    if tcd.step("Note: If you want to enable sIOV, rather than SR-IOV enabled by default. You need modify PF configure files under /etc/. Detail steps are list below."):
        # Note: If you want to enable sIOV, rather than SR-IOV enabled by default. You need modify PF configure files under /etc/. Detail steps are list below.
        
        # Modify PF configure file to enable SIOV
        # vim /etc/4xxx_dev0.conf
        
        #vim /etc/4xxx_dev0.conf
        # set as below
        
        ##############################################
        # Kernel Instances Section
        ##############################################
        # [KERNEL]
        # NumberCyInstances = 0
        # NumberDcInstances = 0
        
        ##############################################
        # ADI Section for Scalable IOV
        ##############################################
        # [SIOV]
        # NumberAdis = 64
        
        ##############################################
        # User Process Instance Section
        ##############################################
        # [SSL]
        # NumberCyInstances = 0
        # NumberDcInstances = 0
        
        # Restart related device to make configuration effective.
        # service qat_service stop
        # service qat_service start
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/siov_enable_conf.py -s 64 -a True', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_service_stop_start.py', timeout=10*60)
        ### Notes ###
        # If you want to set SIOV = 64, you should set the NumberCyInstances = 0 and NumberDcInstances = 0 in both at [KERNEL] section and [SSL] section
        ##################
        
        
    ## 4
    if tcd.step("Verify sIOV enabled on device"):
        # Verify sIOV enabled on device
        # Using below command, you can get the available sym/asym/dc ADI resource on. If sIOV not enabled, available sym/asym/dc should be 0. For device already enable sIOV, you can create related vdev/vqat of different service.
        # ./build/vqat_ctl show
        # ./build/vqat_ctl -help
        
        # Create sym MDEV on first QAT device
        # ./build/vqat_ctl create 0000:6b:00.0 sym
        # VQAT-sym created successfully, device name = a14d54d2-bfd3-4bfa-b1ec-896d98c5e29a
        
        # Verify as below
        # ./build/vqat_ctl show
        
        # Launch QEMU VM with QAT MDEV
        # dnf update --nogpg --allowerasing
        # dnf install qemu-kvm -y
        # /usr/libexec/qemu-kvm -name guestVM1 -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 16384 -cpu host -drive format=raw,file=/home/spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img -bios /home/OVMF.fd -smp 16 -nic user,hostfwd=tcp::2201-:22 -nographic -device vfio-pci,sysfsdev=/sys/bus/mdev/devices/a14d54d2-bfd3-4bfa-b1ec-896d98c5e29a
        
        #If kernel is 5.15+, use /usr/libexec/qemu-kvm to replace qemu-system-x86_64
        
        sutos.execute_cmd(sut, f'dnf update --nobest --nogpg --allowerasing -y', timeout=10*60)
        sutos.execute_cmd(sut, f'dnf install qemu-kvm -y', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -m "keywords" -c \'cd $Accelerator_REMOTE_TOOL_PATH/QAT && ./build/vqat_ctl show\' -l \'64\'')
        sutos.execute_cmd(sut, f'pip3 install setuptools_rust paramiko scp', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/resource_config_login.py -d \'qat\' -s \'64\' -g \'2\' -p \'1\' -m \'sym\'', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_config.py', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# ./build/vqat_ctl create 0000:6b:00.0 sym")
        tcd.log("VQAT-sym created successfully, device name = a14d54d2-bfd3-4bfa-b1ec-896d98c5e29a")
        tcd.log("# ./build/vqat_ctl show")
        tcd.log("BDF: 0000:6b:00.0")
        tcd.log("Available sym : 63")
        tcd.log("Available asym : 0")
        tcd.log("Available dc : 0")
        tcd.log("Active VQATs:")
        tcd.log("--------------------------------------------------------------")
        tcd.log("INDEXTYPE                                UUIDSTATUS")
        tcd.log("1syma14d54d2-bfd3-4bfa-b1ec-896d98c5e29a")
        tcd.log("--------------------------------------------------------------")
        tcd.log("BDF: 0000:70:00.0")
        tcd.log("Available sym : 0")
        tcd.log("Available asym : 0")
        tcd.log("Available dc : 0")
        tcd.log("Active VQATs:")
        tcd.log("...")
        tcd.log("...")
        ##################
        
        
    ## 5
    if tcd.step("Set password and copy the QAT package inside the VM"):
        # Set password and copy the QAT package inside the VM
        #passwd
        #cd root
        #mkdir QAT
        #sftp <hostip>
        # > get /root/QAT/qat20.l.0.9.0-00023_1.zip
        # > get /root/kernel-spr-bkc-pc-devel-6.13-0.el8.x86_64.rpm
        # > get /root/accelerators_interop_multi_vm_scripts-master/accelerators_guest_script.sh
        # > bye
        
        #mv qat20.l.0.9.0-00023_1.zip QAT/
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $Accelerator_REMOTE_TOOL_PATH/QAT"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$QAT_DRIVER_NAME" -d "$SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$KERNEL_PKG" -d "$SUT_TOOLS"', timeout=10*60)
        #Execute Command: timeout=10*60, cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$ACC_INTEROP_SCRIPT_NAME" -d "$Accelerator_REMOTE_TOOL_PATH/QAT"
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# passwd")
        tcd.log("Changing password for user root.")
        tcd.log("New password:")
        tcd.log("BAD PASSWORD: The password fails the dictionary check - it is based on a dictionary word")
        tcd.log("Retype new password:")
        tcd.log("passwd: all authentication tokens updated successfully.")
        ##################
        
        
    ## 6
    if tcd.step("Install QAT dependency:"):
        # Install QAT dependency:
        
        #rpm -Uvh *.rpm --force --nodeps
        
        #yum -y install zlib-devel.x86_64 yasm systemd-devel boost-devel.x86_64 openssl-devel libnl3-devel gcc make gcc-c++ libgudev.x86_64 libgudev-devel.x86_64 systemd*
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $SUT_TOOLS && unzip -o kernel-packages-spr-bkc-pc-*.zip -d $Accelerator_REMOTE_TOOL_PATH/QAT"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $Accelerator_REMOTE_TOOL_PATH/QAT && rpm -Uvh *.rpm --force --nodeps"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $SUT_TOOLS && python3 $API_SCRIPT/qat_dependency_setup.py"', timeout=20*60)
        ##################
        
        
    ## 7
    if tcd.step("Install QAT driver on Guest"):
        # Install QAT driver on Guest
        
        # first check devices assigned (e.g.)
        # lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0000'
        
        # cd /root/QAT
        # unzip qat20.l.0.5.6-00008.zip
        # tar -zxvf QAT20.L.0.5.6-00008.tar.gz
        # ./configure --enable-icp-sriov=guest
        # make install
        # make samples-install
        
        # Shutdown the VM
        # shutdown now
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/qat_install.py -w \'guest\'"', timeout=30*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("#lspci -v -d 8086:0da5 -vmm | grep -E \'SDevice | 0000\'")
        tcd.log("SDevice:        Device 0000")
        ### Notes ###
        # Vqats share same device ID in guest, you can distinguish them by subsystem ID 'SDevice'.
        # # lspci -vnd:4941 => cpm2.0 VF
        # # lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0001' => cpm2.0 asym vqat
        # # lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0002' => cpm2.0 dc vqat
        ##################
        
        
    ## 8
    if tcd.step("Repeat the Step 5 and 6 to launch Multiple VMs. The max MDEVs that can be created on single QAT device is 64."):
        # Repeat the Step 5 and 6 to launch Multiple VMs. The max MDEVs that can be created on single QAT device is 64.
        
        # Try to crate maximum possible number of VMs to utilize all the MDEVs that can be created on a device.
        
        # E.g. Create 64 VMs with 1 QAT MDEV each
        # or
        # Create 32 VMs with 2 QAT MDEVs each
        
        # 1.Config VM_IMAGE and VM_BIOS path in config.sh
        # cd /root/accelerators_interop_multi_vm_scripts-master
        #vi config.sh
        # VM_IMAGE="/home/spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img" # location of VM guest image
        # VM_BIOS="/home/OVMF.fd" # location of VM guest BIOS
        
        # 2.Start VM using launch script
        # ./Accelerators_SIOV_Multi_VM.sh -n 64 -Q sym -m 1 -c 8 -i gva
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
        tcd.log("# ./Accelerators_SIOV_Multi_VM.sh -n 64 -Q sym -m 1 -c 8 -i gva")
        tcd.log("Shutting down VMs...")
        tcd.log("Total VMs = 8")
        tcd.log("VM per Device = true")
        tcd.log("Host Device Number = 0")
        tcd.log("...")
        tcd.log("...")
        tcd.log("root@localhost\'s password:")
        tcd.log("00:00.0 Host bridge: Intel Corporation 82G33/G31/P35/P31 Express DRAM Controller")
        tcd.log("00:01.0 VGA compatible controller: Device 1234:1111 (rev 02)")
        tcd.log("00:02.0 Ethernet controller: Red Hat, Inc. Virtio network device")
        tcd.log("00:03.0 Co-processor: Intel Corporation Device 0da5 (rev 02)")
        tcd.log("00:1f.0 ISA bridge: Intel Corporation 82801IB (ICH9) LPC Interface Controller (rev 02)")
        tcd.log("00:1f.2 SATA controller: Intel Corporation 82801IR/IO/IH (ICH9R/DO/DH) 6 port SATA Controller [AHCI mode] (rev 02)")
        tcd.log("00:1f.3 SMBus: Intel Corporation 82801I (ICH9 Family) SMBus Controller (rev 02)")
        tcd.log("Executing lspci on VM using port 2002...")
        tcd.log("...")
        tcd.log("...")
        tcd.log("### VM SSH Connection Info ###")
        tcd.log("VM running on port 2001...")
        tcd.log("to connect to VM: ssh -p 2001 localhost")
        tcd.log("VM running on port 2002...")
        tcd.log("to connect to VM: ssh -p 2002 localhost")
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
        # Command to launch 64 VMs on a device and 1 MDEVs per VM with QAT MDEVs
        # # ./Accelerators_SIOV_Multi_VM.sh -n 64 -Q sym -m 1 -c 8 -i gva
        # To run QAT worklaod in all VMs concurently for a given time: (given that accelerator_guest_script.sh is copied into VMs and drivers and workloads installed in all VMs )
        # # ./Accelerators_SIOV_Multi_VM.sh -r "./accelerator_guest_script.sh -Q -t 43200"
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
        
        
    ## 9
    if tcd.step("Open new terminals to login and run QAT workload on all VMs Concurrently which uses SIOV Virtual device interface"):
        # Open new terminals to login and run QAT workload on all VMs Concurrently which uses SIOV Virtual device interface
        
        # ssh -p 2001 localhost
        # ssh -p 2002 localhost
        # ...
        # ...
        # lspci -vd :0da5
        # Check vqat device status , if device is down , please enable it.
        # adf_ctl status
        # cd /root/qat/build
        # ./adf_ctl qat_dev0 up
        # ./cpa_sample_code signOfLife=1 runTests=1
        
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -m \'no_found\' -c \'adf_ctl status\' -l \'down\'"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/run_qat_sample_code.py -q \' signOfLife=1 runTests=1\'"', timeout=43200)
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on\'')
        sutos.execute_cmd(sut, f'cd /home/ && rm -rf vm*.qcow2 && rm -rf vm*.img', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS && rm -rf vm*.qcow2', timeout=20*60)
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# lspci -vd :0da5")
        tcd.log("00:03.0 Co-processor: Intel Corporation Device 0da5 (rev 02)")
        tcd.log("Subsystem: Intel Corporation Device 0000")
        tcd.log("Flags: bus master, fast devsel, latency 0, IOMMU group 3")
        tcd.log("Memory at 800024000 (64-bit, prefetchable) [size=8K]")
        tcd.log("Memory at 800000000 (64-bit, prefetchable) [size=128K]")
        tcd.log("Memory at 800026000 (64-bit, prefetchable) [size=4K]")
        tcd.log("Capabilities: [50] Express Root Complex Integrated Endpoint, MSI 00")
        tcd.log("Capabilities: [90] MSI-X: Enable+ Count=2 Masked-")
        tcd.log("Kernel driver in use: vqat-adi")
        tcd.log("Kernel modules: qat_vqat")
        tcd.log("#./cpa_sample_code signOfLife=1 runTests=1")
        tcd.log("qaeMemInit started")
        tcd.log("icp_sal_userStartMultiProcess(\"SSL\") started")
        tcd.log("*** QA version information ***")
        tcd.log("device ID= 0")
        tcd.log("software = 0.9.0")
        tcd.log("*** END QA version information ***")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Inst 0, Affin: 1, Dev: 0, Accel 0, EE 0, BDF 00:03:00")
        tcd.log("---------------------------------------")
        tcd.log("Cipher AES256-CBC")
        tcd.log("Direction             Encrypt")
        tcd.log("API                   Data_Plane")
        tcd.log("Packet Mix        40%-64B 20%-752B 35% 1504B 5%-8892B")
        tcd.log("Number of Threads     1")
        tcd.log("Total Submissions     20")
        tcd.log("Total Responses       20")
        tcd.log("Total Retries         0")
        tcd.log("---------------------------------------")
        tcd.log("Sample code completed successfully.")
        ### Notes ###
        # sym -> ./cpa_sample_code runTests=1 signOfLife=1
        # asym -> ./cpa_sample_code runTests=30 signOfLife=1
        # dc -> ./cpa_sample_code runTests=32 signOfLife=1
        # sym/dc -> ./cpa_sample_code runTests=33 signOfLife=1
        # asym/dc -> ./cpa_sample_code runTests=62 signOfLife=1
        ##################
        
        
    ## 10
    if tcd.step("To run QAT worklaod in all VMs concurently for a given time"):
        # To run QAT worklaod in all VMs concurently for a given time
        # Change the terminal to host
        # /Accelerators_SIOV_Multi_VM.sh -r "./accelerators_guest_script.sh -Q -t 43200"
        
        # Check the log
        # cd logs/Acc_RuncmCmd-*****/
        # cat run_cmd-vm-20**.log
        ##################
        tcd.log("### Expected result ###")
        tcd.log("#/Accelerators_SIOV_Multi_VM.sh -r \"./accelerators_guest_script.sh")
        tcd.log("Executing command \"./accelerators_guest_script.sh -Q -t 300\" on VM using port 2001...")
        tcd.log("Check log /root/accelerators_interop_multi_vm_scripts-master/logs/Acc_RunCmd-20220527-074654/run_cmd-vm-2001.log")
        tcd.log("Executing command \"./accelerators_guest_script.sh -Q -t 300\" on VM using port 2002...")
        tcd.log("Check log /root/accelerators_interop_multi_vm_scripts-master/logs/Acc_RunCmd-20220527-074654/run_cmd-vm-2002.log")
        tcd.log("Waiting for Command to Complete...")
        tcd.log("root@localhost\'s password: root@localhost\'s password:")
        tcd.log("password")
        tcd.log("Workloads run successfully of 2 VMs")
        tcd.log("Check logs in /root/accelerators_interop_multi_vm_scripts-master/logs/Acc_RunCmd-20220527-074654")
        tcd.log("# cat run_cmd-vm-2001.log")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Sample code completed successfully.")
        tcd.log("Sample code completed successfully.")
        tcd.log("QAT Workload ran successfully: Pass in Loop - 4")
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
