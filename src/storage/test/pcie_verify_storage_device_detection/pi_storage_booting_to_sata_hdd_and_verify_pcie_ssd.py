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
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import SutInventoryConstants

from src.provider.storage_provider import StorageProvider
from src.environment.os_installation import OsInstallation



class StorageBootingToSataHdd(BaseTestCase):
    """
    Glasgow ID/PhoenixID - EGS_PV_2030/16013546737 : Pcie SSD - Verify system booting with all PCIeSSD populated to all pcieslots
    Glasgow ID/PhoenixID - EGS_PV_2028/16013546193 : Pcie SSD - Verify all storage devices detection in Pcieslots
    Glasgow ID/PhoenixID - EGS_PV_1971/16013591350 : Pcie SSD - Verify system booting with all PCIeSSD populated to all pcieslots
    Glasgow ID/PhoenixID - EGS_PV_2047/16013591558 : Pcie SSD - Verify all storage devices detection in Pcieslots in Rhel
    To install CENTOS\RHEL on SATA ssd and verify PCIe SSD.
    """
    TEST_CASE_ID = ["EGS_PV_2030", "16013546737",
                    "Pcie SSD - Verify system booting with all PCIeSSD populated to all Pcie slots",
                    "EGS_PV_2028", "16013546193", "Pcie SSD - Verify all storage devices detection in Pcie slots",
                    "EGS_PV_1971", "16013591350",
                    "Pcie SSD - Verify system booting with all PCIeSSD populated to all pcie slots",
                    "EGS_PV_2047", "16013591558",
                    "Pcie SSD - Verify all storage devices detection in Pcie slots in Rhel"]

    STEP_DATA_DICT = {
        1: {'step_details': 'Perform Graceful AC Power Off and Power On and wait for Boot to OS',
            'expected_results': 'Ac Power Off and Power On performed and OS booted'},
        2: {'step_details': 'verify pcie device at OS level',
            'expected_results': 'pcie device verified at OS level'},
    }

    SCAN_PCIE_CMD_LINE = "smartctl --scan"
    SCAN_PCIE_CMD_STR = "scanning pcie devices connected to SUT"
    NVME_INFO_CMD = "smartctl -i {pcie_device}"
    NVME_INFO_CMD_STR = "getting pcie device information"
    SCAN_PCIE_CMD_TIMEOUT = 5

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToSataHdd object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        self._cc_log_path = arguments.outputpath
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

        super(StorageBootingToSataHdd, self).__init__(test_log, arguments, cfg_opts)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds

        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self._os, self._cfg_opts, None)
        self._product_family = self._common_content_lib.get_platform_family()
        self.reboot_timeout = \
            self._common_content_configuration.get_reboot_timeout()

        self.pcie_ssd_inventory = []  # pcie nvme device listed in sut_inventory.cfg file
        self.pcie_ssd_sut = []  # pcie nvme device listed in sut at os level
        self.log_dir = None

    @classmethod
    def add_arguments(cls, parser):
        super(StorageBootingToSataHdd, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        # Step logger Start for Step 1
        self._test_content_logger.start_step_logger(1)

        # read sut_inventory file and collect all pcie nvme details
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if (SutInventoryConstants.NVME in line):
                    line = line.split("=")[1]
                    self.pcie_ssd_inventory.append(line.strip())
            if not self.pcie_ssd_inventory:
                raise content_exceptions.TestError("Unable to find pcie nvme for pcie vrification, "
                                                   "please check the sut_inventory.cfg file "
                                                   "under {} and update it correctly".format(sut_inv_file_path))

        self._log.info("pcie nvme SSD Name from config file : {}".format(self.pcie_ssd_inventory))

        # perform power off - power on 
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)        
        # wait till SUT boots at OS level 
        self._os.wait_for_os(self.reboot_timeout)
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        This function is responsible for linux os installation in SATA device

        :return: True, if the test case is successful.
        :raise: TestFail
        """
        # Step logger Start for Step 2
        self._test_content_logger.start_step_logger(2)
        # initialise return value variable for test result = False
        ret_val = False
        self._log.info("\'{}\' drives will be compared to SUT pcie drives".format(self.pcie_ssd_inventory))

        self.log_dir = self._common_content_lib.get_log_file_dir()

        # scan pcie nvme device in OS using in-built smart controller tool        
        scan_pcie_ssd_output = self._common_content_lib.execute_sut_cmd(self.SCAN_PCIE_CMD_LINE, self.SCAN_PCIE_CMD_STR,
                                                                        self.SCAN_PCIE_CMD_TIMEOUT)
        # SUT pcie drives detected at OS level
        self._log.info("\'{}\' drives detected at OS level ".format(scan_pcie_ssd_output))

        # scrapping pcie scan cmd results per line
        scan_pcie_ssd_lst = scan_pcie_ssd_output.split("\n")

        for scan_pcie in scan_pcie_ssd_lst:
            if len(scan_pcie.split()):

                # scrapping pcie device file name from scan pcie cmd
                device_file_name = scan_pcie.split()[0]

                # collect pcie device information to find serial number of pcie device
                nvme_cmd_output = self._common_content_lib.execute_sut_cmd(self.NVME_INFO_CMD.format(pcie_device=device_file_name),
                                                                           self.NVME_INFO_CMD_STR,
                                                                           self.SCAN_PCIE_CMD_TIMEOUT)
                # collect pcie device serial number for one to one mapping
                for device_ in nvme_cmd_output.split("\n"):
                    if device_.startswith("Serial Number"):
                        serial_num = device_.split(":")[1]
                        self.pcie_ssd_sut.append(serial_num.strip())
        
        # prepare result list by matching serial number of SUT inventory pcie device and OS detected pcie device
        res_list = []
        for inventory_drives in self.pcie_ssd_inventory:
            for sut_drives in self.pcie_ssd_sut:
                if sut_drives in inventory_drives:
                    res_list.append(inventory_drives)

        # finally compare sut inventory pce nvme device list and os level pcie nvme device list
        if len(self.pcie_ssd_inventory) == len(res_list):
            ret_val = True
        else:
            raise content_exceptions.TestFail(
                "PCIE SSD Verification FAILED : devices are not matching with inventory list")

        self._log.info("Successfully verified that system booting with all PCIeSSD populated to all pcie slots")
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        return ret_val

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageBootingToSataHdd, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToSataHdd.main() else Framework.TEST_RESULT_FAIL)
