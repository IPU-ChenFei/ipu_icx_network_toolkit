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


class CxlDevice0toNativeDdrRemoteS1Opcode3n7AndDevice1toNativeDdrRemoteS0Opcode2n4(CxlCtgCommon):
    """
    hsdes_id :  16015478527 Using CTG tool Generate CXL cache stress traffic between  CXL Device0 to
    Native DDR Remote Socket1 and CXL Device1 to Native DDR Remote Socket0

    Below CTG cache opcodes are used :
    CXL Device0 to Native DDR Remote Socket1 :    WrInv/WrInvF:3 , WOWrInv/WrPart_I:7
    CXL Device1 to Native DDR Remote Socket0:  ItoMWr/WrPush_I:2 , WrInv/WrInv: 4
    """
    CMD_FOR_1ST_INSTANCE = "./ctg -v -p {} --sc 0 --vm {} --s1 3 --sc 1 --vm {} --s1 7 -t {} > cmd_1_instance.txt"
    CMD_FOR_2ND_INSTANCE = "./ctg -v -p {} --sc 0 --vm {} --s1 2 --sc 1 --vm {} --s1 4 -t {} > cmd_2_instance.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlDevice0toNativeDdrRemoteS1Opcode3n7AndDevice1toNativeDdrRemoteS0Opcode2n4.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlDevice0toNativeDdrRemoteS1Opcode3n7AndDevice1toNativeDdrRemoteS0Opcode2n4, self).__init__(
            test_log, arguments, cfg_opts, bios_config_file)
        self.ctg_tool_sut_path = self.install_collateral.install_ctg_tool()
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)

    def prepare(self):
        """
        This is to execute prepare.
        1. clear OS log
        2. Bios loading
        3. Execute to cxl ctg pre-condition to write few register.
        """
        super(CxlDevice0toNativeDdrRemoteS1Opcode3n7AndDevice1toNativeDdrRemoteS0Opcode2n4, self).prepare(self.sdp)

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
        socket_0_bus, socket_1_bus = self.get_cxl_device_bus(sockets=[0, 1])

        socket_1_dimm_0 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(tool="ctg", socket=1)[0]

        socket_1_ddr_start_txt = self.create_and_copy_dimm_vm_on_sut(dimm_name=socket_1_dimm_0,
                                                                     ctg_tool_path=self.ctg_tool_sut_path, csp=self.csp)

        socket_1_dimm_1 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(tool="ctg", socket=1)[1]
        socket_1_ddr_end_txt = self.create_and_copy_dimm_vm_on_sut(
            dimm_name=socket_1_dimm_1, ctg_tool_path=self.ctg_tool_sut_path, csp=self.csp, stride_addr=0x40)

        socket_0_dimm_0 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(tool="ctg", socket=0)[0]

        socket_0_ddr_start_txt = self.create_and_copy_dimm_vm_on_sut(dimm_name=socket_0_dimm_0,
                                                                     ctg_tool_path=self.ctg_tool_sut_path, csp=self.csp)

        socket_0_dimm_1 = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(tool="ctg", socket=0)[1]
        socket_0_ddr_end_txt = self.create_and_copy_dimm_vm_on_sut(
            dimm_name=socket_0_dimm_1, ctg_tool_path=self.ctg_tool_sut_path, csp=self.csp, stride_addr=0x40)

        cmd_1_instance = self.CMD_FOR_1ST_INSTANCE.format(int(socket_0_bus, 16), socket_1_ddr_start_txt, socket_1_ddr_end_txt,
                                                          self.execution_time_in_sec)

        cmd_2_instance = self.CMD_FOR_2ND_INSTANCE.format(int(socket_1_bus, 16), socket_0_ddr_start_txt, socket_0_ddr_end_txt,
                                                          self.execution_time_in_sec)

        self.execute_and_poll_ctg_stress(command_list=[cmd_1_instance, cmd_2_instance])

        self.verify_bw_in_ctg_output_files(file_names=["cmd_1_instance.txt", "cmd_2_instance.txt"],
                                           signatures=[self.BW_0_SIG, self.BW_0_SIG])
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if
             CxlDevice0toNativeDdrRemoteS1Opcode3n7AndDevice1toNativeDdrRemoteS0Opcode2n4.main() else
             Framework.TEST_RESULT_FAIL)
