import os

from dtaf_core.lib.tklib.basic.const import SUT_STATUS
from dtaf_core.lib.tklib.basic.log import *
from dtaf_core.lib.tklib.basic.testcase import Case
from dtaf_core.lib.tklib.infra.sut import get_default_sut
#from dtaf_core.lib.tklib._outof_band_sut import SUT
from dtaf_core.lib.tklib.steps_lib.os_scene import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to



SILENT_CONTINUE = "$progressPreference = 'silentlyContinue'"
ENABLE_HYPER_V_CMD = "powershell.exe {}; Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V" \
                     " -All -NoRestart".format(SILENT_CONTINUE)
INSTALL_HYPER_V_MODULES = "powershell.exe {}; Install-WindowsFeature -Name RSAT-Hyper-V-Tools". \
    format(SILENT_CONTINUE)
GET_HYPER_V_INSTALLED_CMD = "powershell.exe Get-Command *-VM"

vm_sut_win_path = "C:\\auto_poc\\src\\vm_sut_w.py"


def vm_setup(sut, test_file="", my_os=None):
    """
    Install and enable needed vm tools onto the sut according to sut's os
    """

    logger.info("Enable vm required tools")

    # install WIN vm
    if sut.default_os == SUT_STATUS.S0.WINDOWS:
        cwd = os.path.dirname(__file__)
        file = os.path.join(cwd, 'vm_sut_w.py')
        sut.upload_to_remote(file, 'C:\\BKCPkg\\domains\\network\\')

        ret, out, err = sut.execute_shell_cmd(ENABLE_HYPER_V_CMD, timeout=60)
        logger.debug("Hyper-V enabled: {}".format(out))

        if not _is_hyperV_installed(sut):
            logger.info("installing Hyper-V")
            ret, out, err = sut.execute_shell_cmd(INSTALL_HYPER_V_MODULES, timeout=60)
        if "True" not in out:
            raise RuntimeError("Install Hyper-V failed")
        # Reboot the sut system to meet the Hyper-V requirement
        my_os.reset_cycle_step(sut)

    # install Red Hat vm
    else:
        logger.info("installing vm dependencies for RHEL")
        _yum_install(sut, "libvrt")
        _yum_install(sut, "virt-install")
        _yum_remove(sut, "virt-viewer")

        logger.info("installing kvm dependencies for RHEL")
        _yum_install(sut, "qemu-kvm virt-install virt-manager")
        _yum_install(sut, "@virt")
        sut.execute_shell_cmd("systemctl start libvirtd")
        sut.execute_shell_cmd("systemctl enable libvirtd")

        _set_ssh_config(sut)
        # Transmit script & xml template
        cwd = os.path.dirname(__file__)
        if test_file == "":
            file = os.path.join(cwd, 'vm_sut_l.py')
            sut.upload_to_remote(file, "/home/BKCPkg/domains/network/")
        elif test_file == 'ixvss':
            file = os.path.join(cwd, 'vm_sut_ixvss_l.py')
            sut.upload_to_remote(file, "/home/BKCPkg/domains/network/")
        elif test_file == 'fio':
            file = os.path.join(cwd, 'vm_sut_fio_l.py')
            sut.upload_to_remote(file, "/home/BKCPkg/domains/network/")
        file = os.path.join(cwd, 'pci_device.xml')
        sut.upload_to_remote(file, "/home/BKCPkg/domains/network")


def _is_hyperV_installed(sut):
    # type: (SUT) -> bool

    logger.info("See if Hyper-V is installed")
    ret, out, err = sut.execute_shell_cmd(GET_HYPER_V_INSTALLED_CMD)

    if "New-VM" not in out:
        logger.error("Hyper-V is not installed")
        return False
    return True


def _yum_install(sut, pkg_name, group_install=False):
    cmd = "yum list installed {}".format(pkg_name)
    ret, out, err = sut.execute_shell_cmd(cmd)
    if str(pkg_name).lower() in str(out).lower():
        logger.info("package {} already installed!".format(pkg_name))
        return

    # importing rpm key
    sut.execute_shell_cmd("rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY*")
    try:
        if not group_install:
            ret, out, err = sut.execute_shell_cmd("yum -y install {}".format(pkg_name))
        else:
            ret, out, err = sut.execute_shell_cmd("yum -y groupinstall {}".format(pkg_name))
        logger.debug("yum execution result: {}".format(out))
    except Exception as ex:
        logger.error(ex)
    logger.info("{} installed successfully".format(pkg_name))


def _yum_remove(sut, pkg_name):
    logger.info("Uninstalling {}".format(pkg_name))
    ret, out, err = sut.execute_shell_cmd("yum -y remove {}".format(pkg_name))

    if ret == 0:
        logger.debug(out)
        logger.info("Uninstalling {} succeed")
    else:
        logger.error(err)


def _set_ssh_config(sut):
    # config ssh to ignore asking for authentication
    logger.info("Setting ssh option so no authentication required when using ssh")
    ret, _, err = sut.execute_shell_cmd("sed -i 's\\#   StrictHostKeyChecking ask\\   StrictHostKeyChecking no\\g' "
                                        "/etc/ssh/ssh_config")
    if ret != 0:
        raise RuntimeError(err)
    logger.info("Updated sut ssh config")

# if __name__ == "__main__":
#     sut = get_default_sut()
#
#     vm_setup(sut)
