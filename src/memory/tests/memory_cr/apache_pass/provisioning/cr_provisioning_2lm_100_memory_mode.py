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
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon


class CRProvisioning2LM100MemoryMode(CrProvisioningTestCommon):
    """
    Glasgow ID: 57207
    Verification of the platform supported DCPMM capabilities in a Microsoft Windows OS environment.

    1. Create DCPMMs in 2LM Memory Mode 100% mode.
    2. Two-level memory (2LM) hierarchical memory model with DCPMM is referred to as Memory Mode.
    3. The DCPMM configured volatile memory acts as the second tier which provides large memory capacities.
    4. Confirm all existing Namespaces are removed and the entire memory configuration is configured as 2LM memory.
    """

    BIOS_CONFIG_FILE = "cr_provision_2lm_memory_mode_100_bios_knobs.cfg"
    TEST_CASE_ID = "G57207"

    _ipmctl_executer_path = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRProvisioning2LM100MemoryMode object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(CRProvisioning2LM100MemoryMode, self).__init__(test_log,
                                                             arguments, cfg_opts,
                                                             self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.
        5. Copy ipmctl tool to windows SUT.
        6. Unzip file under home folder.

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # To clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        self._ipmctl_executer_path = self._install_collateral.install_ipmctl()

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. It is first confirmed that the DCPMMs are capable of supporting Memory mode with 2LM enabled.
        2. All installed DCPMM(s) are configured with 100% of capacity as volatile memory.
        3. Create namespaces for the memory regions.
        4. Verify namespaces and region status.
        5. Save DCPMM configuration data to a file.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = []

        # Creating a data frame with dimm information and adding extra columns as per our test case need.
        dimm_show = self.populate_memory_dimm_information(self._ipmctl_executer_path)

        # Get the list of dimms which are healthy and log them.
        self.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy are matching with the pmem disk output.
        self.verify_all_dcpmm_dimm_healthy()

        # Verify the firmware version of each dimms are matching with the pmem disk output.
        self.verify_dimms_firmware_version()

        # Pre-existing namespaces are identified here.
        namespace_info = self.dcpmm_get_disk_namespace()

        # If namespace exists, remove them from DCPMMs.
        self.dcpmm_check_disk_namespace_initilize(namespace_info)

        # Get the list of just created namespaces.
        self.dcpmm_get_disk_namespace()

        # Get the Pmem-Unused Regions.
        self.dcpmm_get_pmem_unused_region()

        # Get the latest memory information about the DCPMMs after goal creation.
        self.ipmctl_show_mem_resources(self._ipmctl_executer_path)

        # Configure all capacity on the installed DCPMM(s) with 100% as volatile memory.
        dcpmm_disk_goal = self.dcpmm_configuration(
            self._ipmctl_executer_path, cmd=r".\ipmctl.exe create -f -goal memorymode=100", cmd_str="with 100% as "
                                                                                                    "volatile memory")
        self._os.reboot(self._reboot_timeout)

        # Verify the goal is displayed showing 100% of the DCPMM capacity is configured as Volatile memory.
        return_value.append(self.verify_app_direct_mode_provisioning(mode="mem",
                                                                     mode_percentage=100,
                                                                     total_memory_result_data=dimm_show,
                                                                     app_direct_result_data=dcpmm_disk_goal))
        # Verify 2LM provisioning mode
        return_value.append(self.verify_lm_provisioning_configuration_win(dcpmm_disk_goal, mode="2LM"))

        return all(return_value)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if CRProvisioning2LM100MemoryMode.main() else Framework.TEST_RESULT_FAIL)
