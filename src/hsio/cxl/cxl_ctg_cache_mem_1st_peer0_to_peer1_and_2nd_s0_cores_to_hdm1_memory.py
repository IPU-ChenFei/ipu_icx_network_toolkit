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


class CxlCtgCacheMem1stPeer0toPeer1And2ndS0CoresToHdm1MemoryStress(CxlCtgCommon):
    """
    hsdes_id :  16015484090 Using CTG tool Generate CXL cache stress traffic between  Peer caches and Socket cores to
    remote HDM memory

    Instance1:  Peer0 to Peer1   Opcode 2 ,3
    Instance2: Socket0 Cores to HDM1 Memory (Opcode 12)

    Below CTG cache, mem opcodes are used :
    Peer0 to Peer1 :  ItoMWr/WrPush_I:2 ,  WrInv/WrInvF:3
    Socket0 Cores to HDM1 Memory: MemRdData/MemWrL :12
    """
    CTG_PEER0_TO_PEER1 = " > peer_0_to_peer_1.txt"
    CTG_SO_TO_HDM1_FILE_NAME = " > socket_0_to_hdm1_memory_instance_{}.txt"
    CMD_FOR_PEER0_TO_PEER1 = "./ctg -v -p {} --sc 0 --vm {} --s1 2 --sc 1 --vm {} --s1 3 -t {}"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCtgCacheMem1stPeer0toPeer1And2ndS0CoresToHdm1MemoryStress, self).__init__(test_log, arguments,
                                                                                           cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCtgCacheMem1stPeer0toPeer1And2ndS0CoresToHdm1MemoryStress, self).prepare(sdp=self.sdp)

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

        self._log.info("Creating the HDM-1 VM addresses range file")

        hdm1_start_txt, hdm1_end_txt = self.get_hdm_vm_sut_path(socket=1)
        self._log.info("HDM-1 VM addresses file got created- {} and {}".format(hdm1_start_txt, hdm1_end_txt))

        instance_1_cmd = self.CMD_FOR_PEER0_TO_PEER1.format(int(socket_0_bus, 16), hdm1_start_txt, hdm1_end_txt,
                                                            self.execution_time_in_sec)
        instance_1_cmd = instance_1_cmd + self.CTG_PEER0_TO_PEER1

        self._log.info("Command to put traffic from Peer0 to Peer1 - {}".format(instance_1_cmd))

        socket_0_cores = self.get_the_core_list(cpu=0)

        self._log.info("Creating command using Socket 0 core thread")
        instance_2_cmd = self.create_mem_traffic_cmd(int(socket_1_bus, 16), ct_list=socket_0_cores, addr_start=0x0,
                                                     addr_stop=0x400000, stride_addr=0x400000,
                                                     iteration_addr=1048578, opcode="s1", opcode_value=12,
                                                     t=self.execution_time_in_sec
                                                     )
        instance_2_cmd = instance_2_cmd + self.CTG_SO_TO_HDM1_FILE_NAME.format(2)

        self._log.info("Command for first instance - {}".format(instance_1_cmd))
        self._log.info("Command for second instance - {}".format(instance_2_cmd))

        self.execute_and_poll_ctg_stress(command_list=[instance_1_cmd, instance_2_cmd])

        self.verify_bw_in_ctg_output_files(["peer_0_to_peer_1.txt", "socket_0_to_hdm1_memory_instance_2.txt"],
                                           [self.BW_0_SIG, self.BW_0_SIG])

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCtgCacheMem1stPeer0toPeer1And2ndS0CoresToHdm1MemoryStress.main() else
             Framework.TEST_RESULT_FAIL)
