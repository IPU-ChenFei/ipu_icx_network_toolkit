#!/usr/bin/env python
#################################################################################
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
#################################################################################


import re
from typing import Dict, List, Match, Pattern, Union

from dtaf_core.lib.os_lib import LinuxDistributions

from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.cbnt_constants import RedhatVersion
from src.lib.common_content_lib import CommonContentLib

# Submenu entries may start with whitespace followed by the keyword submenu. The name is contained in either
# single or double quotes which can consist of letters, numbers, slashes, dashes and dots.
# It ends with the opening token {
submenu_re: str = r"(\s*submenu\s*('|\")(?P<submenu>[.\s\d\w_,/\\-]+)('|\")\s*{)"
# Menu entries may start with whitespace followed by the keyword menuentry. The name is contained in either
# single or double quotes which can consist of letters, numbers, slashes, dashes and dots. It may be followed
# by options in the format --<option> <value>.
# It ends with the opening token {
menuentry_re: str = r"(\s*menuentry\s*('|\")(?P<menuentry>[.\s\d\w_,/\\-]+)('|\").*{)"
# Joining the patterns this way means we only have to search a line once
entry_re: Pattern = re.compile("|".join([submenu_re, menuentry_re]))
# This the token that starts a block
open_token: Pattern = re.compile(r"{")
# This the token that ends a block
close_token: Pattern = re.compile(r"}")

class GrubUtil(object):
    """
    Grub util sets the different boot option
    """
    GRUBBY_KERNEL_CMD = 'grubby --info=ALL | grep -e ^kernel=".*" -e ^index'
    GRUBBY_INFO_KERNEL_CMD = "grubby --info {}"
    GRUBBY_GET_DEFAULT_BOOT_KERNEL_CMD = "grubby --default-index"
    GRUBBY_ADD_ARGS_CMD = "grubby --args={} --update-kernel {}"
    GRUBBY_DELETE_ARGS_CMD = "grubby --remove-args={} --update-kernel {}"
    GET_CURRENT_KERNEL_VERSION_CMD = "uname -r"
    BASE_KERNEL = "x86_64"
    INTEL_NEXT_KERNEL = "intel-next"

    def __init__(self, log, common_content_config: ContentConfiguration, common_content_lib: CommonContentLib):
        """
        Create an instance of GrubUtil

        :param log: Log object
        :param common_content_config_obj: common_content_config_obj config file
        :param arguments: None
        """
        self._log = log
        self._common_content_conf = common_content_config
        self._common_content_lib = common_content_lib
        self._command_timeout = int(self._common_content_conf.get_command_timeout())
        self._reboot_timeout = int(self._common_content_conf.get_reboot_timeout())

    def __set_default_rhel_7(self, boot_option):
        """
        setting default index for rhel 7
        :raise: content_exception.TestNotImplementedError if not implementation.
        """
        raise content_exceptions.TestNotImplementedError("implementation pending for RHEL 7 versions")

    def get_linux_version(self):
        """
        get the linux version

        return linux version
        :raise: content_exception.TestFail if unable to get the linux version
        """
        get_os_info_cmd = "cat /etc/os-release"
        version_id_re = r'(?<=VERSION_ID=)\s*(.*)'
        self._log.info("Get linux version")
        output = self._common_content_lib.execute_sut_cmd(get_os_info_cmd, "linux os info cmd", self._command_timeout)
        self._log.debug("Linux os command output {}".format(output))
        value = re.search(version_id_re, output)
        if not value:
            raise content_exceptions.TestFail("unable to get the linux version")
        self._log.debug("Version of the linux os is {} ".format(value.group(0)))
        return value.group(0)

    def set_grub_boot_index(self, grub_index: Union[str, int]) -> bool:
        """
        Set default boot index
        :param grub_index: String or integer indicating which index to boot
        :returns: True if no errors are detected. False otherwise.
        """
        self._log.info("Setting grub boot index")
        grub_set_index_cmd = f'grub2-set-default "{grub_index}"'
        self._log.debug("Set index {} as the first boot order".format(grub_index))
        set_def_out: str = self._common_content_lib.execute_sut_cmd(grub_set_index_cmd, grub_set_index_cmd, self._command_timeout)
        if set_def_out.lower().find("error") > 0:
            # grub2-set-default can error out with a zero exit code for some reason
            self._log.error(f"Error found when setting grub boot index:\n{set_def_out}")
            return False
        return True

    def get_grub_boot_index(self) -> str:
        """
        Get default boot index
        :return: default boot index value
        """
        self._log.debug("Get grub boot index")
        result = self._common_content_lib.execute_sut_cmd(self.GRUBBY_GET_DEFAULT_BOOT_KERNEL_CMD,
                                                          "getting grub default boot index", self._command_timeout)
        return result

    def set_default_boot_rhel_8(self, kernel):
        """
        Set the default boot index for rhel 8 os.

        :raise: content_exception.TestFail if unable to get the kernel info
        """
        reg_os_index = r'(?<=index=)\s*(.*)'
        reg_kernel = r'^index(.+)\n^kernel=\".*{}'.format(kernel)
        self._log.debug("Running grub configuration command '{}' ".format(self.GRUBBY_KERNEL_CMD))
        command_result = self._common_content_lib.execute_sut_cmd(
            self.GRUBBY_KERNEL_CMD, "get menuentry info", self._command_timeout)
        self._log.debug("Grub command output {}".format(command_result))
        if not command_result.strip():
            raise content_exceptions.TestFail("Unable to get the kernel info")
        kernel_index = re.compile(reg_kernel, re.MULTILINE).search(command_result)
        if not kernel_index:
            raise content_exceptions.TestFail("Unable to get kernel and index info")
        index = re.search(reg_os_index, kernel_index.group(0))
        if not index:
            raise content_exceptions.TestFail("Unable to get index info")
        self.set_grub_boot_index(index.group(0))

    def set_default_base_kernel(self):
        """
        Set the default boot index for base kernel.
        """
        if any(version in self.get_linux_version() for version in RedhatVersion.RHEL_8_VERSION):
            self.set_default_boot_rhel_8(self.BASE_KERNEL)
        else:
            self.__set_default_rhel_7(self.BASE_KERNEL)

    def set_default_intel_next_kernel(self):
        """
        Set the default boot index for intel next kernel.
        """
        if any(version in self.get_linux_version() for version in RedhatVersion.RHEL_8_VERSION):
            self.set_default_boot_rhel_8(self.INTEL_NEXT_KERNEL)
        else:
            self.__set_default_rhel_7(self.INTEL_NEXT_KERNEL)

    def set_default_boot_cent_os_server_kernel(self):
        """
        This function is used to set the +server kernel in Cent OS.
        """
        linux_flavour = self._common_content_lib.get_linux_flavour()
        self._log.info("Linux Flavour is : {}".format(linux_flavour))
        self._log.info("Setting +server kernel if OS is Cent OS ...")
        if linux_flavour.lower() == LinuxDistributions.CentOS.lower():
            uname_command = "uname -r"
            kernel_version_in_sut = self._common_content_lib.execute_sut_cmd(uname_command, uname_command,
                                                                             self._command_timeout).strip()
            self._log.debug("command {} output is : \n{}".format(uname_command, kernel_version_in_sut))
            try:
                desired_kernel_version = self._common_content_conf.get_kernel_version()
            except (KeyError, AttributeError):  # if param is missing from content_configuration.xml
                self._log.warning(f"Could not find desired kernel information in content_configuration.xml file! "
                                  f"Continuing test with current kernel version: {kernel_version_in_sut}")
                desired_kernel_version = kernel_version_in_sut
            if desired_kernel_version == "":  # if tag exists, but no data supplied in content_configuration.xml
                self._log.warning(f"Could not find desired kernel information in content_configuration.xml file! "
                                  f"Continuing test with current kernel version: {kernel_version_in_sut}")
                desired_kernel_version = kernel_version_in_sut
            # Adding extra backslash to escape from a control char +
            if "+" in desired_kernel_version:
                desired_kernel_version = re.sub(r"\+", r"\+", desired_kernel_version)
            reg_index_kernel = r'^index=\d\nkernel="/boot/vmlinuz-{}'.format(desired_kernel_version)
            reg_os_index = r'(?<=index=)\s*(.*)'
            index = None
            self._log.info("Desired Version for kernel is {}".format(desired_kernel_version))
            server_kernel = re.findall(desired_kernel_version, kernel_version_in_sut)
            if server_kernel:
                self._log.info("Server already in desired kernel : {}".format(server_kernel))
            else:
                self._log.info("Changing the kernel to {} in Cent OS....".format(desired_kernel_version))
                self._log.info("Running grubby configuration command '{}' ".format(self.GRUBBY_KERNEL_CMD))
                command_result = self._common_content_lib.execute_sut_cmd(
                    self.GRUBBY_KERNEL_CMD, "get menu entry info", self._command_timeout)
                self._log.debug("Command output {} is: \n{}".format(self.GRUBBY_KERNEL_CMD, command_result))
                try:
                    kernel_index = re.compile(reg_index_kernel, re.MULTILINE).search(command_result)
                    if kernel_index:
                        index = (re.search(reg_os_index, kernel_index.group(0))).group(0)
                except AttributeError:  # attribute error raised when re results return nothing
                    raise content_exceptions.TestSetupError("Failed to find desired kernel version"
                                                            "in OS.")
                self._log.info("Kernel index :{}".format(index))
                self.set_grub_boot_index(index)
        else:
            self._log.info("Kernel change not required for OS : {}".format(linux_flavour))

    def get_linux_name(self):
        """
        get the linux name

        return linux name
        :raise: content_exception.TestFail if unable to get the linux Name
        """
        get_os_info_cmd = "cat /etc/os-release"
        version_id_re = r'(?<=NAME=)\s*(.*)'
        self._log.info("Get linux Name")
        output = self._common_content_lib.execute_sut_cmd(get_os_info_cmd, "linux os info cmd", self._command_timeout)
        self._log.debug("Linux os command output {}".format(output))
        value = re.search(version_id_re, output)
        if not value:
            raise content_exceptions.TestFail("unable to get the linux Name")
        self._log.debug("Name of the linux os is {} ".format(value.group(0)))
        return value.group(0)

    def get_kernel_args(self, kernel: str) -> dict:
        """Get specified kernel's boot parameters from grubby.
        :param kernel: which kernel to get data for
        :return: data returned from grubby command"""
        if "/boot/vmlinuz" not in kernel:
            kernel_path = f"/boot/vmlinuz-{kernel}"
        else:
            kernel_path = kernel
        grubby_info_kernel_cmd = self.GRUBBY_INFO_KERNEL_CMD.format(kernel_path)
        grubby_kernel_data = self._common_content_lib.execute_sut_cmd(grubby_info_kernel_cmd, "get grubby kernel info",
                                                                      self._command_timeout).strip()
        grubby_kernel_data = grubby_kernel_data.split("\n")
        grubby_data = dict()
        for info in grubby_kernel_data:
            info = info.split("=", 1)
            grubby_data[info[0]] = info[1]
        self._log.debug(f"Grubby data from OS for kernel {kernel}:")
        for key in grubby_data.keys():
            self._log.debug(f"{key}: {grubby_data[key]}")
        return grubby_data

    def add_kernel_args(self, argument: str, kernel: str) -> None:
        """Add kernel param data to current kernel's boot command.
        :param argument: param to be added to the kernel command line
        :param kernel: kernel for which to add parameter"""
        if "/boot/vmlinuz" not in kernel:
            kernel_path = f"/boot/vmlinuz-{kernel}"
        else:
            kernel_path = kernel
        kernel_details = self.get_kernel_args(kernel)
        if argument.lower() in kernel_details['args'].lower():  # ignore case when checking if substring exists
            self._log.debug(f"Param {argument} is already present in kernel args.  Nothing to do.")
        else:
            self._log.debug(f"Param {argument} is not present in kernel args.  Adding param with grubby.")
            results = self._common_content_lib.execute_sut_cmd(self.GRUBBY_ADD_ARGS_CMD.format(argument, kernel_path),
                                                               "add kernel args with grubby command",
                                                               self._command_timeout).strip()
            if results != "":
                raise content_exceptions.TestError(f"Failed to add param {argument} to args for kernel {kernel}!")

    def get_current_kernel_version(self) -> str:
        """Get current kernel version.
        :return: version of current kernel used in OS"""
        return self._common_content_lib.execute_sut_cmd(self.GET_CURRENT_KERNEL_VERSION_CMD,
                                                        "get current kernel command", self._command_timeout).strip()

    @classmethod
    def get_entries(cls, config: str) -> Dict:
        '''Get menu and submenu entries from a grub.cfg file
        :param config: String with data from a grub.cfg file
        :raises Exception: If there's an error in the grub.cfg file
        :returns: Dictionary reflecting boot entries
        Note: This isn't intended to be a perfect parser/tokenizer; just something that digs
        out the names of menu and submenu entries and returns them in a dictionary reflecting
        the structure thereof.
        '''
        # Final output. Nested dict with submenu names as keys reflecting the
        # hierarchy detailed in the config. Each level will have an 'entries'
        # key that is a list of the menu entries in that submenu. Nested
        # submenus will be their own dict with the same.
        cfg_data: Dict = dict()
        cfg_data['entries'] = list()
        # Current submenu hierarchy. When empty, at the top level
        submenus: List[str] = list()
        # current submenu dict
        curr_level: Dict = cfg_data
        # Keeps track of open/closing braces to ensure proper parsing
        open_cnt: int = 0
        # indicates if the last open was a submenu or a menu entry so
        # we know when to pop from the submenu list
        in_sub: bool = False

        for (line_n, line) in enumerate(config.splitlines()):
            e: Union[None, Match] = entry_re.search(line)
            if e:
                open_cnt += 1
                if e.group("submenu"):
                    name: str = e.group("submenu")
                    submenus.append(name)
                    in_sub = True
                    curr_level[name] = dict()
                    curr_level = curr_level[name]
                    curr_level['entries'] = list()
                elif e.group("menuentry"):
                    in_sub = False
                    curr_level['entries'].append(e.group("menuentry"))
            else:
                open: Union[None, Match] = open_token.search(line)
                close: Union[None, Match] = close_token.search(line)
                if open and close:
                    # Configs use ${NAME} to use variables which we don't care about
                    continue
                elif close:
                    open_cnt -= 1
                    if open_cnt < 0:
                        raise SyntaxError(f"Unexpected closure on line {line_n+1}")
                    if in_sub:
                        curr_level = cfg_data
                        submenus.pop()
                        if not submenus:
                            in_sub = False
                        else:
                            for s in submenus:
                                curr_level = curr_level[s]
                    elif submenus:
                        in_sub = True
                elif open:
                    open_cnt += 1

        return cfg_data

    @classmethod
    def dict_to_paths(cls, entry_dict: Dict, _level_path="") -> List[str]:
        '''Convert the dict result from get_entries() to a list of grub paths
        Note: Recursive function
        :params path_dict: Dict result from get_entries()
        :params _level_path: used interally
        :return: List of strings with paths
        '''
        paths: List[str] = list()
        for level, values in entry_dict.items():
            if level == "entries":
                for v in values:
                    p: str = f"{v}" if _level_path == "" else f"{_level_path}>{v}"
                    paths.append(p)
            else:
                new_path: str = f"{level}" if _level_path == "" else f"{_level_path}>{level}"
                paths.extend(cls.dict_to_paths(values, _level_path=new_path))

        return paths
