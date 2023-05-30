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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.power_management.lib.reset_base_test import ResetBaseTest
from src.storage.test.storage_common import StorageCommon
from src.lib import content_exceptions


class RebootCyclesSataLinux(ResetBaseTest, StorageCommon):
    """
    Pheonix_ID: 16013647293-sata6_gbps_reboot_cycling_at_os_use_mix_of_all_satassd
    This TestCase is Used to Verify Warm Reset Cycles and verifying the status in Every Cycle.
    """
    TEST_CASE_ID = ["16013647293", "sata6_gbps_reboot_cycling_at_os_use_mix_of_all_satassd"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PowerManagementRebootCycles object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(RebootCyclesSataLinux, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Verify if the SUT is booted from Sata

        :return: None
        """
        device_type = self._common_content_configuration.get_device_booted_device_type()
        self.verify_sata_disks_in_sut_and_host()
        lsblk_res = self._storage_provider.get_booted_device()
        device_info = self._storage_provider.get_device_type(lsblk_res, device_type)
        if "SATA" not in device_info["usb_type"].upper():
            raise content_exceptions.TestFail("OS not Booted from on the SATA SSD, please try again..")
        self._log.info("SUT booted from SATA SSD")
        super(RebootCyclesSataLinux, self).prepare()

    def execute(self):
        """
        This Method is used to run the '

        :return: True or False
        """
        for cycle_number in range(self._common_content_configuration.get_num_of_reboot_cycles()):
            self.verify_sata_disks_in_sut_and_host()
            self._log.info("Reboot cycle %d", cycle_number)
            self.warm_reset()
        self._log.info("Sut is booted back to OS in all the '{}' Reboot Cycles"
                       .format(self._common_content_configuration.get_num_of_reboot_cycles()))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RebootCyclesSataLinux.main() else Framework.TEST_RESULT_FAIL)
