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
import os
import sys
import time

from src.sdsi.lib.tools.artifactory_tool import ArtifactoryTool
from src.sdsi.tests.agent.general.ib_provisioning_test import InBandProvisioningTest


class IbProvisioningTestUnderStress(InBandProvisioningTest):
    """
    Verify the IB provisioning of the SSKU enabled CPU by applying an LAC and
    verify it is available while a stress application is running on the SUT.
    """
    STRESS_DIR = "/usr/sbin"

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013674015

    def __init__(self, test_log, arguments, config):
        super().__init__(test_log, arguments, config)
        self.artifactory_tool = ArtifactoryTool(test_log, self.os)

    def execute(self) -> None:
        """
        Verify the IB provisioning of the SSKU enabled CPU by applying an LAC and
        verify it is available while a stress application is running on the SUT.
        """
        self._log.info("Read the maximum load average of the CPU prior to StressAppTest execution on SUT.")
        before_max_load_avg = self.get_max_load_average()
        self._log.info(f"Load average value prior to stress app test is {before_max_load_avg}.")

        self._log.info("Install a stress test binary to SUT.")
        self.artifactory_tool.download_tool_to_sut(self.artifactory_tool.STRESSAPP_TOOL_LINUX, self.STRESS_DIR)

        self._log.info("Execute stress application on the SUT.")
        self.execute_stress_app_installer_on_sut()

        self._log.info("Read the maximum load average of the CPU after stress app test execution on SUT.")
        after_max_load_avg = self.get_max_load_average()
        self._log.info(f"Load average value after to StressAppTest is {after_max_load_avg}")
        if after_max_load_avg < before_max_load_avg * 4:
            error_msg = "There is no significant increase in the CPU load after stress application."
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Load average on the CPU has increased after stress application.")

        self._log.info("Provision the CPU with a random payload while stress application is running on the SUT.")
        super().execute()

        self._log.info("Copy the stress log to the host.")
        self.os.copy_file_from_sut_to_local(f"{self.STRESS_DIR}/stress.log", os.path.join(self.log_dir, "stress.log"))

    def get_load_average(self):
        """
        This method will fetch the load average value from the SUT
        return: Value of Load Average
        """
        response = self.sut_os_tool.execute_cmd("cat /proc/loadavg")
        load_average_list = list(map(float, (response.split())[0:3]))
        if not load_average_list:
            log_error = "load_average value is not present in system"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return load_average_list

    def get_max_load_average(self):
        """
        This method will get max load average value
        return: Max load average value from list
        """
        max_load_value = max(self.get_load_average())
        self._log.info(f"Maximum load average value {max_load_value}")
        return max_load_value

    def execute_stress_app_installer_on_sut(self):
        """
        Execute the stress app test file.
        """
        remove_log_cmd = "rm -rf stress.log"
        self.sut_os_tool.execute_cmd(remove_log_cmd)

        self._log.info("Starting the stress app test")
        run_stress_cmd = f"./stressapptest -s {120} -l stress.log > /dev/null 2>&1 & disown"
        self.sut_os_tool.execute_cmd(run_stress_cmd, self.STRESS_DIR)
        time.sleep(5)

if __name__ == "__main__":
    sys.exit(not IbProvisioningTestUnderStress.run())
