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
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib


class MemoryCeErrorInjectionLinuxVm(IoVirtualizationCommon):
    """
    GLASGOW ID: G67405

    This Test case to inject Memory correctable error while creating a VM with KVM hypervisor

    This test case will use fisher to launch virsh install to create a VM while fisher inject errors during the process.
    """
    VM = VMs.RHEL
    VM_NAME = None
    BIOS_CONFIG_FILE = "mem_ce_error_injection.cfg"
    TEST_CASE_ID = ["G67412", "inject_memory_correctable_error_while_creating_VM"]
    FISHER_CMD = r"echo fisher --workload=\'{}\' --cycles=8 --injection-type=memory-correctable --match=CRd >> fisher.sh"
    FISHER_LOG_LOCATION = "/tmp/fisher"
    FISHER_REGEX = ".*stats: PASS = \d+ - FAIL = (\d+)"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new MemoryCeErrorInjectionLinuxVm object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(MemoryCeErrorInjectionLinuxVm, self).__init__(test_log, arguments, cfg_opts, bios_config_file=self.BIOS_CONFIG_FILE)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.virtualization_obj = VirtualizationCommon(self._log, arguments, cfg_opts)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._sut_os = self.os.os_type.lower()

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(MemoryCeErrorInjectionLinuxVm, self).prepare()
        self._log.info("checking fisher package is installed on SUT")
        try:
            fisher_status = self._common_content_lib.execute_sut_cmd("pip freeze | grep fish-automation", "check fisher package on SUT", self._command_timeout)
            self._log.info(fisher_status)
        except Exception as err:
            raise content_exceptions.TestFail("Fisher package is not installed on the SUT, please install the package")
        self._log.info("Loading EINJ module on SUT")
        self._common_content_lib.execute_sut_cmd("modprobe einj", "install einj", self._command_timeout)

    def execute(self):
        """
        1. use Fisher tool to inject memory correctable error while creating VM
        2. check the result
        3. Check the VM status

        :raise : content_exceptions.TestFail
        :return : True on Success
        """

        #  Create VM names dynamically according to the OS
        self.VM_NAME = self.VM + "_0"
        mac_addr_flag = self._common_content_configuration.enable_with_mac_id()
        memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, self.VM)
        no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, self.VM)
        disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, self.VM)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, self.VM)
        create_vm_command = self._vm_provider_obj._create_linux_vm(self.VM_NAME, os_variant, no_of_cpu, disk_size, memory_size, vm_creation_timeout=1600,
                         vm_nested=None, mac_addr=mac_addr_flag, pool_id=None, get_vm_create_command=True)
        self._log.info("create VM command  \n{}".format(create_vm_command))

        corrected_create_vm_command = create_vm_command.replace('"', '\\\"')
        fisher_command = self.FISHER_CMD.format(corrected_create_vm_command)

        if not self.os.check_if_path_exists(self.FISHER_LOG_LOCATION, directory=True):
            self._common_content_lib.execute_sut_cmd("mkdir -p fisher", "create fisher log directory",
                                                     self._command_timeout, cmd_path="/tmp")
        else:
            self._common_content_lib.execute_sut_cmd("rm -rf /tmp/fisher/*", "delete fisher directory content",
                                                     self._command_timeout)

        self._common_content_lib.execute_sut_cmd(fisher_command, "create fisher file", self._command_timeout, cmd_path=self.FISHER_LOG_LOCATION)
        self._common_content_lib.execute_sut_cmd("chmod 777 fisher.sh", "modify fisher file permission", self._command_timeout, cmd_path=self.FISHER_LOG_LOCATION)
        self._log.info("Injecting Memory Error - {}".format(fisher_command))
        self._common_content_lib.execute_sut_cmd("./fisher.sh", "inject mem correctable error", self._command_timeout, cmd_path=self.FISHER_LOG_LOCATION)

        if not self.os.check_if_path_exists(self.FISHER_LOG_LOCATION + "/fisher*.log"):
            raise content_exceptions.TestFail("Fisher log files were not present in {}".format(self.FISHER_LOG_LOCATION))
        fisher_result = self._common_content_lib.execute_sut_cmd("cat fisher*.log", "fisher log", self._command_timeout, cmd_path=self.FISHER_LOG_LOCATION)

        self._log.info("Inject error cmd output \n{}".format(fisher_result))
        failure_list = re.findall(self.FISHER_REGEX, fisher_result, re.MULTILINE | re.IGNORECASE)
        if not failure_list:
            raise content_exceptions.TestFail("Fisher stats were not present in logs")
        self._log.debug("Memory correctable failure - {}".format(failure_list))
        if not all([failure == "0" for failure in failure_list]):
            raise content_exceptions.TestFail("Memory correctable error injection has failures")

        vm_status = self._vm_provider_obj.find_vm_state(self.VM_NAME)
        if not 'running' == vm_status[0]:
            raise content_exceptions.TestFail("VM is not in running state")
        self._log.info("VM is in running state after injecting the Memory correctable error")

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        try:
            self.virtualization_obj.vm_provider.destroy_vm(self.VM_NAME)
        except Exception as ex:
            raise content_exceptions.TestFail("Unable to Destroy the VM")
        super(MemoryCeErrorInjectionLinuxVm, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemoryCeErrorInjectionLinuxVm.main()
             else Framework.TEST_RESULT_FAIL)
