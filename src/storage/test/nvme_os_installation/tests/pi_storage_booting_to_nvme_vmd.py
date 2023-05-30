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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider


from src.environment.os_installation import OsInstallation
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.provider.storage_provider import StorageProvider
from src.storage.test.storage_common import StorageCommon
from src.lib.bios_util import ItpXmlCli
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import BootOptions
from src.lib.install_collateral import InstallCollateral
from src.lib.uefi_util import UefiUtil
from src.lib.test_content_logger import TestContentLogger
from src.storage.test.pi_pcie_ssd_rste_vmd_driver_installation_check_l import PiRSTeVMDDriverInstallationCheckL


class StorageBootingToNvmeLinux(BaseTestCase):
    """
    HPQC : H80240-PI_Storage_BootingToNVMe_VMD_L.

    1.Enable Vmd Bios Knobs and Verify
    2.Changes the Boot order to UEFI shell and Executes command
    3.Install RHEL OS on the platform
    """

    TEST_CASE_ID = ["H80240", "PI_Storage_BootingToNVMe_VMD_L"]
    WAIT_TIME_OUT = 5
    PCI_CMD = "PCI"
    MASS_NON_VOLATILE_STR = "Mass Storage Controller - Non-volatile memory subsystem"

    step_data_dict = {1: {'step_details': 'Enable VMD BIOS knobs',
                          'expected_results': 'BIOS Setting Config VMD enabled in BIOS'},
                      2: {'step_details': 'Changes the boot order to UEFI shell and executes command',
                          'expected_results': 'Navigates to UEFI shell navigates, executes like PCI'},
                      3: {'step_details': 'Install RHEL OS on the platform',
                          'expected_results': 'RHEL OS installed in NVME device'},
                      4: {'step_details': 'Check if the RSTe VMD driver is preinstalled along with Linux OS',
                          'expected_results': 'RSTe driver should be present'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToNvmeLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        self._cc_log_path = arguments.outputpath
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        super(StorageBootingToNvmeLinux, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self.install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self.itp_xml_cli_util = None
        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider
        self._common_content_configuration = ContentConfiguration(self._log)
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self.ac_power,
            self._common_content_configuration, self._os)
        self.previous_boot_oder = None
        self.current_boot_order = None
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = None
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self.reboot_timeout = \
            self._common_content_configuration.get_reboot_timeout()
        self._storage_provider = None
        self.log_dir = None
        self.storage_common_obj = StorageCommon(self._log, arguments, cfg_opts)
        self._get_ledmon_mdadm_obj = PiRSTeVMDDriverInstallationCheckL(self._log, arguments, cfg_opts)
        self._content_base_test = ContentBaseTestCase(self._log, arguments, cfg_opts)

    @classmethod
    def add_arguments(cls, parser):
        super(StorageBootingToNvmeLinux, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def execute(self):

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.storage_common_obj.enable_vmd_bios_knobs()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg_opts)
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_oder))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for uefi shell..")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        time.sleep(self.WAIT_TIME_OUT)
        cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.PCI_CMD)
        self._log.info(cmd_output)
        non_volatile_list = []
        for each in cmd_output:
            if self.MASS_NON_VOLATILE_STR in each:
                non_volatile_list.append(each[:-1])
        self._log.debug("All pci ports info:{}".format(cmd_output))
        self._log.info("Identfies the pci bus and Mass Storage Controller-Non-volatile memory "
                       "subsystem info:{}".format(non_volatile_list))

        if not cmd_output:
            raise content_exceptions.TestFail("unable to execute pci command in uefi shell")

        self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for os to be alive")
        self._os.wait_for_os(self.reboot_timeout)
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Closing the Serial Port")
        self._content_base_test.cng_log.serial.close()
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        ret_val = []
        ret_val.append(self._os_installation_lib.rhel_os_installation())
        self._log.info("Closing the Serial Port")
        self._content_base_test.cng_log.serial.close()

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        self._get_ledmon_mdadm_obj.execute()

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._storage_provider = StorageProvider.factory(self._log, self._os, self._cfg_opts, "os")
        self._common_content_lib = CommonContentLib(self._log, self._os, None)

        self.log_dir = self._common_content_lib.get_log_file_dir()
        lsblk_res = self._storage_provider.get_booted_device()
        self._log.info("booted device is {}".format(str(lsblk_res)))

        if "NVME" not in lsblk_res.upper():
            raise content_exceptions.TestFail("OS not installed on the NVME SSD, please try again..")

        self._log.info("Successfully verified that OS installed in NVME device..")

        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageBootingToNvmeLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToNvmeLinux.main() else Framework.TEST_RESULT_FAIL)
