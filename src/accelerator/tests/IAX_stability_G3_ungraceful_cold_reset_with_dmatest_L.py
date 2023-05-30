# Tool Version [0.2.13]
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


    # Tool Version [0.2.13]
    #ID/LINK: https://hsdes.intel.com/appstore/article/#/15010635427
    #TITLE: IAX_stability_G3_ungraceful_cold_reset_with_dmatest_L
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
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && find . -type f | xargs dos2unix;')
        sutos.execute_cmd(sut, f'mkdir -p $Accelerator_REMOTE_TOOL_PATH')
        ### Call TCDB accel.path_import End
        
        
        ## Set BIOS knob: VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1
        set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
        if set_cli:
            sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1")
            sutos.reset_cycle_step(sut)
            tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1, InterruptRemap=0x1, PcieEnqCmdSupport=0x1, ProcessorVmxEnable=0x1, ProcessorVmxEnable=0x1"))
        
        
        ## Boot to Linux
        boot_to(sut, sut.default_os)
        tcd.os = "Linux"
        tcd.environment = "OS"
        
        # BIOS Configuration
        # Verify the following BIOS settings.
        # EDKII Menu > Socket Configuration > IIO configuration > PCIe ENQCMD > ENQCMDS = enabled
        # EDKII Menu > Socket Configuraiton > IIO Configuration >IOAT configuration >socket <n> IOAT configure > DSA = enabled
        # Notes: This is only support on SPR, not support GNR
        # EDKII Menu > Socket Configuraiton > IIO Configuration > VT-d = enabled
        # EDKII Menu > Socket Configuration > Processor Configuration > VMX = enabled
        # 2. Install kernel-spr-bkc-pc-modules-internal-6.13-0.el8.x86_64.rpm
        # rpm -ivhF kernel-spr-bkc-pc-modules-internal-6.13-0.el8.x86_64.rpm
        sutos.execute_cmd(sut, f'cd $SUT_TOOLS &&  rpm -ivhF $INTERNAL_MODULE_NAME')
        # 3.Kernel parameters in host:
        # For intel next kernel 5.15 ornewer , 'idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce'  is no longer needed
        # grubby --args="intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce" --update-kernel=/boot/vmlinuz-*.intel_next.*.x86_64+server
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check_and_add --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        
        
    #################################################################
    # Steps Section
    #################################################################
    ## 1
    if tcd.step("Boot to Linux OS."):
        # Boot to Linux OS.
        # Check Linux command line.
        # cat /proc/cmdline
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op check --cmd "intel_iommu=on,sm_on,iova_sl"')
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Kernel parameters include:")
        tcd.log("intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce")
        ##################
        
        
    ## 2
    if tcd.step("Clean dmesg"):
        # Clean dmesg
        # dmesg -C
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        ##################
        
        
    ## 3
    if tcd.step("Check IAX/DSA devices"):
        # Check IAX/DSA devices
        # Execute the following command.
        # accel-config list -i
        
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("accel-config shows the expected number of devices and work-queues.")
        tcd.log("# accel-config list -i")
        tcd.log("[")
        tcd.log("{")
        tcd.log("\"dev\":\"dsa0\",")
        tcd.log("\"token_limit\":0,")
        tcd.log("\"max_groups\":4,")
        tcd.log("\"max_work_queues\":8,")
        tcd.log("\"max_engines\":4,")
        tcd.log("\"work_queue_size\":128,")
        tcd.log("\"numa_node\":0,")
        tcd.log("\"op_cap\":[")
        tcd.log("\"0x1003f03ff\",")
        tcd.log("\"0\",")
        tcd.log("\"0\",")
        tcd.log("\"0\"")
        tcd.log("],")
        tcd.log("\"gen_cap\":\"0x40915f010f\",")
        tcd.log("\"version\":\"0x100\",")
        tcd.log("\"state\":\"disabled\",")
        tcd.log("\"max_tokens\":96,")
        tcd.log("\"max_batch_size\":1024,")
        tcd.log("\"ims_size\":2048,")
        tcd.log("\"max_transfer_size\":2147483648,")
        tcd.log("\"configurable\":1,")
        tcd.log("\"pasid_enabled\":1,")
        tcd.log("\"cdev_major\":236,")
        tcd.log("")
        tcd.log("...")
        tcd.log("...")
        tcd.log("\"threshold\":0,")
        tcd.log("\"ats_disable\":0,")
        tcd.log("\"state\":\"disabled\",")
        tcd.log("\"clients\":0")
        tcd.log("}")
        tcd.log("],")
        tcd.log("\"ungrouped_engines\":[")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.0\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.1\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.2\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.3\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.4\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.5\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.6\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.7\"")
        tcd.log("}")
        tcd.log("]")
        tcd.log("}")
        tcd.log("]")
        ##################
        
        
    ## 4
    if tcd.step("1. Configure IAX device"):
        # 1. Configure IAX device
        # vi configure_iax_device.sh
        # add Script as below
        
        #!/usr/bin/env bash
        # for iax_path in /sys/bus/dsa/devices/iax*
        # do
        # i=${iax_path##*iax}
        # accel-config config-engine iax${i}/engine${i}.0 --group-id=0
        # accel-config config-engine iax${i}/engine${i}.1 --group-id=0
        # accel-config config-wq iax${i}/wq${i}.0 -g 0 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        # accel-config config-wq iax${i}/wq${i}.1 -g 0 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        # accel-config config-wq iax${i}/wq${i}.2 -g 0 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        # accel-config config-wq iax${i}/wq${i}.3 -g 0 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        
        # accel-config config-engine iax${i}/engine${i}.2 --group-id=1
        # accel-config config-engine iax${i}/engine${i}.3 --group-id=1
        # accel-config config-wq iax${i}/wq${i}.4 -g 1 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        # accel-config config-wq iax${i}/wq${i}.5 -g 1 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        # accel-config config-wq iax${i}/wq${i}.6 -g 1 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        # accel-config config-wq iax${i}/wq${i}.7 -g 1 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        
        # Enable Devices
        # accel-config enable-device iax${i}
        # accel-config enable-wq iax${i}/wq${i}.0 iax${i}/wq${i}.1 iax${i}/wq${i}.2 iax${i}/wq${i}.3 iax${i}/wq${i}.4 iax${i}/wq${i}.5 iax${i}/wq${i}.6 iax${i}/wq${i}.7
        
        # done
        
        
        # 2.Run Script
        # chmod 777 configure_iax_device.sh
        # ./configure_iax_device.sh
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Script run successfully")
        tcd.log("# ./configure_iax_device.sh")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        tcd.log("enabled 1 device(s) out of 1")
        tcd.log("enabled 8 wq(s) out of 8")
        ##################
        
        
    ## 5
    if tcd.step("Check IAX config"):
        # Check IAX config
        # accel-config list -i
        ##################
        tcd.log("### Expected result ###")
        tcd.log("#accel-config list -i")
        tcd.log("[")
        tcd.log("{")
        tcd.log("\"dev\":\"dsa0\",")
        tcd.log("\"token_limit\":0,")
        tcd.log("\"max_groups\":4,")
        tcd.log("\"max_work_queues\":8,")
        tcd.log("\"max_engines\":4,")
        tcd.log("\"work_queue_size\":128,")
        tcd.log("\"numa_node\":0,")
        tcd.log("\"op_cap\":[")
        tcd.log("\"0x1003f03ff\",")
        tcd.log("\"0\",")
        tcd.log("\"0\",")
        tcd.log("\"0\"")
        tcd.log("],")
        tcd.log("\"gen_cap\":\"0x40915f010f\",")
        tcd.log("\"version\":\"0x100\",")
        tcd.log("\"state\":\"disabled\",")
        tcd.log("\"max_tokens\":96,")
        tcd.log("\"max_batch_size\":1024,")
        tcd.log("\"ims_size\":2048,")
        tcd.log("\"max_transfer_size\":2147483648,")
        tcd.log("\"configurable\":1,")
        tcd.log("\"pasid_enabled\":1,")
        tcd.log("\"cdev_major\":236,")
        tcd.log("\"clients\":0,")
        tcd.log("...")
        tcd.log("...")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"group9.2\",")
        tcd.log("\"traffic_class_a\":0,")
        tcd.log("\"traffic_class_b\":1")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"group9.3\",")
        tcd.log("\"traffic_class_a\":0,")
        tcd.log("\"traffic_class_b\":1")
        tcd.log("}")
        tcd.log("],")
        tcd.log("\"ungrouped_engines\":[")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.4\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.5\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.6\"")
        tcd.log("},")
        tcd.log("{")
        tcd.log("\"dev\":\"engine9.7\"")
        tcd.log("}")
        tcd.log("]")
        tcd.log("}")
        tcd.log("]")
        ##################
        
        
    ## 6
    if tcd.step("1.Configure dmatest"):
        # 1.Configure dmatest
        # modprobe dmatest
        # modprobe idxd_ktest         ## This step is not needed when kernel is intel next kernel 5.15 or new .
        # echo 2000 > /sys/module/dmatest/parameters/timeout
        # echo 10000 > /sys/module/dmatest/parameters/iterations
        # echo 2 > /sys/module/dmatest/parameters/threads_per_chan
        # echo "" > /sys/module/dmatest/parameters/channel
        
        # 2. Run dmatest
        # echo 1 > /sys/module/dmatest/parameters/run
        
        ##################
        tcd.log("### Expected result ###")
        tcd.log("Work-queue configured successfully.")
        tcd.log("dmatest runs for 10000 iterations without errors.")
        ##################
        
        
    ## 7
    if tcd.step("Check result"):
        # Check result
        #dmesg
        ##################
        tcd.log("### Expected result ###")
        tcd.log("dmesg shows all dmatest iterations passed on each channel and no errors.")
        tcd.log("# dmesg")
        tcd.log("[  596.163897] idxd iax1: Device iax1 enabled")
        tcd.log("[  596.172899] dmaengine wq1.0: wq wq1.0 enabled")
        tcd.log("[  596.178217] dmaengine wq1.1: wq wq1.1 enabled")
        tcd.log("[  596.183577] dmaengine wq1.2: wq wq1.2 enabled")
        tcd.log("...")
        tcd.log("...")
        tcd.log("[  648.883241] dmatest: Added 2 threads using dma0chan0")
        tcd.log("[  648.889106] dmatest: Added 2 threads using dma0chan1")
        tcd.log("[  648.894979] dmatest: Added 2 threads using dma0chan2")
        tcd.log("...")
        tcd.log("...")
        tcd.log("[  656.768869] dmatest: Started 2 threads using dma0chan0")
        tcd.log("[  656.774739] dmatest: Started 2 threads using dma0chan1")
        tcd.log("[  656.780619] dmatest: Started 2 threads using dma0chan2")
        tcd.log("[  656.786480] dmatest: Started 2 threads using dma0chan3")
        tcd.log("...")
        tcd.log("...")
        tcd.log("[  659.305368] dmatest: dma7chan3-direc: summary 10000 tests, 0 failures 14973.75 iops 119593 KB/s (0)")
        tcd.log("[  659.316002] dmatest: dma7chan6-direc: summary 10000 tests, 0 failures 15279.37 iops 122267 KB/s (0)")
        tcd.log("[  659.316101] dmatest: dma7chan5-direc: summary 10000 tests, 0 failures 15191.28 iops 121439 KB/s (0)")
        tcd.log("[  659.323633] dmatest: dma7chan4-direc: summary 10000 tests, 0 failures 14835.64 iops 118867 KB/s (0")
        ##################
        
        
    ## 8
    if tcd.step("Trigger a G3 cycle and repeat steps 2-7 .Please repeat this step 10 times ."):
        # Trigger a G3 cycle and repeat steps 2-7 .Please repeat this step 10 times .
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        
        ### Call TCDB accel.iax_cycle Start
        sutos.execute_cmd(sut, f'dmesg -C')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py -c "accel-config list -i" -m "no_found" -l \'"state":"enabled"\'')
        sutos.execute_cmd(sut, f'\cp $API_SCRIPT/configure_iax_device.sh $Accelerator_REMOTE_TOOL_PATH/configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && chmod 777 configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $Accelerator_REMOTE_TOOL_PATH && ./configure_iax_device.sh')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_config_check.py -a "iax"', timeout=10*60)
        sutos.execute_cmd(sut, f'modprobe dmatest')
        #Execute Command: modprobe idxd_ktest
        sutos.execute_cmd(sut, f'echo 2000 > /sys/module/dmatest/parameters/timeout')
        sutos.execute_cmd(sut, f'echo 10000 > /sys/module/dmatest/parameters/iterations')
        sutos.execute_cmd(sut, f'echo 2 > /sys/module/dmatest/parameters/threads_per_chan')
        sutos.execute_cmd(sut, f'echo "" > /sys/module/dmatest/parameters/channel')
        sutos.execute_cmd(sut, f'echo 1 > /sys/module/dmatest/parameters/run')
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/dmesg_check.py')
        sut.ac_off()
        tcd.sleep(180)
        sut.ac_on()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        ### Call TCDB accel.iax_cycle End
        
        
        
        sutos.execute_cmd(sut, f'cd $API_SCRIPT && python3 $API_SCRIPT/accel_check_kernel_cmd.py --op remove --cmd \'intel_iommu=on,sm_on,iova_sl\'')
        tcd.warm_reset()
        tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
        
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
