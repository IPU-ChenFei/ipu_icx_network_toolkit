from src.virtualization.lib.const import *
from src.virtualization.lib.virtualization import get_vmmanger

class Precondition:
    def __init__(self, precond_info):
        self.name = precond_info["name"]
        self.support_auto_setup = precond_info["auto_setup"]
        self.main_type = precond_info["type"]
        self.sub_type = precond_info["subtype"] if "subtype" in precond_info else None
        self.keyword = precond_info["keyword"] if "keyword" in precond_info else None
        self.needed_number = precond_info["number"] if "number" in precond_info else 1
        self.host = precond_info["host"] if "host" in precond_info else False


class PrecondChecker:
    def __init__(self, sut):
        self.sut = sut
        self.vmm = get_vmmanger(sut)

    def __check_preconditions(self, *precond_info_list):
        preconditions = []
        for precond_info in precond_info_list:
            preconditions.append(Precondition(precond_info))

        unsatisfied = []
        for precond in preconditions:
            logger.info(f"checking precondition [{precond.name}] ................")
            if not self.check_precond(precond):
                unsatisfied.append(precond)

        return unsatisfied

    def check_preconditions(self, *precond_info_list):
        unsatisfied = self.__check_preconditions(*precond_info_list)
        if len(unsatisfied) == 0:
            logger.info("all precondition have been satisfied")
            return

        name_list = [precond.name for precond in unsatisfied]
        err_msg = f"error: precondition [{', '.join(name_list)}] not satisfied, fix them please\n"
        for precond in unsatisfied:
            err_msg += f"\t{precond.main_type}: {precond.name} is not "
            if precond.main_type == PRECOND_MAIN_TYPE_FILE:
                err_msg += "existed in HOST:" if precond.host else "existed in SUT:"
                err_msg += f"{sut_tool(precond.keyword)}\n"
            else:
                err_msg += "satisfied\n"
        raise Exception(err_msg)

    def check_preconditions_setup(self, *precond_info_list):
        unsatisfied = self.__check_preconditions(*precond_info_list)
        if len(unsatisfied) == 0:
            logger.info("all precondition have been satisfied")
            return

        unsupported = []
        name_list = [precond.name for precond in unsatisfied]
        logger.info(f"precondition [{', '.join(name_list)}] not satisfied, try to setup them")
        for precond in unsatisfied:
            logger.info(f"try to setup {precond.name}...")
            if not precond.support_auto_setup:
                unsupported.append(precond)
            self.setup_precond(precond)
        if len(unsupported) > 0:
            name_list = [precond.name for precond in unsupported]
            raise Exception(f"error: preconditions [{', '.join(name_list)}] cannot setup automatically, "
                            f"fix them by manual please")

    def check_device(self, precond):
        # type: (Precondition) -> bool
        raise NotImplemented

    def check_file(self, precond):
        # type: (Precondition) -> bool
        raise NotImplemented

    def check_precond(self, precond):
        # type: (Precondition) -> bool
        if precond.main_type == PRECOND_MAIN_TYPE_VM:
            return self.vmm.is_vm_exist(precond.name)
        elif precond.main_type == PRECOND_MAIN_TYPE_DEV:
            return self.check_device(precond)
        elif precond.main_type == PRECOND_MAIN_TYPE_SWITCH:
            cmd = f"Get-VMSwitch | Where-Object{{$_.Name -eq '{precond.name}'}}"
            out = self.sut.execute_shell_cmd(cmd, powershell=True)[1]
            return out.strip() != ""
        elif precond.main_type == PRECOND_MAIN_TYPE_BRIDGE:
            cmd = "ifconfig br0"
            out = self.sut.execute_shell_cmd(cmd)[1]
            return "Device not found" not in out
        elif precond.main_type == PRECOND_MAIN_TYPE_FILE:
            return self.check_file(precond)

    def setup_precond(self, precond):
        if precond.main_type == PRECOND_MAIN_TYPE_VM:
            self.setup_vm_precond(precond)
        elif precond.main_type == PRECOND_MAIN_TYPE_SWITCH:
            self.vmm.create_switch(precond.name)
        elif precond.main_type == PRECOND_MAIN_TYPE_BRIDGE:
            self.setup_virtual_bridge(precond)
        else:
            raise Exception(f"error: precondition [{precond.name}] cannot setup automatically, "
                            "setup it by manual please")

    def setup_virtual_bridge(self, precond):
        raise NotImplemented

    def setup_vm_precond(self, precond):
        raise NotImplemented


class LinuxPrecondChecker(PrecondChecker):
    def __init__(self, sut):
        super().__init__(sut)

    def check_device(self, precond):
        # type: (Precondition) -> bool
        if precond.name == "U-Disk":
            cmd = f"lsusb | grep -i {precond.keyword}"
        else:
            cmd = f"lspci | grep -i {precond.keyword}"
        std_out = self.sut.execute_shell_cmd(cmd)[1]
        return std_out.strip() != ""

    def setup_vm_precond(self, precond):
        vm_template = KVM_RHEL_TEMPLATE if "rhel" in precond.name else KVM_WINDOWS_TEMPLATE
        self.vmm.create_vm_from_template(precond.name, vm_template)

    def check_file(self, precond):
        # type: (Precondition) -> bool
        std_out = self.sut.execute_shell_cmd(f"ls {sut_tool(precond.keyword)}")[1]
        return std_out.strip() != ""


class WindowsPrecondChecker(PrecondChecker):
    def __init__(self, sut):
        super().__init__(sut)

    def check_device(self, precond):
        # type: (Precondition) -> bool
        if precond.sub_type == PRECOND_SUB_TYPE_NIC:
            cmd = f"Get-NetAdapter | select InterfaceDescription | findstr {precond.keyword}"
            std_out = self.sut.execute_shell_cmd(cmd, powershell=True)[1]
            return std_out.strip() != ""
        elif precond.sub_type == PRECOND_SUB_TYPE_DISK:
            return self.__check_disk(precond)
        else:
            raise Exception(f"error: unsupported device type {precond.sub_type}")

    def __check_disk(self, precond):
        # type: (Precondition) -> bool
        cmd = f"wmic diskdrive get /value | findstr PNPDeviceID"
        dev_id_list = self.sut.execute_shell_cmd(cmd)[1].splitlines()
        cmd = f"wmic diskdrive get /value | findstr Partitions"
        partition_list = self.sut.execute_shell_cmd(cmd)[1].splitlines()

        disk_list = []
        for i in range(len(dev_id_list)):
            if precond.keyword in dev_id_list[i] and int(partition_list[i].strip().split("=")[-1]) < 3:
                disk_list.append(dev_id_list[i])

        return len(disk_list) >= precond.needed_number

    def check_file(self, precond):
        # type: (Precondition) -> bool
        cmd = f"Test-Path {sut_tool(precond.keyword)}"
        res = self.sut.execute_shell_cmd(cmd, powershell=True)[1]
        return res.strip() == "True"

    def setup_vm_precond(self, precond):
        vm_template = HYPERV_RHEL_TEMPLATE if "rhel" in precond.name else HYPERV_WINDOWS_TEMPLATE
        self.vmm.create_vm_from_template(precond.name, vm_template)


class VMwarePrecondChecker(PrecondChecker):
    def __init__(self, sut):
        super().__init__(sut)

    def check_device(self, precond):
        # type: (Precondition) -> bool
        if precond.name == "U-Disk":
            cmd = f"lsusb | grep -i {precond.keyword}"
        else:
            cmd = f"lspci | grep -i {precond.keyword}"
        std_out = self.sut.execute_shell_cmd(cmd)[1]
        return std_out.strip() != ""

    def setup_vm_precond(self, precond):
        if "rhel" in precond.name:
            self.check_precond(PrecondInfo.RHEL_TEMPLATE_V)
            vm_template = ESXI_RHEL_TEMPLATE
        elif "win" in precond.name:
            self.check_precond(PrecondInfo.WINDOWS_TEMPLATE_V)
            vm_template = ESXI_WINDOWS_TEMPLATE
        else:
            self.check_precond(PrecondInfo.CENTOS_TEMPLATE_V)
            vm_template = ESXI_CENTOS_TEMPLATE
        self.vmm.create_vm_from_template(precond.name, vm_template)

    def check_file(self, precond):
        # type: (Precondition) -> bool
        if not precond.host:
            std_out = self.sut.execute_shell_cmd(f"ls {sut_tool(precond.keyword)}")[1]
            return std_out.strip() != ""
        else:
            std_out = self.sut.execute_host_cmd(f"Test-Path {sut_tool(precond.keyword)}", powershell=True)[1]
            return std_out.strip() == "True"


def get_precond_checker(sut):
    # type: (SUT) -> PrecondChecker
    precond_checker_list = {
        SUT_STATUS.S0.LINUX: LinuxPrecondChecker,
        SUT_STATUS.S0.WINDOWS: WindowsPrecondChecker,
        SUT_STATUS.S0.VMWARE: VMwarePrecondChecker,
    }
    return precond_checker_list[OS.get_os_family(sut.default_os)](sut)

class SwitchPrecondition(BasePrecondition):
    def __init__(self, sut, name, setup=False) -> None:
        super().__init__(sut, name, setup)
        self.vmm = get_vmmanger(sut)

    def check_win(self):
        cmd = f"Get-VMSwitch | Where-Object{{$_.Name -eq '{self.name}'}}"
        out = self.execute_sut_ps_cmd(cmd)[1]
        return out.strip() != ""

    def setup_common(self):
        self.vmm.create_switch(self.name)


class BridgePrecondition(BasePrecondition):
    def __init__(self, sut, name, setup=False) -> None:
        super().__init__(sut, name, setup)

    def check_win(self):
        raise NotADirectoryError('No bridge checker for Windows SUT.')

    def check_common(self):
        cmd = "ifconfig br0"
        out = self.execute_sut_cmd(cmd)[1]
        return "Device not found" not in out


class VirtualMachinePrecondition(BasePrecondition):
    def __init__(self, sut, name, setup=False) -> None:
        super().__init__(sut, name, setup)
        self.vmm = get_vmmanger(sut)

    def check_common(self):
        return self.vmm.is_vm_exist(self.name)

    def setup_linux(self):
        vm_template = KVM_RHEL_TEMPLATE if "rhel" in self.name else KVM_WINDOWS_TEMPLATE
        self.vmm.create_vm_from_template(self.name, vm_template)

    def setup_win(self):
        vm_template = HYPERV_RHEL_TEMPLATE if "rhel" in self.name else HYPERV_WINDOWS_TEMPLATE
        self.vmm.create_vm_from_template(self.name, vm_template)

    def setup_vmware(self):
        vm_template = None
        if "rhel" in self.name:
            vpre = FilePrecondition(self.sut, 'rhel0.ovf', sut_tool('VT_RHEL_TEMPLATE_H'))
            if vpre.check():
                vm_template = ESXI_RHEL_TEMPLATE
            else:
                logger.error(vpre.error_message())
        elif "win" in self.name:
            vpre = FilePrecondition(self.sut, 'windows0.ovf', sut_tool('VT_WINDOWS_TEMPLATE_H'))
            if vpre.check():
                vm_template = ESXI_WINDOWS_TEMPLATE
            else:
                logger.error(vpre.error_message())
        else:
            vpre = FilePrecondition(self.sut, 'centos0.ovf', sut_tool('VT_CENTOS_TEMPLATE_H'))
            if vpre.check():
                vm_template = ESXI_CENTOS_TEMPLATE
            else:
                logger.error(vpre.error_message())

        if vm_template is not None:
            self.vmm.create_vm_from_template(self.name, vm_template)
