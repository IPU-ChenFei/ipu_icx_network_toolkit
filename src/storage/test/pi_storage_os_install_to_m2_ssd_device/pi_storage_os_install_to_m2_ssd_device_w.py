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
import re
import os

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_provider import BiosProvider

from src.environment.os_installation import OsInstallation
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.bios_util import BiosUtil
from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.storage.lib.storage_common import StorageCommon


class StorageOSInstallM2SsdSataDevice(BaseTestCase):
    """
    HPALM : H97915-PI_Storage_OS_Install_to_M.2_SSD_device_W

    Install windows OS on the platform
    """
    BIOS_CONFIG_FILE_NAME = "pi_storage_os_install_to_m2_ssd_device.cfg"
    TEST_CASE_ID = ["H97915", "PI_Storage_OS_Install_to_M.2_SSD_device_W"]
    SMARTCTL_CMD_TO_SCAN = r"smartctl.exe --scan"
    C_DRIVE_PATH = "C:\\"
    REGEX_FOR_WINDOWS_SATA_DISK = r"(\/dev\/\S+)\s+\-.*ATA\sdevice"
    step_data_dict = {1: {'step_details': 'Set the bios knob SATA Mode Selection to AHCI',
                          'expected_results': 'bios setting is done'},
                      2: {'step_details': 'start windows OS installation',
                          'expected_results': 'Windows OS installed successfully'},
                      3: {'step_details': 'Verify the bios knob SATA Mode Selection to AHCI',
                          'expected_results': 'Verified the bios knob SATA Mode Selection to AHCI'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageOSInstallM2SsdSataDevice object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath
        super(StorageOSInstallM2SsdSataDevice, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg_opts)
        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = os.path.join(cur_path, self.BIOS_CONFIG_FILE_NAME)
        self._bios_util = BiosUtil(self._cfg_opts, bios_config_file_path,
                                   self._bios, self._log, self._common_content_lib)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        self.log_dir = self._common_content_lib.get_log_file_dir()
        
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.install_collateral_obj = InstallCollateral(self._log, self.os, self._cfg_opts)
        self.storage_common = StorageCommon(self._log, self._cfg_opts)

    @classmethod
    def add_arguments(cls, parser):
        super(StorageOSInstallM2SsdSataDevice, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        if not self.os.is_alive():
            self._log.error("System is not alive")
            self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)  # To make the system alive
            self.os.wait_for_os(self._reboot_timeout)

        if self.os.os_type == OperatingSystems.WINDOWS:
            self._log.info("We have windows OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Windows OS required for test case")

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.install_collateral_obj.copy_smartctl_exe_file_to_sut()
        execute_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.SMARTCTL_CMD_TO_SCAN,
                                                                      cmd_str=self.SMARTCTL_CMD_TO_SCAN,
                                                                      execute_timeout=self._command_timeout,
                                                                      cmd_path=self.C_DRIVE_PATH)
        sata_disk_list = re.findall(self.REGEX_FOR_WINDOWS_SATA_DISK, execute_cmd_output)
        if len(sata_disk_list) >= 2:
            self._log.info("we have spare SSD to install the OS ..")
        else:
            raise content_exceptions.TestFail("We need 2 storage devices connected to SUT. One storage device should "
                                              "contain Windows OS and another one is M.2")

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):

        ret_val = list()

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        ret_val.append(self._os_installation_lib.windows_os_installation())

        self._log.info("Windows OS installed successfully ...")

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        self.os.wait_for_os(self._reboot_timeout)

        if not self.os.is_alive():
            self._log.error("System is not alive")
            raise content_exceptions.TestFail("System is not alive")

        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        ret_val.append(self.storage_common.verify_os_boot_device_type("SATA"))

        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageOSInstallM2SsdSataDevice, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageOSInstallM2SsdSataDevice.main() else Framework.TEST_RESULT_FAIL)
