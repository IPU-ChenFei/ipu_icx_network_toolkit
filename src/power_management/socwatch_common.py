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
import time
import threading

from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.socwatch_provider import SOCWatchProvider, SocWatchCSVReader, PacakgePState
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class SocWatchBaseTest(ContentBaseTestCase):
    """
    Base class extension for SocWatchBaseTest which holds common functionality
    """
    RESIDENCY_PERCENT_MATCH = "Residency (%)"
    P0_SUM_DICT = {}

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of sut SocWatchBaseTest.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SocWatchBaseTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)
        self.socwatch_provider = SOCWatchProvider.factory(self._log, cfg_opts, self.os)  # type: SOCWatchProvider
        self.stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self.os, cfg_opts=cfg_opts)
        csv_file_path = os.path.join(self.log_dir, self.socwatch_provider.CSV_FILE)
        self.csv_reader_obj = SocWatchCSVReader(self._log, csv_file_path)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        This function will Clear the mce errors and load bios defaults to SUT
        """
        self._common_content_lib.clear_mce_errors()
        super(SocWatchBaseTest, self).prepare()

    def execute_socwatch_tool(self, socwatch_runtime=120, burnin_config_file=None, bit_timeout=0,
                              system_idle_timeout=0, execute_stress=True):
        """
        1. This function check if mce errors
        2. This function install socwatch tool, burnintest
        2. Execute socwatch command on specific time
        3. Execute burnintest command to load the system with specific percentage
        4. Copy the Csv file from host to sut

        :raise: raise content_exceptions.TestError if found the MCE errors
        """
        bit_location = None
        burnin_thread = None
        mce_error = self._common_content_lib.check_if_mce_errors()
        if mce_error:
            raise content_exceptions.TestError("MCE Logs detected after reboot the sut, Error: %s" % mce_error)
        socwatch_dir_path = self.socwatch_provider.install_socwatch_tool()  # install socwatch tool
        if execute_stress:
            bit_location = self.collateral_installer.install_burnintest()  # install burnin tool
        self._log.info("Waiting for %d to make the system IDLE " % system_idle_timeout)
        time.sleep(system_idle_timeout)  # system idle time
        # run burnin test
        if execute_stress:
            burnin_thread = threading.Thread(target=self.stress_app_provider.execute_burnin_test,
                                             args=(self.log_dir, bit_timeout, bit_location,
                                                         burnin_config_file,))
            # Thread has been started
            burnin_thread.start()
        self.socwatch_provider.socwatch_command(socwatch_runtime, socwatch_dir_path)  # Run socwatch command
        if execute_stress:
            burnin_thread.join()
        # Copy Csv file from host to sut
        self.socwatch_provider.copy_csv_file_from_sut_to_host(self.log_dir, socwatch_dir_path)
        # Update the csv file to the csv reader provider
        self.csv_reader_obj.update_csv_file(os.path.join(self.log_dir, self.socwatch_provider.CSV_FILE))

    def set_verify_bios_knobs(self, bios_config_file):
        """
        This function set and verify bios knobs
        """
        self.bios_util.set_bios_knob(bios_config_file)
        self.perform_graceful_g3()
        self.bios_util.verify_bios_knob(bios_config_file)

    def add_p0_values(self, package_p_state, p_state_table):
        """
        This function is used to add all the values for P0 different frequencies

        :param package_p_state: get the package state
        :param p_state_table: P state Table
        :return: Sum of P0 values for all P0 Frequencies
        """
        p_state_values = None
        try:
            if PacakgePState.PACKAGE_P_STATE_P0 in package_p_state:
                p_state_values = p_state_table[package_p_state]
                for key, value in p_state_values.items():
                    if self.RESIDENCY_PERCENT_MATCH in key:
                        if key in self.P0_SUM_DICT:
                            self.P0_SUM_DICT[key] = float(value) + self.P0_SUM_DICT[key]
                        else:
                            self.P0_SUM_DICT[key] = float(value)
        except KeyError:
            raise content_exceptions.TestFail("%s package P state does not exist in SoCWatchOutput",
                                              p_state_values)
        return self.P0_SUM_DICT

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self.collateral_installer.roll_back_embargo_repo()
        super(SocWatchBaseTest, self).cleanup(return_status)
