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
from src.manageability.lib.manageability_cscripts_common import ManageabilityCscriptsCommon


class VerifyMinMaxMemoryPowerRangeMatchedSku(ManageabilityCommon):
    """
    TC : H80027
    This test confirms the ITP &  PythonSV reads of CPU minimum and maximum TDP memory power match the values from the
    Node Manager command.

    """
    _USER_DOMAIN_ID = 2

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of VerifyMinMaxMemoryPowerRangeMatchedSku

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(VerifyMinMaxMemoryPowerRangeMatchedSku, self).__init__(test_log, arguments, cfg_opts)
        self._miv_cscripts_obj = ManageabilityCscriptsCommon(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        os.remove(self.get_nm_capabilities_obj.miv_log_file)

    def execute(self):
        """
        Test Flow:
        The point of this test is to ensure that the Node Manager can get correct accurate power numbers for the CPU
        Package.
        The test will use two different methods to gain the same data, the given data should match each other (Minimum
        found in method 1 should match Minimum found in method 2).
        Test will run a Native Modules command to get the Minimum and Maximum power numbers for the memory domain
        Test will use an ITP and PythonSV commands to get the same Minimum and Maximum power numbers for the CPU domain
        The min and max numbers obtained using these two methods should match.  If they match the test passes, if they
        do not the test fails.

        """
        self.verify_ip_connectivity()
        if self.get_dev_id_obj.get_region_name() == self.get_dev_id_obj.OPERATIONAL_MODE:
            self._log.info("Device is in Operational Mode")
        else:
            log_error = "Device is not in Operational Mode"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("Record the Max and Min system memory power wattages")

        nm_max_power = self.get_nm_capabilities_obj.get_max_power(self._USER_DOMAIN_ID)
        self._log.info("Max Memory Power Wattage from Node Manager = {}".format(nm_max_power))

        nm_min_power = self.get_nm_capabilities_obj.get_min_power(self._USER_DOMAIN_ID)
        self._log.info("Min Memory Power Wattage from Node Manager = {}".format(nm_min_power))

        self._log.info("Record the Max, Tdp and Min system wattages using cscripts!")

        tdp_power_from_cscripts = self._miv_cscripts_obj.get_cscripts_tdp_memory_power_value()
        self._log.info("Max (TDP) Memory Power Wattage from cscripts = {}".format(tdp_power_from_cscripts))

        min_power_from_cscripts = self._miv_cscripts_obj.get_cscripts_min_memory_power_value()
        self._log.info("Min Memory Power Wattage from cscripts = {}".format(min_power_from_cscripts))

        max_power_from_cscripts = self._miv_cscripts_obj.get_cscripts_max_memory_power_value()
        self._log.info("Max Memory Power Wattage from cscripts = {}".format(max_power_from_cscripts))

        if float(nm_max_power) != float(tdp_power_from_cscripts):
            log_error = "Max Memory Power Wattage from Node Manager Command does not match with Max Memory Power " \
                        "Wattage from ITP or PythonSV"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        if float(nm_min_power) != float(min_power_from_cscripts):
            log_error = "Min Memory Power Wattage from Node Manager Command does not match with Min Memory Power " \
                        "Wattage from ITP or PythonSV"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("Max and Min Memory Power Wattages from Node Manager matches with Max and Min Memory Power "
                       "Wattages from ITP or PythonSV")

        self._log.info("Perform Sanity Check : max > tdp > min ")
        if max_power_from_cscripts > tdp_power_from_cscripts > min_power_from_cscripts:
            self._log.info("Sanity Check successfull : max > tdp > min ")
            ret_value = True
        else:
            log_error = "Sanity Check failed!"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("Detailed MIV Log is Available in '{}'".format(self.dtaf_montana_log_path))
        return ret_value

    def cleanup(self, return_status):
        """Test Cleanup"""
        super(VerifyMinMaxMemoryPowerRangeMatchedSku, self).cleanup(return_status=True)
        if os.path.isfile(self.get_nm_capabilities_obj.miv_log_file):
            os.remove(self.get_nm_capabilities_obj.miv_log_file)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyMinMaxMemoryPowerRangeMatchedSku.main() else Framework.TEST_RESULT_FAIL)
