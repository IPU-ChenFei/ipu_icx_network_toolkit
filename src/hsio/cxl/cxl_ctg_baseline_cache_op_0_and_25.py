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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib import content_exceptions

from src.hsio.cxl.cxl_ctg_base_test import CxlCtgCommon
from src.lib.dtaf_content_constants import TimeConstants


class CxlCtgBaselineCacheOp0And25(CxlCtgCommon):
    """
    hsdes_id :  18014074769

    Objective:
    Generate CXL.cache traffic using CTG tool.  Perform baseline check on BW throughput to see if the CXL device
    is meeting expected BW (within 10% tolerance).

    This is a base line functional test to see that a CXL end point to CPU CXL tiles is functioning correctly and
    that the cache OpCode 0,25 BW Test(WoWrInvF/RdCurr)  transfer BW is within a reasonable range of the expected
    performance levels.  This test will run OpCode selected.

    Expected numbers for cache opcode 0,25 BW Test(WoWrInvF/RdCurr)  is  85% of 79.1 GB/s with 10% tolerance level

    https://docs.intel.com/documents/cicg_ip/CXL/gen3.5/releases/R2104/HAS/CXLCM_Gen3_5_R2104_HAS.html#bw-expectations

    Execution Timing Recommendations:

    Run this check point test prior to any new HW stress test CFG execution runs.

    Test is intended as a baseline test to see the BW of a CXL device in slot behind CPU Socket.
    """
    CMD = "./ctg -v -p {} --sc 0 --vm {} --s3 25 --vm {} --s1 0 --sc 1 --vm {} --s3 25 --vm {} --s1 0 -t {} > " \
          "cache_ctg_log.txt"
    EXPECTED_BW = 79.1

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCtgBaselineCacheOp4.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCtgBaselineCacheOp0And25, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCtgBaselineCacheOp0And25, self).prepare(self.sdp)

    def execute(self):
        """
        This method is to execute.
        1. Get the bus of CXL device.
        3. Get Socket 0 core list.
        3. Create Command
        4. Execute the stress and poll it.
        4. Verify the Log
        """
        socket = int(self._common_content_configuration.get_cxl_ctg_socket_list()[0])
        bus = self._common_content_configuration.get_cxl_target_bus_list(tool="ctg")[socket]
        if not self.is_bus_enumerated(bus):
            raise content_exceptions.TestFail("Card is not enumerated in OS")
        self._log.info("Card bus- {} is enumerated as Expected".format(bus))

        dimm_name_1 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(socket=socket)[0]
        dimm_name_2 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(socket=socket)[1]

        if dimm_name_1 == dimm_name_2:
            raise content_exceptions.TestFail("Both dimms are same in content config. Please check the tag -"
                                              "<targeted_dimms></targeted_dimms>")

        dimm_1_txt_dict = self.create_and_copy_dimm_vm_on_sut(dimm_name=dimm_name_1,
                                                              ctg_tool_path=self.ctg_tool_sut_path,
                                                              csp=self.csp, no_of_files=2)
        dimm_2_txt_dict = self.create_and_copy_dimm_vm_on_sut(dimm_name=dimm_name_2,
                                                              ctg_tool_path=self.ctg_tool_sut_path,
                                                              csp=self.csp, no_of_files=2)

        execution_time_in_sec = self._common_content_configuration.get_cxl_stress_execution_runtime(tool="ctg")

        traffic_cmd = self.CMD.format(int(bus, 16), dimm_1_txt_dict[0], dimm_1_txt_dict[1], dimm_2_txt_dict[0],
                                      dimm_2_txt_dict[1], execution_time_in_sec)
        self._log.info("Cache Mem traffic Command to execute - {}".format(traffic_cmd))

        self.execute_and_poll_ctg_stress(command_list=[traffic_cmd])

        self.verify_bw_number_in_ctg_output(file_name="cache_ctg_log.txt", tolerance_percent=15,
                                            expected_bw=self.EXPECTED_BW)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCtgBaselineCacheOp0And25.main() else Framework.TEST_RESULT_FAIL)
