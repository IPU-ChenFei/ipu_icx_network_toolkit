#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import re
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.common_content_lib import CommonContentLib
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class MaxMemoryConfig(TxtBaseTest):
    """
    PHOENIX ID : 18014070904-Max Memory Config
    Verify maximum memory capacity and verify able to do a Trusted Boot.
    Exploring remapping memory to simulate full capacity.
    """
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    TEST_CASE_ID = ["MaxMemoryConfig", "18014070904"]

    step_data_dict = {1: {'step_details': 'Enable TXT Bios Knobs', 'expected_results': 'Verify TXT is enable'},
                      2: {'step_details': 'Checking dimm and max memory',
                          'expected_results': 'Verify dimm and max memory'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of MaxMemoryConfig

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(MaxMemoryConfig, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._common_obj = CommonContentLib(self._log, self._os, cfg_opts)
        self.sut_cmd = 'lsmem'

    def prepare(self):
        # type: () -> None
        """
        Verify maximum memory capacity (per TOPS) and verify able to do a Trusted Boot.
        Exploring remapping memory to simulate full capacity.

        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._log.info("enable txt")
        self.enable_and_verify_bios_knob()
        super(MaxMemoryConfig, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
          Verify maximum memory capacity (per TOPS) and verify able to do a Trusted Boot.
        :return True else false
        """
        self._test_content_logger.start_step_logger(2)
        #  Show System Memory info
        self._log.info("into BIOS menu...")
        self._os.reboot(self._reboot_timeout)
        if self._serial_bios_util.navigate_bios_menu():
            ret = self._serial_bios_util.get_current_screen_info()
        else:
            self._log.error("GET BIOS INFO ERROR")
            return False
        self._log.info("ret: {}".format(ret))
        bios_info = ret.split('\n')
        memory = [i for i in bios_info if "MB RAM" in i]
        memory = re.findall(r' ([^"]+)MB', memory[0])
        ram_num_mb = re.sub("\D", "", memory[0])
        ram_num_gb = int(ram_num_mb) / 1024
        time.sleep(15)

        self._log.info("Waiting for the SUT to boot to OS.")
        self._os.wait_for_os(self._reboot_timeout)
        if not self._os.is_alive():
            self._log.error("SUT did not power on within the timeout of {} seconds.".format(self._reboot_timeout))
            return False
        else:
            self._log.info("SUT booted to OS successfully.")

        self._log.info("Execute ‘lsmem’ on the SUT and totalmemory")
        cmd_res = self._os.execute(self.sut_cmd, self._command_timeout)
        cmd_res = cmd_res.stdout
        self._log.info("SysMemory info is {}".format(cmd_res))
        memory_info = cmd_res.split('\n')
        total_memory = [i for i in memory_info if re.search(r'Total online memory', memory_info)]
        memory = total_memory[0].split('Total online memory: ')
        memory_gb = memory[1].split('G')[0]
        if not round(ram_num_gb) == round(memory_gb):  # 取整
            self._log.error("SysMemory info is {}, and bios read RAM is {}".format(memory_gb, ram_num_gb))
            return False
        else:
            self._log.info("System memory equals biosmenu read RAM")
        self._test_content_logger.end_step_logger(2, return_val=True)

    def cleanup(self, return_status):  # type: (bool) -> None
        super(MaxMemoryConfig, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MaxMemoryConfig.main() else Framework.TEST_RESULT_FAIL)
