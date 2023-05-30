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
import re
import sys
import time

from src.sdsi.tests.agent.general.ib_provisioning_test import InBandProvisioningTest


class InBandCStateMonitoring(InBandProvisioningTest):
    """
    Verify the In Band provisioning of the SSKU enabled CPU by applying the license key certificate,
    and a capability activation payload and verify it is available and monitor C-state.
    """
    BIOS_CONFIG_FILE = "c_state_knobs.cfg"
    GET_POWER_STATE = 'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
    APPLY_POWERSAVE_MODE = 'for c in $( ls /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor ) ; do echo ' \
                           '"powersave" > $c ; done'

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013734218

    def execute(self) -> None:
        """
        Verify the In Band provisioning of the SSKU enabled CPU by applying the license key certificate,
        and a capability activation payload and verify it is available and monitor C-state.
        """
        self._log.info("Set required BIOS knobs.")
        self.set_c_state_knobs()
        self.cycling_tool.perform_ac_cycle()

        self.verify_c_state()

        super().execute()

        self.verify_c_state()

    def verify_c_state(self):
        """
        Ensure platform is set to powersave mode and verify load average is low.
        """
        if 'powersave' not in self.sut_os_tool.execute_cmd(self.GET_POWER_STATE):
            self.sut_os_tool.execute_cmd(self.APPLY_POWERSAVE_MODE)
        self._log.info("Platform is set to Powersave mode")

        time.sleep(30)

        load_average = re.findall(r"load average: (.*?),", self.sut_os_tool.execute_cmd('uptime'))[0]
        self._log.info(f"Load average is {load_average}")
        if float(load_average) > 2.0:
            error_msg = 'Load average too high.'
            self._log.error(error_msg)
            raise RuntimeError(error_msg)

    def set_c_state_knobs(self):
        """
        Set the knobs required for C state test.
        """
        self.xmlcli_tool.set_bios_knobs({"MonitorMWait": "0x1",
                                         "C1AutoDemotion": "0x1",
                                         "C1AutoUnDemotion": "0x1",
                                         "C6Enable": "0x1",
                                         "ProcessorC1eEnable": "0x1",
                                         "PackageCState": "0xFF",
                                         "ProcessorHWPMEnable": "0x3",
                                         "BootPState": "0x1",
                                         "serialDebugMsgLvl": "0x1",
                                         "PpinControl": "0x1",
                                         "VTdSupport": "0x1"})

if __name__ == "__main__":
    sys.exit(not InBandCStateMonitoring.run())
