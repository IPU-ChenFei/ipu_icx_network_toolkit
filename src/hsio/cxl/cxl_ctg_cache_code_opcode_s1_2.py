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


class CxlCtgCacheOpcodeS1Value2(CxlCtgCommon):
    """
    hsdes_id :  16015614776 Using CTG tool Generate CXL.cache traffic across all supported slots for 30 Minutes .
    This is to ensure CXL cards are compatible across all the supported slots

    Currently as only type of CXL card is available i.e FM85 , the same card will be checked across  the supported slots

    Going forward once other types of CXL cards are available, they will be  inserted across the supported slots.

    Supported Slots : Slot B, Left Riser Top, Left Riser Bottom, SlotE . If there are no physical mechanical
    constraints while inserting the cards in to Right Riser Top and Right Riser Bottom those slots should also
    be validated
    """
    CMD = " ./ctg -v -p {} --sc 0 --vm {} --s1 2 --sc 1 --vm {} --s1 2 -t {} > ctg_log.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCtgSocket0CoresToHdm0AndSocket1CoresToHdm1MemoryStress.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCtgCacheOpcodeS1Value2, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCtgCacheOpcodeS1Value2, self).prepare()

    def execute(self):
        """
        This method is to execute.
        1. Get the bus of CXL device.
        2. Get the stress execution time
        3. Execute the Stress
        4. Verify the Log in tools output
        """
        #  Getting the bus of the CXL device
        socket = int(self._common_content_configuration.get_cxl_ctg_socket_list()[0])
        bus = self._common_content_configuration.get_cxl_target_bus_list(tool="ctg")[socket]
        if not self.is_bus_enumerated(bus):
            raise content_exceptions.TestFail("Card is not enumerated in OS")

        self._log.info("Card bus- {} is enumerated as Expected".format(bus))

        execution_time_in_sec = 1800
        dimm_name = self._common_content_configuration.get_cxl_cache_dimm_list_to_target(socket=socket)[0]

        txt_dict = self.create_and_copy_dimm_vm_on_sut(dimm_name=dimm_name, ctg_tool_path=self.ctg_tool_sut_path,
                                                       csp=self.csp, no_of_files=2)

        instance_1_cmd = self.CMD.format(int(bus, 16), txt_dict[0], txt_dict[1], execution_time_in_sec)
        self._log.debug(instance_1_cmd)

        self._log.info("Starting the stress ...")
        self.os.execute_async(instance_1_cmd, self.ctg_tool_sut_path)

        self.poll_the_ctg_tool(execution_time_seconds=execution_time_in_sec, api_to_check=[instance_1_cmd])
        self._log.info("Stress execution completed Successfully")

        self._log.info("Checking the bandwidth speed in CTG output. It should not be 0.")
        self.verify_bw_in_ctg_output_files(file_names=["ctg_log.txt"],
                                           signatures=[self.BW_0_SIG])

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCtgCacheOpcodeS1Value2.main() else
             Framework.TEST_RESULT_FAIL)
