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
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.security.tests.cbnt_txt.secrets import SecretsBaseFlow
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider
from src.lib.reaction_lib import ReactionLib


class VerifyMemoryClearingWithSecretBitClear(SecretsBaseFlow):
    """
    Glasgow ID : 58219
    This test case aims to Verify memory clearing with Secret bit clear and LT.Wake.Error set on reset vector.
    pre-requisites:
    1.Ensure that the system is in sync with the latest BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.
    3.Ensure that the platform has a TPM provisioned with an ANY policy installed
        and active
    """
    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of VerifyMemoryClearingWithSecretBitClear

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(VerifyMemoryClearingWithSecretBitClear, self).__init__(test_log, arguments, cfg_opts,
                                                                     self._BIOS_CONFIG_FILE)
        self.tboot_index = None
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider
        phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
        self._phy = ProviderFactory.create(phy_cfg, test_log)  # type: PhysicalControlProvider

    def prepare(self):
        # type: () -> None
        """
        Pre-validating whether sut is configured with tboot by getting the tboot index in OS boot order
        Loading BIOS defaults settings.
        Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.

        :raise : NotImplementedError if the OS is not LINUX
        :return: None
        :TODO: Need to implement for Vmware OS as well
        """
        if not self._os.os_type == OperatingSystems.LINUX:
            # TODO: Need to implement for Vmware OS as well
            raise NotImplementedError("Test Not implemented for the OS '{}'  " + str(self._os.os_type))
        self.tboot_index = self.get_tboot_boot_position()  # get the tboot_index from grub menu entry
        self.set_default_boot_entry(self.tboot_index)  # Set tboot as default boot
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob setting
        self._os.reboot(self._reboot_timeout)  # To apply Bios changes
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

    def clear_secret_flag(self):
        """
        This function clears the secret flag and verifies if it is cleared successfully.

        :raise: RuntimeError if the secret flag is not cleared
        :return: None
        """
        address_secret_flag = hex(self.txt_consts.TXT_REG_PRIVATE_BASE +
                                  self.txt_consts.TXT_REG_OFFSETS["SECRETS_PRIV"]).rstrip('L') + 'p'
        lt_e2sts_mem_address = hex(self.txt_consts.TXT_REG_PUBLIC_BASE +
                                   self.txt_consts.TXT_REG_OFFSETS["LT_E2STS"]).rstrip('L') + 'p'
        byte_size_to_write = 8
        value_to_write = 1
        byte_size_to_read = 4
        thread_index = 0
        expected_e2sts_val = 0x0
        self._log.info("Halting the CPU to check secret flag is clear or not")
        self._sdp.halt()
        self._log.info("Writing to memory location '{}' to clear the secret flag".format(address_secret_flag))
        self._sdp.itp.threads[thread_index].mem(address_secret_flag, byte_size_to_write, value_to_write)
        read_e2sts = self._sdp.mem_read(lt_e2sts_mem_address, byte_size_to_read)
        self._log.info("Read back value at address '{}' is: {}".format(lt_e2sts_mem_address, hex(read_e2sts)))
        self._sdp.go()
        if (hex(read_e2sts)) == hex(expected_e2sts_val):
            self._log.info("secret bit is cleared")
        else:
            self._log.error("secret bit is not cleared")
            raise RuntimeError("secret bit is not cleared")

    def surprise_reset(self):
        """
        This function performs the ungraceful reset and also performs the clear CMOS operation

        :raise: RuntimeError: If Fail to perform AC power off
        :raise: RuntimeError: If Fail to perform clear CMOS
        :raise: RuntimeError: If Fail to perform AC power ON
        :return: None
        """

        if self._ac.ac_power_off():  # To perform a Ungraceful Shutdown
            self._log.info("AC power is turned OFF")
        else:
            self._log.error("AC power is not turned OFF")
            raise RuntimeError("AC power is not turned OFF")
        if self._phy.set_clear_cmos():  # Clears CMOS value
            self._log.info("Clear CMOS is done successfully")
        else:
            self._log.error("Clear CMOS is not done successfully")
            raise RuntimeError("Clear CMOS is not done successfully")
        if self._ac.ac_power_on():  # Power on the system
            self._log.info("AC power is turned ON")
        else:
            self._log.error("AC power is not turned ON")
            raise RuntimeError("AC power is not turned ON")

    def execute(self):
        """

        :raise: RuntimeError: If fail to launch MLE and unable to set secret bit.
        :raise: RuntimeError: If the INIT break trigger is missed.
        :return: True if the test case pass and False if fails
        """
        ret_val = False
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # Check if tboot is set as default boot
        self._os.reboot(self._reboot_timeout)  # Reboot for a graceful restart of system
        if not self.verify_trusted_boot():  # verify the sut boot with trusted environment
            self._log.info("SUT did not Boot into Trusted environment")
            return ret_val
        self._log.info("Parsing e820 table to get usable memory ranges.")
        memory_ranges = self.parse_e820_table()
        # Verify if MLE is launched and secret bit is set
        if self._validate_txt_registers_trusted(expect_ltreset=False, mask_ltreset=False):
            self._log.info("MLE launched successfully and secret bit is set")
        else:
            self._log.info("MLE did not launched successfully and secret bit is not set")
            raise RuntimeError("MLE did not launched successfully and secret bit is not set")
        self._log.info("Writing secrets into memory.")
        self.write_secrets(memory_ranges)
        self.clear_secret_flag()  # Clear secret flag
        self.surprise_reset()  # Surprise reset
        self._log.info("Registering serial log trigger.")
        with ReactionLib(self._log, self._console_log, True) as reaction_engine:
            self._log.info("Waiting for init break.")
            reaction_engine.register_reaction(" Boot in Normal mode", self.init_break_trigger)
            if self._init_break_event.is_set():
                raise RuntimeError("Missed the INIT break trigger! Check for blocking tasks before this call.")
            if not self._init_break_event.wait(timeout=self.INIT_BREAK_TIMEOUT):
                raise RuntimeError("Did not get the INIT break trigger!")
            self._log.info("Got the init trigger event........")
            self._log.info("Halting cpu")
            self._sdp.halt()
            self._log.info("Checking for secrets.")
            try:
                result = self.check_for_secrets_clear()  # Checks if the secrets are clear
            finally:
                self._sdp.go()

            if not result:
                self._log.error("Secrets still found in memory. Test failed.")
            else:
                self._log.info("Finished checking secrets! Waiting for OS to boot.")

        time.sleep(self._reboot_timeout)  # Waits until the system comes up
        self._bios_util.set_bios_knob()  # To set the bios knob setting
        self._os.reboot(self._reboot_timeout)  # To apply Bios changes
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set
        if self.verify_trusted_boot():  # verify the sut boot with trusted environment
            self._log.info("SUT Booted to Trusted environment Successfully")
            ret_val = True
        else:
            if self.verify_trusted_boot(expect_ltreset=True):  # verify the sut boot with trusted environment
                self._log.info("SUT Booted to Trusted environment Successfully")
                ret_val = True
            else:
                self._log.error("SUT did not Boot into Trusted environment")
        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyMemoryClearingWithSecretBitClear.main() else
             Framework.TEST_RESULT_FAIL)
