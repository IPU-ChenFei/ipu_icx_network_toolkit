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

from src.ras.lib.lmce_util import LmceUtil
from src.ras.tests.lmce.lmce_common import LmceCommon


class LmceRecoveryExecutionPath(LmceCommon):
    """
    Glasgow_id : G58332-_76_02_01_tonytools
    LMCE allows the capability to deliver the SRAR-type of UCR event to only affected logical processor receiving the
    corrupted data (poison). This feature is supported as part of advanced RAS feature and offered in only shelf4 and
    shelf3 based processor SKUs.

    LMCE implements following capabilities:

    Enumeration: Software mechanism to identify HW support for LMCE
    Control Mechanism: Ability for UEFI-FW to enable/disable LMCE. Requirement for SW to opt-in to LMCE.
    Identification of LMCE: Upon MCE delivery SW is able to determine if the delivered MCE was to only one logical
    processor and global rendezvous participation is not required.
    """
    TEST_CASE_ID = ["G58332", "_76_02_01_tonytools"]
    _BIOS_CONFIG_FILE = "lmce_recovery_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new McaRecoveryExecutionPath object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(LmceRecoveryExecutionPath, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog.conf file to sut and reboot
        2. Clear All Os Logs before Starting the Test Case
        3. Set the bios knobs to its default mode.
        4. Set the bios knobs as per the test case.
        5. Reboot the SUT to apply the new bios settings.
        6. Verify the bios knobs whether they updated properly.

        :return: None
        """
        self._install_collateral.copy_mcelog_conf_to_sut()
        super(LmceRecoveryExecutionPath, self).prepare()

    def execute(self):
        """
        executing verifying_whether_lmce_is_enable to check the lmce is enable or not.
        and executing mca_inject_and_check method from ras_mca_common to inject mca error using Ras Tools and verify the
        error in Os Logs.

        :return: True or False
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        lmce_obj = LmceUtil(self.os, self._log, sdp_obj, cscripts_obj, self._common_content_lib,
                            self._common_content_configuration)
        try:
            ret_val = False
            lmce_enabled = lmce_obj.verify_lmce_is_enabled()
            if lmce_enabled:
                self._log.info("Lmce is enable as Expected...")
            else:
                log_err = "Error: Lmce is not enable"
                self._log.info(log_err)
                raise log_err
            if self._mca_common.mca_inject_and_check(self._mca_common.RAS_MCA_EXE_PATH):
                ret_val = self.lmce_check_log()

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LmceRecoveryExecutionPath.main() else Framework.TEST_RESULT_FAIL)
