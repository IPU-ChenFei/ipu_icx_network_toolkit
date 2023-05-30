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


class CxlCtgCacheMem1stDevice0toDdrS1And2ndS1CoresToHdm1MemoryStress(CxlCtgCommon):
    """
    hsdes_id :  16015484388

    Using CTG tool Generate CXL cache stress traffic between  CXL Device0  to
    Native DDR Remote Socket1  and Socket cores to remote HDM1 memory

    Instance1:  CXL Device0  to Native DDR Remote Socket   ( Opcode 6 ,7)
    Instance2: Socket0 Cores to HDM1 Memory (Opcode 12)

    Below CTG cache, mem opcodes are used :
    CXL Device0  to Native DDR Remote Socket1:  MemWr/MemWr,:6 ,  WOWrInv/WrPart_I: 7

    Socket0 Cores to HDM1 Memory: MemWrPtl/Uncacheable :11
    """
    CTG_PEER0_TO_PEER1 = " > peer_0_to_peer_1.txt"
    CTG_SO_CORE_TO_HDM1_FILE_NAME = " > socket_0_core_to_hdm1_memory_instance_{}.txt"
    CMD_FOR_PEER0_TO_PEER1 = "./ctg -v -p {} --sc 0 --vm {} --s1 6 --sc 1 --vm {} --s1 7 -t {}"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCtgCacheMem1stDevice0toDdrS1And2ndS1CoresToHdm1MemoryStress, self).__init__(test_log, arguments,
                                                                                             cfg_opts, bios_config_file)
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCtgCacheMem1stDevice0toDdrS1And2ndS1CoresToHdm1MemoryStress, self).prepare(self.sdp)

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
        socket_0_bus, socket_1_bus = self.get_cxl_device_bus(sockets=[0, 1])

        self._log.info("Creating the DDR addresses range file")

        #  Get the First dimm from socket 1 to target for stress
        dimm0 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(tool="ctg", socket=1)[0]

        dimm0_txt = self.create_and_copy_dimm_vm_on_sut(dimm_name=dimm0, ctg_tool_path=self.ctg_tool_sut_path,
                                                        csp=self.csp)

        #  Get the Second dimm from socket 1 to target for stress
        dimm1 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(tool="ctg", socket=1)[1]
        dimm1_txt = self.create_and_copy_dimm_vm_on_sut(dimm_name=dimm1, ctg_tool_path=self.ctg_tool_sut_path,
                                                        csp=self.csp, stride_addr=0x40)

        self._log.info("DDr addresses file got created- {} and {}".format(dimm0_txt, dimm1_txt))

        instance_1_cmd = self.CMD_FOR_PEER0_TO_PEER1.format(int(socket_0_bus, 16), dimm0_txt, dimm1_txt,
                                                            self.execution_time_in_sec)
        instance_1_cmd = instance_1_cmd + self.CTG_PEER0_TO_PEER1

        self._log.info("Command to put traffic from Peer0 to Peer1 - {}".format(instance_1_cmd))

        socket_1_cores = self.get_the_core_list(cpu=1)

        self._log.info("Creating command using Socket 0 core thread")
        instance_2_cmd = self.create_mem_traffic_cmd(int(socket_1_bus, 16), ct_list=socket_1_cores, addr_start=0x0,
                                                     addr_stop=0x400000, stride_addr=0x400000,
                                                     iteration_addr=1048578, opcode="s1", opcode_value=11,
                                                     t=self.execution_time_in_sec
                                                     )
        instance_2_cmd = instance_2_cmd + self.CTG_SO_CORE_TO_HDM1_FILE_NAME.format(2)

        self._log.info("Command for first instance - {}".format(instance_1_cmd))
        self._log.info("Command for second instance - {}".format(instance_2_cmd))

        self.execute_and_poll_ctg_stress(command_list=[instance_1_cmd, instance_2_cmd])

        self.verify_bw_in_ctg_output_files(
            file_names=["peer_0_to_peer_1.txt", "socket_0_core_to_hdm1_memory_instance_2.txt"],
            signatures=[self.BW_0_SIG, self.BW_0_SIG])

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCtgCacheMem1stDevice0toDdrS1And2ndS1CoresToHdm1MemoryStress.main() else
             Framework.TEST_RESULT_FAIL)
