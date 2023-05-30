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
import re

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


class PoisonCommon(BaseTestCase):
    """
    Glasgow_id : 58273
    Common base class for Memory Poison Enable test case
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
        Creates a new PoisonEnable object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PoisonCommon, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider

        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file[
            self._cscripts.silicon_cpu_family])

        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """
        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.

        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # To set the bios knob setting.

        self._log.info("Bios Knobs are Set as per our TestCase and Reboot to Apply the Settings")
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.

        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def is_memory_poison_enable(self):
        """
        This functions Verifies whether memory poison is enable or not.

        return: Returns True if memory poison is enable, Else False when Not Enabled
        """
        try:
            self._log.info("Halt the Processor ")
            self._sdp.halt()
            ret_val = False
            self._log.info("Read the msr 0x178 register value")
            poison_enable_read_value = self._sdp.msr_read(0x178)
            self._log.info("Verify the 0th bit of the register 0x178 value")
            poison_enable_bit = self._common_content_lib.get_bits(list(poison_enable_read_value), 0)
            if poison_enable_bit == 1:
                self._log.info("Memory Poison is enable")
                ret_val = True
            else:
                self._log.error("Memory Poison is not enable")
            self._log.info("Resume the processor")
            self._sdp.go()

        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex
        return ret_val

