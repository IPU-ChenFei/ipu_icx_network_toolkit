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
import os
import sys
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from src.lib import content_exceptions
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.hsio.cxl.cxl_ctg_base_test import CxlCtgCommon
from src.lib.dtaf_content_constants import TimeConstants


class RemoteSocketCxlPeer0toPeer1AndPeer1toPeer0CtgCacheStress(CxlCtgCommon):
    """
    hsdes_id : 16015451699 - Using CTG tool Generate CXL cache stress traffic between  Peer0 to Peer1 & Peer1 to Peer0 concurrently  .
    Below CTG cache opcodes are used :

    Peer 0 to Peer 1 cache : RdCurr/RdLine : 25,  WOWRInvF/WrLine_I: 0
    Peer1 to Peer0 cache :ItoMWr/WrPush_I: 2, WrInv/WrInvF: 3
    """
    CMD_FOR_PEER0_TO_PEER1 = "./ctg -v -p {} --sc 0 --vm {} --s1 0 --sc 1 --vm {} --s3 25 -t {} > peer0_to_peer1.txt"
    CMD_FOR_PEER1_TO_PEER0 = "./ctg -v -p {} --sc 0 --vm {} --s1 2 --sc 1 --vm {} --s1 3 -t {} > peer1_to_peer0.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(RemoteSocketCxlPeer0toPeer1AndPeer1toPeer0CtgCacheStress, self).__init__(test_log, arguments,
                                                                                       cfg_opts, bios_config_file)

        self.ctg_tool_sut_path = self.install_collateral.install_ctg_tool()
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(RemoteSocketCxlPeer0toPeer1AndPeer1toPeer0CtgCacheStress, self).prepare(self.sdp)

    def execute(self):
        """
        This method is to execute.

        1. Get the CXL PCIe Device bus.
        2. Get the stress execution time.
        3. Create HDM addresses file
        4. Execute the peer0 to peer1 stress and peer1 to peer0 stress.
        5. Verify the expected signature in tool execution output.
        """
        #  Getting the bus of the CXL device
        bus1 = self._common_content_configuration.get_cxl_target_bus_list(tool="ctg")[0]

        if not self.is_bus_enumerated(bus1):
            raise content_exceptions.TestFail("Card bus({}) is not enumerated in OS".format(bus1))
        self._log.info("Card bus - {} is enumerated as expected")

        bus2 = self._common_content_configuration.get_cxl_target_bus_list(tool="ctg")[1]
        if not self.is_bus_enumerated(bus2):
            raise content_exceptions.TestFail("Card bus({}) is not enumerated in OS".format(bus2))
        self._log.info("Card bus - {} is enumerated as expected")

        execution_time_in_sec = self._common_content_configuration.get_cxl_stress_execution_runtime(tool="ctg")

        peer0 = self._common_content_configuration.get_cxl_target_peer_point_device_list(tool="ctg")[0]
        peer1 = self._common_content_configuration.get_cxl_target_peer_point_device_list(tool="ctg")[1]

        self._log.info("Creating the HDM-0 VM addresses range file")
        hdm0_start_txt = self.create_and_copy_hdm_vm_on_sut(peer_name=peer1, addr_range="start",
                                                            ctg_tool_path=self.ctg_tool_sut_path)
        hdm0_end_txt = self.create_and_copy_hdm_vm_on_sut(peer_name=peer1, addr_range="end",
                                                          ctg_tool_path=self.ctg_tool_sut_path)
        self._log.info("HDM-0 VM addresses file got created- {} and {}".format(hdm0_start_txt, hdm0_end_txt))

        self._log.info("Creating the HDM-1 VM addresses range file")
        hdm1_start_txt = self.create_and_copy_hdm_vm_on_sut(peer_name=peer0, addr_range="start",
                                                            ctg_tool_path=self.ctg_tool_sut_path)
        hdm1_end_txt = self.create_and_copy_hdm_vm_on_sut(peer_name=peer0, addr_range="end",
                                                          ctg_tool_path=self.ctg_tool_sut_path)
        self._log.info("HDM-1 VM addresses file got created- {} and {}".format(hdm1_start_txt, hdm1_end_txt))

        peer0_to_peer1 = self.CMD_FOR_PEER0_TO_PEER1.format(int(bus1, 16), hdm0_start_txt, hdm0_end_txt,
                                                            execution_time_in_sec)

        self._log.info("Command to put traffic from Peer0 to Peer1 - {}".format(peer0_to_peer1))

        peer1_to_peer0 = self.CMD_FOR_PEER1_TO_PEER0.format(int(bus2, 16), hdm1_start_txt, hdm1_end_txt,
                                                            execution_time_in_sec)

        self._log.info("Command to put traffic from Peer1 to Peer0 - {}".format(peer1_to_peer0))

        try:
            self._log.info("Executing the command to put traffic from Peer0 to Peer1")
            self.os.execute_async(peer0_to_peer1, self.ctg_tool_sut_path)

            self._log.info("Executing the command to put traffic from Peer1 to Peer0")
            self.os.execute_async(peer1_to_peer0, self.ctg_tool_sut_path)

            self._log.info("Stress execution started...")
            if not self.poll_the_ctg_tool(execution_time_seconds=execution_time_in_sec, api_to_check=[peer0_to_peer1,
                                          peer1_to_peer0]):
                raise content_exceptions.TestFail("CTG tool fail to run")
            self._log.info("Stress execution completed Successfully")
        except Exception as ex:
            raise content_exceptions.TestFail("CTG tool fail to run - {}".format(ex))
        finally:
            if not self.os.is_alive():
                self.perform_graceful_g3()

            self.os.copy_file_from_sut_to_local(source_path=Path(os.path.join(self.ctg_tool_sut_path,
                                                                              "peer0_to_peer1.txt")).as_posix(),
                                                destination_path=os.path.join(self.log_dir, "peer0_to_peer1.txt"))

            self.os.copy_file_from_sut_to_local(source_path=Path(os.path.join(self.ctg_tool_sut_path,
                                                                              "peer1_to_peer0.txt")).as_posix(),
                                                destination_path=os.path.join(self.log_dir, "peer1_to_peer0.txt"))

        self._log.info("Checking the bandwidth in CTG executed Log - Total bandwidth should not be 0.")
        self.verify_bw_in_ctg_tool_output("peer0_to_peer1.txt", self.ctg_tool_sut_path)
        self.verify_bw_in_ctg_tool_output("peer1_to_peer0.txt", self.ctg_tool_sut_path)

        self._log.info("Expected Bandwidth captured in stress execution output")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RemoteSocketCxlPeer0toPeer1AndPeer1toPeer0CtgCacheStress.main() else
             Framework.TEST_RESULT_FAIL)
