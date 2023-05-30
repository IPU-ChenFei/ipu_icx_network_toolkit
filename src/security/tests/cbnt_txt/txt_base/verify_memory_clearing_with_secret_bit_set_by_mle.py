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
from dtaf_core.providers.dc_power import DcPowerControlProvider


class SecretsColdReset(SecretsBaseFlow):
    """
    Glasgow ID : 58993

    This test case Write to memory in OS and check again after surprise reset  to ensure memory is cleaned.
    1.Ensure that the system is in sync with the latest BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.
    3.Ensure that the platform has a TPM provisioned with an ANY policy installed
        and active

    """
    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SecretsColdReset

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SecretsColdReset, self).__init__(test_log, arguments, cfg_opts,
                                               self._BIOS_CONFIG_FILE)
        self.tboot_index = None
        dc_cfg = cfg_opts.find(DcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._dc = ProviderFactory.create(dc_cfg, test_log)  # type: DcPowerControlProvider
        self._dc_delay = self._common_content_configuration.dc_power_sleep_time()

    def prepare(self):
        # type: () -> None
        """
        Pre-validating whether sut is configured with tboot by getting the tboot index in OS boot order
        Loading BIOS defaults settings.
        Sets the bios knobs according to configuration file.
        verifies if bios knobs sets successfully.
        Verify trusted boot

        :raise : NotImplementedError if the OS is not LINUX
        :raise: RuntimeError if SUT did not Boot into Trusted environment
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
        if self.verify_trusted_boot(expect_ltreset=False):  # Verify trusted boot
            self._log.info("SUT Booted to Trusted environment Successfully")
        else:
            self._log.error("SUT did not Boot into Trusted environment")
            raise RuntimeError("SUT did not Boot into Trusted environment")

    def surprise_reset(self):
        """
        This function performs the DC reset to the platform

        :raise: RuntimeError: If Fail to perform DC power off
        :raise: RuntimeError: If Fail to perform DC power ON
        :return: None
        """

        if self._dc.dc_power_off():  # To perform a DC Power off
            self._log.info("DC power is turned OFF")
        else:
            self._log.error("DC power is not turned OFF")
            raise RuntimeError("DC power is not turned OFF")
        time.sleep(self._dc_delay)
        if self._dc.dc_power_on():  # Power on the system
            self._log.info("DC power is turned ON")
        else:
            self._log.error("DC power is not turned ON")
            raise RuntimeError("DC power is not turned ON")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SecretsColdReset.main() else
             Framework.TEST_RESULT_FAIL)
