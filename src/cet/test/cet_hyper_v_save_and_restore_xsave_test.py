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



class CetSaveRestoreXsaveTest(ContentBaseTestCase):
    """
        This test is to verify the system runs without error when vm is paused and resumed
        while XSAVE test is running on root.
    """
    WAIT_TIME = 120
    def __init__(self, test_log, arguments, cfg_opts):
        super(CetSaveRestoreXsaveTest, self).__init__(test_log, arguments, cfg_opts)

        self._cet_common_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)
        self.windows_vm = self._cet_common_obj.parse_config(self._cet_common_obj.WINDOWS_GEN2_LEVEL1_VM)

    def prepare(self):
        # type: () -> None
        """
            Prepare the sut for XSAVE TEST
            
            1. Update bcdedit settings 
            2. reboot the system
            3. wait till the system fully restarts
            4. Start a windows vm 
        """
        self._log.info("Updating bcdedit settings")
        self._cet_common_obj.set_bcdedit_setting()
        self.perform_graceful_g3()
        self._cet_common_obj.start_vm(self.windows_vm.get('vm_name'))

    def sigma_test_thread_fun(self):
        self._log.info('Starting sigma test thread')
        self._cet_common_obj.sigma_test()

    def save_and_restore_thread_fun(self):
        time.sleep(self.WAIT_TIME)
        self._log.info("Suspending VM")
        pause_vm_cmd = self._cet_common_obj.SUSPEND_VM_CMD.format(self.windows_vm.get('vm_name'))
        time.sleep(self.WAIT_TIME)
        self._log.info("Resuming VM")
        resume_vm_cmd = self._cet_common_obj.RESUME_VM_CMD.format(self.windows_vm.get('vm_name'))


    def execute(self):
        """This program will execute XSAVE test
            while XSave test is running manually pause and resume the windows VM
        """
        thread_1 = threading.Thread(target=self.sigma_test_thread_fun, args=(), daemon=True)
        thread_2 = threading.Thread(target=self.save_and_restore_thread_fun, args=(), daemon=True)

        thread_1.start()
        thread_2.start()

        thread_1.join()
        thread_2.join()

        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetSaveRestoreXsaveTest.main() else Framework.TEST_RESULT_FAIL)
