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
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib.dmidecode_verification_lib import DmiDecodeVerificationLib


class SmBiosStructureValidation(DDRCommon):
    """
    Glasgow ID: 63311
    1. Verify that the SMBIOS structures are listed and correct as applicable per the current SMBIOS specification.
    2. The DMIDECODE utility output is used to view the applicable system hardware data.  This is a default function in
    major enterprise Linux Distributions.
    3. This test case is focused on reviewing memory specific output to ensure it is complete and correct.
    """
    _bios_config_file = "smbios_table_structure_validation.cfg"
    TEST_CASE_ID = "G63311"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new SmBiosStructureValidation object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(SmBiosStructureValidation, self).__init__(test_log, arguments, cfg_opts, self._bios_config_file)
        self._dmi_decode_verification = DmiDecodeVerificationLib(test_log, self._os)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # To clear Os logs
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def execute(self):
        """
        Create an output file of the smbios information and verify them as per the test case procedures.

        :return: True, if the test case is successful.
        :raise: None.
        """
        dmi_comparision_results = []
        dmi_cmd = "dmidecode > dmi.txt"
        self._common_content_lib.execute_sut_cmd(dmi_cmd, "get dmi dmidecode output", self._command_timeout,
                                                 cmd_path=self.LINUX_USR_ROOT_PATH)

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(test_case_id=self.TEST_CASE_ID,
                                                                            sut_log_files_path=self.LINUX_USR_ROOT_PATH,
                                                                            extension=".txt")

        # Check whether the dmi.txt exists in the folder has been done inside the "dmidecode_parser" function.
        dict_dmi_decode_from_tool = self._dmidecode_parser.dmidecode_parser(log_path_to_parse)
        dict_dmi_decode_from_spec = self._smbios_config.get_smbios_table_dict()
        self._log.info("Template SMBIOS informaton.. \n {}".format(dict_dmi_decode_from_spec))

        # Check the Desktop Management Interface Type 0 - Bios Information.
        dmi_comparision_results.append(self._dmi_decode_verification.verify_bios_information(
            dict_dmi_decode_from_tool, dict_dmi_decode_from_spec))

        # Check the Desktop Management Interface Type 1 - System Information.
        dmi_comparision_results.append(self._dmi_decode_verification.verify_system_information(
            dict_dmi_decode_from_tool, dict_dmi_decode_from_spec))

        # Check the processor information.
        dmi_comparision_results.append(self._dmi_decode_verification.verify_processor_information(
            dict_dmi_decode_from_tool, dict_dmi_decode_from_spec))

        # Check the Desktop Management Interface Type 16 - Physical Memory Array
        dmi_comparision_results.append(self._dmi_decode_verification.verify_physical_memory_array(
            dict_dmi_decode_from_tool, dict_dmi_decode_from_spec))

        # Check the Desktop Management Interface Type 17 - Memory Device
        dmi_comparision_results.append(self._dmi_decode_verification.verify_memory_device(
            dict_dmi_decode_from_tool, dict_dmi_decode_from_spec))

        # Check the Desktop Management Interface Type 19 - Memory Array Mapped Address
        dmi_comparision_results.append(self._dmi_decode_verification.verify_memory_array_mapped_address(
            dict_dmi_decode_from_tool))

        # Check the Desktop Management Interface Type 20 - Memory Device Mapped Addresses
        dmi_comparision_results.append(self._dmi_decode_verification.verify_memory_device_mapped_address(
            dict_dmi_decode_from_tool))

        # Check the End of Table pattern
        dmi_comparision_results.append(self._dmi_decode_verification.verify_end_of_table(
            self._dmidecode_parser.dmi_output.strip().split('\n')[-1]))

        return all(dmi_comparision_results)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SmBiosStructureValidation.main() else Framework.TEST_RESULT_FAIL)
