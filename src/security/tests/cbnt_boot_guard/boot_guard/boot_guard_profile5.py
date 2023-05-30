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

from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory


class BootGuardProfile5(BootGuardValidator):
    """
    Glasgow ID : G58206.7-BootGuard Profile 5, Phoenix ID : 18014075463 - PI_Security_BootGuard_profile5_UEFI
    This Test case Flashes Profile 5 Ifwi and checks for MSR values matches with the excepted value.
    Profile 5 is binary is build based on the information which is populated in content_configuration.xml file.

    pre-requisites:
    Case of non provider container following information has to be updated in content_configuration.xml file
    1.user needs to set the common/ifwi/profile_container value to False
    2.user needs to populate path of the folder of the ifwi and name of ifwi which needs to be modified in the
      in the section common/ifwi/ifwi-file/path and common/ifwi/ifwi-file/name
    3.user needs to populate path of the path of the spsfit tool and name of the executable to be used to modify
    Profile information
    1.user needs to populate as common/profiles/profile5/<bootProfile>Boot Guard Profile 5 - FVME</bootProfile>
    2.user needs to populate as common/build_xml_modifier/<bootProfile>BtGuardProfileConfig</bootProfile>
    3.user needs to populate as common/build_xml_modifier/<keyManifest>0x1</keyManifest>
    ifwi binary in the section common/ifwi/fit_tool/path and common/ifwi/fit_tool/name
    Case of provider container following information has to be updated in content_configuration.xml file
    1.user needs to set the  common/ifwi/profile_container value to True.
    2.user needs to populate path of the folder of the ifwi container folder in the section common/ifwi/container/path
    3.user needs to populate name of the build xml in the section common/ifwi/container/build_xml.
    4.user needs to populate name of the build file in the section common/ifwi/container/build_file.
    5.user needs to modify python build file in case build xml is different which is present in the build file.
    """
    TEST_CASE_ID = ["G58206.7", "BootGuard_Profile_5"]
    step_data_dict = {1: {'step_details': 'Modifying the IFWI binary files for boot profile 5'
                          'key hash value to be updated as AF69F62499DF4234265A43E9FABE6A34A3034DA4CB3F9FADF95CA685BFE7683C'
                                          'key Manifest ID to be updated as 1 and boot to Os after flashing',
                          'expected_results': 'modification with parameters to be successful and Booted to os flashing is successful'},
                      2: {'step_details': 'Verification of MSR_BOOT_GUARD_SACM_INFO should match the excepted value '
                        'TPM1.2: 0x70000007B/0xF0000007B ,TPM2.0: 0x70000007D/0xF0000007D, PTT on HCI: 0x70000007F/0xF0000007F',
                         'expected_results': 'matched the excepted'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of BootGuardProfile5

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(BootGuardProfile5, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_obj = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

    def prepare(self):
        """
        Pre-validating whether sut is alive and checks for Bios flash version before flashing ifwi.

        :return: None
        """
        self._test_content_logger.start_step_logger(1)
        # super(BootGuardProfile5, self).prepare()

    def execute(self):
        """
        This function is used to flash profile 5 binary and compares the value of bios version after flashing.
        Also verifies whether system booted with flash profile 5.

        :return: True if Test case pass
        :raise: content Exception if Boot guard verification fails
        """
        #self._log.info("ac_off")
        self._ac_obj.ac_power_off(10)
        self.flash_binary_image(self.PROFILE5)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        if not self.verify_profile_5():
            raise content_exceptions.TestFail("Bootguard profile 5 verification failed")
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BootGuardProfile5.main() else Framework.TEST_RESULT_FAIL)
