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
from src.power_management.lib.reset_base_test import ResetBaseTest
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.storage.test.storage_common import StorageCommon


class RebootCyclesNvmeWin(ResetBaseTest, StorageCommon):
    """
    Pheonix_ID: 16013613550-U2_NVME_Reboot_cycling_at_OS_use_mix_of_all_NVMe
    This TestCase is Used to Verify Warm Reset Cycles and verifying the status in Every Cycle.
    """
    TEST_CASE_ID = ["16013613550", "U2_NVME_Reboot_cycling_at_OS_use_mix_of_all_NVMe"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PowerManagementRebootCycles object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(RebootCyclesNvmeWin, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise NotImplementedError("This Test Case is Only Supported on Windows")

    def prepare(self):
        # type: () -> None
        """
        1. Verify if the SUT is booted from NVME

        :return: None
        """
        device_type = self._common_content_configuration.get_device_booted_device_type()
        self.verify_os_boot_device_type_windows(device_type)
        super(RebootCyclesNvmeWin, self).prepare()

    def execute(self):
        """
        This Method is used to run the '

        :return: True or False
        """
        for cycle_number in range(self._common_content_configuration.get_num_of_reboot_cycles()):
            self.verify_disks_in_sut_and_host()
            self._log.info("Reboot cycle %d", cycle_number)
            self._common_content_lib.clear_mce_errors()
            self.warm_reset()

        self._log.info("Sut is booted back to OS in all the '{}' Reboot Cycles"
                       .format(self._common_content_configuration.get_num_of_reboot_cycles()))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RebootCyclesNvmeWin.main() else Framework.TEST_RESULT_FAIL)
