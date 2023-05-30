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

from dtaf_core.lib.dtaf_constants import Framework
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib.dmidecode_verification_lib import DmiDecodeVerificationLib


class ReducedSpeedMemModeStressTest(DDRCommon):
    """
    Glasgow ID: 63310
    This test case is to demonstrate DC system reset cycles including OS boot and shutdown without unexpected errors.
    This testing covers the below tasks..
    1. Covers reliability testing of a standard Memory configuration with OS shutdown to system off, then power on (DC)
    cycling.
    2. Memory "Fast" Warm and Cold reset are disabled, forcing a platform memory reconfiguration by the MRC on each boot
    cycle.
    3. Stressapptest is executed for about two minutes on each cycle to exercise system memory.
    """
    _bios_config_file = "reduced_speed_memory_bios_knobs.cfg"
    TEST_CASE_ID = "G63310"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new StressTestRebootFastBootEn object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(ReducedSpeedMemModeStressTest, self).__init__(test_log,
                                                            arguments, cfg_opts,
                                                            self._bios_config_file)
        self._dmi_decode_verification = DmiDecodeVerificationLib(test_log, self._os)
        self._mlc_extract_path = None

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.
        5. Copy MLC and stressapp test tool tar file to Linux SUT.
        6. Unzip tar file under user home folder.

        :return: None
        """
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        total_memory_before_bios = self.get_total_memory()
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        total_memory_after_bios = self.get_total_memory()
        self.compare_memtotal(total_memory_before_bios, total_memory_after_bios)
        self._common_content_lib.clear_dmesg_log()
        self._common_content_lib.clear_os_log()
        load_avg_value = self.get_load_average()
        max_load_avg = self.get_max_load_average(load_avg_value)
        self._log.info("Correct load average value {}".format(max_load_avg))
        if float(max_load_avg) <= self.CMP_LOAD_AVERAGE_BEFORE_STRESSAPP:
            self._log.info("Success as maximum value of load average value is less than threshold value")
        else:
            log_err = "Failed as maximum value of load average value more than threshold value"
            self._log.error(log_err)
            raise RuntimeError(log_err)

        self._mlc_extract_path = self._install_collateral.install_mlc()
        self._install_collateral.install_stress_test_app()

    def execute(self):
        """
        Check the DMI Type 17 data against the config file data.
        Perform MLC test.
        Run stress app test to observe load average value more than threshold value as 40
        Also, checks logs for any unexpected error.

        :return: True, if the test case is successful.
        :raise: RuntimeError: If load average is not matching with threshold value..
        """
        return_value = []
        dmi_cmd = "dmidecode > dmi.txt"
        self._common_content_lib.execute_sut_cmd(dmi_cmd, "get dmi dmidecode output", self._command_timeout,
                                                 cmd_path=self.LINUX_USR_ROOT_PATH)

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(test_case_id=self.TEST_CASE_ID,
                                                                            sut_log_files_path=self.LINUX_USR_ROOT_PATH,
                                                                            extension=".txt")

        dict_dmi_decode_from_tool = self._dmidecode_parser.dmidecode_parser(log_path_to_parse)

        dict_dmi_decode_from_spec = self._smbios_config.get_smbios_table_dict()
        self._log.info("Template SMBIOS informaton.. \n {}".format(dict_dmi_decode_from_spec))

        # Checking the Desktop Management Interface Type 17
        return_value.append(self._dmi_decode_verification.verify_diff_param_memory_device(
            dict_dmi_decode_from_tool, dict_dmi_decode_from_spec))

        self._common_content_lib.execute_sut_cmd("modprobe msr", "Load msr", self._command_timeout)

        self._common_content_lib.execute_sut_cmd("chmod +x mlc", "Assigning executable privileges ",
                                                 self._command_timeout, self._mlc_extract_path)

        self._common_content_lib.execute_sut_cmd("./mlc -Z 2>&1 | tee -a mlc_poff.out",
                                                 "run mlc",
                                                 self._command_timeout, self._mlc_extract_path)
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(test_case_id=self.TEST_CASE_ID,
                                                                            sut_log_files_path=self._mlc_extract_path,
                                                                            extension=".out")
        mlc_out_path = os.path.join(log_path_to_parse, "mlc_poff.out")
        return_value.append(self._mlc_utils.verify_mlc_log_with_template_data(mlc_out_path))

        self.execute_installer_stressapp_test_linux()
        load_avg_value = self.get_load_average()
        max_load_avg = self.get_max_load_average(load_avg_value)
        self._log.info("Correct load average value {}".format(max_load_avg))
        if float(max_load_avg) >= self.CMP_LOAD_AVERAGE_AFTER_STRESSAPP:
            self._log.info("Correct load average value...")
        else:
            log_error = "Incorrect load average value"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._common_content_lib.create_dmesg_log()
        self._common_content_lib.create_mce_log()

        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(test_case_id=self.TEST_CASE_ID,
                                                                            sut_log_files_path=self.LINUX_USR_ROOT_PATH,
                                                                            extension=".log")

        return self.log_parsing_stress_app_test(log_file_path=log_path_to_parse)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ReducedSpeedMemModeStressTest.main() else Framework.TEST_RESULT_FAIL)
