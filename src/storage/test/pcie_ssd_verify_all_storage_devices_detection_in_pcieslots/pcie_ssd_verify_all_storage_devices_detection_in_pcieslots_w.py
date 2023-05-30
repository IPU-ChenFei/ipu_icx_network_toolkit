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

from src.lib.content_base_test_case import ContentBaseTestCase
from src.environment.os_installation import OsInstallation
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import SutInventoryConstants
from src.provider.storage_provider import StorageProvider
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class VerifyAllStorageDeviceDetectionInPcieSlots(ContentBaseTestCase):
    """
    PhoenixID - 16013593122 : Pcie SSD - Verify all storage devices detection in Pcieslots
    PhoenixID - 16013591407 : Pcie SSD - Verify system booting with all PCIeSSD populated to all pcieslots
    To verify PCIe SSD.
    """
    TEST_CASE_ID = ["16013593122", "Pcie SSD - Verify all storage devices detection in Pcieslotsl", "16013591407", "Pcie SSD - Verify system booting with all PCIeSSD populated to all Pcie slots"]

    STEP_DATA_DICT = {
        1: {'step_details': 'Boot to OS',
            'expected_results': 'System booted to OS'},
        2: {'step_details': 'verify pcie device at OS level',
            'expected_results': 'pcie device verified at OS level'},
    }
    SMARTCTL_CMD_TO_SCAN = r"smartctl.exe --scan"
    C_DRIVE_PATH = "C:\\"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToSataHdd object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        self._cc_log_path = arguments.outputpath

        super(VerifyAllStorageDeviceDetectionInPcieSlots, self).__init__(test_log, arguments, cfg_opts)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, None)
        self.install_collateral_obj = InstallCollateral(self._log, self.os, self._cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

        # self.name_ssd = None
        self.pcie_ssd_inventory = []  # pcie nvme device listed in sut_inventory.cfg file
        self.pcie_ssd_sut = []  # pcie nvme device listed in sut at os level

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        # getting the pcie storage device names from the sut_inventory
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if SutInventoryConstants.NVME in line:
                    line = line.split("=")[1]
                    self.pcie_ssd_inventory.append(line.strip())
            if not self.pcie_ssd_inventory:
                raise content_exceptions.TestError("Unable to find pcie nvme for pcie verification, "
                                                   "please check the sut_inventory.cfg file "
                                                   "under {} and update it correctly".format(sut_inv_file_path))

        self._log.info("pcie nvme SSD Name from config file : {}".format(self.pcie_ssd_inventory))

        # installing smartctl.exe tool to the SUT
        self._log.info("Copying smartctl.exe to the SUT")
        self.install_collateral_obj.copy_smartctl_exe_file_to_sut()

    def execute(self):
        """
        This function is responsible for linux os installation in SATA device
        :return: True, if the test case is successful.
        :raise: TestFail
        """
        ret_val = False
        # Step logger Start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

        # Step logger Start for Step 2
        self._test_content_logger.start_step_logger(2)
        self._log.info("\'{}\' drives will be compared to SUT pcie drives".format(self.pcie_ssd_inventory))
        # Executing smartctl.exe command to get the pcie devices details on OS
        scan_pcie_ssd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.SMARTCTL_CMD_TO_SCAN,
                                                                      cmd_str=self.SMARTCTL_CMD_TO_SCAN,
                                                                      execute_timeout=self._command_timeout,
                                                                      cmd_path=self.C_DRIVE_PATH)

        scan_pcie_ssd_lst = scan_pcie_ssd_output.split("\n")
        # verify the serial no of the Pcie storage devices
        for scan_pcie in scan_pcie_ssd_lst:
            if len(scan_pcie.split()):
                nvme_info_cmd = f"smartctl.exe -i {scan_pcie.split()[0]}"
                nvme_cmd_output = self._common_content_lib.execute_sut_cmd(nvme_info_cmd, "executing cmd {}".format(
                    nvme_info_cmd), self._command_timeout, cmd_path=self.C_DRIVE_PATH)
                for device_ in nvme_cmd_output.split("\n"):
                    if device_.startswith("Serial Number"):
                        serial_num = device_.split(":")[1]
                        self.pcie_ssd_sut.append(serial_num.strip())
        self._log.info("Pcie SSD list from OS : {}".format(self.pcie_ssd_sut))
        # comparing the device details in between inventory file data and data from OS
        res_list = []
        for inventory_drives in self.pcie_ssd_inventory:
            for sut_drives in self.pcie_ssd_sut:
                if sut_drives in inventory_drives:
                    res_list.append(inventory_drives)

        if len(self.pcie_ssd_inventory) == len(res_list):
            ret_val = True
        else:
            raise content_exceptions.TestFail("PCIE SSD Varifiaction FAILED : devices are not matching with inventory "
                                              "list")

        self._log.info("Successfully verified that system booting with all PCIeSSD populated to all pcie slots")
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        return ret_val

    def cleanup(self, return_status):
        """Test Cleanup"""

        super(VerifyAllStorageDeviceDetectionInPcieSlots, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyAllStorageDeviceDetectionInPcieSlots.main()
             else Framework.TEST_RESULT_FAIL)