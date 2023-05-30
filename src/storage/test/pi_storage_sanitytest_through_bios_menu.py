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
import re

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import PlatformConfigReader, ItpXmlCli
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class StorageSanityTestthroughBIOSmenu(ContentBaseTestCase):
    """
    Glasgow_id : H80279-PI_Storage_SanityTest_through_BIOS_menu(GG-57139)
    This Testcase is used to check PCIe slot information and verification
    """
    TEST_CASE_ID = ["H80279-PI_Storage_SanityTest_through_BIOS_menu(GG-57139)"]
    step_data_dict = {
        1: {'step_details': 'After booting to BIOS:EDKII menu >> Intel SSDXXX (PCIe SSD or U.2 NVMe) '
                            '>> check for device information',
            'expected_results': 'Intel SSDXXX BIOS Knob should present under EDKII menu'},
        2: {'step_details': 'Check relevant PCIe information is present under Intel SSDXXXX. ',
            'expected_results': 'All relevant PCIe information should be displayed correctly'}}

    MODEL_NUMBER_REGEX_PATTERN = r"Model Number[^A-Za-z0-9]*(\S+\s\S+)"
    SERIAL_NUMBER_REGEX_PATTERN = r"Serial Number[^A-Za-z0-9]*(\S+)"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a StorageSanityTestthroughBIOSmenu object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StorageSanityTestthroughBIOSmenu, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(StorageSanityTestthroughBIOSmenu, self).prepare()

    def execute(self):
        """
        1. Gets Platform Config file path.
        2. Store commented line information from Platform Config file in a variable.
        3. PCIe card interface details which is connected to PCIe slot's
        4. Checks for all PCIe card interface details in platform config file commented data.
        5. Sort out failed slots to get information and fails the test case.

        :return: True or False
        :raise: content_exceptions.TestFail
        """
        csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        itp_xmlcli = ItpXmlCli(self._log, self._cfg)
        self._sdp.halt()
        self.platform_config_read = PlatformConfigReader(itp_xmlcli.get_platform_config_file_path(),
                                                         test_log=self._log)
        self._sdp.go()

        #  Gets Platform Config file path
        platform_config_path = itp_xmlcli.get_platform_config_file_path()

        self._log.info("Platform Config file path:{}".format(platform_config_path))

        # Store commented line information from Platform Config file in a variable.
        platform_config_commented_info = self.platform_config_read.get_commented_info()
        self._log.debug("Commented information from platform config file:\n {}".format(platform_config_commented_info))
        self._test_content_logger.start_step_logger(1)
        # PCIe card interface details which is connected to PCIe slot's
        self._log.info("PCIe NVMe card information: {}".
                       format(self._common_content_configuration.get_nvme_cards_info()))
        verified_nvme_cards = set()

        # Checks for all PCIe card interface details in platform config file commented data.

        for each_slot in self._common_content_configuration.get_nvme_cards_info():

            for each_line in platform_config_commented_info.split("\n"):
                if each_slot in each_line:
                    verified_nvme_cards.add(each_slot)

        # Sort out failed slots to get information and fails the test case.
        if len(verified_nvme_cards) != len(self._common_content_configuration.get_nvme_cards_info()):
            failed_slots = set(self._common_content_configuration.get_nvme_cards_info()) - verified_nvme_cards
            raise content_exceptions.TestFail("Failed to verify these bios knobs: {}".format(failed_slots))

        self._log.debug("successfully verified these bios knobs is: {}".format(verified_nvme_cards))

        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        model_number = re.findall(self.MODEL_NUMBER_REGEX_PATTERN, platform_config_commented_info)
        serial_number = re.findall(self.SERIAL_NUMBER_REGEX_PATTERN, platform_config_commented_info)

        serial_number = [num for num in serial_number if str(num) != 'N/A']

        self._log.debug("Model and Serial Numbers of NVMe cards:\nModel numbers:{}\n"
                        "Serial Numbers:{}".format(model_number, serial_number))
        if len(model_number) != len(self._common_content_configuration.get_nvme_cards_info()) and \
                len(serial_number) != len(self._common_content_configuration.get_nvme_cards_info()):
            raise content_exceptions.TestFail("Few Model and Serial Numbers are incorrect\nModel numbers:{}\n"
                                              "Serial Numbers:{}".format(model_number, serial_number))
        self._log.info("successfully verified NVMe cards details")
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageSanityTestthroughBIOSmenu.main() else Framework.TEST_RESULT_FAIL)
