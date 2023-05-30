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
# treaty provisions0. No part of the Material may be used, copied, reproduced,
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
import pandas as pd
import numpy as np


from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.common_content_lib import CommonContentLib


class VerifyC6Residency(TxtBaseTest):
    """
       Glasgow ID : 58209
       Verify that the CPUs on the system are entering/exiting C6 state while in a trusted environment.
       To enable TXT refer Glasgow ID : 58199
        1. Ensure that system is in sync with the latest BKC
        2. Ensure that the system's TPM is provisioned with an ANY policy and is capable of booting trusted
        3. Ensure that C-states are enabled in the BIOS.
    """
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    PCI_CMD = "lspci"
    CPU_CMD = "lscpu"
    MEM_CMD = "lsmem"

    def __init__(self, test_log, arguments, cfg_opts):
        """
         Create instance of Verify_C6_Residency
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(
            VerifyC6Residency,
            self).__init__(
            test_log,
            arguments,
            cfg_opts,
            self.BIOS_CONFIG_FILE)
        self._common_obj = CommonContentLib(self._log, self._os, cfg_opts)
        self.pre_tboot_pci = None
        self.pre_tboot_cpu = None
        self.pre_tboot_mem = None
        self.post_tboot_pci = None
        self.post_tboot_cpu = None
        self.post_tboot_mem = None
        self.tboot_index = None

    def prepare(self):
        # type: () -> None
        """
        1. Execute OS commands before the trusted boot set.
        2. Pre-validate whether sut is configured with trusted boot by get the trusted boot index in OS boot order.
        3. Load BIOS defaults settings.
        4. Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        """
        # Checking  Operating system live or not

        if not self._os.os_type == OperatingSystems.LINUX:
            self._log.error("This test case only applicable for LINUX system")
            raise RuntimeError("This test case only applicable for LINUX system")
        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise RuntimeError("OS is not alive")
        # get pre trusted boot lsmem, lscpu and lspci data
        self.pre_tboot_mem = self._common_obj.execute_sut_cmd(
            self.MEM_CMD, "details of mem", self._command_timeout)
        self.pre_tboot_cpu = self._common_obj.execute_sut_cmd(
            self.CPU_CMD, "details of cpu", self._command_timeout)
        self.pre_tboot_pci = self._common_obj.execute_sut_cmd(
            self.PCI_CMD, "details of pci", self._command_timeout)

        self.tboot_index = self.get_tboot_boot_position()  # Get the trusted boot _index from grub menu entry
        self.set_default_boot_entry(self.tboot_index)  # Set trusted boot  as default boot
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob
        self._os.reboot(self._reboot_timeout)
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

    def check_msr_core_values(self):
        """
        This function will compare the msr(0x3F9) values after halt()

        :return  True if no cores' msr values match before and after system halt.
        """
        msr_value = False

        data1 = self.get_sdp_msr_values(self.txt_msr_consts)
        time.sleep(self._msr_time_sleep)
        data2 = self.get_sdp_msr_values(self.txt_msr_consts)

        msr_data = pd.DataFrame({'msr_read1': data1, 'msr_read2': data2})
        if (msr_data['msr_read1'] != 0).all() and (msr_data['msr_read2'] != 0).all():
            msr_data['col3'] = np.where(msr_data['msr_read1'] == msr_data['msr_read2'], True, False)
            self._log.info("MSR_COMPARISON_TABLE {} ".format(msr_data))
            col_3_list = msr_data['col3'].tolist()
            if any(col_3_list):
                self._log.error("Core Values matched in some rows")
            else:
                msr_value = True
                self._log.info("All Cores have different values...")
        else:
            self._log.error("Some registers have zero Values")
        return msr_value

    def execute(self):
        """
        This function is used to check SUT boot with trusted boot and compare results of lsmem, lscpu and lspci after trusted boot.

        :return: True if Test case pass else fail
        """
        # check if trusted boot
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if the system booted in Trusted mode.
        self._os.reboot(self._reboot_timeout)
        if self.verify_trusted_boot():  # verify the sut boot with trusted env
            self._log.info("SUT Booted to Trusted environment Successfully")
        else:
            return False

        # get post trusted boot lsmem, lscpu and lspci data
        self.post_tboot_mem = self._common_obj.execute_sut_cmd(
            self.MEM_CMD, "details of mem", self._command_timeout)
        self.post_tboot_cpu = self._common_obj.execute_sut_cmd(
            self.CPU_CMD, "details of cpu", self._command_timeout)
        self.post_tboot_pci = self._common_obj.execute_sut_cmd(
            self.PCI_CMD, "details of pci", self._command_timeout)

        # Compare results of lsmem, lscpu and lspci before and after trusted boot
        mem_cpu_pci_comp_status = self.compare_mem_cpu_pci_data(
            self.pre_tboot_pci,
            self.post_tboot_pci,
            self.pre_tboot_cpu,
            self.post_tboot_cpu,
            self.pre_tboot_mem,
            self.post_tboot_mem)

        # Condition will check trusted boot enable and then checking MSR values
        if not mem_cpu_pci_comp_status:
            self._log.error("SUT Not Booted to Trusted environment Successfully")
        return mem_cpu_pci_comp_status and self.check_msr_core_values()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyC6Residency.main() else Framework.TEST_RESULT_FAIL)
