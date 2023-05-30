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
from src.hsio.cxl.cxl_ctg_base_test import CxlCtgCommon


class CxlCtgS0CoresHdm1Op10AndS1CoresHdm0Op23(CxlCtgCommon):
    """
    hsdes_id :  16015482559 Using CTG tool Generate mem traffic from  Socket Core0 to HDM1 Memory & Socket Core1 to
    HDM0 Memory

    CXL - CTG. stress.mem.socket.concurrent traffic :

    Instance1:  Socket0 Cores to HDM1 Memory(Opcode 10)
    Instance2: Socket1 Cores to HDM0 Memory(Opcode 23)

    Below CTG mem opcodes are used :
    Socket0 Cores to HDM1 Memory :  MemWrL/Cacheable: 10
    Socket1 Cores to HDM0 Memory : MemInv/MemInv :23
    """
    CTG_S0_OUTPUT_FILE_NAME = " > socket_0_to_memory_instance_{}.txt"
    CTG_S1_OUTPUT_FILE_NAME = " > socket_1_to_memory_instance_{}.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCommon.
        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCtgS0CoresHdm1Op10AndS1CoresHdm0Op23, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCtgS0CoresHdm1Op10AndS1CoresHdm0Op23, self).prepare(sdp=self.sdp)

    def execute(self):
        """
        This method is to execute.
        1. Get the bus of CXL device.
        2. Get the stress execution time
        3. Create Cmd for both Session
        4. Execute the Stress
        5. Verify the Log in tools output
        """

        socket_0_bus, socket_1_bus = self.get_cxl_device_bus(sockets=[0, 1])

        cores_0 = self.get_the_core_list(cpu=0)
        self._log.info("Creating command using first-half core thread of cpu 0")
        instance_1_cmd = self.create_mem_traffic_cmd(int(socket_1_bus, 16), ct_list=cores_0, addr_start=0x0,
                                                     addr_stop=0x400000, stride_addr=0x400000,
                                                     iteration_addr=1048578, opcode="s1", opcode_value=10,
                                                     t=self.execution_time_in_sec
                                                     )
        instance_1_cmd = instance_1_cmd + self.CTG_S0_OUTPUT_FILE_NAME.format(1)

        cores_1 = self.get_the_core_list(cpu=1)
        instance_2_cmd = self.create_mem_traffic_cmd(int(socket_0_bus, 16), ct_list=cores_1,
                                                     addr_start=0x0,
                                                     addr_stop=0x400000,
                                                     stride_addr=0x400000, iteration_addr=1048578,
                                                     opcode="s2", opcode_value=23,
                                                     t=self.execution_time_in_sec
                                                     )

        instance_2_cmd = instance_2_cmd + self.CTG_S1_OUTPUT_FILE_NAME.format(2)

        self._log.info("Command for first instance - {}".format(instance_1_cmd))
        self._log.info("Command for second instance - {}".format(instance_2_cmd))

        self.execute_and_poll_ctg_stress(command_list=[instance_1_cmd, instance_2_cmd])

        self.verify_bw_in_ctg_output_files(file_names=["socket_0_to_memory_instance_1.txt",
                                                       "socket_1_to_memory_instance_2.txt"],
                                           signatures=[self.BW_0_SIG, self.BW_0_SIG])

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCtgS0CoresHdm1Op10AndS1CoresHdm0Op23.main() else
             Framework.TEST_RESULT_FAIL)
