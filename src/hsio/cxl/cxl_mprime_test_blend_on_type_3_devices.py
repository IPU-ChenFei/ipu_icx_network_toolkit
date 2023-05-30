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
from src.hsio.cxl.cxl_common import CxlCommon
from src.lib.dtaf_content_constants import TimeConstants, Mprime95ToolConstant


class CxlMprimeTestBlendOnType3Devices(CxlCommon):
    """
    hsdes_id :  16016844568 CXL mprime test(Blend) on  Host Managed Device Memory for CXL Type3 devices

    """
    CXL_BIOS_KNOBS = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), "cxl_common_bios_file.cfg")

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=CXL_BIOS_KNOBS):
        """
        Create an instance of CxlMprimeTestBlendOnType3Devices.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlMprimeTestBlendOnType3Devices, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._mprime_sut_folder_path = self.install_collateral.install_prime95()


    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlMprimeTestBlendOnType3Devices, self).prepare()
        self.install_collateral.screen_package_installation()
        self.install_collateral.copy_collateral_script(Mprime95ToolConstant.MPRIME95_LINUX_SCRIPT_FILE,
                                                       self._mprime_sut_folder_path.strip())

    def execute(self, type_of_torture=4):
        """
        Method covers
        The Linux implementation is called mprime
        running Blend type torture test.

        :param type_of_torture: type of torture test
        """
        for socket, port, dax_device in zip(self.dax_socket_list, self.dax_port_list, self.dax_device):
            self._log.info(f"Running mprime test for cxl device with dax {dax_device} at socket- {socket} {port}")

            # configure the cxl device on which mprime stress has to run
            node_num, node_mem, core_count = self.configure_cxl_device_with_dax(socket, port, dax_device)

            # Update mprime argument dict
            self.MPRIME_TORTURE_TEST_ARGUMENT_IN_DICT["cmd"] = self.MPRIME_TORTURE_TEST_ARGUMENT_IN_DICT["cmd"].format(node_num)
            self.MPRIME_TORTURE_TEST_ARGUMENT_IN_DICT["Type of torture test to run"] = type_of_torture
            self.MPRIME_TORTURE_TEST_ARGUMENT_IN_DICT["Memory to use"] = node_mem[:-3]
            self.MPRIME_TORTURE_TEST_ARGUMENT_IN_DICT["Time to run each FFT size"] = TimeConstants.ONE_MIN_IN_SEC
            self.MPRIME_TORTURE_TEST_ARGUMENT_IN_DICT["Number of torture test threads to run"] = core_count
            self._stress_provider.execute_mprime(
                arguments=self.MPRIME_TORTURE_TEST_ARGUMENT_IN_DICT, execution_time=TimeConstants.TWO_HOUR_IN_SEC,
                cmd_dir=self._mprime_sut_folder_path.strip(), check_mprime=True)

            for error_sig in self.ERROR_DMESG_SIGNATURES:
                if self._check_os_log. \
                        verify_os_log_error_messages(__file__, self._check_os_log.DUT_DMESG_FILE_NAME,
                                                     error_sig):
                    self._log.info(
                        f"mprime test Failed for cxl device with dax {dax_device} at socket- {socket} {port}")
                    return False
            self._log.info(f"mprime test passed for cxl device with dax {dax_device} at socket- {socket} {port}")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlMprimeTestBlendOnType3Devices.main() else
             Framework.TEST_RESULT_FAIL)
