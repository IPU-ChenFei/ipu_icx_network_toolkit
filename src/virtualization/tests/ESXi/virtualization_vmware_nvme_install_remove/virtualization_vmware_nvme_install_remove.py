from src.virtualization.lib.virtualization import *
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
import time
import sys


class VirtualizationVmdNvmeDriverInstall(VirtualizationCommon):
    """
       Phoenix ID: 18014074804
       Purpose of this test case is to Verify VMD driver installation based on a bootable ESXi system.
        1. Enable the BIOS setup and enable VMD
        2. copy VMD driver into /var/tmp folder and get the vib driver.
        3. Set the system into maintanence mode
        4. Install the vib driver
        5. Reboot the system
        6. Check the driver installed and verify the driver version
        7.If driver already installed, Then remove and verify if successfull
    """

    DEFAULT_DIRECTORY_ESXI = "/vmfs/volumes/datastore1"
    TEST_CASE_ID = ["P18014074804", "VirtualizationVmdNvmeDriverInstall"]
    BIOS_CONFIG_FILE = "virtualization_nvme_vmd_driver_install_knobs.cfg"
    STEP_DATA_DICT = {
        1: {'step_details': "Enable the BIOS setup and enable VMD",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "Copy VMD driver into /var/tmp folder and get the vib driver.",
            'expected_results': "Should be successful"},
        3: {'step_details': "Set the system into maintanence mode",
            'expected_results': "Setting to maintanence mode should be successfull"},
        4: {'step_details': "Install the vib driver",
            'expected_results': "Vib driver installation should be successfull"},
        5: {'step_details': "Reboot the system",
            'expected_results': "Reboot host should be successfull"},
        6: {'step_details': "Check the driver installed and verify the driver version",
            'expected_results': "Driver installation  and verification should be successfull"},
        7: {'step_details': "If driver already installed, Then uninstall the driver and verify",
            'expected_results': "Driver removal should be successfull"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmdNvmeDriverInstall object.
        """
        super(VirtualizationVmdNvmeDriverInstall, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # Need to implement bios configuration for ESXi SUT
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type != OperatingSystems.ESXI:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._log.info("VMWare ESXi SUT detected for the testcase")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Enable the BIOS setup and enable VMD
        2. copy VMD driver into /var/tmp folder and get the vib driver.
        3. Set the system into maintanence mode
        4. Install the vib driver
        5. Reboot the system
        6. Check the driver installed and verify the driver version
        7. If driver already installed, Then uninstall the driver and verify
        """
        self._test_content_logger.start_step_logger(2)
        self._log.info("Unzip the NVMe driver installation package to a new folder")

        (vib_file, nvme_file_path) = self._install_collateral.get_nvme()
        self._log.info("Check whether the installation file was uploaded successfully")
        path_full = nvme_file_path + "/" + vib_file
        cmd_copy = "chmod 777 {}"
        self._common_content_lib.execute_sut_cmd(cmd_copy.format(vib_file), "software vib1",
                                                 self._command_timeout,
                                                 nvme_file_path)

        self.os.execute('cp -r {} /var/tmp'.format(path_full), self._command_timeout)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self._log.info("Set system as maintenance mode")
        check_maintanence = " vim-cmd /hostsvc/hostsummary | grep inMaintenanceMode | cut -f2 -d'='"
        output = self._common_content_lib.execute_sut_cmd(check_maintanence, "Check Maintanence mode",
                                                          self._command_timeout,
                                                          self.DEFAULT_DIRECTORY_ESXI)

        if 'false' in output:
            cmd_maintanence_mode = "esxcli system maintenanceMode set --enable true"
            self._common_content_lib.execute_sut_cmd(cmd_maintanence_mode, "Enable Maintanence mode",
                                                     self._command_timeout,
                                                     self.DEFAULT_DIRECTORY_ESXI)
        else:
            self._log.info("Already in Maintanence mode")

        self._test_content_logger.end_step_logger(3, return_val=True)

        cmd4 = "esxcfg-scsidevs -a"
        output = self._common_content_lib.execute_sut_cmd(cmd4, "list software vibdev", self._command_timeout,
                                                          self.DEFAULT_DIRECTORY_ESXI)
        if 'iavmd' not in output:
            self._test_content_logger.start_step_logger(4)
            self._install_collateral.vib_install_software(vib_file, path_full)
            self._test_content_logger.end_step_logger(6, return_val=True)
            self._install_collateral.vib_remove_software()
        else:
            self._test_content_logger.start_step_logger(7)
            self._log.info("Intel NVME VMD has already been installed verified successfully")
            self._install_collateral.vib_remove_software()
            self._test_content_logger.end_step_logger(7, return_val=True)
            self._install_collateral.vib_install_software(vib_file)

        self._log.info("Setting back system to Normal mode from Maintanence mode")
        cmd_maintanence_mode_disable = "esxcli system maintenanceMode set --enable false"
        self._common_content_lib.execute_sut_cmd(cmd_maintanence_mode_disable, "Disable Maintanence mode",
                                                 self._command_timeout,
                                                 self.DEFAULT_DIRECTORY_ESXI)
        self._log.info("Disabled from Maintanence mode")

    def cleanup(self, return_status):
        super(VirtualizationVmdNvmeDriverInstall, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmdNvmeDriverInstall.main()
             else Framework.TEST_RESULT_FAIL)
