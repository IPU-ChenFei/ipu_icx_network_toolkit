#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,
# copied, reproduced, modified, published, uploaded, posted, transmitted,
# distributed, or disclosed in any way without Intel's prior express written
# permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import sys
import os
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.security.tests.mktme.mktme_common import MktmeBaseTest
from src.lib.bios_util import ItpXmlCli, PlatformConfigReader
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


class MktmeDiscoveryBiosKnobs(MktmeBaseTest):
    """
    HPQC : H79552-PI_Security_MKTME_Discovery_BIOS knobs
    GLASGOW ID : G59513.2-MKTME Discovery (in-band)_BIOS knobs
    Phoenix ID : P18014075076-PI_Security_MKTME_Discovery_BIOSknobs
    Phoenix ID : P18014070387 - Verify TME and MKTME BIOS knobs are present in the menus
    Verify TME and MKTME BIOS knobs are present in the BIOS menus
    """
    TEST_CASE_ID = ["H79552", "PI_Security_MKTME_Discovery_BIOS_knobs",
                    "G59513", "MKTME Discovery (in-band)_BIOS knobs",
                    "P18014075076-PI_Security_MKTME_Discovery_BIOSknobs",
                    "P18014070387 - Verify TME and MKTME BIOS knobs are present in the menus"]
    BIOS_CONFIG_FILE = "../enable_tme/tme_enable_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of MktmeDiscoveryBiosKnobs

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.tme_bios_enable_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                        self.BIOS_CONFIG_FILE)
        super(MktmeDiscoveryBiosKnobs, self).__init__(test_log, arguments, cfg_opts)
        self.xml_config_file = None
        self.platform_xml_config_reader = None

    def prepare(self):
        # type: () -> None
        """
         verify if system supports the TME and Enable TME and MKTME knob

        :return: None
        """
        super(MktmeDiscoveryBiosKnobs, self).prepare()
        # Verify platform will support MKTME or not
        if not self.verify_mktme():
            raise content_exceptions.TestNAError("This CPU SKU does not support for MK-TME")
        self._log.info("SUT supports MK-TME")

    def execute(self):
        """
        1. Check the TME knobs status if TME Bios knob is hidden raise an exception TestFail
        2. Enable the TME Bios knob and update platform config file
        3. Check the MK-TME knobs status
        4. Verify if MK-TME Bios knobs is still hidden after TME has been enabled then raise an exception TestFail.

        :return: True if test completed successfully
        """
        self._csp = ProviderFactory.create(self.sil_cfg, self._log)
        self.xml_config_file = ItpXmlCli(self._log, self._cfg)
        self.platform_xml_config_reader = PlatformConfigReader(self.xml_config_file.get_platform_config_file_path(),
                                                               test_log=self._log)
        # Display the TME knob status
        tme_knob_status = self.platform_xml_config_reader.get_knob_status(self.TME_KNOB_NAME)
        self._log.info("TME Knob status in bios menu= %s", tme_knob_status)
        # Verify if TME Bios knob is accessible
        if self.platform_xml_config_reader.HIDDEN_KNOB_STATUS == tme_knob_status:
            raise content_exceptions.TestFail("TME BIOS knob is not exposed")
        # Enabling TME BIOS Knob
        time.sleep(self.WAIT_TIME_DELAY)
        self.bios_util.set_bios_knob(bios_config_file=self.tme_bios_enable_config_path)
        self.perform_graceful_g3()
        self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_enable_config_path)
        self.platform_xml_config_reader.update_xml_file(self.xml_config_file.get_platform_config_file_path())
        time.sleep(self.WAIT_TIME_DELAY)
        # Display the MK-TME knob status
        mktme_knob_status = self.platform_xml_config_reader.get_knob_status(self.MKTME_KNOB_NAME)
        self._log.info("MK-TME BIOS Knob status in bios menu= %s", mktme_knob_status)
        # Verify if MK-TME Bios knob is accessible after TME has been enabled
        if self.platform_xml_config_reader.HIDDEN_KNOB_STATUS == mktme_knob_status:
            raise content_exceptions.TestFail("MK-TME BIOS knob is not exposed after enabling TME knob")

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        time.sleep(self.WAIT_TIME_DELAY)
        super(MktmeDiscoveryBiosKnobs, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeDiscoveryBiosKnobs.main() else Framework.TEST_RESULT_FAIL)
