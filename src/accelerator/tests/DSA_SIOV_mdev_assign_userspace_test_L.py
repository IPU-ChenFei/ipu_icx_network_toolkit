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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010986853
    #TITLE: DSA_SIOV_mdev_assign_userspace_test_L
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
        
        sutos.execute_cmd(sut, f'dmesg -C')
        # 1. BIOS Configuration
        
        # Verify the following BIOS settings.
        # EDKII Menu > Socket Configuration > IIO configuration > PCIe ENQCMD > ENQCMDS = enabled
        # EDKII Menu > Socket Configuration > IIO Configuration >IOAT configuration >socket <n> IOAT configure > DSA = enabled
        # Notes: This knob only support on SPR, not support GNR
        
        # EDKII Menu > Socket Configuration > IIO Configuration > Intel VT for Directed I/O (VT-d) > Intel VT for Directed I/O = enabled
        # EDKII Menu > Socket Configuration > Processor Configuration > VMX = enabled
        ## Set BIOS knob: VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        
        # 2.Kernel parameters in host:
        # grubby --args="intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce" --update-kernel=/boot/vmlinuz-*.intel_next.*.x86_64+serve
        # Note: For intel next kernel 5.15 or newer , idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce
        # is no longer needed
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        # 3.Kernel Parameters in gues grubby --args="intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce" --update-kernel=/boot/vmlinuz-*.intel_next.*.x86_64+server
        # Note:
        # For intel next kernel 5.15 or newer , idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce
        # is no longer needed
        # 4.cp or git clone accel-random-config-and-test to /root/DSA  for host and guest
        
        # git clone
        # https://github.com/intel-sandbox/accel-random-config-and-test.git
        # 5.Install kernel-spr-bkc-pc-modules-internal-6.13-0.el8.x86_64.rpm
        # rpm -ivhf kernel-spr-bkc-pc-modules-internal-6.13-0.el8.x86_64.rpm
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS &&  rpm -ivhf $INTERNAL_MODULE_NAME', no_check=True)
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Check Linux command line."):
        
        # Check Linux command line.
        # cat /proc/cmdline
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Kernel parameters in host:")
        tcd.log("intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce")
        ### Notes ###
        # For intel next kernel 5.15 or newer , idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce is no longer needed
        ##################
        
        
    ## 2
    if tcd.step("Launch virtual machine image:"):
        # Launch virtual machine image:
        
        
        # qemu-system-x86_64 \
        # -name test \
        # -machine q35 \
        # -enable-kvm \
        # -global kvm-apic.vapic=false \
        # -m 10240 \
        # -cpu host \
        # -drive format=raw,file=/home/centos-8.4.2105-embargo-coreserver-<current version>.img \
        # -bios /home/OVMF.fd \
        # -smp 16 \
        # -serial mon:stdio \
        # -nic user,hostfwd=tcp::2222-:22 \
        # -nographic
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_img_copy.py -n \'1\' -f $CENTOS_IMG_NAME')
        sutos.execute_cmd(sut, f'\cp $OVMF_NAME /home/')
        sutos.execute_cmd(sut, f'pip3 install setuptools_rust paramiko scp', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_startvm.py -c "/usr/libexec/qemu-kvm -name guestVM0 -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 8192 -cpu host -net nic,model=virtio -nic user,hostfwd=tcp::2222-:22 -drive format=raw,file=/home/vm0.img -bios /home/OVMF.fd -smp 4 -serial mon:stdio -nographic"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_config.py -p 2222', timeout=30*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # New
        ##################
        
        
    ## 3
    if tcd.step("Config the kernel cmdline in gust vm and cp file to vm."):
        # Config the kernel cmdline in gust vm and cp file to vm.
        # grubby --args="intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce" --update-kernel=/boot/vmlinuz-*.intel_next.*.x86_64+server
        #sftp hostip
        # >get -r /root/DSA/accel-random-config-and-test /root
        # >bye
        #reboot
        # Wait os reboot done then shutdown vm
        #shutdown now
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on no5lvl\'"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "reboot"', no_check=True, timeout=10*60)
        tcd.sleep(120)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$ACCE_RANDOM_CONFIG_NAME" -d "$SUT_TOOLS" -p 2222', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "shutdown now"', no_check=True, timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("New")
        ### Notes ###
        # For intel next kernel 5.15 or newer , idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce is no longer needed
        ##################
        
        
    ## 4
    if tcd.step("Config VM_IMAGE and VM_BIOS path in config.sh"):
        # Config VM_IMAGE and VM_BIOS path in config.sh
        # cd /root/DSA/accel-random-config-and-test
        #vi config.sh
        # VM_IMAGE="/home/centos-8.4.2105-embargo-coreserver-202111012334.img" # location of VM guest image
        # VM_BIOS="/home/OVMF.fd" # location of VM guest BIOS
        
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && sed -i \'s#VM_IMAGE=.*#VM_IMAGE=/home/vm0.img#g\' config.sh')
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && sed -i \'s#VM_BIOS=.*#VM_BIOS=/home/OVMF.fd#g\' config.sh')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# cat config.sh")
        tcd.log("# configurables. Modify this file for your specific configuration")
        tcd.log("DSA_TEST=${DIR}/dsa_test/dsa_test # location of \"dsa_test\" executable")
        tcd.log("IAX_TEST=${DIR}/iax_test/iax_test # location of \"iax_test\" executable")
        tcd.log("VM_IMAGE=\"/home/centos-8.4.2105-embargo-coreserver-202111012334.img\" # location of VM guest image")
        tcd.log("VM_BIOS=\"/home/OVMF.fd\" # location of VM guest BIOS")
        tcd.log("VM_NETWORK=\"-nic user,hostfwd=tcp::2222-:22\" # VM guest network device")
        tcd.log("VM_MEMORY=4096 # Memory allocation for VM (MiB)")
        tcd.log("# default QEMU iommu device")
        tcd.log("qemu_iommu_device=\"-device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode=modern,device-iotlb=on,aw-bits=48\"")
        ##################
        
        
    ## 5
    if tcd.step("Configure mdev work-queues and start virtual machine"):
        # Configure mdev work-queues and start virtual machine
        
        # 1. Configure work-queues.
        # ./Setup_Randomize_DSA_Conf.sh -maM -F1 -w 10
        
        
        # 2. Start VM using launch script created with "Setup_Randomize_DSA_Conf.sh" above.
        # logs/DSA_MDEV-<date-time>/launch_vm.sh
        
        sutos.execute_cmd(sut, f'cd $ACCE_RANDOM_CONFIG_TEST_PATH_L && rm -rf logs/DSA_MDEV-*')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/acce_random_test.py -c \'Setup_Randomize_DSA_Conf.sh -maM -F1 -w 10\' -u \'False\'', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_startvm.py -c "cd $ACCE_RANDOM_CONFIG_TEST_PATH_L/logs/DSA_MDEV-* && bash launch_vm.sh"', timeout=10*60)
        tcd.sleep(5)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Work-queues are configured successfully.")
        tcd.log("# ./Setup_Randomize_DSA_Conf.sh -maM -F1 -w 10")
        tcd.log("Randomly configuring 4 DSA Devices")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Enabling devices:")
        tcd.log("dsa2 dsa4 dsa6 dsa0")
        tcd.log("enabled 4 device(s) out of 4")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Virtual machine boots normally.")
        ##################
        
        
    ## 6
    if tcd.step("In VM"):
        # In VM
        # Check Linux command line.
        # cat /proc/cmdline
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd \'intel_iommu=on,sm_on no5lvl\'"', timeout=10*60)
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$DSA_NAME" -d "$SUT_TOOLS" -p 2222', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum install -y autoconf automake libtool pkgconf rpm-build rpmdevtools" -p 2222', no_check=True, timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum groupinstall -y \'Development Tools\'" -p 2222', no_check=True, timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "yum install -y asciidoc xmlto libuuid-devel json-c-devel" -p 2222', no_check=True, timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "python3 $API_SCRIPT/accel_config_install.py" -p 2222', timeout=20*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Kernel Parameters in guest:")
        tcd.log("intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce")
        ### Notes ###
        # For intel next kernel 5.15 or newer , idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce is no longer needed
        ##################
        
        
    ## 7
    if tcd.step("dsa_test on random work-queues"):
        # dsa_test on random work-queues
        
        
        # 1. Change to PV DSA IAX Test Directory.
        # cd /root/accel-random-config-and-test
        
        
        # 2. Configure work-queues.
        #./Guest_Mdev_Randomize_DSA_Conf.sh -c
        
        
        # 3. Run dsa_test.
        #./Guest_Mdev_Randomize_DSA_Conf.sh -o 0x3
        
        
        # 4. change to log directory.
        # cd logs/DSA_Test-<date-time>
        
        
        # 5. Check each wq log file.
        # less dsa#-wq#.#-<opcode>.log
        
        
        # 6. Verify no errors in dmesg.
        #journalctl --dmesg
        
        
        # 7. Repeat this steps 3-5 changing the "-o" option to available OpCodes:
        # '0x0' '0x2' '0x3' '0x4' '0x5' '0x6' '0x9'
        
        # 8. Disable work-queues
        #./Guest_Mdev_Randomize_DSA_Conf.sh -d
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "python3 $API_SCRIPT/dsa_test.py -s \'Guest_Mdev_Randomize_DSA_Conf.sh\' -m \'random\'"', timeout=30*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("DSA and work queues configured without errors.")
        tcd.log("Script output shows devices enabled.")
        tcd.log("Script output shows wq(s) enabled.")
        tcd.log("#./Guest_Mdev_Randomize_DSA_Conf.sh -c")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Enabling work-queues:")
        tcd.log("dsa0/wq0.0 dsa1/wq1.0 dsa2/wq2.0 dsa3/wq3.0")
        tcd.log("enabled 4 wq(s) out of 4")
        tcd.log("...")
        tcd.log("#./Guest_Mdev_Randomize_DSA_Conf.sh -o 0x3")
        tcd.log("Running dsa_test with # of WQs: 4; opcode: 0x3; transfer size: 4096")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Waiting for tests to finish.")
        tcd.log("...")
        tcd.log("4 of 4 work queues logged completion records")
        tcd.log("Script shows all WQs logged completitions.")
        tcd.log("Each Descriptor in each WQ log file should show a completion value of \"0x0000000000000001\"")
        tcd.log("[debug] compl[0]: 0x0000000000000001")
        tcd.log("No errors found in dmesg.")
        ##################
        
        
    ## 8
    if tcd.step("dsa_test on all available work-queues"):
        # dsa_test on all available work-queues
        
        # 1. Configure work-queues.
        #./Guest_Mdev_Randomize_DSA_Conf.sh -u
        
        
        # 2. Run dsa_test.
        #./Guest_Mdev_Randomize_DSA_Conf.sh -o 0x3
        
        
        # 3. Repeat this step 2 changing the "-o" option to available OpCodes:
        # '0x0' '0x2' '0x3' '0x4' '0x5' '0x6' '0x9'
        
        
        # 5. Verify no errors in dmesg.
        #journalctl --dmesg
        
        
        # 8. Disable work-queues
        #./Guest_Mdev_Randomize_DSA_Conf.sh -d
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "python3 $API_SCRIPT/dsa_test.py -s \'Guest_Mdev_Randomize_DSA_Conf.sh\' -m \'all\'"', timeout=30*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("DSA and work queues configured without errors.")
        tcd.log("Script output shows devices enabled.")
        tcd.log("Script output shows wq(s) enabled.")
        tcd.log("Script shows all WQ pass successfully.")
        tcd.log("#./Guest_Mdev_Randomize_DSA_Conf.sh -u")
        tcd.log("disabled 1 wq(s) out of 1dsa0/wq0.0")
        tcd.log("disabled 1 wq(s) out of 1dsa1/wq1.0")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Enabling work-queues:")
        tcd.log("dsa0/wq0.0 dsa1/wq1.0 dsa2/wq2.0 dsa3/wq3.0")
        tcd.log("enabled 4 wq(s) out of 4")
        tcd.log("# ./Guest_Mdev_Randomize_DSA_Conf.sh -o 0x3")
        tcd.log("Running dsa_test with # of WQs: 4; opcode: 0x3; transfer size: 4096")
        tcd.log("...")
        tcd.log("...")
        tcd.log("Waiting for tests to finish.")
        tcd.log("4 of 4 work queues logged completion records")
        tcd.log("...")
        tcd.log("#./Guest_Mdev_Randomize_DSA_Conf.sh -d")
        tcd.log("disabled 1 wq(s) out of 1dsa0/wq0.0")
        tcd.log("disabled 1 wq(s) out of 1dsa1/wq1.0")
        tcd.log("disabled 1 wq(s) out of 1dsa2/wq2.0")
        tcd.log("disabled 1 wq(s) out of 1dsa3/wq3.0")
        tcd.log("No errors found in dmesg.")
        tcd.log("Work-queues are disabled successfully")
        ##################
        
        
    ## 9
    if tcd.step("Shutdown Guest VM"):
        # Shutdown Guest VM
        # shutdown now
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -p 2222 -c "shutdown now"', no_check=True, timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Guest VM shuts down")
        ##################
        
        
    ## 10
    if tcd.step("Disable work-queues and MDEV devices"):
        # Disable work-queues and MDEV devices
        
        
        # ./Setup_Randomize_DSA_Conf.sh -d
        
        sutos.execute_cmd(sut, f'python3 $API_SCRIPT/acce_random_test.py -c \'./Setup_Randomize_DSA_Conf.sh -d\' -u \'False\'', timeout=10*60)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("All work-queues and DSA devices are disabled")
        tcd.log("Mdev devices are disabled")
        tcd.log("# ./Setup_Randomize_DSA_Conf.sh -d")
        tcd.log("disabled 1 wq(s) out of 1dsa0/wq0.1")
        tcd.log("disabled 1 wq(s) out of 1dsa0/wq0.2")
        tcd.log("disabled 1 wq(s) out of 1dsa0/wq0.3")
        tcd.log("disabled 1 wq(s) out of 1dsa0/wq0.4")
        tcd.log("disabled 1 wq(s) out of 1dsa0/wq0.5")
        tcd.log("disabled 1 wq(s) out of 1dsa0/wq0.6")
        tcd.log("disabled 1 wq(s) out of 1dsa0/wq0.7")
        tcd.log("disabled 1 device(s) out of 1dsa0")
        tcd.log("...")
        tcd.log("...")
        tcd.log("disabled 1 wq(s) out of 1dsa6/wq6.0")
        tcd.log("disabled 1 wq(s) out of 1dsa6/wq6.1")
        tcd.log("disabled 1 wq(s) out of 1dsa6/wq6.2")
        tcd.log("disabled 1 wq(s) out of 1dsa6/wq6.3")
        tcd.log("disabled 1 wq(s) out of 1dsa6/wq6.4")
        tcd.log("disabled 1 wq(s) out of 1dsa6/wq6.5")
        tcd.log("disabled 1 wq(s) out of 1dsa6/wq6.6")
        tcd.log("disabled 1 wq(s) out of 1dsa6/wq6.7")
        tcd.log("disabled 1 device(s) out of 1dsa6")
        ##################
        
        
    ## 11
    if tcd.step("Verify no errors in Host dmesg"):
        # Verify no errors in Host dmesg
        # dmesg
        
        sutos.execute_cmd(sut, f'python3 $API_SCRIPT/dmesg_check.py -i \'QAT: Failed to enable AER, error code -5,ERST: Error Record Serialization Table (ERST) support is initialized.\'', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        sutos.execute_cmd(sut, f'cd /home/ && rm -rf vm*.qcow2 && rm -rf vm*.img', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS && rm -rf vm*.qcow2', timeout=20*60)
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ##################
        tcd.log("### Expected result ###")
        tcd.log("No errors reported.")
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
