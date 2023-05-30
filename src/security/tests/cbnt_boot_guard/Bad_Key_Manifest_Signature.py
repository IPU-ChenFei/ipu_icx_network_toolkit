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

from dtaf_core.lib.configuration import ConfigurationHelper
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from src.lib.bios_util import BootOptions, ItpXmlCli
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.flash_util import FlashUtil
from src.lib.uefi_util import UefiUtil

from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class BadKeyManifestSignature(TxtBaseTest):
    """
    PHOENIX ID : 18014069466- BadKeyManifestSignature
    """
    TEST_CASE_ID = ["18014069466", "BadKeyManifestSignature"]
    step_data_dict = {
        1: {'step_details': ' enable Boot Guard Profile 5 on the SUT.', 'expected_results': ''},
        2: {'step_details': 'Reboot the system to the UEFI shell'},
        3: {'step_details': 'Ensure that SUT booted measured+verified by executing the last step of '
                            'https://hsdes.intel.com/appstore/article/#/18014070216',
            'expected_results': 'Results should match the expected results of '
                                'https://hsdes.intel.com/appstore/article/#/18014070216'},
        4: {'step_details': 'Using the ShellDmpLog2.efi utility, read the platform PCR data and save the results.',
            'expected_results': 'The file generates with non-zero PCR values.'},
        5: {'step_details': 'Check SHA256 EventLog and TPM SHA256 PCR'}}


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of FitTableCorruption

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(BadKeyManifestSignature, self).__init__(test_log, arguments, cfg_opts)
        self.PROFILE5 = "Profile5"
        self.PROFILE3 = "Profile3"
        self._log = test_log
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_obj = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider
        self._common_content_configuration = ContentConfiguration(self._log)
        self.boot_guard = BootGuardValidator(self._log, arguments, cfg_opts)
        self.sut = ConfigurationHelper.get_sut_config(cfg_opts)
        banino_flash_cfg = ConfigurationHelper.filter_provider_config(sut=self.sut,
                                                                      provider_name=r"flash",
                                                                      attrib=dict(id="2"))
        banino_flash_cfg = banino_flash_cfg[0]
        self._flash = ProviderFactory.create(banino_flash_cfg, test_log)  # type: FlashProvider
        self._flash_obj = FlashUtil(self._log, self._os, self._flash, self._common_content_lib,
                                    self._common_content_configuration)  # type: FlashUtil
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self._ac_obj,
            self._common_content_configuration, self._os)
        super(BadKeyManifestSignature, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._itp_xmlcli = ItpXmlCli(self._log, self._cfg)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        """
        :return: None
        """
        self._test_content_logger.start_step_logger(1)
        super(BadKeyManifestSignature, self).prepare()

    def execute(self):
        """
        :return: True if Test case pass
        :raise: content Exception if Boot guard verification fails
        """
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self.flash_binary_image(self.PROFILE3)
        self._log.info("Getting current boot order")
        self._itp_xmlcli.set_default_boot(BootOptions.UEFI)
        self._log.info("Current boot order {}".format(self.previous_boot_order))
        self._log.info("Setting the default boot order to {}".format(BootOptions.UEFI))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._log.info("waiting for UEFI shell")
        self._uefi_util_obj.graceful_sut_ac_power_on()
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        cmd = "mem 0xfed30328 4"
        cmd_return_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(cmd)
        self._log.info("cmd return value:{}".format(cmd_return_value))
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        self.flash_binary_image(self.PROFILE5)
        self._test_content_logger.end_step_logger(3, return_val=True)
        if not self._os.is_alive():
            return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BadKeyManifestSignature.main() else Framework.TEST_RESULT_FAIL)
