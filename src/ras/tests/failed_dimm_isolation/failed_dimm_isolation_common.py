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

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider

from src.lib.install_collateral import InstallCollateral
from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.ras.lib.ras_einj_common import RasEinjCommon
from src.lib.content_configuration import ContentConfiguration
from dtaf_core.providers.ac_power import AcPowerControlProvider
from src.lib.content_base_test_case import ContentBaseTestCase


class FailedDimmIsolationBaseTest(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Failed Dimm Isolation Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            FailedDimmIsolationBaseTest,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self._common_content_config = ContentConfiguration(self._log)

        self._reboot_timeout_in_sec = self._common_content_config.get_reboot_timeout()
        self._execute_cmd_timeout_in_sec = self._common_content_config.get_command_timeout()
        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)
        self._einj_error = RasEinjCommon(self._log, self._os, self._common_content_lib, self._common_content_config,
                                         self._ac_power)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.

        :return: None
        """
        super(FailedDimmIsolationBaseTest, self).prepare()

    def inject_correctable_error(self):
        """
        This Method is used to Inject the Correctable Error and verify if failed DIMM isolation info is
        reported to the OS logs.

        :return: failed_dimm_isolation_status for correctable error
        """
        try:
            failed_dimm_isolation_status = self._einj_error.einj_inject_and_check(
                self._einj_error.EINJ_MEM_CORRECTABLE,
                failed_dimm_isolation_check=True)
            return failed_dimm_isolation_status

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
