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
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15011179216
    #TITLE: DLB_SIOV_Stress_Test_Single_VM_per_device
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
        
        sutos.execute_cmd(sut, f'unzip -o $DPDK_DRIVER_ZIP_NAME', timeout=10*60)
        # 1.Enable SRIOV and VT-D
        # EDKII->Socket Configuration -> IIO Configuration -> Intel  VT For Directed I/O (VT-d) - Intel  VT For Directed I/O Enable
        # EDKII->Platform Configuration -> Miscellaneous Configuration -> SR-IOV Support Enable
        ## Set BIOS knob: VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        # 2.Please Download DLB driver from BKC release and copy it to /root/dlb
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH/dlb')
        sutos.execute_cmd(sut, f'\cp $DLB_DRIVER_NAME $Accelerator_REMOTE_TOOL_PATH/dlb')
        # 3.Please Download dpdk package from https://fast.dpdk.org/rel/ and copy it to /root/dlb
        # Note: The version must match the patch in DLB
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH/dlb/dpdk-main')
        sutos.execute_cmd(sut, f'tar xfJ $DPDK_DRIVER_NAME -C $Accelerator_REMOTE_TOOL_PATH/dlb/dpdk-main')
        # 4.Download 5.15 Kernel rpms to /root/ from BKC releaseKERNEL-PACKAGES-SPR-BKC-PC-6.13-0
        sutos.execute_cmd(sut, f'unzip -o $KERNEL_PKG -d $Accelerator_REMOTE_TOOL_PATH/dlb')
        # 5.VM test need copy OVMF.fd and img files to system.
        # wget https://ubit-artifactory-or.intel.com/artifactory/linuxmvpstacks-or-local/linux-stack-bkc/2022ww17/internal-images/spr-bkc-pc-centos-stream-8-coreserver-5.12.0.img.xz to /home/
        # OVMF file copy to /home/OVMF.fd
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_img_copy.py -d \'dlb\' -s \'1\' -g \'1\' -f $CENTOS_IMG_NAME', timeout=10*60)
        sutos.execute_cmd(sut, f'\cp $OVMF_NAME /home/')
        
        
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
        tcd.log("make -C /lib/modules/`uname -r`/build M=/root/dlb/driver/dlb2 modules")
        tcd.log("make[1]: Entering directory \'/usr/src/kernels/5.15.0-spr.bkc.pc.6.13.0.x86_64\'")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_main.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_file.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_ioctl.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/base/dlb2_resource.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_pf_ops.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_intr.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_dp.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_sriov.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_vf_ops.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_vdcm.o")
        tcd.log("LD [M]  /root/dlb/driver/dlb2/dlb2.o")
        tcd.log("MODPOST /root/dlb/driver/dlb2/Module.symvers")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2.mod.o")
        tcd.log("LD [M]  /root/dlb/driver/dlb2/dlb2.ko")
        tcd.log("BTF [M] /root/dlb/driver/dlb2/dlb2.ko")
        tcd.log("Skipping BTF generation for /root/dlb/driver/dlb2/dlb2.ko due to unavailability of vmlinux")
        tcd.log("make[1]: Leaving directory \'/usr/src/kernels/5.15.0-spr.bkc.pc.6.13.0.x86_64\'")
        ### Notes ###
        # If you are use intel next kernel , please rmmod dlb2 driver first .
        # #rmmod dlb2
        ##################
        
        
    ## 3
    if tcd.step("Install qemu for 5.15 kernel"):
        # Install qemu for 5.15 kernel
        # dnf update --allowerasing --nobest
        # dnf install qemu-kvm -y --allowerasing
        
        sutos.execute_cmd(sut, f'dnf update --allowerasing --nobest -y', timeout=10*60)
        sutos.execute_cmd(sut, f'dnf install qemu-kvm -y --allowerasing', timeout=10*60)
        ##################
        
        
    ## 4
    if tcd.step("Configure resources in DLB:"):
        # Configure resources in DLB:
        # export SYSFS_PATH=/sys/class/dlb2/dlb0/
        # export UUID=`uuidgen`
        # export MDEV_PATH=/sys/bus/mdev/devices/$UUID/dlb2_mdev/
        
        # Create the mdev
        # echo $UUID > $SYSFS_PATH/device/mdev_supported_types/dlb2-dlb/create
        
        # Assign it all of the PF's resources
        # echo 2048 > $MDEV_PATH/num_atomic_inflights
        # echo 96 > $MDEV_PATH/num_dir_ports
        # echo 2048 > $MDEV_PATH/num_hist_list_entries
        # echo 16384 > $MDEV_PATH/num_ldb_credits
        # echo 64 > $MDEV_PATH/num_ldb_ports
        # echo 32 > $MDEV_PATH/num_ldb_queues
        # echo 32 > $MDEV_PATH/num_sched_domains
        # echo 16 > $MDEV_PATH/num_sn0_slots
        # echo 16 > $MDEV_PATH/num_sn1_slots
        
        # Start VM using QEMU:
        # qemu-system-x86_64 -name DLBGuest1 -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 4096 -cpu host -net nic,model=virtio -nic user,hostfwd=tcp::2222-:22 -drive format=raw,file=/home/abhaskar/resources/centos-8.2.2004-embargo-coreserver-202101121459.img -bios /usr/share/qemu/OVMF.fd -device vfio-pci,sysfsdev=/sys/bus/mdev/devices/$UUID -smp 4 -serial mon:stdio
        
        
        sutos.execute_cmd(sut, f'pip3 install setuptools_rust paramiko scp', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/resource_config_login.py -d \'dlb\' -s \'1\' -g \'1\'', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_config.py', timeout=20*60)
        
        ### Notes ###
        # SPR:
        # # echo 4096 > $MDEV_PATH/num_dir_credits
        # # echo 64 > $MDEV_PATH/num_dir_ports
        # # echo 8192 > $MDEV_PATH/num_ldb_credits
        # GNR:
        # # echo 96 > $MDEV_PATH/num_dir_ports
        # # echo 16384 > $MDEV_PATH/num_ldb_credits
        # If kernel is 5.15+, use /usr/libexec/qemu-kvm to replace qemu-system-x86_64
        ##################
        
        
    ## 5
    if tcd.step("Check dlb device in VM"):
        # Check dlb device in VM
        #lspci
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c \'lspci |grep -e 2715 -e 2711\' -m \'keyword\' -l \'Intel Corporation Device\'"')
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("DLB device show as below:")
        tcd.log("07:00.0 Co-processor: Intel Corporation Device 2715")
        ##################
        
        
    ## 6
    if tcd.step("Copy the DLB and DPDK package and kernel rpms inside the VM"):
        # Copy the DLB and DPDK package and kernel rpms inside the VM
        #cd /root
        #mkdir dlb
        # sftp host_ip_address
        # > get /root/dlb/release_ver_7.5.2.zip
        # > get /root/dlb/dpdk-20.11.3.tar.xz
        # > get /root/kernel-packages-spr-bkc-pc-*.zip
        # > bye
        
        # mv release_ver_7.5.2.zip dpdk-20.11.3.tar.xz /root/dlb
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $Accelerator_REMOTE_TOOL_PATH/dlb"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "mkdir -p $SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$DPDK_DRIVER_NAME" -d "$SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$DLB_DRIVER_NAME" -d "$SUT_TOOLS"', timeout=10*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_copy.py -s "$KERNEL_PKG" -d "$SUT_TOOLS"', timeout=10*60)
        ##################
        
        
    ## 7
    if tcd.step("Install dependencies"):
        # Install dependencies
        # unzip kernel-packages-spr-bkc-pc-*.zip
        # rpm -Uvh *.rpm --force --nodeps
        # yum install make gcc
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $SUT_TOOLS && unzip -o kernel-packages-spr-bkc-pc-*.zip -d $Accelerator_REMOTE_TOOL_PATH/dlb"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $Accelerator_REMOTE_TOOL_PATH/dlb && rpm -Uvh *.rpm --force --nodeps"', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $Accelerator_REMOTE_TOOL_PATH/dlb && yum install make gcc -y"', timeout=20*60)
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Dependencies install successfully")
        ##################
        
        
    ## 8
    if tcd.step("Install the DLB driver on VM"):
        # Install the DLB driver on VM
        # Update Kernel and Install required packages.
        # Load DLB driver.
        #cd /root/dlb
        #unzip release_ver_7.5.2.zip
        #cd /root/dlb/driver/dlb2
        #make
        #insmod ./dlb2.ko
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/dlb_install.py -c \'False\'"', timeout=30*60)
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("make -C /lib/modules/`uname -r`/build M=/root/dlb/driver/dlb2 modules")
        tcd.log("make[1]: Entering directory \'/usr/src/kernels/5.15.0-spr.bkc.pc.6.13.0.x86_64\'")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_main.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_file.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_ioctl.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/base/dlb2_resource.o")
        tcd.log("CC [M]  /root/dlb/driver/dlb2/dlb2_pf_ops.o")
        tcd.log("...")
        tcd.log("...")
        tcd.log("make[1]: Leaving directory \'/usr/src/kernels/5.15.0-spr.bkc.pc.6.13.0.x86_64\'")
        ### Notes ###
        # If you are use intel next kernel , please rmmod dlb2 driver first .
        # #rmmod dlb2
        ##################
        
        
    ## 9
    if tcd.step("Inside VM:"):
        # Inside VM:
        # Down DPDK package, apply the addon patch and build DPDK.
        # cd /root/dlb
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
        
        
    ## 10
    if tcd.step("Inside VM - DPDK test app Run:"):
        # Inside VM - DPDK test app Run:
        # mkdir -p /mnt/hugepages
        # mount -t hugetlbfs nodev /mnt/hugepages
        # echo 2048 > /proc/sys/vm/nr_hugepages
        # cd $DPDK_DIR/builddir/app
        # ./dpdk-test-eventdev -c 0xf --vdev=dlb2_event -- --test=order_queue --plcores=1 --wlcore=2,3 --nb_flows=64
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/vm_execute.py -c "cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c \'cd $DPDK_DRIVER_PATH_L/dpdk-*/builddir/app &&  ./dpdk-test-eventdev -c 0xf --vdev=dlb2_event -- --test=order_queue --plcores=1 --wlcore=2,3 --nb_flows=64\' -m \'keyword\' -l \'Success\'"', timeout=30*60)
        
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("# ./dpdk-test-eventdev -c 0xf --vdev=dlb2_event -- --test=order_queue --plcores=1 --wlcore=2,3 --nb_flows=64")
        tcd.log("EAL: Detected 112 lcore(s)")
        tcd.log("EAL: Detected 2 NUMA nodes")
        tcd.log("EAL: Detected static linkage of DPDK")
        tcd.log("EAL: Multi-process socket /var/run/dpdk/rte/mp_socket")
        tcd.log("EAL: Selected IOVA mode \'VA\'")
        tcd.log("EAL: No available hugepages reported in hugepages-1048576kB")
        tcd.log("EAL: Probing VFIO support...")
        tcd.log("EAL: VFIO support initialized")
        tcd.log("EAL: DPDK is running on a NUMA system, but is compiled without NUMA support.")
        tcd.log("EAL: This will have adverse consequences for performance and usability.")
        tcd.log("EAL: Please use --legacy-mem option, or recompile with NUMA support.")
        tcd.log("PMD: Initialising DLB2 dlb2_event on NUMA node 0")
        tcd.log("EAL: No legacy callbacks, legacy socket not created")
        tcd.log("driver : dlb2_event")
        tcd.log("test : order_queue")
        tcd.log("dev : 0")
        tcd.log("verbose_level : 1")
        tcd.log("socket_id : -1")
        tcd.log("pool_sz : 16384")
        tcd.log("main lcore : 0")
        tcd.log("nb_pkts : 67108864")
        tcd.log("nb_timers : 100000000")
        tcd.log("available lcores : {0 1 2 3}")
        tcd.log("nb_flows : 64")
        tcd.log("worker deq depth : 16")
        tcd.log("producer lcores : {1}")
        tcd.log("nb_wrker_lcores : 2")
        tcd.log("worker lcores : {2 3}")
        tcd.log("nb_evdev_ports : 3")
        tcd.log("nb_evdev_queues : 2")
        tcd.log("Result: Success")
        ##################
        
        
    ## 11
    if tcd.step("11"):
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on iommu=on\'')
        sutos.execute_cmd(sut, f'cd /home/ && rm -rf vm*.qcow2 && rm -rf vm*.img', timeout=20*60)
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS && rm -rf vm*.qcow2', timeout=20*60)
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        # Repeat the steps from 4 to 8 steps to create one VM forevery  DLB devices. Please launch VMs and run test parallelly
        ##################
        tcd.log("### Expected result ###")
        tcd.log("test succeed")
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
