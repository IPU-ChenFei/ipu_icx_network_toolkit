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
import os
import time
from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.emca_csmi_morphing.emca_csmi_morphing_common import VerifyEmcaCsmiMorphingBase


class VerifyEmcaCsmiMorphing(VerifyEmcaCsmiMorphingBase):
    """
    Glasgow_id : 58266 , 63548
    Verify basic SMI signaling- core CSMI via IFU eMCA gen 2
    This test verifies EMCA CSMI Morphing functionally is supported as a basis for corrected error SMI test cases

    :return:  True if pass, False if not

    """
    _EMCA_CSMI_BIOS_CONFIG_FILE = "emca_csmi_morphing_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EMCACSMIMorphing object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._console_log_path = os.path.splitext(os.path.basename(sys.argv[0]))[0] + '_console.log'
        super(VerifyEmcaCsmiMorphing, self).__init__(test_log, arguments, cfg_opts,
                                               self._EMCA_CSMI_BIOS_CONFIG_FILE, self._console_log_path)

    def prepare(self):
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # This Method is used to Clear All OS Logs.
        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._log.info("Bios Knobs are Set as per our TestCase and Reboot to Apply the Settings")
        self._os.reboot(int(self._reboot_timeout_in_sec))  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def execute(self):
        """
        Execute Main test case.
        With eMCA gen2  enabled, Check that the proper DPA, Rank and SPA address are recorded in the
        error signature when a correctable error is injected with DDRT memory configured in AppDirect mode.

        :return: True if test completed successfully, False otherwise.
        """
        ret_val = False
        if self.verify_emca_csmi_morphing():
            self._os.wait_for_os(self._os_time_out_in_sec)
            if not self._os.is_alive():  # Check to OS is alive
                self._log.info("SUT got powered OFF after injecting error, perform power cycle to bring SUT UP..")
                if self._ac_power.ac_power_off(self._ac_power_time_out_in_sec):
                    self._log.info("AC power supply has been removed")
                else:
                    log_error = "Failed to power-off SUT.."
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
                time.sleep(self._ac_power_time_out_in_sec)
                if self._ac_power.ac_power_on(self._ac_power_time_out_in_sec):
                    self._log.info("AC power supply has been connected")
                else:
                    log_error = "Failed to power-on SUT.."
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
                self._os.wait_for_os(self._os_time_out_in_sec)  # Wait for System to come in OS State
            self._common_content_lib.collect_all_logs_from_linux_sut()
            ret_val = True
        return ret_val


# Execute this test with TestEngine when run as main.
if __name__ == '__main__':
    test_result = VerifyEmcaCsmiMorphing.main()
    sys.exit(Framework.TEST_RESULT_PASS if test_result else Framework.TEST_RESULT_FAIL)
