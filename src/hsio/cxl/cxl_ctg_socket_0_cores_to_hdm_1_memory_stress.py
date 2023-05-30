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


class CxlCtgSocket0CoresToHdm1MemoryStress(CxlCtgCommon):
    """
    hsdes_id :  16015480282 Using CTG tool Generate mem traffic from  Socket0 Cores to HDM1 Memory

    Below CTG mem opcodes are used :
    Socket0 Cores to HDM1 Memory : MemRdData/MemWrL:12, MemWrL/Uncacheable:9
    """
    CTG_OUTPUT_FILE_NAME = " > socket_0_to_memory_instance_{}.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCtgSocket0CoresToHdm1MemoryStress, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self.ctg_tool_sut_path = self.install_collateral.install_ctg_tool()
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCtgSocket0CoresToHdm1MemoryStress, self).prepare(self.sdp)

    def execute(self):
        """
        This method is to execute.
        1. Get the bus of CXL device.
        2. Get the stress execution time
        3. Create Cmd for both Session
        4. Execute the Stress
        5. Verify the Log in tools output
        """
        #  Getting the bus of the CXL device
        bus = self._common_content_configuration.get_cxl_target_bus_list(tool="ctg")[1]
        if not self.is_bus_enumerated(bus):
            raise content_exceptions.TestFail("Card is not enumerated in OS")

        execution_time_in_sec = self._common_content_configuration.get_cxl_stress_execution_runtime(tool="ctg")

        cores = self.get_the_core_list(cpu=0)
        self._log.info("Creating command using first-half core thread of cpu 0")
        instance_1_cmd = self.create_mem_traffic_cmd(int(bus, 16), ct_list=cores[:int(len(cores)/2)], addr_start=0x0,
                                                     addr_stop=0x400000, stride_addr=0x400000,
                                                     iteration_addr=1048578, opcode="s1", opcode_value= 9,
                                                     t=execution_time_in_sec
                                                     )
        instance_1_cmd = instance_1_cmd + self.CTG_OUTPUT_FILE_NAME.format(1)
        import re
        last_addr_1st_instance = re.findall(r"--addr-stop\s([0-9a-z]+)", instance_1_cmd)
        if not last_addr_1st_instance:
            raise content_exceptions.TestFail("Unable to get the last address from cmd - {}".format(instance_1_cmd))
        self._log.info("Start Address and Last Address - for 1st Instance is - {} and {}".format(
            0x0, last_addr_1st_instance[-1]))

        self._log.info("Creating command using last-half core thread of cpu 0")
        instance_2_cmd = self.create_mem_traffic_cmd(int(bus, 16), ct_list=cores[int(len(cores)/2):],
                                                     addr_start=int(last_addr_1st_instance[-1], 16),
                                                     addr_stop=int(last_addr_1st_instance[-1], 16) + 0x400000,
                                                     stride_addr=0x400000, iteration_addr=1048578,
                                                     opcode="s1", opcode_value=12,
                                                     t=execution_time_in_sec
                                                     )

        instance_2_cmd = instance_2_cmd + self.CTG_OUTPUT_FILE_NAME.format(2)

        import re
        last_addr_2nd_instance = re.findall(r"--addr-stop\s([0-9a-z]+)", instance_2_cmd)
        if not last_addr_2nd_instance:
            raise content_exceptions.TestFail("Unable to get the last address from cmd - {}".format(instance_2_cmd))

        self._log.info("Start Address and Last Address - for 2st Instance is - {} and {}".format(
            last_addr_1st_instance[-1], last_addr_2nd_instance[-1]))

        self._log.info("Command for first instance - {}".format(instance_1_cmd))
        self._log.info("Command for second instance - {}".format(instance_2_cmd))

        self.os.execute_async(instance_1_cmd, self.ctg_tool_sut_path)
        self.os.execute_async(instance_2_cmd, self.ctg_tool_sut_path)

        if not self.poll_the_ctg_tool(execution_time_seconds=execution_time_in_sec, api_to_check=[instance_1_cmd,
                                                                                                  instance_2_cmd]):
            raise content_exceptions.TestFail("CTG tool fail to run")
        self._log.info("Stress execution completed Successfully")

        self.verify_bw_in_ctg_output_files(["socket_0_to_memory_instance_1.txt"],
                                            [self.BW_0_SIG])
        self.verify_bw_in_ctg_output_files(["socket_0_to_memory_instance_2.txt"],
                                           [self.BW_0_SIG])

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCtgSocket0CoresToHdm1MemoryStress.main() else
             Framework.TEST_RESULT_FAIL)
