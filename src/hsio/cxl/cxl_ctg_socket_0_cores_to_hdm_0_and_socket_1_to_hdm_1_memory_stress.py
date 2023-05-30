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


class CxlCtgSocket0CoresToHdm0AndSocket1CoresToHdm1MemoryStress(CxlCtgCommon):
    """
    hsdes_id :  16015482419 Using CTG tool Generate mem traffic from  Socket Core0 to HDM0 Memory &
    Socket Core1 to HDM1 Memory

    Below CTG mem opcodes are used :
    Socket0 Cores to HDM0 Memory :  MemRdData/Cacheable: 30
    Socket1 Cores to HDM1 Memory : MemWrPtl/Uncacheable :11
    """
    CTG_S0_OUTPUT_FILE_NAME = " > socket_0_to_memory_instance_{}.txt"
    CTG_S1_OUTPUT_FILE_NAME = " > socket_1_to_memory_instance_{}.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCtgSocket0CoresToHdm0AndSocket1CoresToHdm1MemoryStress.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCtgSocket0CoresToHdm0AndSocket1CoresToHdm1MemoryStress, self).__init__(test_log, arguments, cfg_opts,
                                                                                        bios_config_file)
        self.ctg_tool_sut_path = self.install_collateral.install_ctg_tool()
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCtgSocket0CoresToHdm0AndSocket1CoresToHdm1MemoryStress, self).prepare(self.sdp)

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
        bus_0 = self._common_content_configuration.get_cxl_target_bus_list(tool="ctg")[0]
        if not self.is_bus_enumerated(bus_0):
            raise content_exceptions.TestFail("Card is not enumerated in OS")

        self._log.info("Card bus- {} is enumerated as Expected".format(bus_0))

        bus_1 = self._common_content_configuration.get_cxl_target_bus_list(tool="ctg")[1]
        if not self.is_bus_enumerated(bus_1):
            raise content_exceptions.TestFail("Card is not enumerated in OS")

        self._log.info("Card bus- {} is enumerated as Expected".format(bus_1))

        execution_time_in_sec = self._common_content_configuration.get_cxl_stress_execution_runtime(tool="ctg")

        cores_0 = self.get_the_core_list(cpu=0)
        instance_1_cmd = self.create_mem_traffic_cmd(int(bus_0, 16), ct_list=cores_0, addr_start=0x0,
                                                     addr_stop=0x400000, stride_addr=0x400000,
                                                     iteration_addr=1048578, opcode="s3", opcode_value=30,
                                                     t=execution_time_in_sec
                                                     )
        instance_1_cmd = instance_1_cmd + self.CTG_S0_OUTPUT_FILE_NAME.format(1)
        self._log.info("Command for 1st instance (Socket 0 to HDM 0 Memory) - {}".format(instance_1_cmd))

        cores_1 = self.get_the_core_list(cpu=1)

        instance_2_cmd = self.create_mem_traffic_cmd(int(bus_1, 16), ct_list=cores_1,
                                                     addr_start=0x0,
                                                     addr_stop=0x400000, stride_addr=0x400000, iteration_addr=1048578,
                                                     t=execution_time_in_sec, opcode="s1", opcode_value=11
                                                     )

        instance_2_cmd = instance_2_cmd + self.CTG_S1_OUTPUT_FILE_NAME.format(2)
        self._log.info("Command for Second instance (Socket 1 to HDM 1 Memory) - {}".format(instance_2_cmd))

        self._log.info("Starting the stress for Socket 0 cores to HDM-0")
        self.os.execute_async(instance_1_cmd, self.ctg_tool_sut_path)

        self._log.info("Starting the stress for Socket 1 cores to HDM-1")
        self.os.execute_async(instance_2_cmd, self.ctg_tool_sut_path)
        if not self.poll_the_ctg_tool(execution_time_seconds=execution_time_in_sec, api_to_check=[instance_1_cmd,
                                                                                           instance_2_cmd]):
            raise content_exceptions.TestFail("CTG tool failed to run")
        self._log.info("Stress execution completed Successfully")

        self._log.info("Checking the bandwidth speed in CTG output. It should not be 0.")
        self.verify_bw_in_ctg_output_files(file_names=["socket_0_to_memory_instance_1.txt",
                                                       "socket_1_to_memory_instance_2.txt"],
                                           signatures=[self.BW_0_SIG, self.BW_0_SIG])

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCtgSocket0CoresToHdm0AndSocket1CoresToHdm1MemoryStress.main() else
             Framework.TEST_RESULT_FAIL)
