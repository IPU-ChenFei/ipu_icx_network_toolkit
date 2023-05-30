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
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.cet.lib.cet_common_lib import CETCommon


class CetShadowstackStressTest(CETCommon):
    HOST = 'root'
    GUEST_VM = "Windows L1A"

    def __init__(self, test_log, arguments, cfg_opts):
        super(CetShadowstackStressTest, self).__init__(test_log, arguments, cfg_opts)
        self._cet_common_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)
        self.vm_name = (self._cet_common_obj.parse_config(self.GUEST_VM).get('vm_name'))

    def prepare(self):
        # type: () -> None
        """set CET bits in Regisrty Editor"""
        self._cet_common_obj.check_vm_exists(self.vm_name)
        vm_state = self._cet_common_obj.get_vm_state(self.vm_name)

        if vm_state is not "Running":
            self._cet_common_obj.start_vm(self.vm_name)

    def thread_function_root(self):
        self._log.info("Starting a stress test thread: ")
        self._cet_common_obj.shadowstack_stress_test()

    def thread_function_Level_1(self):
        self._log.info("Starting a stress test on Level 1")
        spec_test_cmd = (self._cet_common_obj.DEFAULT_DIR + self._cet_common_obj.SPEC_TEST_PATH)
        self._cet_common_obj.ssh_execute_level1(self.GUEST_VM, spec_test_cmd)

    def test_thread(self):
        self._log.info("Wait for 2 hours and check if both systems are still not crashed")
        time.sleep(self._cet_common_obj.STRESS_WAIT_TIME)

        self._log.info("Pinging the systems")
        self._cet_common_obj.ping_system(self.HOST)
        self._cet_common_obj.ping_system(self.GUEST_VM)
        kill_stress_test = self._cet_common_obj._os.execute(self._cet_common_obj.SHADOWSTACK_KILL_CMD, self._command_timeout).stdout
        self._log.info(kill_stress_test)
        self._cet_common_obj.ssh_execute_level1(self.GUEST_VM, self._cet_common_obj.SHADOWSTACK_KILL_CMD)

    def execute(self):
        """This program executes shadowstack stress test on 5 instances"""

        threads = []
        for i in range(5):
            t = threading.Thread(target=self.thread_function_root, args=(), daemon=True)
            t.start()
            threads.append(t)

        threads_on_vm = []
        for i in range(5):
            t = threading.Thread(target=self.thread_function_Level_1, args=(), daemon=True)
            t.start()
            threads_on_vm.append(t)

        last_thread = threading.Thread(target=self.test_thread, args=(), daemon=True)
        last_thread.start()

        for thread in threads:
            thread.join()

        for thread in threads_on_vm:
            thread.join()

        last_thread.join()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetShadowstackStressTest.main() else Framework.TEST_RESULT_FAIL)
