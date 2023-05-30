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
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.lib.common_content_lib import CommonContentLib

from src.provider.sgx_provider import SGXProvider
from src.security.tests.sgx.sgx_constant import SGXConstant
from src.lib import content_base_test_case


class SgxRegistrationCommon(content_base_test_case.ContentBaseTestCase):
    """
    Base class for SGX Auto Multi Package Registration which holds common arguments, functions
    """
    MP_BIOS_CONFIG_FILE = "sgx_auto_multipackage_registration.cfg"
    DAM_CONFIG_FILE = "delayed_authentication_mode.cfg"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of SgxRegistrationCommon

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.mp_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.MP_BIOS_CONFIG_FILE)
        self.dam_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.DAM_CONFIG_FILE)
        if bios_config_file:
            self.bios_config_file = SGXConstant(test_log).sgx_bios_knobs([bios_config_file, self.dam_config_file])
        else:
            self.bios_config_file = SGXConstant(test_log).sgx_bios_knobs(self.dam_config_file)
        super(SgxRegistrationCommon, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SgxRegistrationCommon, self).prepare()

    def execute_sgx_registration(self):
        """
        Executes MP registration installation process
        """
        self.sgx.verify_dam_enabled()
        self.sgx.check_sgx_enable()
        self.sgx.check_psw_installation()
        self.sgx.install_mp_registration()

    def enable_mp_registration_bios_knob(self):
        """
        Enables Auto registration bios knob
        """
        self._log.info("Setting SGX bios settings")
        self.bios_util.set_bios_knob(self.mp_bios_config_file)
        self.perform_graceful_g3()
        self._log.info("Verifying bios settings")
        self.bios_util.verify_bios_knob(self.mp_bios_config_file)
