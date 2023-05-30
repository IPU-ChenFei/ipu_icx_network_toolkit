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

from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib import content_exceptions
from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.cxl.cxl_ctg_base_test import CxlCtgCommon


class RemoteSocketCxlDevice0toNativeDdrRemoteSocket1CtgCacheStress(CxlCtgCommon):
    """
    hsdes_id :  16015462103 Using CTG tool Generate CXL cache stress traffic between  CXL Device0 to Native DDR
    Remote Socket1

    Below CTG cache opcodes are used :
    CXL Device0 to Native DDR Remote Socket1 : RdOwnNoData/WrLine_M,: 1 ,  MemWr/MemWr: 6.
    """
    STRESS_CMD_FOR_D0_TO_NATIVE_DDR = "./ctg -v -p {} --sc 0 --vm {} --s1 1 --sc 1 --vm {} --s1 6 -t {} > " \
                                      "cxl_ddr_output.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(RemoteSocketCxlDevice0toNativeDdrRemoteSocket1CtgCacheStress, self).__init__(test_log, arguments,
                                                                                           cfg_opts, bios_config_file)
        self.ctg_tool_sut_path = self.install_collateral.install_ctg_tool()
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(RemoteSocketCxlDevice0toNativeDdrRemoteSocket1CtgCacheStress, self).prepare(self.sdp)

    def execute(self):
        """
        This method is to execute.
        1. Get the bus of CXL device.
        2. Get the stress execution time
        3. Create VM addresses file
        4. Execute the Stress
        5. Verify the Log in tools output
        """
        #  Getting the bus of the CXL device
        bus = self._common_content_configuration.get_cxl_target_bus_list(tool="ctg")[0]
        if not self.is_bus_enumerated(bus):
            raise content_exceptions.TestFail("Card is not enumerated in OS")

        execution_time = self._common_content_configuration.get_cxl_stress_execution_runtime(tool="ctg")

        #  Get the First dimm from socket 1 to target for stress
        dimm0 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(tool="ctg", socket=1)[0]

        dimm0_txt = self.create_and_copy_dimm_vm_on_sut(dimm_name=dimm0, ctg_tool_path=self.ctg_tool_sut_path,
                                                        csp=self.csp)

        #  Get the Second dimm from socket 1 to target for stress
        dimm1 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(tool="ctg", socket=1)[1]
        dimm1_txt = self.create_and_copy_dimm_vm_on_sut(dimm_name=dimm1, ctg_tool_path=self.ctg_tool_sut_path,
                                                        csp=self.csp, stride_addr=0x40)
        self._log.info("Device bus- {}".format(int(bus, 16)))

        d0_to_native_ddr_cmd = self.STRESS_CMD_FOR_D0_TO_NATIVE_DDR.format(
            int(bus, 16), dimm0_txt, dimm1_txt, execution_time)

        self.os.execute_async(d0_to_native_ddr_cmd, self.ctg_tool_sut_path)
        if not self.poll_the_ctg_tool(execution_time_seconds=execution_time, api_to_check=[d0_to_native_ddr_cmd]):
            raise content_exceptions.TestFail("CTG tool fail to run")
        self._log.info("Stress execution completed Successfully")

        self.verify_bw_in_ctg_tool_output("cxl_ddr_output.txt", self.ctg_tool_sut_path)

        self._log.info("Bandwidth Captured as expected ")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RemoteSocketCxlDevice0toNativeDdrRemoteSocket1CtgCacheStress.main() else
             Framework.TEST_RESULT_FAIL)
