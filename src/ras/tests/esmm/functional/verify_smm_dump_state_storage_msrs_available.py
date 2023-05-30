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
from dtaf_core.providers.provider_factory import ProviderFactory

from src.ras.lib.esmm_util import EsmmSaveUtil
from src.ras.tests.esmm.esmm_common import EsmmSaveCommon

class VerifySmmDumpStateStorageMsrs(EsmmSaveCommon):
    """
    Glasgow_id : G58338-_74_02_02_verify_smm_dump_state_storage_msrs_available
    This test verifies Spurious SMI Handling flow support

    """
    TEST_CASE_ID = ["G58338", "_74_02_02_verify_smm_dump_state_storage_msrs_available"]
    BIOS_CONFIG_FILE = "esmm_save_state_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifySmmDumpStateStorageMsrs object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifySmmDumpStateStorageMsrs, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self.cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        self.sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        self.esmm_utils_obj = EsmmSaveUtil(self._log, self.sdp_obj, self.cscripts_obj, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        Creates a new VerifySmmDumpStateStorageMsrs object and we are calling a Prepare function
        Prepare Function does the Following tasks:
            2. Set the bios knobs to its default mode.
            3. Set the bios knobs as per the test case.
            4. Reboot the SUT to apply the new bios settings.
            5. Verify the bios knobs that are set.
        :return: None
        """
        super(VerifySmmDumpStateStorageMsrs, self).prepare()

    def execute(self):
        """
        This Method is Used to execute below:
        1.is_long_and_blocked_flow_indication_enabled method and check whether long and
        blocked flow indication is Enabled
        2.is_esmm_bios_write_protect_enable method and check whether Esmm Bios Protect
        is Enabled
        3.Verifies spurious smi handling flow is supported

        :return: True or False
        """
        return (self.esmm_utils_obj.is_long_and_blocked_flow_indication_enabled()
                and self.esmm_utils_obj.is_esmm_save_state_enable() and
                self.esmm_utils_obj.is_esmm_bios_write_protect_enable()
                and self.esmm_utils_obj.verify_smm_dump_state_storage_msrs_available(
                    verify_non_smm_break_msrs=True, verify_smm_break_msrs=False))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifySmmDumpStateStorageMsrs.main() else Framework.TEST_RESULT_FAIL)
