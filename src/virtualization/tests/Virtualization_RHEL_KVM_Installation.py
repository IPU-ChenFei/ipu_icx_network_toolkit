from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "The system checks use of all supported Pagetable sizes"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    boot_to(sut, sut.default_os)
    Case.step('systemctl status libvirtd')
    code, out, err = sut.execute_shell_cmd('systemctl status libvirtd')
    Case.expect("systemctl status libvirtd successfully and returns a zero return code ", err == "")

    Case.step('systemctl start libvirtd')
    code, out, err = sut.execute_shell_cmd('systemctl start libvirtd')
    Case.expect("systemctl start libvirtd successfully and returns a zero return code", err == "")

    Case.step('systemctl enable libvirtd')
    code, out, err = sut.execute_shell_cmd('systemctl enable libvirtd')
    Case.expect("systemctl enable libvirtd successfully and returns a zero return code", err == "")

    Case.step('virt-install')
    code, out, err = sut.execute_shell_cmd('yum -y install qemu-kvm virt-install virt-manager')
    Case.expect("virt-install successfully", err == "")

    Case.step('check kvm_intel module in order to ensure is loaded by the kernel')
    code, out, err = sut.execute_shell_cmd('lsmod | grep kvm')
    Case.expect("successfully", err == "")


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
