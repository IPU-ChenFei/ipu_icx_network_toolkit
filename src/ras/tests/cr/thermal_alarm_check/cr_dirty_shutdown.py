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

from dtaf_core.lib.dtaf_constants import Framework

from src.ras.tests.cr.thermal_alarm_check.thermal_alarm_check_common import ThermalAlarmCheckCommon


class CrDirtyShutDown(ThermalAlarmCheckCommon):
    """
        Glasgow_id : 58866

        This test checks if the dirty shutdown sensor count increments and reports correct status after an unclean
        shutdown occurs.
    """
    _BIOS_CONFIG_FILE = "thermal_alarm_check_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new CrDirtyShutDown object
        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(CrDirtyShutDown, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.
        :return: None
        """
        super(CrDirtyShutDown, self).prepare()

    def execute(self):
        """
        This Method is used to verify if the dirty shutdown sensor count increments and reports correct status after
        an unclean shutdown occurs.
        1. Populating Memory Dimm Information.
        2. Get the List of Dimms which are Healthy and Manageable.
        3. Verify Initial Shutdown Sensor Status and its Current Value.
        4. Verify if DCPMM Dimms are Configured in 1 LM Mode.
        5. List the Existing Error Logs of DCPMM.
        6. Trigger Dirty Shutdown on Targetted DCPMM Dimm.
        7. Set the DCPMM Access Path to Auto and Refreshing the Dimm Topology.
        8. Get the List of Dcpmm Dimms which are Enabled.
        9. Verify if Latch System Shutdown State is Enabled.
        10. Verify Shutdown Sensor Status and its Current Value after Triggering Dirty Shutdown on DIMM.
        11. Rebooting the Sut to verify whether Dirty Shutdown is Triggered Properly.
        12. Verify Shutdown Sensor Status and its Current Value after Triggering Dirty Shutdown on DIMM and
        Rebooting the SUT.
        13. Verify if the DCPMM Dimms are still in Enabled State or Not.
        14. Verify if Latch System Shutdown State is Enabled.
        15. Verify if DCPMM Dimm Latched System Shutdown State is Dirty Shutdown.
        16. Clear all the Errors on Targetted DCPMM Dimm.
        17. Collect All OS Logs.

        :return:
        """
        self.populate_memory_dimm_information()
        self.get_list_of_dimms_which_are_healthy_and_manageable()
        self.verify_shutdown_sensor_status_and_current_value()
        self.verify_dcpmms_are_configured_in_1lm_mode()
        self.list_dcpmm_existing_error_logs()
        self.trigger_dirty_shutdown_on_dcpmm_dimm()
        self.set_dcpmm_access_path_to_auto_and_refresh_topology()
        self.obtaining_list_of_dcpmm_dimms()
        self.verify_latch_system_state()
        self.verify_shutdown_sensor_status_and_current_value(is_dirty_shutdown_triggered=True)
        self.rebooting_the_sut()
        self.verify_shutdown_sensor_status_and_current_value(is_dirty_shutdown_triggered=True, is_system_rebooted=True)
        self.obtaining_list_of_dcpmm_dimms()
        self.verify_latch_system_state()
        self.verify_dcpmm_latch_last_shutdown_status()
        self.clear_dcpmm_errors()
        self.collect_all_logs()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CrDirtyShutDown.main() else Framework.TEST_RESULT_FAIL)
