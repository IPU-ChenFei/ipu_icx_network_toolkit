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



class CetHyperVRootLevel2Root(ContentBaseTestCase):
    """
           Phoenix_ID  :

           This test is to test CETQuickTest and CETTest on Hyper-V enabled Root.

           """

    def __init__(self, test_log, arguments, cfg_opts):
        super(CetHyperVRootLevel2Root, self).__init__(test_log, arguments, cfg_opts)

        self._cet_common_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)
        self.windows_vm_l1 = self._cet_common_obj.parse_config(self._cet_common_obj.WINDOWS_GEN2_LEVEL1_VM)
        self.windows_vm_l2 = self._cet_common_obj.parse_config(self._cet_common_obj.WINDOWS_GEN2_LEVEL2_VM)

    def prepare(self):
        # type: () -> None
        """
            Prepare the system to run CET test on windows l1 and windows l2 vms
        """
        self._cet_common_obj.start_vm(self.windows_vm_l1.get('vm_name'))
        self._cet_common_obj.ssh_execute_level1(self._cet_common_obj.WINDOWS_GEN2_LEVEL1_VM,
                                                self._cet_common_obj.START_VM_CMD.format(self.windows_vm_l2.get('vm_name')))


    def execute(self):
        """This program will execute Cet test and cet quick test on nested windows hyper v vm"""

        cet_test_cmd = (self._cet_common_obj.DEFAULT_DIR + self._cet_common_obj.CET_TEST_PATH)
        cmd_list = self._cet_common_obj.create_quicktest_command_list()

        output = self._cet_common_obj.ssh_execute_level2(self._cet_common_obj.WINDOWS_GEN2_LEVEL1_VM,
                                                         self._cet_common_obj.WINDOWS_GEN2_LEVEL2_VM, cet_test_cmd)
        cet_test_result = output[0]
        results_list = []

        for command in cmd_list:
            output = self._cet_common_obj.ssh_execute_level2(self._cet_common_obj.WINDOWS_GEN2_LEVEL1_VM,
                                                             self._cet_common_obj.WINDOWS_GEN2_LEVEL2_VM, command)
            if output[0] != '':
                results_list.append(output[0])
                self._log.info(output[0])
            else:
                results_list.append(output[1])

        audit_mode_recurse_output = results_list[4]
        auditIsValid = self._cet_common_obj.verify_Shadowstack_values(audit_mode_recurse_output)

        strict_mode_recurse_output = results_list[7]
        strictIsValid = self._cet_common_obj.verify_Shadowstack_values(strict_mode_recurse_output)

        # ssh_client = paramiko.SSHClient()
        # ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh_client.connect(self._ip, username=self._user, password=self._password)
        #
        # dest_addr = ('10.165.92.164', 22)
        # local_addr = ('10.165.92.99', 22)
        # ssh_session = ssh_client.get_transport().open_channel("direct-tcpip", dest_addr, local_addr)
        #
        # jhost = paramiko.SSHClient()
        # jhost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # jhost.connect('10.165.93.164', username='Administrator', password='intel@123', sock=ssh_session)
        #
        # stdin, stdout, stderr = jhost.exec_command(cet_test_cmd)


        if self.check_shadowstack_event_log(results_list[-2].decode("utf-8")):
            validError = True

        return self.cet_test(cet_test_result) and validError and auditIsValid and strictIsValid


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetHyperVRootLevel2Root.main() else Framework.TEST_RESULT_FAIL)
