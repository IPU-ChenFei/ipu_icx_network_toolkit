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

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider

from src.lib.bios_util import BiosUtil
from src.lib.content_configuration import ContentConfiguration
from src.lib.common_content_lib import CommonContentLib


class IomcaEmcaCommon(BaseTestCase):
    """
    Glasgow_id : 58469, 58468
    Common base class for iomca and emca enable test cases
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
        Creates a new IomcaEmca object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param bios_config_file: Used for bios config file
        """
        super(IomcaEmcaCommon, self).__init__(test_log, arguments, cfg_opts)

        self._cfg = cfg_opts

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # AcPowerControlProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = None  # object will be created when we need to use it

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._product = self._common_content_lib.get_platform_family()

        if isinstance(bios_config_file, dict):
            bios_config_file = bios_config_file[self._product]

        cur_path = os.path.dirname(os.path.realpath(__file__))  # getting current path
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path,
                                                                              bios_config_file)

        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()

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
        if not self._os.is_alive():
            self._common_content_lib.perform_graceful_ac_off_on(self._ac)
            self._log.info("Waiting for OS to be alive..")
            self._os.wait_for_os(self._reboot_timeout)

        self._log.info("Clear all OS error logs...")
        self._common_content_lib.clear_all_os_error_logs()
        
        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.

        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # To set the bios knob setting.

        self._log.info("Bios Knobs are Set as per our TestCase and Reboot in Progress to Apply the Settings")
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._log.info("Waiting for OS to be alive..")
        self._os.wait_for_os(self._reboot_timeout)
        self._log.info("Verify the bios knobs after SUT reboot...")
        try:
            self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        except Exception as ex:
            self._log.debug("Ignoring the exception '{}' for now due to instability of the system...".format(ex))
