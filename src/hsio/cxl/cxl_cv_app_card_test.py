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
import sys
import os


from src.provider.stressapp_provider import StressAppTestProvider
from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.hsio.cxl.cxl_common import CxlCommon
from src.lib.dtaf_content_constants import TimeConstants, CvCliToolConstant


class CxlCvAppCardTest(CxlCommon):
    """
    hsdes_id :  15011028896 CXL - CV App Card Compliance Check Test - (Rev 1.0)

    """
    CXL_BIOS_KNOBS = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), "cxl_common_bios_file.cfg")

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=CXL_BIOS_KNOBS):
        """
        Create an instance of CxlCvAppCardTest.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCvAppCardTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._cv_cli_sut_folder_path = self.install_collateral.copy_cv_cli_file_to_sut()
        self._cv_cli_sut_folder_path = self._cv_cli_sut_folder_path.strip() + "/cxl_cv-0.1.0-Linux/bin"
        self.cxl_cv_cli_test_to_run = "1 2 3 4 5 6 7 8 14"
        self.cxl_cv_cli_string_to_check = "CT_{} Completed Successfully"

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCvAppCardTest, self).prepare()
        self.install_collateral.screen_package_installation()
        self.install_collateral.copy_collateral_script(CvCliToolConstant.CV_CLI_LINUX_SCRIPT_FILE,
                                                       self._cv_cli_sut_folder_path)

    def execute(self):
        """
        Method covers
        Basic steps to run compliance verification tests on a CXL device using the CXL_CV test application on a
        "Fedora" Linux platform

        """
        lspci_output = self._common_content_lib.execute_sut_cmd("lspci", "output of lspci", self._command_timeout)
        self._log.info("lspci output for all devices - {}".format(lspci_output))
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self._log.info("Executing cxl cv cli test app run for cxl devices listed - {}".format(self.cxl_bus))
        if not self._common_content_configuration.get_user_inputs_for_cxl_flag:
            self.cxl_bus = self._common_content_configuration.get_cxl_target_bus_list()
        else:
            self.cxl_bus = []
            cxl_inventory_dict = self.get_cxl_device_inventory()
            for key, value in cxl_inventory_dict.items():
                for port in value:
                    if port:
                        bdf = self.get_cxl_bus(port, key, self.csp)
                        self.cxl_bus.append(bdf[2:])
        for bdf in self.cxl_bus:
            if not "{}:00.0".format(bdf) in lspci_output:
                raise content_exceptions.TestFail("Target cxl device - {} not present in lspci listing".format(bdf))
            self._log.info("Running CXL_CV_CLI_TEST for cxl device - {} on the sut".format(bdf))
            cxl_cv_cli_argument_list = ["0x{}".format(bdf), self.cxl_cv_cli_test_to_run]
            json_file_path = self._stress_provider.execute_cv_cli_test(
                arguments=cxl_cv_cli_argument_list, execution_time=TimeConstants.FIVE_MIN_IN_SEC,
                cv_app_dir=self._cv_cli_sut_folder_path.strip(), host_log_dir=self.log_dir)

            # Opening JSON file
            with open(json_file_path, "r") as f:
                data = f.read()

            pass_tests = []
            fail_tests = []
            self._log.info("Json file output after running the selected tests - {}".format(data))
            for test_number in cxl_cv_cli_argument_list[1].split():
                if not self.cxl_cv_cli_string_to_check.format(test_number) in data:
                    fail_tests.append(test_number)
                else:
                    pass_tests.append(test_number)
            self._log.info("Test result status for cxl device - {}".format(bdf))
            self._log.info(" Test numbers passed in cv_cli_app = {}".format(pass_tests))
            self._log.info(" Test numbers failed in cv_cli_app = {}".format(fail_tests))
            if fail_tests:
                return False
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCvAppCardTest.main() else
             Framework.TEST_RESULT_FAIL)
