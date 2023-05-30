#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import six
import os
import time

from retry import retry
from abc import ABCMeta
from typing import Tuple

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.exceptions import OsCommandTimeoutException, OsCommandException

from src.security.tests.tdx.tdx_common import TdxBaseTest
from src.lib import content_exceptions


@six.add_metaclass(ABCMeta)
class LinuxTdxBaseTest(TdxBaseTest):
    """Base class extension for TDX which holds common arguments, functions."""

    # TODO: has to be a better way to do this....
    _BIOS_CONFIG_FILE_TDX_ENABLE = "collateral/tdx_en_linux_reference_knobs.cfg"
    _TDVM_LINUX_RUN_SCRIPT = "collateral/run-vm.sh"
    _EXPECT_LINUX_SCRIPT = "collateral/ssh_vm_expect.sh"
    _VM_CONFIG_FILE = "collateral/vm_configs"
    _PROXY_SCRIPT = "collateral/proxy.sh"

    def __init__(self, test_log, arguments, cfg_opts):
        """Create an instance of LinuxTdxBaseTest

        :param cfg_opts: Configuration Object of provider
        :type cfg_opts: str
        :param test_log: Log object
        :type arguments: Namespace
        :param arguments: None
        :type cfg_opts: Namespace
        :return: None
        """
        super(LinuxTdxBaseTest, self).__init__(test_log, arguments, cfg_opts)

        if self.sut_os != OperatingSystems.LINUX:
            raise content_exceptions.TestSetupError("Cannot run Linux test on {} OS.".format(self.sut_os))

        # TODO: has to be a better way to do this....
        self.tdx_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            self._BIOS_CONFIG_FILE_TDX_ENABLE)
        try:
            intel_next = self.tdx_properties[self.tdx_consts.INTEL_NEXT]
            self._log.warning("Intel Next is used by default and legacy MVP stack launch scripts are no longer "
                              "supported. Intel Next setting in content_configuration.xml file will be ignored.")
        except KeyError:
            pass
        self.run_linux_td_guest_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    self._TDVM_LINUX_RUN_SCRIPT)
        self.expect_linux_script_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     self._EXPECT_LINUX_SCRIPT)
        self.vm_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._VM_CONFIG_FILE)
        self.proxy_environment_variable_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            self._PROXY_SCRIPT)

        self.TDVM_OSes = self.tdx_consts.TDVMOS
        self.tdvms = []  # list of TDVMs and properties

    def seam_install_check(self) -> None:
        """Verify SUT has TDX seam package installed."""
        try:
            if self.tdx_properties[self.tdx_consts.BIOS_SEAM_ENABLE]:
                self._log.debug("BIOS SEAMLDR will be used, skipping OS SEAM check.")
                return
        except KeyError:
            self._log.warning("Could not determine if BIOS SEAMLDR is expected to be used... will install OS SEAM "
                              "just to be safe.")
        if not self.os.check_if_path_exists(self.tdx_consts.LibSeamLoaderFiles.SEAM_FW_PATH, directory=True):  # check if SEAM files exist in OS
            self._log.debug(f"SEAM modules not found in {self.tdx_consts.SEAM_FW_PATH}; installing SEAM module "
                            f"package.")
            self.execute_os_cmd(f"mkdir -p {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}")
            self.install_collateral.yum_install("tdx-seam-module")

    def os_preparation(self):
        """Following checks:
        1. Get BIOS version.
        2. Set the date.
        3. Set proxy.
        4. Verify python3 is installed and softlink is in place.
        5. Clear all old OS logs.
        6. Remove known hosts file to avoid SSH issues with new VM copies.
        7. Install prereq Linux packages.
        8. Verify SEAM is installed in the OS if the BIOS SEAM loader is not enabled."""
        self.check_console_kernel_boot_param()
        self._log.debug("BIOS version on platform: {}".format(self.execute_os_cmd(
            self.tdx_consts.DMIDECODE_GET_BIOS_VERSION)))
        # set the date
        self._common_content_lib.set_datetime_on_linux_sut()  # set time in OS
        self.execute_os_cmd("hwclock --systohc")  # sync hardware clock
        # copy proxy file over
        self.os.copy_local_file_to_sut(self.proxy_environment_variable_file, "/etc/profile.d/")
        # check if softlink exists, if it does not, install and set the softlink
        if self.execute_os_cmd("python --version") == "":
            # python 3 is not installed or the softlink is missing
            self.install_collateral.yum_install("python38")
            self.execute_os_cmd("ln -s -f /usr/bin/python3.8 /usr/bin/python")
            if self.execute_os_cmd("python --version") == "":
                raise content_exceptions.TestSetupError("Could not install Python3, please verify SUT networking is "
                                                        "set up.")
        # erase all old system logs
        self._log.debug("Deleting preexisting system log files.")
        self.execute_os_cmd("rm -rf /var/log/*")
        # remove known hosts file; any previous known_hosts file will have conflicting entries with previous VM copies
        self._log.debug("Removing known_hosts file.")
        self.execute_os_cmd("rm -f ~/.ssh/known_hosts")
        self._log.debug("Verifying necessary packages are installed: {}.".format(self.tdx_consts.YUM_REQUIRED_PACKAGES))
        try:
            self.install_collateral.yum_install(self.tdx_consts.YUM_REQUIRED_PACKAGES)
        except content_exceptions.TestSetupError:
            raise content_exceptions.TestSetupError("Failed to set up required packages from yum.  Please verify that "
                                                    "the SUT is connected to network and proxy information (if needed) "
                                                    "is correct.")

        try:
            self._log.debug("Installing optional tools epel-release and msr-tools.")
            self.install_collateral.yum_install("epel-release")
            self.install_collateral.yum_install(self.tdx_consts.YUM_OPTIONAL_PACKAGES)
        except content_exceptions.TestSetupError:
            self._log.warning("Failed to set up epel and/or msr-tools, will use ITP to read MSR instead.  This can "
                              "cause OS instability (kernel panic) for Linux OS and is NOT recommended.")
        self.seam_install_check()
        self._log.info("Checking for TD guest and log directories.")
        for path in [self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_DIR], self.tdx_consts.TD_GUEST_LOG_PATH_LINUX,
                     self.tdx_consts.TDX_HOME_DIR]:
            if not self.os.check_if_path_exists(path, directory=True):
                self.execute_os_cmd(f"mkdir -p {path}")
        self.auto_root_login()
        self.install_collateral.screen_package_installation()

    def check_console_kernel_boot_param(self):
        """
        Verify console params are provided to kernel boot.
        """
        # add console log and tdx_host params to kernel boot
        os_kernel = self._grub_obj.get_current_kernel_version().strip()
        self._log.debug(f"OS using kernel version {os_kernel}")
        for argument in self.tdx_consts.TDX_HOST_KERNEL_ARGS:
            self._log.debug(f"Attempting to add arg {argument} to kernel {os_kernel} boot. ")
            self._grub_obj.add_kernel_args(argument, os_kernel)

    def prepare(self):
        self.os_preparation()
        if self.tdx_properties[self.tdx_consts.AC_RESET]:
            self._log.warning("Using AC cycle to reboot SUT instead of graceful reboot from OS.")
        try:
            seamldr = self.tdx_properties[self.tdx_consts.BIOS_SEAM_ENABLE]
        except KeyError:
            self._log.warning("No defined behaviour for BIOS SEAM loader behaviour; will enable by default.")
            self.tdx_properties[self.tdx_consts.BIOS_SEAM_ENABLE] = True
        super(LinuxTdxBaseTest, self).prepare()

    def auto_root_login(self):
        """Set root user to automatically be logged in."""
        GDM_FILE_LOC = "/etc/gdm/custom.conf"
        for line in self.tdx_consts.ROOT_AUTOMATIC_LOGIN_VALUE:
            if self.execute_os_cmd(f"grep {line} {GDM_FILE_LOC}") == "":
                result = self.execute_os_cmd(f"sed -i 's/\\[daemon\\]/\\[daemon\\]\\n{line}/g' {GDM_FILE_LOC}")
                if result != "":
                    raise content_exceptions.TestSetupError(f"Unexpected response when setting root auto login settings:"
                                                            f" {result}")
        self._log.debug("Automatic log in for user root is set.")
        self.execute_os_cmd(self.tdx_consts.ROOT_UNLOCK_SESSIONS_CMD)
        self._log.debug("Session 0 login is unlocked.")

    def ssh_to_vm(self, key: int = None, cmd: str = None, async_cmd: bool = False, timeout: float = None) -> str:
        """SSH to VM with specific ID key.

        :param key: key of VM to be SSHed to.
        :param cmd:  Command to send to VM.
        :param async_cmd: Asynchronously launch SSH command to TD guest (does not wait for response).
        :return: Output response from command."""

        if key is None:
            raise ValueError("VM key is not defined.  Key: {}".format(key))
        if cmd is None:
            raise ValueError("No valid command provided to send to TD guest.  Command string: {}".format(cmd))
        if timeout is None:
            timeout = self.command_timeout

        ssh_string = "ssh -o StrictHostKeyChecking=no -p {} {}@localhost \"{}\"".format(
            self.tdvms[key][self.tdx_consts.SSH_PORT_DICT_LABEL], self.tdvms[key][self.tdx_consts.TD_GUEST_USER],
            cmd)
        path = self._stage_expect_script(ssh_string, key)
        self._log.debug("SSHing to vm key {}".format(key))
        expect_script_contents = self.execute_os_cmd("cat {}".format(path))
        self._log.debug("Expect script content: {}".format(expect_script_contents))
        if async_cmd:
            self.os.execute_async("expect {}".format(path))
            self._log.debug("Expect script was launched asynchronously, no response data is available.")
            return ""
        try:
            result = self.os.execute("expect {}".format(path),
                                     timeout)
            self._log.debug("Response stdout: {}; response stderr: {}".format(result.stdout, result.stderr))
            cleaned_stdout = result.stdout.split("\n", 3)  # strip off of the spawn ssh and password prompt
            result.stdout = cleaned_stdout[3]  # returned 'cleaned' output
        except OsCommandTimeoutException:  # catch if command times out
            raise RuntimeError("Command timed out during execution.  Command attempted: {}.".format(cmd))
        if result.cmd_failed() or result.stderr:  # if command fails
            raise RuntimeError("Command failed.  Command attempted: {}; output: {}.".format(cmd, result.stderr))
        return result.stdout.strip()

    def vm_is_alive(self, key: int, timeout: float = None) -> bool:
        """Attempt to SSH to VM to detect if VM is alive.
        :param key: key identifier for VM.
        :return: True if VM is alive, False if VM is not alive.
        :param timeout: timeout for VM launch script"""
        cmd = "ls"
        if timeout is None:
            timeout = self.command_timeout
        try:
            self.ssh_to_vm(key=key, cmd=cmd, timeout=timeout)
        except RuntimeError:  # ssh failed
            return False
        return True

    def check_process_running(self, key: int = None, process_name: str = None) -> None:
        """Check if process with provided string is running on VM.

        :param key: VM identifier.
        :param process_name: name of process to be checked.
        :raise RuntimeError: if process is not running, raise exception."""
        cmd = "pgrep {}".format(process_name)
        result = self.ssh_to_vm(key=key, cmd=cmd)
        if result != "":
            self._log.debug("Process {} is running on VM {}.  Output: {}".format(process_name, key, result))
        else:
            raise RuntimeError("Process {} is not running on VM {}.  Output: {}".format(process_name, key, result))

    def _stage_expect_script(self, cmd: str = None, key: int = None, timeout: float = None) -> str:
        """Process to fill template expect command to ssh into Linux TD guest from TDX host.
        :param cmd: command to execute from SUT to vm
        :param key: key of VM to run the command on.
        :return: path to expect script for executing SSH script."""
        temp_file = "expect.sh"
        if timeout is None:
            timeout = self.command_timeout
        with open(self.expect_linux_script_file) as in_file:
            with open(temp_file, "w") as out_file:
                data = in_file.read()
                data = data.format(timeout, cmd,
                                   "{}@localhost".format(self.tdvms[key][self.tdx_consts.TD_GUEST_USER]),
                                   self.tdvms[key][self.tdx_consts.TD_GUEST_USER_PWD])
                out_file.write(data)
            script_path = self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_DIR] + temp_file
            self.os.copy_local_file_to_sut(temp_file, script_path)
        os.remove(temp_file)
        self.os.execute("dos2unix {}".format(script_path), self.command_timeout)
        self.os.execute("chmod +x {}".format(script_path), self.command_timeout)
        return script_path

    def _stage_vm_run_script(self, key: int = None, vm_os: str = None, tdvm: bool = True) -> None:
        """Process to fill template Linux TD guest run script with attributes from TDX properties dict.  Then, copies
        script to SUT and sets execute permissions.  Path to script is saved in TDVMs dict structure.
        :param key: VM name to call script.
        :param vm_os: OS of VM image to be used
        :param tdvm: True if creating a TD guest, False if creating a legacy VM.
        """

        config_file = self.vm_config_file
        temp_run_file = f"run_td-{key}.sh"

        new_vm_entry = dict()

        # TODO: has to be a better way to do this....
        try:
            new_vm_entry[self.tdx_consts.SSH_PORT_DICT_LABEL] = \
                self.tdvms[-1][self.tdx_consts.SSH_PORT_DICT_LABEL] + 1
        except IndexError:  # if first entry, there is no last element to refer to, so start with default value
            new_vm_entry[self.tdx_consts.SSH_PORT_DICT_LABEL] = self.tdx_properties[self.tdx_consts.SSH_RANGE_START]

        try:
            new_vm_entry[self.tdx_consts.TELNET_PORT_DICT_LABEL] = \
                self.tdvms[-1][self.tdx_consts.TELNET_PORT_DICT_LABEL] + 1
        except IndexError:  # if first entry, there is no last element to refer to, so start with default value
            new_vm_entry[self.tdx_consts.TELNET_PORT_DICT_LABEL] = \
                self.tdx_properties[self.tdx_consts.TELNET_RANGE_START]

        try:
            new_vm_entry[self.tdx_consts.TCP_PORT_DICT_LABEL] = \
                self.tdvms[-1][self.tdx_consts.TCP_PORT_DICT_LABEL] + 1
        except IndexError:  # if first entry, there is no last element to refer to, so start with default value
            new_vm_entry[self.tdx_consts.TCP_PORT_DICT_LABEL] = \
                self.tdx_properties[self.tdx_consts.TCP_RANGE_START]

        new_vm_entry[self.tdx_consts.TD_GUEST_IMAGE_PATH] = \
            self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_PATH + "_" + vm_os].format(key)

        new_vm_entry[self.tdx_consts.TD_GUEST_SERIAL_PATH] = \
            self.tdx_properties[self.tdx_consts.TD_GUEST_SERIAL_PATH].format(key)

        try:
            new_vm_entry[self.tdx_consts.CID_LABEL] = \
                self.tdvms[-1][self.tdx_consts.CID_LABEL] + 1
        except IndexError:  # if first entry, there is no last element to refer to, so start with default value
            new_vm_entry[self.tdx_consts.CID_LABEL] = 3

        new_vm_entry[self.tdx_consts.TD_GUEST_USER] = self.tdx_properties[self.tdx_consts.TD_GUEST_USER]
        new_vm_entry[self.tdx_consts.TD_GUEST_USER_PWD] = \
            self.tdx_properties[self.tdx_consts.TD_GUEST_USER_PWD]

        template_file = self.run_linux_td_guest_file

        with open(config_file) as in_file:
            data = in_file.read()

        data = data.format(self.tdx_properties[self.tdx_consts.TD_GUEST_CORES],
                           self.tdx_properties[self.tdx_consts.TD_GUEST_MEM],
                           new_vm_entry[self.tdx_consts.TD_GUEST_IMAGE_PATH],
                           new_vm_entry[self.tdx_consts.SSH_PORT_DICT_LABEL],
                           new_vm_entry[self.tdx_consts.TELNET_PORT_DICT_LABEL],
                           new_vm_entry[self.tdx_consts.TD_GUEST_SERIAL_PATH],
                           new_vm_entry[self.tdx_consts.CID_LABEL])

        script_path = self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_DIR] + temp_run_file
        template_path = self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_DIR] + template_file.split("/")[-1]
        self.os.copy_local_file_to_sut(template_file, self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_DIR])
        cmd = f"line=\"{data}\"; awk -v text=\"$line\" \'!/^#/ && !p {{print text; p=1}} 1\' " \
              f"{template_path} > {script_path}"
        self.execute_os_cmd(cmd)
        self.execute_os_cmd("dos2unix {}".format(script_path))
        self.execute_os_cmd("chmod +x {}".format(script_path))
        script_path = script_path + " -b grub"
        if not tdvm:
            script_path = script_path + " -t legacy "
        new_vm_entry[self.tdx_consts.RUN_SCRIPT_PATH_DICT_LABEL] = script_path
        self.tdvms.append(new_vm_entry)  # add new VM dict to list

    def get_seam_version(self) -> dict:
        """
        Get SEAM module version information.
        :return: SEAM module version and build information
        """
        version_data = dict()
        get_seam_data = "cat /sys/firmware/tdx/tdx_module/{}"
        seam_data = ["build_num", "minor_version", "major_version", "build_date"]
        version_data = dict()
        for field in seam_data:
            seam_results = self.execute_os_cmd(get_seam_data.format(field))
            if seam_results == "":
                raise content_exceptions.TestError(f"Could not get SEAM version {field} information.")
            version_data[field] = seam_results

        self._log.debug("SEAM version data:")
        for key in version_data.keys():
            self._log.debug(f"{key} {version_data[key]}")
        return version_data

    def create_vm(self, vm_name: str = None, vm_os: str = None, tdvm: bool = False) -> str:
        """Create VM instance.
        :param vm_name: Name of VM to be created.
        :param vm_os:  OS distribution (ex. WOS2019, RHEL, Ubuntu, Fedora).  This is the field checked in the
        content_configuration.xml config file for OS iso and VM information.
        :param tdvm: True if VM is a TDVM, False if VM is not a TDVM.
        :return: path to VM image.
        :raise NotImplementedError: Function not implemented for Linux yet, raise exception.
        """
        raise NotImplementedError("Not yet supported for TD guests.")

    def debug_vm_start(self, key: int = None, tdvm: bool = None, vm_os: str = None, timeout: float = None):
        """Run start VM command to gather command failure data.
        :param key: Key of VM to be started.
        :param tdvm: True if VM is a TDVM, False if VM is not a TDVM.
        :param vm_os: type of OS for VM.
        :param timeout: timeout for VM launch script"""
        if timeout is None:
            timeout = self.command_timeout
        try:
            cmd = self.tdvms[key][self.tdx_consts.RUN_SCRIPT_PATH_DICT_LABEL]
        except (KeyError, AttributeError):  # command is run to debug without first having a VM set up
            self._validate_vm_readiness(key=key, tdvm=tdvm, vm_os=vm_os)
            cmd = self.tdvms[key][self.tdx_consts.RUN_SCRIPT_PATH_DICT_LABEL]
        launch_results = self.os.execute(cmd=cmd, timeout=timeout)
        self._log.debug(f"Results from running qemu command to start VM: \n\tstdout: {launch_results.stdout} "
                        f"\n\tstderr: {launch_results.stderr}"
                        f"\n\treturn code: {launch_results.return_code}.")

    def start_vm(self, key: int = None, tdvm: bool = False, vm_os: str = None) -> None:
        """Start and power on VM instance.
        :param key: Key of VM to be started.
        :param tdvm: True if VM is a TDVM, False if VM is not a TDVM.
        :param vm_os: type of OS for VM.
        :raise content_exceptions.TestFail: SUT OS is not responsive after launching VM.
        :raise ValueError: if VM identifier provided is None.
        """
        if key is None:
            raise ValueError(f"No key provided when starting VM!  Key: {key}.")

        if vm_os is None:
            self._log.debug(f"No OS for VM provided, using OS defined in content_configuration.xml for VM_OS.")
            vm_os = self.tdx_properties[self.tdx_consts.VM_OS]

        self._validate_vm_readiness(key=key, tdvm=tdvm, vm_os=vm_os)
        cmd = self.tdvms[key][self.tdx_consts.RUN_SCRIPT_PATH_DICT_LABEL]
        self._log.debug(f"Using run script located at {cmd}.")
        self.os.execute_async(cmd)
        vm_boot_timeout = int(self.tdx_properties[self.tdx_consts.VM_BOOT_TIMEOUT])
        self._log.info(f"Waiting {vm_boot_timeout} seconds for VM to boot.")
        time.sleep(vm_boot_timeout)
        if not self.os.is_alive():
            raise content_exceptions.TestFail("SUT OS is down after launching VM key {}. Check the serial log "
                                              "files for a kernel panic or other event causing the SUT to "
                                              "reboot.".format(key))

    @retry(content_exceptions.TestError, delay=5, tries=3)
    def launch_vm(self, key: int = None, tdvm: bool = True, vm_os: str = None):
        """Start and power on VM instance.
        :param key: Key of VM to be started.
        :param tdvm: True if VM is a TDVM, False if VM is not a TDVM.
        :param vm_os: type of OS for VM."""
        timeout = 60  # 60 second command timeout for SSH test
        self.start_vm(key=key, tdvm=tdvm, vm_os=vm_os)
        if not self.vm_is_alive(key=key, timeout=timeout):
            self.debug_vm_setup(key=key, timeout=timeout)
            if not self.vm_is_alive(key=key, timeout=timeout):
                self.debug_vm_start(key=key, tdvm=tdvm, vm_os=vm_os, timeout=timeout)
                if not self.vm_is_alive(key=key, timeout=timeout):
                    self._log.debug("Attempting to get TD guest boot fail reason with TD guest launch command.")
                    attempt_to_boot = self.os.execute(self.tdvms[key][self.tdx_consts.RUN_SCRIPT_PATH_DICT_LABEL],
                                                      self.command_timeout)
                    self._log.debug(f"Response when booting TD guest:\n\tstdout: {attempt_to_boot.stdout}\n\t"
                                    f"stderr: {attempt_to_boot.stderr}")
                    raise content_exceptions.TestError(f"Could not verify VM {key} has launched successfully.  Please "
                                                       f"check VM serial "
                                                       f"log {self.tdvms[key][self.tdx_consts.TD_GUEST_SERIAL_PATH]} "
                                                       f"and dtaf_log.log for extra information.")
        self._log.debug(f"Confirmed VM {key} booted.")

    def _validate_vm_readiness(self, key=None, tdvm=None, vm_os=None):
        """Check run script is in place and VM image exists, take necessary action to fix if either are missing.
        :param key: Key of VM to be started.
        :param tdvm: True if VM is a TDVM, False if VM is not a TDVM.
        :param vm_os: type of OS for VM."""
        try:
            path = self.tdvms[key][self.tdx_consts.RUN_SCRIPT_PATH_DICT_LABEL]
        except (KeyError, IndexError):  # VM was not yet set up for test run
            self._log.debug(f"No run script found for VM key {key}. Staging new run script.")
            self._stage_vm_run_script(key=key, vm_os=vm_os, tdvm=tdvm)
            # check VM image exists on SUT, if not, copy from lab  host
            self._check_vm_image(key=key, vm_os=vm_os)

    def get_running_pid_for_vm(self, key: int) -> str:
        """Return PID for screen process running VM.
        :param key: VM identifier.
        :return: PID of process running VM."""
        run_script_location = self.tdvms[key][self.tdx_consts.RUN_SCRIPT_PATH_DICT_LABEL]
        get_screen_process_id_cmd = f"ps aux | grep -i \"screen .* {run_script_location}$\" | " \
                                    f"awk -F\" \" \'{{print $2}}\'"
        pid = self.execute_os_cmd(cmd=get_screen_process_id_cmd)  # get pid for screen process containing vm boot
        self._log.debug(f"VM {key} is running on PID {pid}.")
        return pid

    def write_command_to_vm_console(self, key: int, cmd: str) -> None:
        """Write command to VM console via screen command.
        :param key: VM identifier.
        :param cmd: command to write to VM process."""
        pid = self.get_running_pid_for_vm(key)
        get_dtaf_fabric_cmd = f"screen -ls | grep \"{pid}.dtaf_fabric\" | awk -F\" \" \'{{print $1}}\'"
        screen_pid_name = self.execute_os_cmd(cmd=get_dtaf_fabric_cmd)
        self._log.debug(f"Screen PID {pid} name is {screen_pid_name}.")
        screen_write_cmd = f"screen -S {screen_pid_name} -p 0 -X stuff \"{cmd}^M\""  # ^M == line return
        self.execute_os_cmd(cmd=screen_write_cmd)
        self._log.debug(f"Wrote command {screen_write_cmd} to the screen process {screen_pid_name}.")

    def set_up_vm_credentials(self, key: int) -> None:
        """Log into VM via console to set up user and password provided in content_configuration.xml.
        :param key: VM identifier."""
        commands_list = [self.tdvms[key][self.tdx_consts.TD_GUEST_USER],
                         "passwd",
                         self.tdvms[key][self.tdx_consts.TD_GUEST_USER_PWD],
                         self.tdvms[key][self.tdx_consts.TD_GUEST_USER_PWD]
                         ]
        for command in commands_list:
            self.write_command_to_vm_console(key=key, cmd=command)

    def check_vm_serial_log(self, key: int, search_string: str) -> str:
        """Check VM serial log for provided data.
        :param key: VM identifier.
        :param search_string: information to search for in VM serial log.
        :return: Return lines from serial log with data."""
        serial_log = self.tdvms[key][self.tdx_consts.TD_GUEST_SERIAL_PATH]
        self._log.debug(f"Checking VM serial log {serial_log}.")
        results = self.execute_os_cmd(f"grep \"{search_string}\" {serial_log}")
        return results

    def debug_vm_setup(self, key: int, timeout: float = None) -> None:
        """Attempt to debug VM with common problems.
        :param key: VM identifier.
        :param timeout: timeout for VM launch script"""
        # check VM booted in VM serial log
        if timeout is None:
            timeout = self.command_timeout
        login_prompt = True if self.check_vm_serial_log(key=key, search_string="login") != "" else False
        error_log_file_name = f"error-log-{self.tdvms[key][self.tdx_consts.TD_GUEST_SERIAL_PATH].split('/')[-1]}"
        if not login_prompt:
            self._log.warning(f"VM {key} appears to not have booted to the login prompt.  Stopping the VM to gather "
                              f"logs.")
            self.stop_emulation(key=key)
            # append current vm serial log to an error log
            self.execute_os_cmd(f"cat {self.tdvms[key][self.tdx_consts.TD_GUEST_SERIAL_PATH]} >> "
                                f"{error_log_file_name}")
            raise content_exceptions.TestError(f"Attempted to resolve issues with VM {key}, but could not get VM {key} "
                                               f"to boot.")
        else:
            self._log.debug(f"VM {key} appears to have reached the log in prompt.  Checking SSH.")
        if not self.vm_is_alive(key=key, timeout=timeout):
            self._log.debug(f"SSH on VM {key} failed, attempting to set up user credentials.")
            self.set_up_vm_credentials(key=key)
            self.execute_os_cmd(f"cat {self.tdvms[key][self.tdx_consts.TD_GUEST_SERIAL_PATH]} >> "
                                f"{error_log_file_name}")
            raise content_exceptions.TestError(f"Attempted to resolve issues with VM {key}, but could not get VM {key} "
                                               f"to boot.")
        if not self.vm_is_alive(key=key, timeout=timeout):
            raise content_exceptions.TestError(f"Attempted to resolve issues with VM {key}, but could not get VM {key} "
                                               f"to boot.")

    def set_yum_proxy_on_vm(self, key: int) -> None:
        """Check /etc/yum.conf for proxy data (no_proxy and proxy data).
        :param key: VM identifier."""

        yum_location = "/etc/yum.conf"
        if self.ssh_to_vm(key=key, cmd=f"ls -l {yum_location}") == "":
            self.log.debug("Could not set proxy data for yum, yum.conf does not appear to exist in the expected "
                           "location. Not attempting to set proxy.")
            return
        no_proxy_cmd = f"grep no_proxy= {yum_location}"
        proxy_cmd = f"grep ^proxy= {yum_location}"
        if self.ssh_to_vm(key=key, cmd=no_proxy_cmd) == "":
            self.ssh_to_vm(key=key, cmd=f"echo 'no_proxy=intel.com,.intel.com,localhost' >> {yum_location}")
        if self.ssh_to_vm(key=key, cmd=proxy_cmd) == "":
            self.ssh_to_vm(key=key, cmd=f"echo 'proxy=http://proxy-dmz.intel.com:912' >> {yum_location}")

    def _check_vm_image(self, key: int = None, vm_os: str = None) -> None:
        """Check if VM image already exists in prescribed path on SUT.
        :param key: VM identifier in tdvms list.
        :param vm_os: string of OS or distribution. Check tdx_consts.TDVMOS for expected values.
        """
        if not self.os.check_if_path_exists(self.tdvms[key][self.tdx_consts.TD_GUEST_IMAGE_PATH],
                                            directory=False):
            vm_os_path = "{}_{}".format(self.tdx_consts.TD_GUEST_IMAGE_PATH_HOST, vm_os.upper())
            self._log.info("No VM image found on SUT.  Copying VM template image from "
                           "host located at {}.".format(vm_os_path)
                           )
            self.os.copy_local_file_to_sut(self.tdx_properties[vm_os_path],
                                           self.tdvms[key][self.tdx_consts.TD_GUEST_IMAGE_PATH])
        else:
            self._log.info("Found VM image to use at {}.".format(
                self.tdvms[key][self.tdx_consts.TD_GUEST_IMAGE_PATH]))

    def _send_qemu_cmd(self, key: int = None, cmd: str = None) -> str:
        """Send command to QEMU monitor over VM telnet port.
        :param key: VM identifier
        :param cmd: Command to be sent to QEMU monitor.  Must be a valid QEMU monitor command.
        :return: result of command
        """
        telnet_port = self.tdvms[key][self.tdx_consts.TELNET_PORT_DICT_LABEL]
        template_cmd = "echo {} | nc 127.0.0.1 {}".format(cmd, telnet_port)
        result = self.os.execute(template_cmd, self.command_timeout).stdout
        self._log.debug(f"Sent command {cmd} to QEMU monitor for VM {key}.  Result: {result}")
        return result

    def stop_emulation(self, key: int = None) -> None:
        """Stop QEMU emulation of VM.  Only for Linux hosts.
        :param key: VM identifier to stop emulation.
        """
        self._send_qemu_cmd(key, self.tdx_consts.QemuCommands.STOP_EMULATION)

    def teardown_vm(self, key: int = None, force: bool = False) -> None:
        """Teardown VM.
        :param key: identifier of VM to be shutdown.
        :param force: if True, do not shut down VM cleanly before removing.
        :raise ValueError: raise if no VM identifier is provided.
        """
        if key is None:
            raise ValueError("No specific VM identified to tear down. Key provided: {}".format(key))

        self._log.info("Sending shutdown command to VM {}.".format(key))
        self._send_qemu_cmd(key, self.tdx_consts.QemuCommands.SHUTDOWN)

    def pause_vm(self, key: int = None) -> None:
        """Pause VM, halting all processes.
        :param key: identifier of VM to be shutdown.
        """
        self._log.info("Pausing VM {}.".format(key))
        self._send_qemu_cmd(key, self.tdx_consts.QemuCommands.PAUSE)

    def resume_vm(self, key: int = None) -> None:
        """Resume paused VM, resuming all processes.  Only will work on paused VMs.
        :param key: identifier of VM to be shutdown.
        """
        self._log.info("Resuming VM {}.".format(key))
        self._send_qemu_cmd(key, self.tdx_consts.QemuCommands.RESUME)

    def save_vm(self, vm_name: str = None) -> None:
        """What it says on the tin:  saves VM configuration
        :param vm_name: Name of VM for which configuration should be saved.
        :raise NotImplementedError: Saving VMs is not POR for TD guests, function is not implemented.
        """
        raise NotImplementedError("Not yet supported for TD guests.")

    def restore_vm(self, vm_name: str = None, config_file: str = None) -> None:
        """What it says on the tin:  restores VM configuration.
        :param vm_name: Name of VM for which configuration should be restored.
        :param config_file: Config file of VM.
        :raise NotImplementedError: Saving VMs is not POR for TD guests, function is not implemented.
        """
        raise NotImplementedError("Not yet supported for TD guests.")

    def msr_read(self, register: int = None) -> int:
        """Attempts to read MSR through OS and if it fails, revert to ITP.
        :param register: address of MSR to be read.
        :return: Value of MSR.
        """
        if self.os.is_alive():
            self._log.debug("SUT is booted to OS. Attempting to read MSR {} from OS.".format(hex(register)))
            msr_read_command = "rdmsr {}"
            cmd = msr_read_command.format(register)
            result = self.os.execute(cmd, self.command_timeout)
            result = result.stdout.strip()
            if result == "":  # failed to read MSR with msr-tools package
                self._log.warning("Could not read MSR with msr-tools... attempting to read with ITP, but this can "
                                  "cause OS instability!")
                result = super(LinuxTdxBaseTest, self).msr_read(register)
            else:
                self._log.debug("MSR {} == 0x{}".format(hex(register), result))
                result = int(result, 16)  # convert to int for later usage
        else:
            result = super(LinuxTdxBaseTest, self).msr_read(register)
        return result

    def copy_file_between_sut_and_vm(self, key: int = None, source_file_path: str = None,
                                     destination_file_path: str = None, to_vm: bool = True) -> None:
        """Copy file between SUT to VM on SUT.
        :param key: identifier for VM.
        :param source_file_path: path of file to copy.
        :param destination_file_path: path of where file should go on VM.
        :param to_vm: True if copying to VM, False if copying from VM.
        :raise ValueError: If VM identifier or no valid source file path is provided.
        :raise RuntimeError: if VM is not reachable with expect script.
        """
        self._log.debug("SUT OS is {}, copying file over to TD guest.".format(self.sut_os))
        ssh_failure = "Connection refused"
        if key is None:
            raise ValueError("VM key is not defined.  Key: {}".format(key))
        if source_file_path is None:
            raise ValueError("No valid command provided to send to TD guest.  "
                             "Command string: {}".format(source_file_path))
        if OperatingSystems.LINUX == self.sut_os:  # find port to SSH to on local host
            self._log.debug("Check if copying directory.")
            result = self.os.execute("test -d {}; echo $?".format(source_file_path),
                                     self.command_timeout).stdout
            result = result.strip()
            if int(result) == 0:
                self._log.debug("File to be copied is a directory")
                recursive = "-r"
            else:
                recursive = ""

            if to_vm:
                scp_string = "scp {} -o StrictHostKeyChecking=no -P {} {} {}@localhost:{}".format(
                    recursive,
                    self.tdvms[key][self.tdx_consts.SSH_PORT_DICT_LABEL],
                    source_file_path,
                    self.tdvms[key][self.tdx_consts.TD_GUEST_USER],
                    destination_file_path)
            else:
                scp_string = "scp {} -o StrictHostKeyChecking=no -P {} {}@localhost:{} {}".format(
                    recursive,
                    self.tdvms[key][self.tdx_consts.SSH_PORT_DICT_LABEL],
                    self.tdvms[key][self.tdx_consts.TD_GUEST_USER],
                    source_file_path,
                    destination_file_path)
            path = self._stage_expect_script(scp_string, key)
            self._log.debug(f"SSHing to vm key {key}")
            try:
                result = self.os.execute(f"expect {path}", self.command_timeout)
                self._log.debug(f"Response: {result.stdout}")
            except OsCommandTimeoutException:  # catch if command times out
                raise RuntimeError(f"Failed to SSH to VM {key}.")
            if result.cmd_failed() or ssh_failure in result.stdout:  # if command fails
                raise RuntimeError(f"Failed to SSH to VM {key}.")

    def find_file_on_vm(self, key: int = None, file_name: str = None, find_location: str = None) -> str:
        """Find file on VM.
        :param key: key of VM of which to find the file.
        :param file_name: Name of file to find.
        :param find_location: where to look for the file; if no location si provided, will search at root partition.
        :return: full path to file on the VM.
        """
        if file_name is None:
            raise content_exceptions.TestFail("No file name provided to search.")
        if find_location is None:
            self._log.debug("No location to search provided, defaulting to / partition...")
            find_location = "/"
        ssh_command = "find {} -name \'{}\'".format(find_location, file_name)
        file_path = self.ssh_to_vm(key=key, cmd=ssh_command)
        return file_path

    @retry(content_exceptions.TestError, tries=2)
    def rename_vm_log_files(self, file_rename: str, key: int = None) -> None:
        """Rename VM log files.  Will rename the log file of an individual VM if key is provided, if not, will change
        all current VM log files.
        :param file_rename: new file name to which change VM log file name.
        :param key: VM identifier."""
        if key:
            old_file_name = self.tdvms[key][self.tdx_consts.TD_GUEST_SERIAL_PATH].split(".")
            new_file_name = old_file_name[0] + file_rename + "." + old_file_name[-1]
            self.execute_os_cmd(f"mv {self.tdvms[key][self.tdx_consts.TD_GUEST_SERIAL_PATH]} {new_file_name}")
        elif self.tdvms and self.os.is_alive():
            for vm in self.tdvms:
                old_file_name = vm[self.tdx_consts.TD_GUEST_SERIAL_PATH].split(".")
                new_file_name = old_file_name[0] + file_rename + "." + old_file_name[-1]
                self.execute_os_cmd(f"mv {vm[self.tdx_consts.TD_GUEST_SERIAL_PATH]} "
                                    f"{new_file_name}")
        elif not self.tdvms:
            self._log.debug("No VMs are logged during test, no files to move.")
        elif not self.os.is_alive():
            raise content_exceptions.TestError(f"SUT does not appear to be up, could not rename files.")

    def kill_all_running_vms(self) -> None:
        """Kill all currently running VMs."""
        for key in self.tdvms:
            self._log.debug("Shutting down VM {}.".format(key))
            self.stop_emulation(self.tdvms.index(key))

    def compress_vm_log_files(self) -> str:
        """Zip all log files in designated VM log directory into a zip file.
        :return: location to zip file"""
        td_guest_zip = self.tdx_consts.ZIPPED_TDVM_FILES
        full_path_zipped_file = f"{self.tdx_consts.TD_GUEST_LOG_PATH_LINUX}/{td_guest_zip}"
        self.execute_os_cmd(f"zip -r {full_path_zipped_file} {self.tdx_consts.TD_GUEST_LOG_PATH_LINUX}")
        return full_path_zipped_file

    def reboot_vm(self, key: int) -> None:
        """Reboot VM.
        :param key: VM identifier."""
        self.teardown_vm(key=key)
        time.sleep(20.0)
        if self.vm_is_alive(key=key):
            raise content_exceptions.TestError(f"VM {key} did not shut down during reboot.")
        self.launch_vm(key=key)
        if not self.vm_is_alive(key=key):
            raise content_exceptions.TestError(f"VM {key} did not boot back up after reboot.")

    def check_for_crystal_ridge(self) -> bool:
        """Check device information for Intel manufactured memory devices.
        :return: return if Intel manufactured memory devices are installed on the SUT"""
        self._log.debug("Checking dmidecode for Intel manufactured memory devices.")
        results = int(self.execute_os_cmd("dmidecode -t memory | grep -iw intel | wc -l"))
        if results == 0:
            self._log.debug("No Crystal Ridge dimms recognized on the SUT.")
            return False
        self._log.debug(f"{results} Intel memory devices found on the SUT.")
        return True

    def one_dpc_config_check(self) -> bool:
        """Check if dimms are in 1DPC population.
        :return: True if dimms are in 1DPC, False if dimms are not in 1DPC or if dimms are in 2DPC."""
        return self.dpc_dimm_check()[0]

    def two_dpc_config_check(self) -> bool:
        """Check if dimms are in 2DPC population.
        :return: True if dimms are in 2DPC, False if dimms are not in 2DPC."""
        return self.dpc_dimm_check()[1]

    def dpc_dimm_check(self) -> Tuple[bool, bool]:
        """Check for DPC dimm config; this is required for SNC and memory mirroring tests.
        :return: tuple if 1DPC and 2DPC configurations are installed on SUT."""
        # get all dimms installed
        results = self.execute_os_cmd("dmidecode -t memory | grep -i \"asset tag\"")
        primary_dimm_slots = []
        secondary_dimm_slots = []
        for letter in ["A", "B", "C", "D", "E", "F", "G", "H"]:
            primary_dimm_slots.append(f"{letter}1")
            secondary_dimm_slots.append(f"{letter}2")
        one_dpc_check = True
        two_dpc_check = True
        for dimm_slot in primary_dimm_slots:
            if dimm_slot not in results:
                self._log.debug(f"Dimm {dimm_slot} not populated on platform.")
                two_dpc_check = one_dpc_check = False
            else:
                self._log.debug(f"Dimm {dimm_slot} is populated on the platform.")

        if one_dpc_check:
            for dimm_slot in secondary_dimm_slots:
                if dimm_slot not in results:
                    self._log.debug(f"Dimm {dimm_slot} not populated on platform.")
                    two_dpc_check = False
                else:
                    self._log.debug(f"Dimm {dimm_slot} is populated on the platform.")
        if two_dpc_check:
            one_dpc_check = False
        return one_dpc_check, two_dpc_check

    def get_sockets(self) -> int:
        """Get the number of sockets found by the OS.
        :return: number of sockets on SUT."""
        num_sockets = self.os.execute("lscpu | grep Socket", self.command_timeout).stdout
        num_sockets = num_sockets.split(" ")[-1]
        return int(num_sockets.strip())

    def get_cores(self) -> int:
        """Get the number of cores on each socket.
        :return: number of cores per socket on SUT."""
        cores = self.os.execute(r"lscpu | grep ^CPU\(s\):", self.command_timeout).stdout
        cores = cores.split(" ")[-1]
        return int(cores.strip())

    def cleanup(self, return_status: bool) -> None:
        """Test Cleanup
        :param return_status: True or False if test passed."""
        if self.os.is_alive():
            self._log.info("OS is up, cleaning up open VMs and saving log files.")
            # teardown running VMs
            self._log.info("Killing remaining running VMs.")
            self.kill_all_running_vms()
            if self.tdvms:
                self._log.info("Copying log files to log directory on SUT at {}.".format(self.log_dir))
                td_guest_zip = self.tdx_consts.ZIPPED_TDVM_FILES
                zipped_vm_logs = self.compress_vm_log_files()
                try:
                    self.os.copy_file_from_sut_to_local(zipped_vm_logs, f"{self.log_dir}\\{td_guest_zip}")
                except (FileNotFoundError, IOError, OsCommandException):
                    self._log.warning("Caught exception when attempting to copy VM log files from SUT... likely no VMs "
                                      "successfully launched.")
                self._log.info("Clearing log files from VM directory on SUT.")
                self.execute_os_cmd(f"rm -rf {self.tdx_consts.TD_GUEST_LOG_PATH_LINUX}/*")
        else:
            self._log.warning("OS does not appear to be up - failed to collect VM log files.  Please verify system "
                              "health and save the log files from {} on the SUT OS with the test logs.".format(
                               self.tdx_consts.TD_GUEST_LOG_PATH_LINUX))
        self._log.debug("Exiting LinuxTdxBaseTest cleanup, starting super set clean up.")
        super(LinuxTdxBaseTest, self).cleanup(return_status)
