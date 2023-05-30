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
import re
import paramiko

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_base_test_case import ContentBaseTestCase
from src.cet.lib.cet_common_lib import CETCommon



class CetQuickTestLinux(ContentBaseTestCase):


    def __init__(self, test_log, arguments, cfg_opts):
        super(CetQuickTestLinux, self).__init__(test_log, arguments, cfg_opts)
        self._cet_common_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)
        self.linux_vm = self._cet_common_obj.parse_config(self._cet_common_obj.LINUX_LEVEL1_VM)


    def prepare(self):
        # type: () -> None
        """set Level 1 Linux VM following the BKM Manually"""
        self._cet_common_obj.start_vm(self.windows_vm.get('vm_name'))


    def execute(self):
        """This program will execute CetQuickTestLinux"""
        local = self._cet_common_obj.parse_config(self._cet_common_obj.ROOT)
        dest = self.linux_vm

        local_ip, local_username, local_password = local.get('ip'), local.get('user'), local.get('password')
        dest_ip, dest_username, dest_password = dest.get('ip'), dest.get('user'), dest.get('password')

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(local_ip, username=local_username, password=local_password)

        dest_addr = (dest_ip, 22)
        local_addr = (local_ip, 22)
        ssh_session = ssh_client.get_transport().open_channel("direct-tcpip", dest_addr, local_addr)

        jhost = paramiko.SSHClient()
        jhost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jhost.connect(dest_ip, username=dest_username, password=dest_password, sock=ssh_session)
        #
        stdin, stdout, stderr = jhost.exec_command(" sudo su -c 'source ./cet-smoke-test/run_quick.sh; '", get_pty=True)
        stdin.write("test\n")
        stdin.flush()

        if stderr.channel.recv_exit_status() != 0:
            self._log.info(f'The following error occured: {stderr.readlines()}')
        else:
            self._log.info(f"the following output is produced:\n {stdout.read().decode('utf-8')}")
            return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetQuickTestLinux.main() else Framework.TEST_RESULT_FAIL)
