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

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.sgx.sgx_registration.sgx_registration_common import SgxRegistrationCommon


class OwnerEpochPrid(SgxRegistrationCommon):
    """
    Phoenix ID : P18015174648-Changing OWNER_EPOCH will not change the PRID

    Verify that changing OWNER_EPOCH will not change the PRID
    """
    OWNER_PRID_BIOS_CONFIG_FILE = "owner_epoch_prid.cfg"
    SOCKET0 = 0
    SOCKET1 = 1

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OwnerEpochPrid

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.owner_prid_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                        self.OWNER_PRID_BIOS_CONFIG_FILE)
        super(OwnerEpochPrid, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup
        1. Enable SGX knobs and DAM knobs
        2. Verify SGX
        3. Verify DAM
        """
        super(OwnerEpochPrid, self).prepare()
        self.sgx.check_sgx_enable()
        self.sgx.verify_dam_enabled()

    def execute(self):
        """
        Verify changing OWNER_EPOCH will not change the PRID

        :return: True if Test case pass else False
        """
        socket0_before_prid_values, socket1_before_prid_values = self.sgx.check_prid(self.serial_log_path)
        serial_log_file = os.path.join(self.serial_log_dir, "serial_log_file.log")
        self.cng_log.redirect(serial_log_file)
        self.set_bios_knobs(self.owner_prid_bios_config_file)
        socket0_after_prid_values, socket1_after_prid_values = self.sgx.check_prid(serial_log_file)
        self._log.info("Comparing socket0 prid values")
        self.sgx.compare_prid_values(socket0_before_prid_values, socket0_after_prid_values, self.SOCKET0)
        self._log.info("Comparing socket1 prid values")
        self.sgx.compare_prid_values(socket1_before_prid_values, socket1_after_prid_values, self.SOCKET1)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OwnerEpochPrid.main() else Framework.TEST_RESULT_FAIL)
