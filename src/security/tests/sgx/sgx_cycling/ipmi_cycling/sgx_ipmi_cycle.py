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

import sys
import os
import xmltodict
from xml.etree.ElementTree import Element, tostring

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

import src.lib.content_exceptions as content_exceptions
from src.security.tests.sgx.sgx_cycling.sgx_cycling_common import SGXCyclingCommon
from src.lib.content_artifactory_utils import ContentArtifactoryUtils

from src.provider.sgx_provider import SGXProvider


class SGXIPMICycle(SGXCyclingCommon):
    """
    Testcase_id : P18015174664
    This TestCase is Used to Verify SGX Status by Performing IPMI Cycles and verifying the status in Every Cycle.
    """
    BMC_CFG_OPTS = "suts/sut/silicon/bmc"
    BMC_CFG_NAME = "bmc"
    BMC_CRED = "credentials"
    BMC_IP = "ip"
    BMC_USER = "@user"
    BMC_PWD = "@password"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SGXIPMICycle object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._cfg_opts = cfg_opts
        super(SGXIPMICycle, self).__init__(test_log, arguments, cfg_opts)
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, cfg_opts)
        self.total_sgx_ipmi_cycle_number, self.ipmi_cycle_recovery_mode = \
            self._common_content_configuration.get_sgx_num_of_cycles(self._IPMI_CYCLE)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs whether they updated properly.
        5. Read BMC details from system configuration file.
        6. Get the IPMI tool exe path
        """
        super(SGXIPMICycle, self).prepare()
        self.get_bmc_details()
        self.IPMI_PATH = self.download_ipmi_tool()

    def get_bmc_details(self):
        """
        Gets the details of the BMC Ip , username and password from System configurtaion.xml file
        raise content_exceptions.TestSetupError if the BMC Configuration is not populated in system configuration file.
        """
        bmc_cfg_opts = self._cfg_opts.find(self.BMC_CFG_OPTS)
        try:
            cfg_dict = xmltodict.parse(tostring(bmc_cfg_opts))
            dict_bmc = dict(cfg_dict)
            self.BMC_IP_ADDR = dict_bmc[self.BMC_CFG_NAME][self.BMC_IP]
            dict_bmc_cred = dict_bmc[self.BMC_CFG_NAME][self.BMC_CRED]
            self.BMC_DEBUG_USER = dict_bmc_cred[self.BMC_USER]
            self.BMC_PASSWORD = dict_bmc_cred[self.BMC_PWD]
        except Exception as e:
            raise content_exceptions.TestSetupError("DTAF config file is not populated with BMC configuration.")

    def download_ipmi_tool(self):
        """
        Downloads IPMI tool  from Artifactory and returns the Unzipped path of the IPMI tool
        :raise content_exceptions.TestSetupError Unable to get the IPMI tool path.
        :return: return the path of the IPMI tool exe
        """
        ipmi_zip_file = "ipmitoolex.zip"
        ipmi_exe = "ipmitool.exe"
        try:
            tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(ipmi_zip_file)
            dest_path = os.path.join(os.path.dirname(tool_path), os.path.splitext(ipmi_zip_file)[0])
            self._common_content_lib.extract_zip_file_on_host(tool_path, dest_path)
            return os.path.join(dest_path, ipmi_exe)
        except Exception as e:
            raise content_exceptions.TestSetupError("Unable to download IPMI tool")

    def execute(self):
        """
        This Method is Used to execute verify sgx status in various ipmi cycles
        :raise: raise content_exceptions.TestFail if MSR for SGX does not match
                raise content_exceptions.TestFail if warm reboot cycle fails
        :return: True if all ipmi power cycle complete else False
        """
        ipmi_cycle_str = "Ipmi Cycle"
        if not self.sgx_provider.is_sgx_enabled():
            raise content_exceptions.TestFail("Verifying SGX with MSR and EAX value is not successful")
        self.sgx_provider.check_sgx_tem_base_test()
        self.get_bmc_details()
        self.trigger_sgx_cycle(self.total_sgx_ipmi_cycle_number, self.sgx_cycle_type[self._IPMI_CYCLE],
                               ipmi_cycle_str, self.ipmi_cycle_recovery_mode)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXIPMICycle.main() else Framework.TEST_RESULT_FAIL)
