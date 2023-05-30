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
import os
from typing import List, Union

from src.lib import content_exceptions
from src.lib.content_configuration import ContentConfiguration
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.sgx_provider import SGXProvider
from src.security.tests.sgx.sgx_constant import SGXConstant


class SgxCommon(ContentBaseTestCase):
    """
    Base class extension for SgxCommon which holds common arguments
    and functions.
    """
    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None, primary_bios_knob=True):
        """
        Create an instance of sut SgxCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file_path: Bios config file
        :param primary_bios_knob: CI/LI Bios config file is required to be combined to existing knobs.
        """
        self.bios_config_file_path = None
        self._common_content_configuration = ContentConfiguration(test_log)
        self.sgx_properties = self.load_sgx_properties()
        if primary_bios_knob:
            primary_bios_config_path = self.get_sgx_integrity(test_log, cfg_opts)
            test_log.info("Primary bios config path {}".format(primary_bios_config_path))
            if bios_config_file_path:
                self.bios_config_file_path = self.combine_sgx_bios_knobs([primary_bios_config_path, bios_config_file_path])
            else:
                self.bios_config_file_path = self.combine_sgx_bios_knobs([primary_bios_config_path])
        else:
            if bios_config_file_path:
                self.bios_config_file_path = self.combine_sgx_bios_knobs([bios_config_file_path])
            else:
                self.bios_config_file_path = self.combine_sgx_bios_knobs([])
        super(SgxCommon, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file_path)
        try:
            self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
            self.sdp = ProviderFactory.create(self.si_dbg_cfg, self._log)  # type: SiliconRegProvider
        except Exception as e:
            self._log.error("Unable to create ITP Debugger {}".format(e))
            self.sdp = None
        self.sgx_provider = SGXProvider.factory(self._log, self._cfg, self.os, self.sdp)

    def sgx_bios_knobs(self, second_bios_config_file: Union[str, List[str]] = None):
        """
        Returns sgx bios config file, if two or more files are present, it combines all the files and returns the
        new file
        :param second_bios_config_file: takes 2nd bios file, and combines with sgx_bios_file
        :return: bios_config_file
        """
        bios_config_file = [os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)]
        if second_bios_config_file:
            if type(second_bios_config_file) is list:
                bios_config_file.extend(second_bios_config_file)
            else:
                bios_config_file.append(second_bios_config_file)

        return CommonContentLib.get_combine_config(bios_config_file)

    def combine_sgx_bios_knobs(self, secondary_bios_config_path=None):
        """
        Returns sgx bios config file, if two or more files are present, it combines all the files and returns the
        new file

        :param: secondary_bios_config_path: takes 2nd bios file, and combines with sgx_bios_file
        :return: combined bios config files path.
        """
        if not secondary_bios_config_path:
            return None
        else:
            return CommonContentLib.get_combine_config(secondary_bios_config_path)

    def set_bios_knob_without_default(self, bios_confile_path: str) -> None:
        """
        This function sets the bios knobs without load default

        :param bios_confile_path: Name of the bios config file to set without default.
        :return: None
        """
        self._log.info("Setting required bios settings")
        self.bios_util.set_bios_knob(bios_config_file=bios_confile_path)
        self.perform_graceful_g3()
        self._log.info("Verifying bios settings")
        self.bios_util.verify_bios_knob(bios_config_file=bios_confile_path)

    def get_sgx_integrity(self, test_log, cfg_opts) -> str:
        """
        Function returns the sgx integrity type by reading from content configuration file bios Knob path
        :param test_log: test_log obj to log info.
        :param cfg_opts: Configuration Object of provider
        :return: Path of the Logical integrity or cryptographic integrity type
        """
        test_log.debug("SGX properties {}".format(self.sgx_properties))
        memory_integrity_bios_config_path = None
        if self.sgx_properties.get(SGXConstant.SGX_INTEGRITY) == SGXConstant.SGX_LOGICAL_INTEGRITY:
            test_log.info("SGX Logical Integrity is selected")
            memory_integrity_bios_config_path = SgxCommon.get_bios_knob_cfg_complete_path(
                SGXConstant.PRIMARY_BIOS_CONFIG_FILE_LI, cfg_opts)
        elif self.sgx_properties.get(SGXConstant.SGX_INTEGRITY) == SGXConstant.SGX_CRYPTOGRAPHIC_INTEGRITY:
            test_log.info("SGX Cryptographic Integrity is selected")
            memory_integrity_bios_config_path = SgxCommon.get_bios_knob_cfg_complete_path(
                SGXConstant.PRIMARY_BIOS_CONFIG_FILE, cfg_opts)
        if not memory_integrity_bios_config_path:
            raise content_exceptions.TestSetupError("User did not provider any information on Integrity type")
        return memory_integrity_bios_config_path

    # TODO: Need to read all the properties into place..
    def load_sgx_properties(self) -> dict:
        """Loads the SGX properties from content_configuration.xml into a dict.
        :return: Dict of properties from content_configuration.xml file for SGX.
        """
        properties = self._common_content_configuration.get_sgx_properties_params()
        return properties

    @staticmethod
    def get_bios_knob_cfg_complete_path(bios_config_file: str, cfg_opts) -> str:
        """
        Provides the complete path of the bios configuration file based on the platform familes.
        If family is not specified SPR platform is used as the default.
        :param bios_config_file: Bios configure file path
        :param cfg_opts: Configuration Object of provider
        :return: Complete path of bios config file based
        """
        try:
            product = cfg_opts.find(CommonContentLib.PLATFORM_CPU_FAMILY).text
        except Exception as e:
            product = ProductFamilies.SPR
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), bios_config_file.format(product.lower()))
