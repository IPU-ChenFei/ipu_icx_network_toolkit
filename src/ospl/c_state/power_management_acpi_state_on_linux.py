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

from dtaf_core.lib.dtaf_constants import Framework
from src.power_management.c_state.c_state_common import CStateCommon
from src.lib.dtaf_content_constants import TurboStatConstants
from src.lib.content_exceptions import TestFail


class PowerManagementACPIStateOnLinux(CStateCommon):
    """
    HPALM : H81703-G55961-Power_Management_ACPI_CStates_on_Linux
    Verify that C-States are functioning and being exercised properly under various conditions
    (idle, load, and disabled).

    1. ENABLE all available C States BIOS knobs
    2. Boot to OS & check CPU utilization is low.
    3. Run CPUMONITOR to check deep C state residency counters are suitably high.
    4. Run TurboStat to check %Busy column is low and C state residency counters are suitably high.
    5. Run stress utility on SUT.
    6. Run CPUMONITOR to check deep C state residency counters are suitably low.
    7. Disable stress on the SUT.
    8. Reboot the system and disable all C-States BISO knobs.
    9. Boot to OS & check CPU utilization is low.
    10. Run TurboStat to check 'Bzy_MHz' column is consistent.
    11. Run stress utility on SUT.
    12. Run TurboStat to check 'Bzy_MHz' column is consistent.
    13. Disable stress on the SUT.
    14. Verify System logs.
    """
    TEST_CASE_ID = ["H81703,G55961, PI-Power_Management_ACPI_CStates_on_Linux"]
    BIOS_CONFIG_FILE = "power_management_acpi_state_on_linux_bios_knobs.cfg"
    CS_DISABLE_BIOS_CONFIG_FILE = "power_management_acpi_state_on_linux_c_state_disable_bios_knobs.cfg"
    KERNEL_TOOLS = "kernel-tools"
    C3_STATE_STR = "C3"
    C6_STATE_STR = "C6"
    CX_STATE_STR = "Cx"
    STRESS_TOOL_RUN_CMD = "stress --cpu `nproc --all`"
    THRESHOLD_CPU_PERCENTAGE_VALUE = 5.00
    THRESHOLD_C_STATE_HIGH_VALUE = 90.00
    THRESHOLD_C_STATE_LOW_VALUE = 5.00
    THRESHOLD_BUSY_PERCENT_VALUE = 5.00
    THRESHOLD_BUSY_MHZ_VALUE = 5.00
    THRESHOLD_C3_VALUE = 0.00
    WAIT_TIME_SIXTY_SECONDS = 60
    WAIT_TIME_TWENTY_SECONDS = 20

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PowerManagementACPIStateOnLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PowerManagementACPIStateOnLinux, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):
        self.set_and_verify_bios_knobs(self.BIOS_CONFIG_FILE)
        self._common_content_lib.update_micro_code()
        self._install_collateral.install_stress_tool_to_sut()  # install stress tool
        self._install_collateral.yum_install(self.KERNEL_TOOLS)  # install kernel-tool package for 'CPUMPOWER'
        self._turbostat_executor_path = self._install_collateral.install_turbo_stat_tool_linux()  # install TurboStat
        # wait for the SUT to be idle.
        time.sleep(self.WAIT_TIME_SIXTY_SECONDS)

    def execute(self):
        error_list = []
        # get CPU percentage
        cpu_percentage_value = self._common_content_lib.get_cpu_utilization()
        # verify CPU percentage is low or not
        if cpu_percentage_value > self.THRESHOLD_CPU_PERCENTAGE_VALUE:
            raise RuntimeError("Current CPU utilization value: {} is higher than the expected value: {}"
                               .format(cpu_percentage_value, self.THRESHOLD_CPU_PERCENTAGE_VALUE))
        self._log.info("CPU utilization value: {} is low as expected".format(cpu_percentage_value))

        # run cpumonitor tool
        cpu_power_opt_data = self.execute_cpu_power_tool("monitor")
        parsed_cpu_power_data = self.parse_cpu_monitor_data(cpu_power_opt_data)
        # verify C state residency counters are suitably high
        self._log.info("Evaluating C3 == {}".format(self.THRESHOLD_C3_VALUE))
        c3_invalid_matches = self.evaluate_expression("%s ==" + str(self.THRESHOLD_C3_VALUE),
                                                      parsed_cpu_power_data[self.C3_STATE_STR])
        if len(c3_invalid_matches):
            self._log.error("C3 counter values which are not matching with threshold:\n{}".format(c3_invalid_matches))
            error_list.append("C3-residency values are not zero when C-State BIOS knobs are enabled")
        else:
            self._log.info("C3-residency values are zero when C-State BIOS knobs are enabled")
        self._log.info("Evaluating C6 > {}".format(self.THRESHOLD_C_STATE_HIGH_VALUE))
        c6_invalid_matches = self.evaluate_expression("%s >" + str(self.THRESHOLD_C_STATE_HIGH_VALUE),
                                                      parsed_cpu_power_data[self.C6_STATE_STR])
        if len(c6_invalid_matches):
            self._log.error("C6 counter values which are not matching with threshold:\n{}".format(c6_invalid_matches))
            error_list.append("C6-residency values are not high (C6 > {}) when C-State BIOS knobs are enabled"
                              .format(self.THRESHOLD_C_STATE_HIGH_VALUE))
        else:
            self._log.info("C6-residency values are high (C6 > {}) when C-State BIOS knobs are enabled"
                           .format(self.THRESHOLD_C_STATE_HIGH_VALUE))
        self._log.info("Evaluating Cx > {}".format(self.THRESHOLD_C_STATE_HIGH_VALUE))
        cx_invalid_matches = self.evaluate_expression("%s >" + str(self.THRESHOLD_C_STATE_HIGH_VALUE),
                                                      parsed_cpu_power_data[self.CX_STATE_STR])
        if len(cx_invalid_matches):
            self._log.error("Cx counter values which are not matching with threshold:\n{}".format(cx_invalid_matches))
            error_list.append("Cx-residency values are not high (Cx > {}) when C-State BIOS knobs are enabled"
                              .format(self.THRESHOLD_C_STATE_HIGH_VALUE))
        else:
            self._log.info("Cx-residency values are high (Cx > {}) when C-State BIOS knobs are enabled"
                           .format(self.THRESHOLD_C_STATE_HIGH_VALUE))
        # run and verify TurboStat data
        busy_percent_data_list, busy_mhz_data_list = self.run_and_parse_turbostat_tool()
        self._log.info("Evaluating Busy% < {}".format(self.THRESHOLD_BUSY_PERCENT_VALUE))
        busy_percent_invalid_matches = self.evaluate_expression("%s <" + str(self.THRESHOLD_BUSY_PERCENT_VALUE),
                                                                busy_percent_data_list)
        if len(busy_percent_invalid_matches):
            self._log.error("Busy% counter values which are not matching with threshold:\n{}".format(
                            busy_percent_invalid_matches))
            error_list.append("Busy% values are not low (Busy% < {}) when C-State BIOS knobs are enabled".
                              format(self.THRESHOLD_BUSY_PERCENT_VALUE))
        else:
            self._log.info("Busy% data is low (Busy% < {}) as expected".format(self.THRESHOLD_BUSY_PERCENT_VALUE))

        # run stress Test
        self._stress_tool.execute_async_stress_tool(self.STRESS_TOOL_RUN_CMD, "stress")
        time.sleep(self.WAIT_TIME_TWENTY_SECONDS)
        # run cpumonitor tool
        cpu_power_opt_data = self.execute_cpu_power_tool("monitor")
        parsed_cpu_power_data = self.parse_cpu_monitor_data(cpu_power_opt_data)
        # verify C state residency counters are suitably low
        self._log.info("Evaluating C3 == {}".format(self.THRESHOLD_C3_VALUE))
        c3_invalid_matches = self.evaluate_expression("%s ==" + str(self.THRESHOLD_C3_VALUE),
                                                      parsed_cpu_power_data[self.C3_STATE_STR])
        if len(c3_invalid_matches):
            self._log.error("C3 counter values which are not matching with threshold:\n{}".format(c3_invalid_matches))
            error_list.append("C3-residency values are not zero when Stress tool is running")
        else:
            self._log.info("C3-residency values are zero when C-State BIOS knobs are enabled")
        self._log.info("Evaluating C6 < {}".format(self.THRESHOLD_C_STATE_LOW_VALUE))
        c6_invalid_matches = self.evaluate_expression("%s <" + str(self.THRESHOLD_C_STATE_LOW_VALUE),
                                                      parsed_cpu_power_data[self.C6_STATE_STR])
        if len(c6_invalid_matches):
            self._log.error("C6 counter values which are not matching with threshold:\n{}".format(c6_invalid_matches))
            error_list.append("C6-residency values are not low when Stress tool is running")
        else:
            self._log.info("C6-residency values are low (C6 < {}) when C-State BIOS knobs are enabled"
                           .format(self.THRESHOLD_C_STATE_LOW_VALUE))
        self._log.info("Evaluating Cx < {}".format(self.THRESHOLD_C_STATE_LOW_VALUE))
        cx_invalid_matches = self.evaluate_expression("%s <" + str(self.THRESHOLD_C_STATE_LOW_VALUE),
                                                      parsed_cpu_power_data[self.CX_STATE_STR])
        if len(cx_invalid_matches):
            self._log.error("Cx counter values which are not matching with threshold:\n{}".format(cx_invalid_matches))
            error_list.append("Cx-residency values are not low when Stress tool is running")
        else:
            self._log.info("Cx-residency values are low (Cx < {}) when C-State BIOS knobs are enabled"
                           .format(self.THRESHOLD_C_STATE_LOW_VALUE))
        # kill stress tool
        self._stress_tool.kill_stress_tool("stress", self.STRESS_TOOL_RUN_CMD)

        # disabling c state BIOS knobs
        self.set_and_verify_bios_knobs(self.CS_DISABLE_BIOS_CONFIG_FILE)

        # sleep time system to be idle
        time.sleep(self.WAIT_TIME_SIXTY_SECONDS)
        # get CPU percentage
        cpu_percentage_value = self._common_content_lib.get_cpu_utilization()
        # verify CPU percentage is low or not
        if cpu_percentage_value > self.THRESHOLD_CPU_PERCENTAGE_VALUE:
            raise RuntimeError("Current CPU utilization value: {} is higher than the expected value: {}"
                               .format(cpu_percentage_value, self.THRESHOLD_CPU_PERCENTAGE_VALUE))
        # run and verify TurboStat data
        busy_percent_data_list, busy_mhz_data_list = self.run_and_parse_turbostat_tool()

        # verify Bzy_MHz data
        self._log.info("Evaluating Busy_MHz data are consistent with +-{}% variance"
                       .format(self.THRESHOLD_BUSY_MHZ_VALUE))
        # for -5% variance
        threshold_memtotal_floor = (busy_mhz_data_list[0] - (busy_mhz_data_list[0] *
                                                             (self.THRESHOLD_BUSY_MHZ_VALUE / 100)))
        # for +5% variance
        threshold_memtotal_celling = (busy_mhz_data_list[0] + (busy_mhz_data_list[0] *
                                                               (self.THRESHOLD_BUSY_MHZ_VALUE / 100)))
        busy_mhz_invalid_matches = self.evaluate_expression(str(threshold_memtotal_floor) + "<= %s <=" +
                                                            str(threshold_memtotal_celling),
                                                            busy_mhz_data_list)
        if len(busy_mhz_invalid_matches):
            self._log.error("Inconsistent Bzy_MHz values are:\n{}".format(busy_mhz_invalid_matches))
            error_list.append("Bzy_MHz column values are inconsistent")
        else:
            self._log.info("Bzy_MHz column values inconsistent with +-{}% variance"
                           .format(self.THRESHOLD_BUSY_MHZ_VALUE))

        # run stress tool
        self._stress_tool.execute_async_stress_tool(self.STRESS_TOOL_RUN_CMD, "stress")
        time.sleep(self.WAIT_TIME_TWENTY_SECONDS)

        # parse TurboStat data
        busy_percent_data_list, busy_mhz_data_list = self.run_and_parse_turbostat_tool()
        # verify Bzy_MHz data
        self._log.info("Evaluating Busy_MHz data are consistent with +-{}% variance"
                       .format(self.THRESHOLD_BUSY_MHZ_VALUE))
        # for -5% variance
        threshold_memtotal_floor = (busy_mhz_data_list[0] - (busy_mhz_data_list[0] *
                                                             (self.THRESHOLD_BUSY_MHZ_VALUE / 100)))
        # for +5% variance
        threshold_memtotal_celling = (busy_mhz_data_list[0] + (busy_mhz_data_list[0] *
                                                               (self.THRESHOLD_BUSY_MHZ_VALUE / 100)))
        busy_mhz_invalid_matches = self.evaluate_expression(str(threshold_memtotal_floor) + "<= %s <=" +
                                                            str(threshold_memtotal_celling),
                                                            busy_mhz_data_list)
        if len(busy_mhz_invalid_matches):
            self._log.error("Inconsistent Bzy_MHz values are:\n{}".format(busy_mhz_invalid_matches))
            error_list.append("Bzy_MHz column values inconsistent with +-{}% variance".format(
                self.THRESHOLD_BUSY_MHZ_VALUE))
        else:
            self._log.info("Bzy_MHz column values are consistent with +-{}% variance"
                           .format(self.THRESHOLD_BUSY_MHZ_VALUE))
        # kill stress tool
        self._stress_tool.kill_stress_tool("stress", self.STRESS_TOOL_RUN_CMD)
        if len(error_list):
            raise TestFail("\n".join(error_list))
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        return True

    def run_and_parse_turbostat_tool(self):
        """
        This method is to run and parse TurboStat tool
        """
        self._stress_tool.execute_async_stress_tool(TurboStatConstants.TURBOSTAT_CMD_LINUX.format(TurboStatConstants.
                                                                                                  TURBOSTAT_LOG_FILE_NAME),
                                                    TurboStatConstants.TURBOSTAT_TOOL_FOLDER_NAME,
                                                    executor_path=self._turbostat_executor_path)
        # sleep time to generate the output
        time.sleep(5)
        # killing the TurboStat tool process
        self._stress_tool.kill_stress_tool(TurboStatConstants.TURBOSTAT_TOOL_FOLDER_NAME,
                                           TurboStatConstants.TURBOSTAT_CMD_LINUX.format(TurboStatConstants.
                                                                                         TURBOSTAT_LOG_FILE_NAME))
        # command to get TurboStat output
        turbostat_opt_data = self._common_content_lib.execute_sut_cmd("cat {}".format(TurboStatConstants.
                                                                                      TURBOSTAT_LOG_FILE_NAME),
                                                                      "command to get TurboStat data",
                                                                      self._command_timeout,
                                                                      cmd_path=self._turbostat_executor_path)
        self._log.info("TurboStat tool's output data \n {}".format(turbostat_opt_data))
        # parse TurboStat data
        busy_percent_data_list, busy_mhz_data_list = self.parse_turbostat_data(turbostat_opt_data)
        return busy_percent_data_list, busy_mhz_data_list


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementACPIStateOnLinux.main()
             else Framework.TEST_RESULT_FAIL)
