# Tool Version [0.2.11]
CASE_DESC = [
    "it is a python script generated from validation language"
]

from src.lib.toolkit.steps_lib.vl.vltcd import *
from plat_feature_config import *


def test_steps(tcd):
    sut = tcd.sut
    sutos = tcd.sut.sutos
    assert (issubclass(sutos, GenericOS))
    hostos = tcd.hostos
    tools = get_tool(tcd.sut)
    bmc = get_bmc_info(sut)

    if tcd.prepare("boot to OS"):
        boot_to(sut, sut.default_os)


    # Tool Version [0.2.11]
    ## Set BIOS knob: ProcessorVmxEnable=0x1
    set_cli = not sut.xmlcli_os.check_bios_knobs("ProcessorVmxEnable=0x1")
    if set_cli:
        sut.xmlcli_os.set_bios_knobs("ProcessorVmxEnable=0x1")
        sutos.reset_cycle_step(sut)
        tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("ProcessorVmxEnable=0x1"))
    
    ## Set BIOS knob: VTdSupport=0x1
    set_cli = not sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1")
    if set_cli:
        sut.xmlcli_os.set_bios_knobs("VTdSupport=0x1")
        sutos.reset_cycle_step(sut)
        tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("VTdSupport=0x1"))
    
    ## Set BIOS knob: InterruptRemap=0x1
    set_cli = not sut.xmlcli_os.check_bios_knobs("InterruptRemap=0x1")
    if set_cli:
        sut.xmlcli_os.set_bios_knobs("InterruptRemap=0x1")
        sutos.reset_cycle_step(sut)
        tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("InterruptRemap=0x1"))
    
    ## Set BIOS knob: SRIOVEnable=0x1
    set_cli = not sut.xmlcli_os.check_bios_knobs("SRIOVEnable=0x1")
    if set_cli:
        sut.xmlcli_os.set_bios_knobs("SRIOVEnable=0x1")
        sutos.reset_cycle_step(sut)
        tcd.expect("double check bios knobs", sut.xmlcli_os.check_bios_knobs("SRIOVEnable=0x1"))
    
    
    ## Boot to Linux
    tcd.os = "Linux"
    tcd.environment = "OS"
    
    tcd.wait_and_expect("wait for entering OS ", timeout=60*60,function=sut.check_system_in_os)
    sutos.execute_cmd(sut, f'python /home/BKCPkg/domains/virtualization/virtualization_inband/lnx_exec_with_check.py -c \'cat /proc/cpuinfo | egrep address\' -m \'kv\' -l \'address sizes,57 bits virtual\'')
    


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
