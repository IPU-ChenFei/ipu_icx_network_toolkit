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
from src.lib.content_base_test_case import ContentBaseTestCase
from src.cet.lib.cet_common_lib import CETCommon
import time
import threading


class CetPauseResumeCetTest(ContentBaseTestCase):
    """
        This test is to verify the system runs without error when vm is paused and resumed
        while CETtest is running on root and 2 level 1 vms.
    """
    WAIT_TIME = 120

    def __init__(self, test_log, arguments, cfg_opts):
        super(CetPauseResumeCetTest, self).__init__(test_log, arguments, cfg_opts)

        self._cet_common_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)
        self.windows_vm_1 = self._cet_common_obj.parse_config(self._cet_common_obj.WINDOWS_GEN2_LEVEL1_VM)
        self.windows_vm_2 = self._cet_common_obj.parse_config(self._cet_common_obj.WINDOWS_GEN1_LEVEL1_VM)

    def prepare(self):
        # type: () -> None
        """ Prepare the sut for CET TEST execution

            :start vm1 and vm2 on level 1
        """
        self._cet_common_obj.start_vm(self.windows_vm_1.get('vm_name'))
        self._cet_common_obj.start_vm(self.windows_vm_2.get('vm_name'))

    def root_thread(self):

        " A thread function to start CETTest loop in root "

        cet_folder_directory = self._cet_common_obj.search_folder_directory(self._cet_common_obj.CET_FOLDER_NAME)
        cet_test = (cet_folder_directory + self._cet_common_obj.CET_TEST_INFINITE_LOOP_PATH)
        self._log.info("Starting CET quicktest loop in root")
        self._cet_common_obj._os.execute(cet_test, 3600)

    def vm_thread(self, vm_name):
        """
        A thread function to start CETTest loop in Level 1 windows VM

            :param: VM-Name
        """

        self._log.info("Starting CET quicktest loop in {}".format(vm_name))
        cet_quick_test_cmd = (self._cet_common_obj.DEFAULT_DIR + self._cet_common_obj.CET_TEST_INFINITE_LOOP_PATH)
        self._cet_common_obj.ssh_execute_level1(vm_name, cet_quick_test_cmd)


    def save_and_restore_thread_fun(self):
        " A thread function to Pause and Resume VMs while running Cet Test"

        time.sleep(self.WAIT_TIME)
        self._log.info("Suspending First VM")
        pause_vm_1 = self._cet_common_obj.SUSPEND_VM_CMD.format(self.windows_vm_1.get('vm_name'))
        self._cet_common_obj._os.execute(pause_vm_1, self._command_timeout)

        self._log.info("Suspending Second VM")
        pause_vm_2 = self._cet_common_obj.SUSPEND_VM_CMD.format(self.windows_vm_2.get('vm_name'))
        self._cet_common_obj._os.execute(pause_vm_2, self._command_timeout)

        time.sleep(self.WAIT_TIME)

        self._log.info("Resuming First VM")
        pause_vm_cmd = self._cet_common_obj.RESUME_VM_CMD.format(self.windows_vm_2.get('vm_name'))

        self._log.info("Resuming Second VM")
        resume_vm_cmd = self._cet_common_obj.RESUME_VM_CMD.format(self.windows_vm_2.get('vm_name'))
        time.sleep(self.WAIT_TIME)


    def execute(self):
        """
        This program will execute CET- stress test by pausing and resuming Hyper-V vms \
        while running CETtest in an infinite loop

        """
        thread_1 = threading.Thread(target=self.root_thread, args=(), daemon=True)
        thread_2 = threading.Thread(target=self.vm_thread, args=(self._cet_common_obj.WINDOWS_GEN2_LEVEL1_VM, ), daemon=True)
        thread_3 = threading.Thread(target=self.vm_thread, args=(self._cet_common_obj.WINDOWS_GEN1_LEVEL1_VM,), daemon=True)
        thread_4 = threading.Thread(target=self.save_and_restore_thread_fun, args=(), daemon=True)


        thread_1.start()
        thread_2.start()
        thread_3.start()
        thread_4.start()

        thread_1.join()
        thread_2.join()
        thread_3.join()
        thread_4.join()
        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetPauseResumeCetTest.main() else Framework.TEST_RESULT_FAIL)
