#!/usr/bin/env python
###############################################################################
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
###############################################################################
import os
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.manageability.lib.manageability_common import ManageabilityCommon


class BmcRemoteControlBootDisk(ManageabilityCommon):
    """
        HPALM ID: 80025
        Veirfy IPMI bootable device selection.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of BmcRemoteControlBootDisk
        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(BmcRemoteControlBootDisk, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        os.remove(self.get_dev_id_obj.miv_log_file)

    def execute(self):
        """
            Verifies bootable device selection using IPMI commands
            1. pings SUT and BMC
            2. Shuts down the SUT
            3. Set the system boot option to DISK
            4. Power cycle
        """
        self._log.info("Verify the Connectivity of BMC by Pinging BMC Ip")
        self.verify_ip_connectivity()
        self._log.info("Get the Details of Device and Verify if Device is in Operational Mode")
        if self.get_dev_id_obj.get_region_name() == self.get_dev_id_obj.OPERATIONAL_MODE:
            self._log.info("Device is in Operational Mode")
        else:
            log_error = "Device is not in Operational Mode"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Apply Shutdown to System by using Chassis Control")
        self.chassis_cntrl_obj.chassis_control(control=self.chassis_cntrl_obj.POWER_OFF)
        self._log.info("Keeping the System Idle for {} sec to turn it Off".format
                       (self._common_content_configuration.get_shutdown_timeout()))
        time.sleep(self._common_content_configuration.get_shutdown_timeout())
        if self.os.is_alive():
            log_error = "OS is still alive, after shutting down the SUT.."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Setting system to BOOT to DISK")
        self.boot_options_obj.set_boot_options(bootdev=self.boot_options_obj.SETBOOT_DISK)
        self._log.info("Power On the System by using Chassis Control")
        self.chassis_cntrl_obj.chassis_control(control=self.chassis_cntrl_obj.POWER_ON)
        self._log.info("Keeping the System Idle to turn it On")
        self.os.wait_for_os(self._common_content_configuration.get_reboot_timeout())
        self._log.info("System has been boot to disk successfully")
        self._log.info("Setting system to BOOT to DISK")
        self.boot_options_obj.set_boot_options(bootdev=self.boot_options_obj.SETBOOT_DISK)
        self._log.info("Power On the System by using Chassis Control")
        self.chassis_cntrl_obj.chassis_control(control=self.chassis_cntrl_obj.POWER_CYCLE)
        self._log.info("Keeping the System Idle to turn it On")
        self.os.wait_for_os(self._common_content_configuration.get_reboot_timeout())
        self._log.info("System has been boot to disk successfully")

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        super(BmcRemoteControlBootDisk, self).cleanup(return_status=True)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BmcRemoteControlBootDisk.main() else Framework.TEST_RESULT_FAIL)
