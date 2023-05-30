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
from src.ras.tests.addr_cmd_parity.add_cmd_parity_common import AddrCommon


class CorrectableCapFunctional(AddrCommon):
    """
    Glasgow_id : 58275
    This test inject correctable CAP error and checks MCA values

    MCA (Machine Check Architecture)
    """
    _BIOS_CONFIG_FILE = "addr_bios _knobs.cfg"
    _EXPECTED_CA_ERROR_LIST = ["Corrected error", "Address/Command error"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new CorrectableCapFunctional object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(CorrectableCapFunctional, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs and verify it.

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # This Method is used to Clear All OS Logs.
        self._ras_common.set_and_verify_bios_knobs()  # Set and Verify the bios knobs.

    def execute(self):
        """
        This Method is used to execute the Test Case having following step.
        1. Check the CAP is enable or not.
        2. Inject the CA Perity Error.
        3. Check Os is Alive or not. If not do the pulse power good
        4. Wait for Os.
        5. Verify the OS Log.

        :return: True if Test Case Pass else Fail.
        :raise: RuntimeError
        """
        try:
            if self.is_cap_enabled():
                self._log.info("CAP is Enable")
            else:
                log_err = "CAP is not Enable"
                self._log.error(log_err)
                raise Exception(log_err)
            if self.inject_ca_parity():
                self._log.info("Injected CA Parity Successfully")
            else:
                log_err = "CA Parity Error injection did not happen"
                self._log.error(log_err)
                raise Exception(log_err)
            if not self._os.is_alive():
                self._sdp.pulse_pwr_good()
                self._os.wait_for_os(self._common_content_configuration.get_reboot_timeout())
            ret_val = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                self._os_log_obj.DUT_MESSAGES_FILE_NAME, self._EXPECTED_CA_ERROR_LIST)
        except Exception as ex:
            log_err = "Exception Occurred {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CorrectableCapFunctional.main() else Framework.TEST_RESULT_FAIL)
