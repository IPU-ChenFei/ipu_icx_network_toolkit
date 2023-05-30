from src.power_management.lib.tkinit import *

CASE_DESC = [
    "To verify the platform stability with the system S5 States on VMWARE - SLOW COLD"
]


def test_steps(sut, my_os):
    Case.prepare('boot to OS & launch itp')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute('unlock()')

    Case.step(" Disable AttemptFastBoot and AttemptFastBootCold (Through XmlCli)")
    itp.execute("knobs = 'AttemptFastBoot=0x0,AttemptFastBootCold=0x0'")
    itp.execute("import pysvtools.xmlcli.XmlCli as cli")
    itp.execute("cli.clb.AuthenticateXmlCliApis = True")
    ret = itp.execute("cli.CvProgKnobs(knobs)")
    Case.expect('successful', 'Verify Passed' in ret)

    Case.step('restart')
    my_os.warm_reset_cycle_step(sut)

    write_reg_value = '0x0000cafe'

    for i in range(1, 3):
        Case.step(f'Write to sticky and non sticky registers through ITP-{i}')
        itp.execute(f"{pysv_reg('biosscratchpad6_cfg')} = {write_reg_value}")
        itp.execute(f"{pysv_reg('biosnonstickyscratchpad6_cfg')} = {write_reg_value}")
        Case.sleep(5)

        Case.step('shutdown')
        my_os.shutdown(sut)
        # itp.execute("sv.socket0.io0.uncore.s3m.uarch.s3m_acpi_pm.evt_sts.show()")
        Case.expect('system status is S5', sut.wait_for_power_status(SUT_STATUS.S5, 60))

        Case.step(f"Boot back to OS (vmware)- {i}")
        itp.execute("itp.pulsehook(0,1,True,25000000)")
        Case.wait_and_expect('system back to OS', 10 * 60, sut.check_system_in_os)

        Case.step(f'Check the BIOS log-{i}')
        bios_log_path = sut.get_bios_log()
        knob_line_in_bios_log = find_lines('subBootMode = ColdBoot', bios_log_path)[-1]
        Case.expect('knob in bios log is as expect', knob_line_in_bios_log == 'subBootMode = ColdBoot')

        Case.step(f"Check Sticky and non-sticky registers-{i}")
        itp.execute("sv.refresh()")
        ret1 = itp.execute(f"{pysv_reg('biosscratchpad6_cfg')}.show()")
        ret2 = itp.execute(f"{pysv_reg('biosnonstickyscratchpad6_cfg')}.show()")
        sticky_reg_ret = re.findall(r'0x\w+', ret1)
        non_sticky_reg_ret = re.findall(r'0x\w+', ret2)
        for reg_value in sticky_reg_ret:
            Case.expect('check sticky register right', reg_value != write_reg_value)
        for reg_value in non_sticky_reg_ret:
            Case.expect('check non-sticky register right', reg_value != write_reg_value)

        Case.step(f'Check Punit MC status-{i}')
        check_punit_mc_status(sut, itp)

    Case.step("exit itp link")
    itp.exit()


def clean_up(sut):
    if Result.returncode != 0:
        cleanup.to_s5(sut)


def test_main():

    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
