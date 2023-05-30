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

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.cet.lib.cet_common_lib import CETCommon
from src.lib.content_base_test_case import ContentBaseTestCase
import time
import threading



class CetPauseResumeVMCetQuickTest(ContentBaseTestCase):
    """
        This test is to verify the system runs without error when vm is paused and resumed
        while cetquick test is running on root.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(CetPauseResumeVMCetQuickTest, self).__init__(test_log, arguments, cfg_opts)
        self._cet_common_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)
        self.windows_vm_1 = self._cet_common_obj.parse_config(self._cet_common_obj.WINDOWS_GEN2_LEVEL1_VM)
        self.windows_vm_2 = self._cet_common_obj.parse_config(self._cet_common_obj.WINDOWS_GEN1_LEVEL1_VM)

    def prepare(self):
        # type: () -> None
        """
            Prepare the sut for Hyper-v pause and resume CETQuickTEST
            1. Start VMS
        """
        self._cet_common_obj.start_vm(self.windows_vm_1.get('vm_name'))
        self._cet_common_obj.start_vm(self.windows_vm_2.get('vm_name'))

    def root_thread(self):
        cet_folder_directory = self._cet_common_obj.search_folder_directory(self._cet_common_obj.CET_FOLDER_NAME)
        cet_test = (cet_folder_directory + self._cet_common_obj.CET_TEST_INFINITE_LOOP_PATH)
        self._log.info("Starting CET quicktest loop in root")
        self._cet_common_obj._os.execute(cet_test, self._command_timeout)

    def thread_function_level_1a(self):
        self._log.info("Starting CET quicktest loop in Level 1a")
        cet_quick_test_cmd = (self._cet_common_obj.DEFAULT_DIR +self._cet_common_obj.CET_TEST_INFINITE_LOOP_PATH)
        self._cet_common_obj.ssh_execute_level1(self._cet_common_obj.WINDOWS_GEN2_LEVEL1_VM, cet_quick_test_cmd)


    def thread_function_level_1b(self):
        self._log.info("Starting CET quicktest loop in Level 1b")
        cet_quick_test_cmd = (self.DEFAULT_DIR + self.CET_TEST_INFINITE_LOOP_PATH)
        self._cet_common_obj.ssh_execute_level1(self._cet_common_obj.WINDOWS_GEN1_LEVEL1_VM, cet_quick_test_cmd)

    def pause_and_resume_thread(self):
        time.sleep(120)
        self._log.info("Suspending First VM")
        pause_vm_1 = self._cet_common_obj.SUSPEND_VM_CMD.format(self.windows_vm_1.get('vm_name'))
        self._cet_common_obj._os.execute(pause_vm_1, self._command_timeout)

        self._log.info("Suspending Second VM")
        pause_vm_2 = self._cet_common_obj.SUSPEND_VM_CMD.format(self.windows_vm_2.get('vm_name'))
        self._cet_common_obj._os.execute(pause_vm_2, self._command_timeout)

        time.sleep(120)

        self._log.info("Resuming First VM")
        self._cet_common_obj._os.execute(self._cet_common_obj.RESUME_VM_CMD.format(self.windows_vm_1.get('vm_name')), self._command_timeout)
        self._log.info("Resuming Second VM")
        self._cet_common_obj._os.execute(self._cet_common_obj.RESUME_VM_CMD.format(self.windows_vm_1.get('vm_name')), self._command_timeout)

    def execute(self):
        """
            This function is to verify the cet_test and cet_quick_test continue to run
            without error while 2 vms are paused and resumed.
        """

        thread1 = threading.Thread(target=self.root_thread, args=(), daemon=True)
        thread2 = threading.Thread(target=self.thread_function_level_1a, args=(), daemon=True)
        thread3 = threading.Thread(target=self.thread_function_level_1b, args=(), daemon=True)
        thread4 = threading.Thread(target=self.pause_and_resume_thread, args=(), daemon=True)

        thread1.start()
        thread2.start()
        thread3.start()
        thread4.start()
        time.sleep(self.STRESS_WAIT_TIME)
        thread1.join()
        thread2.join()
        thread3.join()
        thread4.join()

        self._log.info("Pinging System to Check No Crash Occured")
        self.ping_system('root')
        self.ping_system('Win Gen2 L1')
        self.ping_system('Windows Gen1')

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetPauseResumeVMCetQuickTest.main() else Framework.TEST_RESULT_FAIL)
