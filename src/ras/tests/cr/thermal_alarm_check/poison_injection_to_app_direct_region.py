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

import src.lib.content_exceptions as content_exceptions
from dtaf_core.lib.dtaf_constants import Framework

from src.ras.tests.cr.thermal_alarm_check.thermal_alarm_check_common import ThermalAlarmCheckCommon


class PoisonInjectToAppDirectRegion(ThermalAlarmCheckCommon):
    """
    Glasgow ID: 61156.3
    Verify Poison Injection to App Direct Region and Verification by ARS Sideband  DDR4 + CR 1LM.
    """
    _BIOS_CONFIG_FILE = "poison_injection_to_app_direct_region_bios_knobs.cfg"
    _OS_LOG_SIG = ["Uncorrected error", "Media error"]
    _REGEX_FOR_CHECKING_DPA_ERROR = r"The\snumber\sof\serrors\sfound\sduring\sthe\srange\sscrub\s:\s0x01"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PoisonInjectToAppDirectRegion object,

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param arguments: None
        """
        super(PoisonInjectToAppDirectRegion, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """

        self._log.info("Clearing all Linux OS logs...")
        self._common_content_lib.clear_all_os_error_logs()  # Clear all OS Log
        self._ras_common_obj.set_and_verify_bios_knobs()

    def execute(self):
        """
        1. Check the dimm information like: status, topology, and manageability of dimm with
        populate_memory_dimm_information().
        2. Verify dcpmm are configured as 1lm mode and to get range address for injecting error.
        3. Clear Os Log.
        4. Set dcpmm access path to auto and refresh topology.
        5. Obtain list of dcpmm dimms and also getting the socket, mc, ch for required dimm.
        6. get the rank address and sys address from obtain target address funtion.
        7. Set poison bit at valid device and validating the log from inject poison error.
        8. obtain list of dcpmm dimms.
        9. Clear inject media error.
        10. Verify Os Log.

        :return: True if Test Case passed else False
        :raise: Run time Content Exception
        """
        try:
            self._ipmctl_provider.get_memory_dimm_information()  # Call to check or get Dimm Information
            self.verify_dcpmms_are_configured_in_1lm_mode()
            self._common_content_lib.clear_all_os_error_logs()
            self.set_dcpmm_access_path_to_auto_and_refresh_topology()

            #  obtain list of dcpmm dimms populated with the current media state
            dimm_info = self.obtaining_list_of_dcpmm_dimms(get_dimm_config_flag=True)

            #  obtain target address
            (rank_address, sys_addr) = self.obtain_target_address(dimm_info[0][0], dimm_info[0][1], dimm_info[0][2])

            #  Set the poison bit
            self.set_poison_bit_at_valid_device(int(rank_address, 16))

            #  Set address range scrubber and verify long operation output status
            if self.set_address_range_scrubber_to_inject_scrub_poison(self._REGEX_FOR_CHECKING_DPA_ERROR, rank_address):
                self._log.info("DPA Error is Captured as Expected")
            else:
                log_err = "DPA Error was not Captured"
                raise content_exceptions.TestFail(log_err)

            #  Verify Viral Status
            self.check_viral_policy()

            #  Verify DPA error
            if self.check_dpa_error_in_log(rank_address):
                self._log.info("DPA Error is Captured as Expected")
            else:
                log_err = "DPA error was not Captured as expected"
                raise content_exceptions.TestFail(log_err)

            #  Check dcpmm media is enabled
            self.obtaining_list_of_dcpmm_dimms()
            self._sdp.go()

            #  Clear inject media error
            self._ipmctl_provider.clear_inject_media_error(self._ipmctl_provider.dimm_healthy_and_manageable_list[0],
                                                           rank_address)

            #  Perform ARS on dimm to verify if address is clear or not
            if not self.set_address_range_scrubber_to_inject_scrub_poison(self._REGEX_FOR_CHECKING_DPA_ERROR,
                                                                          rank_address):
                self._log.info("Unexpected error is not Captured as expected")
            else:
                log_err = "Unexpected error was Captured"
                raise content_exceptions.TestFail(log_err)
            ret_val = self.verify_os_log(self._OS_LOG_SIG, self._OS_LOG_SIG, self._OS_LOG_SIG)
            if ret_val:
                self._log.info("Unexpected error is not found as expected")
            else:
                log_err = "Unexpected error was Captured"
                raise content_exceptions.TestFail(log_err)
        except Exception as ex:
            raise ex
        finally:
            self._sdp.go()

        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PoisonInjectToAppDirectRegion.main()
             else Framework.TEST_RESULT_FAIL)
