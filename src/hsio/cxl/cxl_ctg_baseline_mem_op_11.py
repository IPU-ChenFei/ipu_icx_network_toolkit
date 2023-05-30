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
import time

from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib import content_exceptions
from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.cxl.cxl_ctg_base_test import CxlCtgCommon
from src.lib.dtaf_content_constants import TimeConstants


class CxlCtgBaselineMemOp11(CxlCtgCommon):
    """
    hsdes_id :  16015652510

    Using CTG tool.  Perform baseline check on BW throughput to see if the CXL device is meeting expected BW
    (within 10% tolerance).
    This is a base line functional test to see that a CXL end point to CPU CXL tiles is functioning correctly
    and that the memory OpCode 11  (11 MemWrPtl (NT Partial Stores by 56 cores to non overlapping HDM regions)
    transfer BW is within a reasonable range of the expected performance levels.  This test will run OpCode selected.

    Expected numbers for mem opcode 11 (MemRd + MemWr ) is  85% of 39.5 GB/s with 10% tolerance level
    Execution Timing Recommendations:

    Run this check point test prior to any new HW stress test CFG execution runs.
    Test is intended as a baseline test to see the BW of a CXL device in slot behind CPU Socket
    """
    CTG_SO_CORE_TO_HDM0_FILE_NAME = " > socket_0_core_to_hdm0_memory.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCtgBaselineMemOp11.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCtgBaselineMemOp11, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCtgBaselineMemOp11, self).prepare(self.sdp)

    def execute(self):
        """
        This method is to execute.
        1. Get the bus of CXL device.
        3. Get Socket 0 core list.
        3. Create Command
        4. Execute the stress and poll it.
        4. Verify the Log
        """
        #  Getting the bus of the CXL device
        socket_0_bus, = self.get_cxl_device_bus(sockets=[0])

        socket_0_cores = self.get_the_core_list(cpu=0)

        self._log.info("Creating command using Socket 0 core thread")
        mem_traffic_cmd = self.create_mem_traffic_cmd(int(socket_0_bus, 16), ct_list=socket_0_cores, addr_start=0x0,
                                                      addr_stop=0x400000, stride_addr=0x400000,
                                                      iteration_addr=1048578, opcode="s1", opcode_value=11,
                                                      t=TimeConstants.FIFTEEN_IN_SEC * 2
                                                      )
        mem_traffic_cmd = mem_traffic_cmd + self.CTG_SO_CORE_TO_HDM0_FILE_NAME
        self._log.info("Mem traffic Command to execute - {}".format(mem_traffic_cmd))

        self.execute_and_poll_ctg_stress(command_list=[mem_traffic_cmd], timeout=TimeConstants.FIFTEEN_IN_SEC * 2)

        self.verify_bw_number_in_ctg_output(file_name="socket_0_core_to_hdm0_memory.txt", tolerance_percent=10,
                                            expected_bw=39.5 * 0.85)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCtgBaselineMemOp11.main() else Framework.TEST_RESULT_FAIL)
