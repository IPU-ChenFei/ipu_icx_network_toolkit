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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15011071039
    #TITLE: QAT_SIOV_Stress_Test_Single_VM_per_device
    #DOMAIN: accelerator
    
    
    #################################################################
    # Pre-Condition Section
    #################################################################
    #
    if tcd.prepare("setup system for test"):
        # Configuration:
        # https://hsdes.intel.com/appstore/article/#/15010469226
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
        
        # 1.Enable SRIOV and VT-D
        # EDKII->Socket Configuration -> IIO Configuration -> Intel  VT For Directed I/O (VT-d) -
        # Intel  VT For Directed I/O Enable
        # EDKII->Platform Configuration -> Miscellaneous Configuration -> SR-IOV Support Enable
        ## Set BIOS knob: VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        # 2. CentOS_QAT_Dependency_need to install
        # :
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
        # 3.VM test need copy OVMF.fd and ISO files to system.
        # centos image copy to/home/centos-8.4.2105-embargo-installer-202107220257.iso
        # OVMF file copy to /home/OVMF.fd
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_img_copy.py -d \'qat\' -s \'1\' -g \'1\' -f $CENTOS_IMG_NAME', timeout=10*60)
        sutos.execute_cmd(sut, f'\cp $OVMF_NAME /home/')
        # 4. Please Download QAT driver from BKC release and copy it to /root/QAT
        sutos.execute_cmd(sut, f'\cp $QAT_DRIVER_NAME $Accelerator_REMOTE_TOOL_PATH/QAT')
        
        
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
    if tcd.step("Configure driver to enable sIOV"):
        # Configure driver to enable sIOV
        
        # Extract QAT package and build driver:
        #cd /root/QAT
        #unzip qat20.l.0.5.6-00008.zip
        #tar -zxvf QAT20.L.0.5.6-00008.tar.gz
        #./configure --enable-icp-sriov=host
        #make install
        #make samples-install
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_install.py -i True', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("All devices show up at the end of driver make install:")
        tcd.log("#make install")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Checking status of all devices.")
        tcd.log("There is 136 QAT acceleration device(s) in the system:")
        tcd.log("qat_dev0 - type: 4xxx,  inst_id: 0,  node_id: 0,  bsf: 0000:6b:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev1 - type: 4xxx,  inst_id: 1,  node_id: 0,  bsf: 0000:70:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev2 - type: 4xxx,  inst_id: 2,  node_id: 0,  bsf: 0000:75:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev3 - type: 4xxx,  inst_id: 3,  node_id: 0,  bsf: 0000:7a:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev4 - type: 4xxx,  inst_id: 4,  node_id: 1,  bsf: 0000:e8:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev5 - type: 4xxx,  inst_id: 5,  node_id: 1,  bsf: 0000:ed:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev6 - type: 4xxx,  inst_id: 6,  node_id: 1,  bsf: 0000:f2:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev7 - type: 4xxx,  inst_id: 7,  node_id: 1,  bsf: 0000:f7:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("...")
        tcd.log("...")
        ### Notes ###
        # For GNR , every socket have 4 QAT PF and 64 vf
        ##################
        
        
    ## 3
    if tcd.step("Note: If you want to enable sIOV, rather than SR-IOV enabled by default. You need modify PF configure files under /etc/. Detail steps as below."):
        # Note: If you want to enable sIOV, rather than SR-IOV enabled by default. You need modify PF configure files under /etc/. Detail steps as below.
        
        # Modify all PFs's configure file to enable SIOV
        
        # Sample:
        #vim /etc/4xxx_dev0.conf
        
        # set as below
        ##############################################
        # ADI Section for Scalable IOV
        ##############################################
        # [SIOV]
        # NumberAdis = [1,64] (This is range , you can give the desired value)
        
        
        
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/siov_enable_conf.py -s 4', timeout=10*60)
        ### Notes ###
        # If you want to set SIOV = 64, you should set the NumberCyInstances = 0 and NumberDcInstances = 0 in both at [KERNEL] section and [SSL] section
        ##################
        
        
    ## 4
    if tcd.step("Restart related device to make configuration effective."):
        # Restart related device to make configuration effective.
        #service qat_service stop
        #service qat_service start
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/qat_service_stop_start.py', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("all device restart successful , every socket have 4 devices.")
        tcd.log("[root@localhost qat]# service qat_service stop")
        tcd.log("disable sriov")
        tcd.log("Stopping device qat_dev8")
        tcd.log("Stopping device qat_dev9")
        tcd.log("...")
        tcd.log("Stopping device qat_dev135")
        tcd.log("Stopping all devices.")
        tcd.log("notes: devices number is (all devices-N*16) , N is the devices number which enabled SIOV.")
        tcd.log("# service qat_service start")
        tcd.log("...")
        tcd.log("There is 104 QAT acceleration device(s) in the system:")
        tcd.log("qat_dev0 - type: 4xxx,  inst_id: 0,  node_id: 0,  bsf: 0000:e8:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev1 - type: 4xxx,  inst_id: 1,  node_id: 0,  bsf: 0000:ed:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev2 - type: 4xxx,  inst_id: 2,  node_id: 0,  bsf: 0000:f2:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("qat_dev3 - type: 4xxx,  inst_id: 3,  node_id: 0,  bsf: 0000:f7:00.0,  #accel: 1 #engines: 9 state: up")
        tcd.log("...")
        ##################
        
        
    ## 5
    if tcd.step("Verify sIOV enabled on device"):
        # Verify sIOV enabled on device
        # Using below command, you can get the available sym/asym/dc ADI resource on. If sIOV not enabled, available sym/asym/dc should be 0. For device already enable sIOV, you can create related vdev/vqat of different service.
        # cd /root/QAT
        # ./build/vqat_ctl show
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -m "kv" -c \'cd $Accelerator_REMOTE_TOOL_PATH/QAT && ./build/vqat_ctl show\' -l \'Available sym,2\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# ./build/vqat_ctl show")
        tcd.log("BDF: 0000:6b:00.0")
        tcd.log("Available sym : 2")
        tcd.log("Available asym : 0")
        tcd.log("Available dc : 2")
        tcd.log("Active VQATs:")
        tcd.log("--------------------------------------------------------------")
        tcd.log("INDEXTYPE                                UUIDSTATUS")
        tcd.log("--------------------------------------------------------------")
        tcd.log("...")
        tcd.log("...")
        ##################
        
        
    ## 6
    if tcd.step("Enable sIOV on all QAT devices."):
        # Enable sIOV on all QAT devices.
        # Sample:
        # cd /root/QAT
        # ./build/vqat_ctl create 0000:6b:00.0 sym
        
        # start VM and attach QAT SIOV virtual device with sym:
        # Note:please launch VM in a new terminal
        # qemu-system-x86_64 -name guestVM1 -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 4096 -cpu host -drive format=raw,file=/home/qemu_centos_12.qcow2 -bios /home/OVMF.fd -smp 2 -serial mon:stdio -net nic,model=virtio -nic user,hostfwd=tcp::2222-:22 -nographic -device vfio-pci,sysfsdev=/sys/devices/pci0000:6b/0000:6b:00.0/25224033-5107-4449-b2f8-44c233374a3a
        
        sutos.execute_cmd(sut, f'pip3 install setuptools_rust paramiko scp', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/resource_config_login.py -d \'qat\' -s \'1\' -g \'1\' -m \'sym\'', timeout=30*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_config.py', timeout=30*60)
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("#./build/vqat_ctl create 0000:6b:00.0 sym")
        tcd.log("VQAT-sym created successfully, device name = 25224033-5107-4449-b2f8-44c233374a3a")
        tcd.log("# ./build/vqat_ctl show")
        tcd.log("BDF: 0000:6b:00.0")
        tcd.log("Available sym    : 1")
        tcd.log("Available asym   : 0")
        tcd.log("Available dc     : 2")
        tcd.log("Active VQATs:")
        tcd.log("--------------------------------------------------------------")
        tcd.log("INDEX   TYPE                                    UUID    STATUS")
        tcd.log("1       sym     25224033-5107-4449-b2f8-44c233374a3a    active")
        tcd.log("")
        tcd.log("...")
        tcd.log("...")
        ##################
        
        
    ## 7
    if tcd.step("ssh login to host and VM"):
        # ssh login to host and VM
        
        # ssh root@localhost -p 2222
        
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("SSH to VM code  without exception")
        ##################
        
        
    ## 8
    if tcd.step("proxy settings:"):
        # proxy settings:
        
        # export http_proxy=http://proxy-iind.intel.com:911
        # export HTTP_PROXY=http://proxy-iind.intel.com:911
        # export https_proxy=http://proxy-iind.intel.com:911
        # export HTTPS_PROXY=http://proxy-iind.intel.com:911
        # export no_proxy='localhost, 127.0.0.1, intel.com, .intel.com'
        ##################
        tcd.log("### Expected result ###")
        tcd.log("the CLI exec successfully and returns a zero return code.")
        ##################
        
        
    ## 9
    if tcd.step("Copy the QAT package inside the VM"):
        
        # Copy the QAT package inside the VM
        #cd root
        #mkdir QAT
        #cd /root/QAT
        #sftp <hostip>
        # > get /root/QAT/qat20.l.0.5.6-00008.zip
        # > bye
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $Accelerator_REMOTE_TOOL_PATH/QAT"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$QAT_DRIVER_NAME" -d "$SUT_TOOLS"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$KERNEL_PKG" -d "$SUT_TOOLS"', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("The python code run without exception")
        ### Notes ###
        # import scp
        # client = scp.Client(host=host, user=user, keyfile=keyfile)
        # # or
        # client = scp.Client(host=host, user=user)
        # client.use_system_keys()
        # # or
        # client = scp.Client(host=host, user=user, password=password)
        # # and then
        # client.transfer('/etc/local/filename', '/etc/remote/filename')
        ##################
        
        
    ## 10
    if tcd.step("Install QAT SW on Guest"):
        # Install QAT SW on Guest
        
        # first check devices assigned (e.g.)
        # lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0000'
        
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c \'lspci -v -d 8086:0da5 -vmm\' -m \'keyword\' -l \' Device 0000\'"', timeout=10*60)
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
        
        
    ## 11
    if tcd.step("Install QAT dependency:"):
        # Install QAT dependency:
        
        #rpm -ivh <kernel-devel-flie>
        
        #yum -y install zlib-devel.x86_64
        
        #yum -y install yasm
        
        #yum -y install systemd-devel
        
        #yum -y install boost-devel.x86_64
        
        #yum -y install openssl-devel
        
        #yum -y install libnl3-devel
        
        #yum -y install gcc
        
        #yum -y install gcc-c++
        
        #yum -y install libgudev.x86_64
        
        #yum -y install libgudev-devel.x86_64
        
        #yum -y install systemd*
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $SUT_TOOLS && unzip -o kernel-packages-spr-bkc-pc-*.zip -d $Accelerator_REMOTE_TOOL_PATH/QAT"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $Accelerator_REMOTE_TOOL_PATH/QAT && rpm -Uvh *.rpm --force --nodeps"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/qat_dependency_setup.py"', timeout=20*60)
        ##################
        
        
    ## 12
    if tcd.step("install QAT driver on Guest"):
        # install QAT driver on Guest
        #cd /root/QAT
        #unzip qat20.l.0.5.6-00008.zip
        #tar -zxvf QAT20.L.0.5.6-00008.tar.gz
        # ./configure --enable-icp-sriov=guest
        # make install
        # make samples-install
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/qat_install.py -w \'guest\'"', timeout=30*60)
        ##################
        
        
    ## 13
    if tcd.step("lspci -vd :0da5"):
        #lspci -vd :0da5
        # Check vqat device status , if device is down , please enable it.
        #adf_ctl status
        #./build/adf_ctl qat_dev0 up
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $Accelerator_REMOTE_TOOL_PATH/QAT && ./build/adf_ctl qat_dev0 up"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -m \'no_found\' -c \'lspci -vd :0da5\' -l \'down\'"', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# lspci -vd:0da5")
        tcd.log("00:04.0 Co-processor: Intel Corporation Device 0da5 (rev 02)")
        tcd.log("Subsystem: Intel Corporation Device 0001")
        tcd.log("Flags: bus master, fast devsel, latency 0, IRQ 33, IOMMU group 4")
        tcd.log("...")
        tcd.log("...")
        tcd.log("00:05.0 Co-processor: Intel Corporation Device 0da5 (rev 02)")
        tcd.log("Subsystem: Intel Corporation Device 0002")
        tcd.log("Flags: bus master, fast devsel, latency 0, IRQ 34, IOMMU group 5")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Kernel driver in use: vqat-adi")
        tcd.log("Kernel modules: qat_vqat")
        tcd.log("## adf_ctl status")
        tcd.log("Checking status of all devices.")
        tcd.log("There is 1 QAT acceleration device(s) in the system:")
        tcd.log("qat_dev0 - type: vqat-adi,  inst_id: 0,  node_id: 0,  bsf: 0000:00:04.0,  #accel: 1 #engines: 1 state: up")
        tcd.log("#./adf_ctl qat_dev0 up")
        tcd.log("Starting device qat_dev0")
        tcd.log("Device qat_dev0 already configured")
        ##################
        
        
    ## 14
    if tcd.step("Run QAT workload which uses SIOV Virtual device interface"):
        # Run QAT workload which uses SIOV Virtual device interface
        #cd /root/QAT/build
        
        #./cpa_sample_code runTests=1 signOfLife=1
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/run_qat_sample_code.py -q \'runTests=1 signOfLife=1\'"', timeout=30*60)
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on\'')
        sutos.execute_cmd(sut, f'cd /home/ && rm -rf vm*.qcow2 && rm -rf vm*.img', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS && rm -rf vm*.qcow2', timeout=20*60)
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Sample code test success. At the end of test show as below:")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Sample code completed successfully.")
        ### Notes ###
        # sym -> ./cpa_sample_code runTests=1 signOfLife=1
        # asym -> ./cpa_sample_code runTests=30 signOfLife=1
        # dc -> ./cpa_sample_code runTests=32 signOfLife=1
        # sym/dc -> ./cpa_sample_code runTests=33 signOfLife=1
        # asym/dc -> ./cpa_sample_code runTests=62 signOfLife=1
        ##################
        
        
    ## 15
    if tcd.step("Repeat steps 7-14"):
        # Repeat steps 7-14
        # Launch VMs for all QAT devices(Single VM per device) and run QAT test parallelly
        ##################
        tcd.log("### Expected result ###")
        tcd.log("test successfully")
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
