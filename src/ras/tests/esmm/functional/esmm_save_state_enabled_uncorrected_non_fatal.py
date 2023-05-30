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

from src.ras.tests.esmm.esmm_common import EsmmSaveCommon


class EsmmUnCorrectableNonFatal(EsmmSaveCommon):
    """
    Glasgow_id : G60694-eSMM Save State Enabled with UCNA Non-Fatal Error Test
    SMM Save State - Provides an option to save/restore context to/from in silicon storage which provides faster access
    time and immunity from DRAM faults.

    The test attempts to exercise this capability by injecting an uncorrectable non-fatal error.
    """
    TEST_CASE_ID = ["G60694", "eSMM_Save_State_Enabled_with_UCNA_Non_Fatal_Error_Test"]
    BIOS_CONFIG_FILE = "esmm_einj_test_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EsmmUnCorrectableNonFatal object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EsmmUnCorrectableNonFatal, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        Creates a new EsmmUnCorrectableNonFatal object and we are calling a Prepare function
        Prepare Function does the Following tasks:
            1. copying the mcelog config on SUT
            2. Set the bios knobs to its default mode.
            3. Set the bios knobs as per the test case.
            4. Reboot the SUT to apply the new bios settings.
            5. Verify the bios knobs that are set.
        :return: None
        """
        self._install_collateral.copy_mcelog_conf_to_sut()
        super(EsmmUnCorrectableNonFatal, self).prepare()

    def execute(self):
        """
        This Method is Used to Inject Un Correctable non Fatal error and verify.

        :return: True or False
        """
        return self._ras_einj_obj.einj_inject_and_check(error_type=self._ras_einj_obj.EINJ_MEM_UNCORRECTABLE_NONFATAL)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EsmmUnCorrectableNonFatal.main() else Framework.TEST_RESULT_FAIL)
