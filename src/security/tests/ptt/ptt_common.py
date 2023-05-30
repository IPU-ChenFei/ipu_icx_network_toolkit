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
import six
import os
from abc import ABCMeta

from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.security.tests.ptt.ptt_constants import PTT
from src.lib.bios_util import BiosUtil


@six.add_metaclass(ABCMeta)
class PttBaseTest(BaseTestCase):
    """
    Base class extension for PTT for common arguments, functions, etc.
    """
    _BIOS_CONFIG_FILE = "security_PTT_bios_knobs_enable.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        super(PttBaseTest, self).__init__(test_log, arguments, cfg_opts)
        self.ptt_consts = PTT.get_subtype_cls("PTT", False)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: XmlCliBiosProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        bios_config_file_path = self._common_content_lib.get_config_file_path(os.path.dirname(__file__),
                                                                              self._BIOS_CONFIG_FILE)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider

    def validate_ptt_enabled(self):
        """
        Checks Device ID and Interface ID register values and compares against expected values for PTT.

        :return: True if all register values match (confirm PTT is enabled),
                 False if any register values do not match (confirm PTT is not enabled)
        """
        register_values = {}
        results = True
        self._sdp.halt()
        for register in self.ptt_consts.PTT_REG_OFFSETS.keys():
            mmio_address = self.ptt_consts.PTT_REG_BASE + self.ptt_consts.PTT_REG_OFFSETS[register]
            self._log.debug("Reading register " + register + " from address 0x%x" % mmio_address)
            reg_val = self._sdp.mem_read(hex(mmio_address).rstrip('L') + 'p', 2)
            register_values[register] = reg_val
        self._sdp.go()
        for reg in self.ptt_consts.PTT_ENABLED_REGISTER_VALUES.keys():
            if register_values[reg] != self.ptt_consts.PTT_ENABLED_REGISTER_VALUES[reg]:
                self._log.info("Register %s does not match expected value 0x%x", register_values[reg],
                               self.ptt_consts.PTT_ENABLED_REGISTER_VALUES[reg])
                results = False
            else:
                self._log.info("Register %s matches expected value 0x%x", register_values[reg],
                               self.ptt_consts.PTT_ENABLED_REGISTER_VALUES[reg])
        return results

    def enable_verify_ptt(self):
        """
        This function is set ptt bios knob and verify the BIOS knobs
        validate the device id and interface registers

        :return: True/False if ptt knob is not setting
        """
        ret_val = False
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob setting
        self._os.reboot(self._reboot_timeout)  # To apply Bios change
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set
        if self.validate_ptt_enabled():
            self._log.info("PTT has been enabled successfully.")
            ret_val = True
        else:
            self._log.info("PTT knob not enabled ")
        return ret_val
