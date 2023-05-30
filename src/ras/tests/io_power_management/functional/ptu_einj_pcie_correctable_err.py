#!/usr/bin/env python
##########################################################################
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
##########################################################################

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.ras.lib.ras_einj_common import RasEinjCommon
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon
from dtaf_core.lib.dtaf_constants import ProductFamilies


class PtuEinjPcieCorrectableError(IoPmCommon):
    """
    Glasgow_id : 70455 PM RAS -  PTU workload + PCIe Correctable Error Injection

    Inject PCIe correctable error using EINJ while PTU tool running workload.
    """
    _BIOS_CONFIG_FILE = "ptu_pcie_correctable_err_bios_knob.cfg"
    WORKLOAD_START_DELAY_IN_SEC = 3

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PtuEinjPcieCorrectableError object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        super(PtuEinjPcieCorrectableError, self).__init__(
            test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self._ras_einj_obj = RasEinjCommon(self._log, self.os, self._common_content_lib,
                                           self._common_content_configuration, self.ac_power)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(PtuEinjPcieCorrectableError, self).prepare()
        self.install_ptu_on_sut_linux()

    def execute(self):

        mount_success = self.mount_nvme()
        if not mount_success:
            return False

        self.ptu_execute_linux(self.PTU_CPU_TEST, self.PTU_WORKLOAD_TEST_DICT[self.product], duration_sec=3600)
        time.sleep(self.WORKLOAD_START_DELAY_IN_SEC)

        return self._ras_einj_obj.einj_inject_and_check(self._ras_einj_obj.EINJ_PCIE_CORRECTABLE, loops_count=75)


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if PtuEinjPcieCorrectableError.main()
             else Framework.TEST_RESULT_FAIL)
