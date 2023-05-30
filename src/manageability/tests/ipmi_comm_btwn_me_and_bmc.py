#!/usr/bin/env python
###############################################################################
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
###############################################################################

import os
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.manageability.lib.manageability_common import ManageabilityCommon


class VerifyIpmiCommunicationBtwnMeAndBmc(ManageabilityCommon):
    """
    This Class is Used to Verify the IPMI Communication between ME and BMC.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of VerifyIpmiCommunicationBtwnMeAndBmc

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(VerifyIpmiCommunicationBtwnMeAndBmc, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        os.remove(self.get_dev_id_obj.miv_log_file)

    def execute(self):
        """
        This Method is Used to Verify the Communication between ME and BMC by Pinging the BMC Ip and get the details of
        device and verify if the device is in Operational Mode or Not.
        """
        self.verify_ip_connectivity()
        if self.get_dev_id_obj.get_region_name() == self.get_dev_id_obj.OPERATIONAL_MODE:
            self._log.info("Device is in Operational Mode")
        else:
            log_error = "Device is not in Operational Mode"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Detailed MIV Log is Available in '{}'".format(self.dtaf_montana_log_path))
        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        super(VerifyIpmiCommunicationBtwnMeAndBmc, self).cleanup(return_status=True)
        if os.path.isfile(self.get_dev_id_obj.miv_log_file):
            os.remove(self.get_dev_id_obj.miv_log_file)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyIpmiCommunicationBtwnMeAndBmc.main() else Framework.TEST_RESULT_FAIL)
