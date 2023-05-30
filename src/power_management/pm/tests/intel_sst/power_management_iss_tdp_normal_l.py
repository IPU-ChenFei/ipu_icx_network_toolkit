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
import sys
import os
import threading
import time
import re

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.dtaf_content_constants import NumberFormats
from src.lib.bios_util import ItpXmlCli, PlatformConfigReader
from src.lib.install_collateral import InstallCollateral
from src.provider.cpu_info_provider import CpuInfoProvider
from src.provider.ptu_provider import PTUProvider
from src.provider.stressapp_provider import StressAppTestProvider
from src.power_management.pm.tests.intel_sst.intel_sst_common import IntelSSTCommon, IntelSSTConfig


class PowermanagementISSTDPNormal(IntelSSTCommon):
    """
    This test case is used for Intel speed select feature validation with TDP Normal.
    HPALM ID : H81631
    """
    TEST_CASE_ID = ["H81631", "PI_Powermanagement_ISS_TDP_Normal_L"]
    REGEX_SST_PP = r"Intel.*SST-PP.*is\ssupported"
    TDP_CONFIG = IntelSSTConfig.BASE
    TDP_LEVEL = '0'
    _BIOS_CONFIG_FILE = "power_management_iss_tdp_normal.cfg"
    BIT_TIMEOUT = 5  # in minutes
    BURNING_50_WORKLOAD_CONFIG_FILE = "cpu_memory_100_workload.txt"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PowermanagementISSTDPNormal

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._BIOS_CONFIG_FILE)
        test_log.debug("Bios config file: %s", self.bios_config_file)
        super(PowermanagementISSTDPNormal, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path=self.bios_config_file)
        self.check_is_iss_supported()
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self.os, cfg_opts=cfg_opts)
        self.burnin_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BURNING_50_WORKLOAD_CONFIG_FILE)
        self._ptu_provider = PTUProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self._cpu_provider = CpuInfoProvider.factory(test_log, cfg_opts, self.os)

    def check_is_iss_supported(self):
        """
        This method is to check whether ISS support on SUT
        raise : raise exception if does not supports
        """
        intel_speed_select_info_cmd = "intel-speed-select -info"
        intel_speed_select_info_res_temp = self.os.execute(intel_speed_select_info_cmd, self._command_timeout)
        intel_speed_select_info_res = intel_speed_select_info_res_temp.stdout + "\n" + intel_speed_select_info_res_temp.stderr
        regex_res = re.findall(self.REGEX_SST_PP, intel_speed_select_info_res)
        if len(regex_res) == 0:
            raise content_exceptions.TestFail("SST PP does not supported in the SKU")

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PowermanagementISSTDPNormal, self).prepare()

    def execute(self):
        """test main logic to check the functionality"""
        errors = []
        intel_sst_bios_details = self.get_intel_sst_info_bios(self.TDP_CONFIG)
        msr_values = self.get_msr_values([self.MSR_x35, self.MSR_649, self.MSR_64A], convert_to=NumberFormats.BINARY)
        if msr_values[hex(self.MSR_x35)]:
            core_count_msr = self._common_content_lib.convert_binary_to_decimal(
                self._common_content_lib.get_binary_bit_range(msr_values[hex(self.MSR_x35)], self.INDICES_16_31))
            self._log.info("MSR %s value is %s", hex(self.MSR_x35), core_count_msr)
        else:
            errors.append("Error in getting Core count for MSR {} and indices {}".format(self.MSR_x35,
                                                                                         self.INDICES_16_31))

        if msr_values[hex(self.MSR_x35)]:
            thread_count_msr = self._common_content_lib.convert_binary_to_decimal(
                self._common_content_lib.get_binary_bit_range(msr_values[hex(self.MSR_x35)],
                                                              self.INDICES_0_15))
            self._log.info("MSR %s value is %s", hex(self.MSR_x35), thread_count_msr)
        else:
            errors.append("Error in getting Thread count for MSR {} and indices {}".format(self.MSR_x35,
                                                                                           self.INDICES_0_15))
        if msr_values[hex(self.MSR_64A)]:
            tdp_value = self._common_content_lib.convert_binary_to_decimal(
                self._common_content_lib.get_binary_bit_range(msr_values[hex(self.MSR_64A)],
                                                              self.INDICES_0_14))
            self._log.info("MSR %s value is %s", hex(self.MSR_64A), tdp_value)
        else:
            errors.append("Error in getting Thread count for MSR {} and indices {}".format(self.MSR_64A,
                                                                                           self.INDICES_0_14))

        p1_ratio = self.get_p1_ratio(IntelSSTConfig.Config1, self.TDP_LEVEL)
        self._log.debug("P1 Ratio is {}".format(p1_ratio))
        if int(p1_ratio) != int(intel_sst_bios_details[self.TDP_LEVEL][self.IntelSSTTable.P1_RATIO]):
            errors.append("PythonSV p1 ratio {} and Bios {} P1 ratios are not matching".format(p1_ratio,
                                                                                               intel_sst_bios_details[
                                                                                                   self.TDP_LEVEL][
                                                                                                   self.IntelSSTTable.P1_RATIO]))
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("Waiting for system to boot up to os")
        self.os.wait_for_os(self.reboot_timeout)
        bit_location = self.install_collateral.install_burnintest()

        burnin_thread = threading.Thread(target=self.stress_app_provider.execute_burnin_test,
                                         args=(self.log_dir, self.BIT_TIMEOUT, bit_location,
                                               self.burnin_config_file,))

        burnin_thread.start()

        sut_folder_path = self._ptu_provider.install_ptu()
        self._ptu_provider.execute_async_ptu_tool(self._ptu_provider.PTUMON_DEFAULT, sut_folder_path)
        pcodeio_map_values = self.get_uncore_pcodeio_map_show_search_io_wp_ia_cv_ps()
        error_pcodeio_map_values = []
        count = 0
        reg_ratio_values = []
        for key, value in pcodeio_map_values.items():
            if value != 0:
                count += 1
                reg_ratio_values.append(value)
                self._log.info("%s register value is matching expected result %s", key, value)
            else:
                error_pcodeio_map_values.append({key: value})

        if count != core_count_msr:
            errors.append("core count {} is not matched with number of core register value {}".format(core_count_msr,
                                                                                                      count))
        if len(reg_ratio_values):
            freq = reg_ratio_values[0] * 100
            self._log.debug("Frequency {}".format(freq * 100))

        burnin_thread.join()
        self._ptu_provider.kill_ptu_tool()
        log_dir = self._common_content_lib.get_log_file_dir()

        if not os.path.exists(os.path.join(log_dir, "testcase_logs")):
            log_dir = log_dir + os.sep + "testcase_logs"
            os.makedirs(log_dir)

        self._common_content_lib.copy_log_files_to_host(test_case_id=log_dir,
                                                        sut_log_files_path=self._ptu_provider.SUT_LOG_FILE_PATH,
                                                        extension=".csv")

        absolute_log_path = log_dir + os.sep + self._ptu_provider.LOG_FILE_NAME
        self._cpu_provider.populate_cpu_info()
        socket_info = int(self._cpu_provider.get_number_of_sockets())
        for number in range(socket_info):
            columun_values = self._ptu_provider.get_column_data(self._ptu_provider.PTU_CPU.format(number),
                                                                self._ptu_provider.PTU_POWER, absolute_log_path)
            self._log.info("{} {}value is: {}".format(self._ptu_provider.PTU_CPU.format(number),
                                                      self._ptu_provider.PTU_POWER, columun_values))


        if errors:
            raise content_exceptions.TestFail("\n".join(errors) + "\n" + self.DEFAULT_ERROR_MESSAGE)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        time.sleep(10)
        super(PowermanagementISSTDPNormal, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowermanagementISSTDPNormal.main() else Framework.TEST_RESULT_FAIL)
