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

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.memory.lib.memory_common_lib import MemoryCommonLib
from src.provider.memory_provider import MemoryProvider
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.memory_constants import MemoryTopology, CpsDimmStepping
from src.lib.install_collateral import InstallCollateral
from src.provider.ipmctl_provider import IpmctlProvider
from src.lib import content_exceptions


class CpsTestCommon(ContentBaseTestCase):
    """
    common class for CPS
    """

    BIOS_CONFIG_FILE_1LM_A1_DIMM_STEPPING = "pi_cr_1lm_osboot_bios_knob_for_a1_stepping.cfg"
    BIOS_CONFIG_FILE_1LM_B0_DIMM_STEPPING = "pi_cr_1lm_osboot_bios_knob_for_b0_stepping.cfg"
    BIOS_CONFIG_FILE_2LM_A1_DIMM_STEPPING = "pi_cr_2lm_osboot_bios_knob_for_a1_stepping.cfg"
    BIOS_CONFIG_FILE_2LM_B0_DIMM_STEPPING = "pi_cr_2lm_osboot_bios_knob_for_b0_stepping.cfg"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None, mode=None):

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os_obj = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._log = test_log

        self._common_content_lib = CommonContentLib(test_log, self._os_obj, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        bios_config_file = self.bios_file_selection(mode)
        super(CpsTestCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._install_collateral = InstallCollateral(test_log, self._os_obj, cfg_opts)
        self._memory_provider = MemoryProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os_obj)
        self._ipmctl_provider = IpmctlProvider.factory(test_log, self._os_obj, execution_env="os", cfg_opts=cfg_opts)
        self._memory_common_lib = MemoryCommonLib(test_log, cfg_opts, self._os_obj)

    def prepare(self):  # type: () -> None
        super(CpsTestCommon, self).prepare()

    def bios_file_selection(self, mode):
        """
        This function is used to get the bios config name based on the Mode and silicon.

        :param: mode : 1LM or 2LM.
        """
        bios_config_file = None
        # ToDo : Currently we are taking CPS Stepping from content configuration xml file and we should take from
        #  PythonSV later.
        cr_dimm_stepping_config = self._common_content_configuration.get_cr_stepping_from_config()
        self._log.info("CPS DIMM Stepping from the config is : {}".format(cr_dimm_stepping_config))
        if mode == MemoryTopology.ONE_LM:
            if cr_dimm_stepping_config.lower() in CpsDimmStepping.A1_STEPPING.lower():
                bios_config_file = self.BIOS_CONFIG_FILE_1LM_A1_DIMM_STEPPING
            elif cr_dimm_stepping_config.lower() in CpsDimmStepping.B0_STEPPING.lower():
                bios_config_file = self.BIOS_CONFIG_FILE_1LM_B0_DIMM_STEPPING
            else:
                raise content_exceptions.TestFail("Please check the CPS DIMM Stepping")
        elif mode == MemoryTopology.TWO_LM:
            if cr_dimm_stepping_config.lower() in CpsDimmStepping.A1_STEPPING.lower():
                bios_config_file = self.BIOS_CONFIG_FILE_2LM_A1_DIMM_STEPPING
            elif cr_dimm_stepping_config.lower() in CpsDimmStepping.B0_STEPPING.lower():
                bios_config_file = self.BIOS_CONFIG_FILE_2LM_B0_DIMM_STEPPING
            else:
                raise content_exceptions.TestFail("Please check the CPS DIMM Stepping")

        self._log.info("The Current BIOS knobs for TC are: {}".format(bios_config_file))
        bios_configfile_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                 bios_config_file)

        return bios_configfile_file_path
