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


class MivResetWarm(ManageabilityCommon):
    """
        HPALM ID: 80031
        PI_miv_reset_warm - This test is intended to validate the Node Manager FirmWare stability
        through multiple warm reset cycles.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of MivResetWarm

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(MivResetWarm, self).__init__(test_log, arguments, cfg_opts)
        self.exec_time = self._common_content_configuration.miv_warm_reset_timeout()

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        if os.path.isfile(self.get_dev_id_obj.miv_log_file):
            os.remove(self.get_dev_id_obj.miv_log_file)

    def execute(self):
        """
            Verifies stability of Node Manager through multiple warm reset cycles.
            Checks the getdeviceid after a power cycle
            1. pings SUT and BMC
            2. Shuts down the SUT and Power On the SUT
            3. Checks the get device id
            4. Power cycle
        """
        self._log.info("Verify the Connectivity of BMC by Pinging BMC Ip")
        self.verify_ip_connectivity()
        if self.get_dev_id_obj.get_region_name() == self.get_dev_id_obj.OPERATIONAL_MODE:
            self._log.info("Device is in Operational Mode")
        else:
            log_error = "Device is not in Operational Mode"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        _init = _now = time.time()
        while self.exec_time > _now - _init:
            self._log.info("Apply Soft Shutdown to System by using Chassis Control")
            self.chassis_cntrl_obj.chassis_control(control=self.chassis_cntrl_obj.SOFT_SHUTDOWN)
            self._log.info("Keep the System Idle for {} sec to turn it Off".format
                           (self._common_content_configuration.get_shutdown_timeout()))
            time.sleep(self._common_content_configuration.get_shutdown_timeout())
            if self.os.is_alive():
                log_error = "OS is still alive, after shutting down the SUT.."
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._log.info("Power On the System by using Chassis Control")
            self.chassis_cntrl_obj.chassis_control(control=self.chassis_cntrl_obj.POWER_ON)
            self._log.info("Keeping the System Idle till its turn On")
            self.os.wait_for_os(self._common_content_configuration.get_reboot_timeout())
            self._log.info("Get device id after System is Turned On and Verify if Device is in Operational Mode")
            self.get_dev_id_obj.repopulate_device_data()
            if self.get_dev_id_obj.get_region_name() == self.get_dev_id_obj.OPERATIONAL_MODE:
                self._log.info("Device is in Operational Mode")
            else:
                log_error = "Device is not in Operational Mode"
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._log.info("Apply the Power Cycle using Chassis Control")
            self.chassis_cntrl_obj.chassis_control(control=self.chassis_cntrl_obj.POWER_CYCLE)
            self._log.info("Keeping the System Idle to complete the power cycle")
            self.os.wait_for_os(self._common_content_configuration.get_reboot_timeout())
            _now = time.time()
        self._log.info("Detailed MIV Log is Available in '{}'".format(self.dtaf_montana_log_path))
        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        super(MivResetWarm, self).cleanup(return_status=True)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MivResetWarm.main() else Framework.TEST_RESULT_FAIL)
