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
import time


from src.provider.stressapp_provider import StressAppTestProvider
from src.lib import content_exceptions
from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.cxl.cxl_common import CxlCommon



class CxlMlcLoadLatencyCheckType3Linux(CxlCommon):
    """
    hsdes_id :  22014456011 CCXL.mem - MLC Loaded Latency Stress for Type3 cards – Linux OS (rev 1.0)
    

    """
    CXL_BIOS_KNOBS = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), "cxl_common_bios_file.cfg")

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=CXL_BIOS_KNOBS):
        """
        Create an instance of CxlCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlMlcLoadLatencyCheckType3Linux, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self.mlc_tool_path = self.install_collateral.install_mlc_internal_linux()
        self.install_collateral.screen_package_installation()
        self.two_min_in_sec = 120
        self.stress_provider = StressAppTestProvider.factory(self._log, self._cfg, self.os)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlMlcLoadLatencyCheckType3Linux, self).prepare()

    def execute(self):
        """
        Method covers
        Platform stress testing, or individual card stress checks to root port.
        CXL.mem Type 3 memory stress testing utilizing MLC (memory latency checker) Loaded Latency work load onto
        Intel Haley Creek (HYC) cxl Type 3 test card.   Is a Linux OS based stress test.
        Prints the loaded memory latency of the platform.
        
        """
        for socket, port, dax_device in zip(self.dax_socket_list, self.dax_port_list, self.dax_device):
            self._log.info(f"Running mlc test for cxl device with dax {dax_device} at socket- {socket} {port}")

            # configure the cxl device on which mlc stress has to run
            node_num, node_mem, core_count = self.configure_cxl_device_with_dax(socket, port, dax_device)

            self._log.info(f"Configured Node - {node_num}, Memory - {node_mem} and core_count - {core_count}")

            self.mlc_tool_path = self.mlc_tool_path + "/Linux"

            # starting the mlc stress
            self._log.info("Starting mlc stress....")
            self.os.execute(self.cxl_mlc_internal_permission_cmd, self._command_timeout, self.mlc_tool_path)
            self.os.execute_async(self.cxl_mlc_idle_run_cmd.format(int(node_num)), self.mlc_tool_path)

            # verify mlc tool has started
            self._log.info("Verifying mlc tool has started....")
            if not self.stress_provider.check_app_running(app_name="mlc_internal", stress_test_command="./mlc_internal"):
                raise content_exceptions.TestFail("MLC tool is not running......")

            while True:
                time.sleep(self.two_min_in_sec)
                if self.stress_provider.check_app_running(app_name="mlc_internal", stress_test_command="./mlc_internal"):
                    self._log.info("mlc tool is running.......")
                else:
                    break
            self._log.info("MLC tool run completed..\nChecking dmesg")
            for error_sig in self.ERROR_DMESG_SIGNATURES:
                if self._check_os_log. \
                    verify_os_log_error_messages(__file__, self._check_os_log.DUT_DMESG_FILE_NAME,
                                                 error_sig):
                    self._log.info(
                        f"mlc test Failed for cxl device with dax {dax_device} at socket- {socket} {port}")
                    return False
            self._log.info(f"mlc test passed for cxl device with dax {dax_device} at socket- {socket} {port}")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlMlcLoadLatencyCheckType3Linux.main() else
             Framework.TEST_RESULT_FAIL)
