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


class CxlP0toP1nP1toP0nS0CorestoHdm1nS1CorestoHdm0(CxlCtgCommon):
    """
    hsdes_id :  16015482724 Using CTG tool Generate CXL cache stress traffic between  CXL device Peer caches and
    Socket cores to HDM memory

    Instance1: Peer0 to Peer1 (Opcode 0,25)
    Instance2: Peer1 to Peer0 (Opcode 4,6)
    Instance3: Socket0 Cores to HDM1 Memory (Opcode 9)
    Instance4: Socket1 Cores to HDM0 Memory(Opcode 10)

    Below CTG cahce and mem opcodes are used :

    Peer0 to Peer1 :  WOWRInvF/WrLine_I: 0  RdCurr/RdLine :25
    Peer1 to Peer0 : RdOwn/WrPart_M:5 ,  MemWr/MemWr:6

    Socket0 Cores to HDM1 Memory: MemWrL/Uncacheable:9
    Socket1 Cores to HDM0 Memory: MemWrL/Cacheable: 10
    """
    CMD_FOR_1ST_INSTANCE = "./ctg -v -p {} --sc 0 --vm {} --s1 0 --sc 1 --vm {} --s3 25 -t {} > cmd_1_instance.txt"
    CMD_FOR_2ND_INSTANCE = "./ctg -v -p {} --sc 0 --vm {} --s1 5 --sc 1 --vm {} --s1 6 -t {} > cmd_2_instance.txt"
    LOG_FILE_NAME = " > cmd_{}_instance.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlP0toP1nP1toP0nS0CorestoHdm1nS1CorestoHdm0.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlP0toP1nP1toP0nS0CorestoHdm1nS1CorestoHdm0, self).__init__(
            test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        This is to execute prepare.
        1. clear OS log
        2. Bios loading
        3. Execute to cxl ctg pre-condition to write few register.
        """
        super(CxlP0toP1nP1toP0nS0CorestoHdm1nS1CorestoHdm0, self).prepare(self.sdp)

    def execute(self):
        """
        This method is to execute.
        1. Get the bus of CXL device.
        2. Get the stress execution time
        3. Create VM addresses file
        4. Execute the Stress
        5. Verify the Log in tools output
        """
        #  Instance - 1
        socket_0_bus, socket_1_bus = self.get_cxl_device_bus(sockets=[0, 1])

        hdm1_start, hdm1_end = self.get_hdm_vm_sut_path(socket=1)

        cmd_1_instance = self.CMD_FOR_1ST_INSTANCE.format(int(socket_0_bus, 16), hdm1_start, hdm1_end,
                                                          self.execution_time_in_sec)

        hdm0_start, hdm0_end = self.get_hdm_vm_sut_path(socket=0)

        cmd_2_instance = self.CMD_FOR_2ND_INSTANCE.format(int(socket_1_bus, 16), hdm0_start, hdm0_end,
                                                          self.execution_time_in_sec)

        cpu_0_cores = self.get_the_core_list(cpu=0)
        cpu_1_cores = self.get_the_core_list(cpu=1)
        cmd = self.create_mem_traffic_cmd(int(socket_1_bus, 16), ct_list=cpu_0_cores,
                                          addr_start=0x0,
                                          addr_stop=0x400000,
                                          stride_addr=0x400000, iteration_addr=1048578,
                                          opcode="s1", opcode_value=9,
                                          t=self.execution_time_in_sec
                                          )

        cmd_3_instance = cmd + self.LOG_FILE_NAME.format(3)

        cmd = self.create_mem_traffic_cmd(int(socket_0_bus, 16), ct_list=cpu_1_cores,
                                          addr_start=0x0,
                                          addr_stop=0x400000,
                                          stride_addr=0x400000, iteration_addr=1048578,
                                          opcode="s1", opcode_value=10,
                                          t=self.execution_time_in_sec
                                          )

        cmd_4_instance = cmd + self.LOG_FILE_NAME.format(4)

        self.execute_and_poll_ctg_stress(command_list=[cmd_1_instance, cmd_2_instance, cmd_3_instance, cmd_4_instance])

        self.verify_bw_in_ctg_output_files(file_names=["cmd_1_instance.txt", "cmd_2_instance.txt", "cmd_3_instance.txt",
                                                       "cmd_4_instance.txt"], signatures=[self.BW_0_SIG, self.BW_0_SIG,
                                                                                          self.BW_0_SIG, self.BW_0_SIG])

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlP0toP1nP1toP0nS0CorestoHdm1nS1CorestoHdm0.main() else
             Framework.TEST_RESULT_FAIL)
