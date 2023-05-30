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

import os
import time

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from src.lib.install_collateral import InstallCollateral
from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.ras_einj_util import RasEinjCommon
from dtaf_core.providers.ac_power import AcPowerControlProvider


class PredictiveFailureAnalysisBaseTest(BaseTestCase):
    """
    This Class is Used as Common Class For all the PredictiveFailureAnalysis Test Cases
    """
    _WAIT_TIME_AFTER_ERROR_INJECTION_IN_SEC = 45
    _MCELOG_DAEMON_CMD = "mcelog --daemon"
    _MCELOG_CLIENT_CMD = "mcelog --client"
    _MCE_LOG_COMMANDS_LIST = [
        "mcelog --daemon",
        "mcelog --client"
    ]

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(PredictiveFailureAnalysisBaseTest, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        bios_config_file = bios_config_file[self._cscripts.silicon_cpu_family]

        cur_path = os.path.dirname(os.path.realpath(__file__))  # getting current path
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path,
                                                                              bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout_in_sec = self._common_content_configuration.get_reboot_timeout()

        # RasEinjCommon
        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)
        self._einj_error = RasEinjCommon(self._log, self._os, cfg_opts, self._common_content_lib,
                                         self._common_content_configuration, self._ac_power)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

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
        self._install_collateral.copy_mcelog_conf_to_sut()
        self._os.reboot(int(self._reboot_timeout_in_sec))
        self._log.info("Clear all OS error logs...")
        self._common_content_lib.clear_all_os_error_logs()

        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.

        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # To set the bios knob setting.

        self._log.info("Bios Knobs are Set as per our TestCase and Reboot in Progress to Apply the Settings")
        self._os.reboot(int(self._reboot_timeout_in_sec))  # To apply the new bios setting.

        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def inject_correctable_error(self):
        """
        This Method is used to Inject the Correctable Error and reported to the OS logs for PFA.

        :return: error_injection_status for correctable error
        """
        try:
            self._einj_error.einj_inject_and_check(self._einj_error.EINJ_MEM_CORRECTABLE)
            time.sleep(self._WAIT_TIME_AFTER_ERROR_INJECTION_IN_SEC)

            for command in self._MCE_LOG_COMMANDS_LIST:
                cmd_result = self._os.execute(command, self._common_content_configuration.get_command_timeout())
                if cmd_result.cmd_failed():
                    log_error = "Failed to run command '{}' with " \
                                "return value = '{}' and " \
                                "std_error='{}'..".format("error", cmd_result.return_code, cmd_result.stderr)
                    self._log.error(log_error)
                    raise RuntimeError(log_error)

            error_injection_status = self._einj_error.verify_os_log_error_messages(
                self._einj_error.DUT_MESSAGES_FILE_NAME, self._einj_error.EINJ_MEM_CE_MESSAGES_LIST)

            if error_injection_status:
                self._log.info("Page offline is triggered because error count reached to the threshold.")
            return error_injection_status

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
