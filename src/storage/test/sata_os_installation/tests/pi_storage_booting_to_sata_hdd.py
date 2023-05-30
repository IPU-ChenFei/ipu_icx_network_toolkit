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
from dtaf_core.lib.os_lib import LinuxDistributions
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.environment.os_installation import OsInstallation
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import SutInventoryConstants
from src.provider.storage_provider import StorageProvider


class StorageBootingToSataHdd(BaseTestCase):
    """
    TEST ID : [H80262-PI_Storage_BootingToSATAHDD_L, P16013763417-SATASSD-OS_and_Driver_installation_check_in_AHCI_Mode_CENTOS, P22013310308-SATASSD-OS_and_Driver_installation_check_in_AHCI_Mode_RHEL]
    
    Install RHEL/CENTOS OS 
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToSataHdd object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath

        super(StorageBootingToSataHdd, self).__init__(test_log, arguments, cfg_opts)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider

        self._storage_provider = StorageProvider.factory(self._log, self._os, self._cfg_opts, "os")
        self._common_content_lib = CommonContentLib(self._log, self._os, None)
        self.name_ssd = None
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
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if (SutInventoryConstants.SATA_SSD_NAME_RHEL in line and self._os.os_subtype.lower() in
                    SutInventoryConstants.SATA_SSD_NAME_RHEL) or (SutInventoryConstants.SATA_SSD_NAME_CENTOS in line and
                        self._os.os_subtype.lower() in SutInventoryConstants.SATA_SSD_NAME_CENTOS):
                    self.name_ssd = line
                    break
            else:
                raise content_exceptions.TestError("Unable to find ssd name for {} installation, please check the file"
                                                   " under {} and update it correctly".format(self._os.os_subtype,
                                                                                              sut_inv_file_path))

        self.name_ssd = self.name_ssd.split("=")[1]

        self._log.info("SSD Name from config file : {}".format(self.name_ssd))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.SATA, self._os.os_subtype.lower())

    def execute(self):
        """
        This function is responsible for linux os installation in SATA device

        :return: True, if the test case is successful.
        :raise: TestFail
        """
        ret_val = []
        self._log.info("\'{}\' os is going to be installed in the SATA device {}".format(self._os.os_subtype,
                                                                                         self.name_ssd))
        if self._os.os_subtype.lower() == LinuxDistributions.RHEL.lower():
            ret_val.append(self._os_installation_lib.rhel_os_installation())
        elif self._os.os_subtype.lower() == LinuxDistributions.CentOS.lower():
            ret_val.append(self._os_installation_lib.centos_os_installation())
        else:
            raise content_exceptions.TestFail("Unsupported os subtype {} for this test case. Please provide the correct"
                                              " os subtype in system_configuration file".format(self._os.os_subtype))
        self.log_dir = self._common_content_lib.get_log_file_dir()

        lsblk_res = self._storage_provider.get_booted_device()

        device_info = self._storage_provider.get_device_type(lsblk_res, self.name_ssd)

        if not device_info["usb_type"]:
            raise content_exceptions.TestFail("Unable to fetch the SATA device type..")

        if not device_info["serial"]:
            raise content_exceptions.TestFail("Unable to fetch the serial number information of the device..")

        if "SATA" not in device_info["usb_type"].upper():
            raise content_exceptions.TestFail("OS not installed on the SATA SSD, please try again..")

        self._log.info("Successfully verified that OS installed in SATA device..")

        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageBootingToSataHdd, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToSataHdd.main() else Framework.TEST_RESULT_FAIL)
