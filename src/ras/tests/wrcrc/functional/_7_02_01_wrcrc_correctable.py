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
import importlib
import os
import sys
import six
from pathlib2 import Path
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from src.lib.content_base_test_case import ContentBaseTestCase
from xml.etree import ElementTree
from src.lib.dtaf_content_constants import ProviderXmlConfigs


class VerifyWrcrcEnabled(ContentBaseTestCase):
    """
    Glassgow_ID : G58283-_7_02_01_wrcrc_correctable
    This feature allows reporting of IIO uncorrected errors via Machine Check Architecture using a dedicated MCA bank.
    This test verifies if BIOS is enabling IOMCA.

    """
    BIOS_CONFIG_FILE = "wrcrc_bios_knobs.cfg"
    TEST_CASE_ID = ["G58283", "_7_02_01_wrcrc_correctable"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyWrcrcEnabled object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        config_file_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
        self._bios_knob_file = os.path.join(config_file_path, self.BIOS_CONFIG_FILE)
        super(VerifyWrcrcEnabled, self).__init__(test_log, arguments, cfg_opts, self._bios_knob_file)
        cpu = self._common_content_lib.get_platform_family()
        pch = self._common_content_lib.get_pch_family()
        sv_cfg = ElementTree.fromstring(ProviderXmlConfigs.PYTHON_SV_XML_CONFIG.format(cpu, pch))
        self.SV = ProviderFactory.create(sv_cfg, self._log)  # type: SiliconRegProvider
        self.reg_provider_obj = ProviderFactory.create(sv_cfg, self._log)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(VerifyWrcrcEnabled, self).prepare()

    def check_wrcrc_enabled(self):
        """"
        This method verifies and injects wrcrc error
        return: True or False
        """
        injected_write_crc = False
        try:
            utils = self.SV.get_mc_utils_obj()
            if utils.is_wrcrc_enabled():
                self._log.info("Wrcrc is enabled successfully")
            else:
                self._log.error("Wrcrc is not enabled successfully")
            errrinj = self.SV.get_err_injection_obj()
            errrinj.inject_wrcrc()
            if utils.show_alert_seen():
                self._log.info("ALERT signal is asserted")
                self._log.info("Error Injection is successfull")
                self._log.info("Doing MCA Check!")
                if utils.set_imc_corr_err_log() == 0:
                    self._log.info("Successfully enabled MC Correctable error logging")
                    injected_write_crc = True
        except Exception as e:
            self._log.error("Unable to Inject Write CRC Transient Error due to the Exception '{}'".format(e))
        return injected_write_crc

    def execute(self):
        """
            This function executes to verify wrcrc enabled:
            return: True or False
        """
        return self.check_wrcrc_enabled()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyWrcrcEnabled.main() else Framework.TEST_RESULT_FAIL)
