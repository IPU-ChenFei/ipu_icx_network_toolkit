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
import os
import sys
import re
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.vm_provider import VMs
from src.lib.common_content_lib import CommonContentLib
from src.ras.lib.ras_upi_util import RasUpiUtil
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions
from src.ras.tests.ieh_global.functional.ieh_register_status_common import IehCommon


class ReliabilityUCEMem(IoVirtualizationCommon):
    """
    GLASGOW ID: G69304

    While running stress on multiple VMs,
    Inject UCE errors via fisher into VMM host

    Verify VMs are still functional after 12H run time

    Verify VM is still functional

    Note: Add number of VMs in content_configuration.xml
    Install Fisher tool to SUT
    """
    VM = [VMs.RHEL]
    VM_NAME = None
    TEST_CASE_ID = ["G69304", "Reliability_uce_mem"]
    BIOS_CONFIG_FILE = "uce_mem_error_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new ReliabilityUCEMem object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(ReliabilityUCEMem, self).__init__(test_log, arguments, cfg_opts,
                                              bios_config_file=bios_config_file
                                              )
        self.ieh_common = IehCommon(test_log, arguments, cfg_opts)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.num_vms = self._common_content_configuration.get_num_vms_to_create()
        self.FISHER_TOOL_RUN_DURATION_HOUR_MIN = "12h"
        self.TWELVE_HOURS_TIMER_SEC = 43200
        self.FISHER_TOOL_RUN_CHECK_FREQ = 12

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(ReliabilityUCEMem, self).prepare()

    def execute(self):
        """
        1. create multiple VMs
        2. check VM is functioning or not
        3. run crunch stress tool on all
        4. run fisher tool
        5. check VMs are alive

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        # change all the tolerant files value from 1 to 3 across all machine checks in order to
        # stop the system from rebooting.
        self.ieh_common.update_linux_tolerants()
        vm_os_obj_dict = {}

        #  Create VMs and it's names dynamically according to the OS
        for index in range(self.num_vms):
            #  Create VM names dynamically according to the OS
            self.VM_NAME = self.VM[0] + "_" + str(index)

            vm_os_obj = self.create_and_verify_vm(self.VM_NAME, self.VM[0], crunch_tool=True,
                                                  enable_yum_repo=True)
            vm_ip = vm_os_obj.execute("hostname -I | awk '{print $1}'", self._command_timeout).stdout.strip("\n")
            vm_os_obj_dict[self.VM_NAME] = [vm_os_obj, vm_ip]

        self._log.info("Displaying all created VMs with IPs - \n{}".format(vm_os_obj_dict))

        # Giving time for crunch tool on last VM to ramp
        self._log.info("Giving 5 minute time for crunch tool on last VM to ramp")
        time.sleep(self.WAIT_TIME*10)
        self._log.info("Displaying all created VMs with IPs - \n{}".format(vm_os_obj_dict))

        # list all VM
        vm_list = self.os.execute(self.virtualization_obj.GET_ALL_VM_LIST, self._command_timeout)
        self._log.info("ALL CREATED VM STATUS - \n{}".format(vm_list.stdout))

        self._common_content_lib.clear_os_log()  # To clear os logs
        self._common_content_lib.clear_dmesg_log()  # To clear dmesg logs

        # Install crunch tool for Fisher
        self._log.info("Install Crunch tool...")
        crunch_tool_path = self._install_collateral.install_crunch_tool()
        self._log.info("Crunch Tool Path - {}".format(crunch_tool_path))

        # Run Fisher tool in parallel
        self.start_fisher_tool(self.FISHER_TOOL_CMD_UCE, self.FISHER_TOOL_WORKLOAD, self.FISHER_TOOL_RUN_DURATION_HOUR_MIN)

        # 12 hours timer
        fisher_tool_run_check_intervals = int(self.TWELVE_HOURS_TIMER_SEC/self.FISHER_TOOL_RUN_CHECK_FREQ)
        self._log.info("Fisher tool run check will be tested in every - {} seconds.".
                       format(fisher_tool_run_check_intervals))
        while self.TWELVE_HOURS_TIMER_SEC:
            if self.TWELVE_HOURS_TIMER_SEC % fisher_tool_run_check_intervals == 0:

                # adjusting 1 sec in the timer wasted for tool run checks
                self.TWELVE_HOURS_TIMER_SEC -= 1

                try:
                    cmd_output = self.os.execute(self.FISHER_TOOL_RUN_CHECK_CMD, self._command_timeout).stdout
                    if self.FISHER_TOOL_CHECK_STRING not in cmd_output:
                        raise content_exceptions.TestFail("fisher tool is not executing")
                    self._log.info("Confirming - fisher Tool was Successfully Started")
                except:
                    self._log.info("Couldn't get fisher tool status due to load")

            mins, secs = divmod(self.TWELVE_HOURS_TIMER_SEC, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            print(timer, end="\r")
            time.sleep(1)

            self.TWELVE_HOURS_TIMER_SEC -= 1
        self._log.info("Timer finished, 12 hours completed")

        err_inj = self.os.execute(self.DUT_JOURNALCTL_ERROR_CHECK_CMD, self._command_timeout).stdout
        self._log.info("Number of errors injected - {}".format(err_inj))

        # wait for system to get stable after memory saturation
        self._log.info("Waiting for 10 minutes for system to get stable before ping check")
        time.sleep(self.WAIT_TIME * 20)
        vm_ping_status = True
        for vm_name, vm_os in vm_os_obj_dict.items():
            vm_ping_status = vm_ping_status and self.check_vm_ping_linux(vm_os[0], vm_name, vm_os[1])

        if not (int(err_inj) > 0 and vm_ping_status):
            return False
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        try:
            for index in range(self.num_vms):
                self.VM_NAME = self.VM[0] + "_" + str(index)
                self.virtualization_obj.vm_provider.destroy_vm(self.VM_NAME)
        except Exception as ex:
            raise content_exceptions.TestFail("Unable to Destroy the VM")
        super(ReliabilityUCEMem, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ReliabilityUCEMem.main()
             else Framework.TEST_RESULT_FAIL)
