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
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions
from src.lib.install_collateral import InstallCollateral
from src.lib.uefi_util import UefiUtil


class PwCyclingS5UEFICycles(ContentBaseTestCase):
    """
    HPQC ID : 82179-PI_PW_Cycling_S5_UEFI_10Cycles_L
    1. Changes the Boot order to UEFI shell.
    2. Navigate to UEFI shell.
    3. Executes command in UEFI shell.
    4. Perform 10 uefi ac Cycles
    5. Changes boot order to default.
    6. Navigates to Os.
    """

    TEST_CASE_ID = ["H82179", "PI_PW_Cycling_S5_UEFI_10Cycles_L"]
    WAIT_TIME_OUT = 5

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of PwCyclingS5UEFICycles.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(PwCyclingS5UEFICycles, self).__init__(test_log, arguments, cfg_opts)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        self.itp_xml_cli_util = ItpXmlCli(self._log , cfg_opts)
        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg,
                                                          test_log)  # type: BiosBootMenuProvider
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_obj = ProviderFactory.create(ac_cfg,
                                              test_log)  # type: AcPowerControlProvider
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self._ac_obj,
            self._common_content_configuration, self.os)
        self.previous_boot_oder = None
        self.current_boot_order = None
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()

    def prepare(self):
        # type: () -> None
        """
        checks if the sut is linux.
        """

        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("This test case only "
                                                 "applicable for linux system")
        super(PwCyclingS5UEFICycles, self).prepare()

    def execute(self):
        """
        Navigates to UEFI shell, executes the command and sets
        the boot order to initial boot order and boot to os.

        :return True else false
        """
        self._log.info("Getting current boot order")
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Current boot order {}".format(self.previous_boot_oder))
        self._log.info("Setting the default boot order to {}".format(BootOptions.UEFI))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for UEFI shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        time.sleep(self.WAIT_TIME_OUT)
        for cycle_number in range(self._common_content_configuration.get_num_of_ac_cycles()):
            self._log.info("Starting UEFI shell cycle: %d", cycle_number)
            self._log.info("Executing reset -s")
            self._uefi_obj.shutdown()
            time.sleep(self.WAIT_TIME_OUT)
            self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
            self._log.info("waiting for UEFI shell")
            self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for os to be alive")
        self.os.wait_for_os(self.reboot_timeout)
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
            self.perform_graceful_g3()
        super(PwCyclingS5UEFICycles, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PwCyclingS5UEFICycles.main()
             else Framework.TEST_RESULT_FAIL)
