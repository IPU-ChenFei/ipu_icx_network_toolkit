#!/usr/bin/env python
##########################################################################
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
##########################################################################

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.lib.platform_config import PlatformConfiguration


class PclsCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Pcls Functionality Test Cases
    """
    _DRAM_NIBBLE_COUNT_PER_MC = 16

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file
    ):
        """
        Create an instance of sut os provider, XmlcliBios provider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            PclsCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts,
            bios_config_file)
        self._product = self._common_content_lib.get_platform_family()
        if self._product not in self._common_content_lib.SILICON_10NM_CPU:
            raise content_exceptions.TestNotImplementedError("This Test Case is Only Supported on ICX, SNR and SPR "
                                                             "Platforms.")
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._command_timeout = self._common_content_configuration.get_command_timeout()

    def verify_pcls_enabled_status_registers(self):
        """
        This Method is to make sure that all the status registers are cleared before execution and verifying
         if pcls are successfully enabled or not.

        :return:
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            try:
                nibble_errors = []
                for dram_nibble in range(self._DRAM_NIBBLE_COUNT_PER_MC):
                    output = cscripts_obj.get_by_path(
                        cscripts_obj.UNCORE,
                        PlatformConfiguration.PCLS_ENABLE_VERIFICATION_DICT[self._product].format(dram_nibble))
                    if output != 0x0:
                        self._log.error("'Pcls{}' is Not enabled".format(dram_nibble))
                        nibble_errors.append("'Pcls{}' is Not enabled".format(dram_nibble))

                if nibble_errors:
                    return False
                self._log.info("All Pcls are Enabled")
                return True

            except Exception as ex:
                self._log.error(
                    "Unable to verify if Pcls are Successfully Enabled or Not due to Exception '{}'".format(ex))
                raise ex
