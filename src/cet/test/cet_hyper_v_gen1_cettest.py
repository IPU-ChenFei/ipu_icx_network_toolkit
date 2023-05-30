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

import paramiko
from dtaf_core.lib.dtaf_constants import Framework
from src.cet.lib.cet_common_lib import CETCommon
from src.lib.content_base_test_case import ContentBaseTestCase


class CetHyperVGen1(CETCommon):
    """
           Phoenix_ID  :

           This test is to test CETQuickTest and CETTest on Generation 1 Windows HyperV VM.

    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(CetHyperVGen1, self).__init__(test_log, arguments, cfg_opts)

        self._cet_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)
        self.gen1_vm_l1 = self._cet_obj.parse_config(self._cet_obj.WINDOWS_GEN1_LEVEL1_VM)
        self.gen1_vm_l2 = self._cet_obj.parse_config(self._cet_obj.WINDOWS_GEN1_LEVEL2_VM)

    def prepare(self):  # type: () -> None
        """
        This method starts the virtual machines for the test.
        it assumes VM creation is already setup manually following the BKM.

        1. Strat Gen1 VM on level 1
        2. Start Gen 1 vm on level 2

        """
        self._cet_obj.start_vm(self.gen1_vm_l1.get('vm_name'))
        # self._cet_obj.ssh_execute_level1(self._cet_obj.WINDOWS_GEN1_LEVEL1_VM,
        #                                         self._cet_obj.START_VM_CMD.format(self.gen1_vm_l2.get('vm_name')))

    def execute(self):
        """
            This function runs cettest and cetquicktest on root and level 1 Gen2 vm
        """
        self._log.info("Executing Cet Test on root")
        cet_test_root = self._cet_obj.cet_test("")

        self._log.info('Executing CetQuickTest on Root')
        cet_quick_test_root = self._cet_obj.cet_quick_test()

        self._log.info('Executing CetTest on Level 1 VM')
        cet_test_cmd = (self.DEFAULT_DIR + self.CET_TEST_PATH)
        cet_test_result = self._cet_obj.ssh_execute_level1(self._cet_common_obj.WINDOWS_GEN1_LEVEL1_VM, cet_test_cmd)

        for out in cet_test_result:
            if out != "":
                cet_output = out

        self._log.info('Executing CetQuickTest on Level 1 VM')
        cmd_list = self._cet_obj.create_quicktest_command_list()

        results_list = []
        for i in cmd_list:
            output = self._cet_obj.ssh_execute_level1(self._cet_common_obj.WINDOWS_GEN1_LEVEL1_VM, i)
            for j in output:
                if output[j] != '':
                    results_list.append(output[j])

        audit_mode_recurse_output = results_list[4]
        auditIsValid = self._cet_obj.verify_Shadowstack_values(audit_mode_recurse_output)

        strict_mode_recurse_output = results_list[7]
        strictIsValid = self._cet_obj.verify_Shadowstack_values(strict_mode_recurse_output)

        self._log.info(results_list)

        if self._cet_obj.check_shadowstack_event_log(results_list[-2]):
            validError = True

        return self._cet_obj.cet_test(cet_output) and validError and auditIsValid and strictIsValid


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetHyperVGen1.main() else Framework.TEST_RESULT_FAIL)
