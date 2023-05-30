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
from src.environment.os_installation import OsInstallation
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.provider.storage_provider import StorageProvider
from src.storage.test.storage_common import StorageCommon
from src.lib.dtaf_content_constants import SutInventoryConstants
from src.lib.content_base_test_case import ContentBaseTestCase
from dtaf_core.lib.os_lib import LinuxDistributions


class StorageBootingToPcieCentOS(ContentBaseTestCase):
    """
    Phoenix ID : 16013540692-DV_PCieSSD-VMD_enable_OS_Install_to_HHHL_VMD_enable_no_raid_Mode_and_NVME_driver_installation_check(use_Samsung_and_intel).

    Test steps:
        1.Enable Vmd Bios Knobs
        3.Install CentOS on the platform
    """
    TEST_CASE_ID = ["P16013540692", "Storage_BootingToPCIe_VMD_CentOS"]
    NVME_SSD_NAME_CENTOS = "nvme_ssd_name_centos"
    name_ssd = None

    step_data_dict = {1: {'step_details': 'Enable the VMD BIOS knobs',
                          'expected_results': 'successfully Enabled VMD BIOS knobs'},
                      2: {'step_details': 'install CentOS OS to PCIe SSD device',
                          'expected_results': 'OS installed successfully'},
                      3: {'step_details': 'Boot into OS',
                          'expected_results': 'Successfully Booted into OS without any errors'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToPcieCentOS object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath

        super(StorageBootingToPcieCentOS, self).__init__(test_log, arguments, cfg_opts)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._os = self.os
        self._storage_provider = StorageProvider.factory(self._log, self._os, self._cfg_opts, "os")
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self.storage_common_obj = StorageCommon(self._log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if self.NVME_SSD_NAME_CENTOS in line:
                    self.name_ssd = line
                    break   

        if not self.name_ssd:
            raise content_exceptions.TestError("Unable to find ssd name for {} installation, please check the file"
                                               " under {} and update it correctly".format(self.os.os_subtype,
                                                                                          sut_inv_file_path))

        self.name_ssd = self.name_ssd.split("=")[1]
        self._log.info("SSD Name from config file : {}".format(self.name_ssd))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.NVME, self.os.os_subtype.lower())

    def execute(self):
        """
        This method is used to install the CENTOS OS
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.storage_common_obj.enable_vmd_bios_knobs()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._log.info("Closing the Serial Port")
        self.cng_log.__exit__(None, None, None)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self._log.info("\'{}\' os is going to be installed in the PCIe device {}".format(self._os.os_subtype,
                                                                                         self.name_ssd))
        if self._os.os_subtype.lower() == LinuxDistributions.CentOS.lower():
            self._os_installation_lib.centos_os_installation(installation_mode="offline")
        else:
            raise content_exceptions.TestFail("Unsupported os subtype {} for this test case. Please provide the correct"
                                              " os subtype in system_configuration file".format(self._os.os_subtype))
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        lsblk_res = self._storage_provider.get_booted_device()
        self._log.info("booted device is {}".format(str(lsblk_res)))

        if SutInventoryConstants.NVME not in lsblk_res:
            raise content_exceptions.TestFail("OS not installed on the PCIE SSD, please try again..")

        self._log.info("Successfully verified that OS installed in PCIE device..")

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        super(StorageBootingToPcieCentOS, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToPcieCentOS.main() else Framework.TEST_RESULT_FAIL)