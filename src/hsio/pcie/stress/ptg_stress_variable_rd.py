#!/usr/bin/env python
#################################################################################
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
#################################################################################

import sys
from datetime import datetime
from src.lib.bios_util import ItpXmlCli
from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_configuration import ContentConfiguration
from src.hsio.pcie.stress.hsio_stress_common import HsioStressCommon


class PtgVarRd(HsioStressCommon):
    """
    Phoenix ID: 15011118743
    Gen5_MSB_Stress_read_Variable_Packet_Transaction

    Test requires a FastPath image!

    Stress_PCIe__Gen5_MSB_rd_Variable_Packet_Transaction_VT-d_On
    """
    TEST_CASE_ID = ["15011118743", "Gen5_MSB_Stress_read_Variable_Packet_Transaction"]
    PTG_APP = "ptg"

    def __init__(self, test_log, arguments, cfg_opts):
        # self.bios_config_file_path = <BIOS CFG PATH>
        super(PtgVarRd, self).__init__(test_log, arguments, cfg_opts)

        # Get test content configurations..
        self.content_config = ContentConfiguration(test_log)
        self.runtime = self.content_config.get_stress_runtime()
        self.pattern_runtime = self.content_config.get_ptg_pattern_runtime()
        self.target_buses = self.content_config.get_target_bus_list()
        if self.target_buses == self.AUTO:
            self.target_buses = self.detect_devices_by_did(self.PTG_FP_DID_LIST)

        self.target_addr = self.content_config.get_ptg_target_address()
        self.test_patterns = "rd8,rd96,rd256,rd512,rd1024"
        self.test_type = "rd"
        self.test_group = "ptg"
        self.itpxml = ItpXmlCli(self._log, cfg_opts)

        # Get log file names
        time_now = str(datetime.now()).replace('-', '_').replace(' ', '_').replace('.', '_').replace(':', "_")
        self.bw_file = f"dtaf_ptg_bw_{time_now}.log"
        self.execution_log = f"ptg_{time_now}.log"

    def prepare(self):
        super(PtgVarRd, self).prepare()

    def execute(self):
        """
        Runs different read patterns -
            rd8,rd96,rd256,rd512,rd1024
        Each test pattern is run for 10 seconds.
        """
        iterations = int(self.runtime) // 10  # Run each test for 10 seconds.
        # Save initial link status information.
        if len(self.target_buses) > 1:
            target_str = ""
            for bus in self.target_buses:
                target_str += f"{bus},"
            target_str = target_str[:-1].replace("0x", '')
            self.check_link_status(target_str.split(','))
        else:
            target_str = self.target_buses[0].replace("0x", '')
            self.check_link_status([target_str])

        # Form command to execute on SUT.
        command = f"python ptg_linux.py -f -b {target_str} -t {self.test_patterns} -s" \
                  f" {self.pattern_runtime} -i {iterations} -a {self.target_addr} " \
                  f"-o {self.bw_file} > {self.execution_log}"
        command = [(command, self.ptg_executable_path, self.PTG_APP)]
        status = self.trigger_wrapper(command=command, runtime=int(self.runtime))
        return status

    def cleanup(self, return_status):
        """
        Copy logs from SUT to Host and verify.
        """
        try:
            return_status = self.verify_ptg(self.test_type, self.execution_log)
        except Exception as e:
            self._log.error(f"Exception occurred while trying to copy/parse logs from PTG wrapper execution.\n{e}")
            return_status = False
        super(PtgVarRd, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PtgVarRd.main() else Framework.TEST_RESULT_FAIL)
