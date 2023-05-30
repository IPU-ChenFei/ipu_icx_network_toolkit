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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.install_collateral import InstallCollateral

from src.lib.common_content_lib import CommonContentLib
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.lib.content_configuration import ContentConfiguration
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon


class CRdiagnosticsCliUefi(CrProvisioningTestCommon):
    """
    Glasgow ID : 55812
    Run a diagnostic test on one or more DCPMM in a UEFI pre boot environment.

    1. Test case involves executing the default suite of all tests and also running each specific test by supplying
     its name.
    2. "Quick" - This test verifies that the DCPMM host mailbox is accessible and that basic health indicators can
     be read and are currently reporting acceptable values.
    3. "Config" - This test verifies that the BIOS platform configuration matches the installed hardware
    and the platform configuration conforms to best known practices
    4. "Security" - This test verifies that all DCPMMs have a consistent security state. It's a best practice
      to enable security on all DCPMMs rather than just some.

    """

    BIOS_CONFIG_FILE = "cr_diagnostics_cli_uefi.cfg"
    TC_ID = "G55812"
    IPMCTL_TXT_FILE = "ipmctl_efi.zip"
    DELAY_TIME = 10.0
    NFIT_VAL = [' ControlRegion', ' Interleave', ' NvDimmRegion', ' SpaRange', ' PlatformCapabilities']
    PCAT_VAL = [' PlatformCapabilityInfoTable', ' MemoryInterleaveCapabilityTable']
    PMTT_VAL = [' PMTT', 'iMC', 'MODULE']

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new diagnostic test on one or more DCPMMs.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        super(CRdiagnosticsCliUefi, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._copy_usb = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self._os)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        _opt_obj, _test_log_obj = cfg_opts, test_log
        self.usb_file_path = None
        self.sut_os = self._os.os_type

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """
        #  To copy ipmctl.efi file from host to usb
        if (OperatingSystems.WINDOWS or OperatingSystems.LINUX) == self.sut_os:
            zip_file_path = self._install_collateral.download_and_copy_zip_to_sut(self.IPMCTL_TXT_FILE.split(".")[0],
                                                                          self.IPMCTL_TXT_FILE)
            self.usb_file_path = self._copy_usb.copy_file_from_sut_to_usb(
                self._common_content_lib, self._common_content_configuration, zip_file_path)
        else:
            self._log.error("Ipmctl efi is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Ipmctl efi is not supported on OS '%s'" % self._os.sut_os)

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. DCPMM Mgmt SW version and PCD data are displayed.
        2. Show the Boot Status Register (BSR) for all DCPMMs to confirm the "BootStatus=Success".
        3. System memory topology & firmware is displayed and correct.
        5. All DCPMMs show a consistent security state.
        6. The DCPMM host mailbox is accessible, basic health indicators can be read and are currently
         reporting acceptable values..
        7. All thermal or media errors on DCPMMs are displayed.

        :return: True, if the test case is successful.
        :raise: None
        """

        #  To enter uefi shell
        self.create_uefi_obj(self._opt_obj, self._test_log_obj)
        if not self._uefi_util_obj.enter_uefi_shell():
            raise RuntimeError("SUT did not enter to UEFI Internal Shell")
        time.sleep(self.DELAY_TIME)

        #  Get usb list drive from  uefi shell
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive_list[0])

        #  To Run ipmctl version in uefi shell
        ipmctl_version = self.ipmctl_version_uefi()
        ipmctl_version = '\n'.join(map(str, ipmctl_version))
        self._log.info("Ipmctl version displaying...{}".format(ipmctl_version))

        #  To Run PCD config data in uefi shell
        pcd_config = self.ipmctl_pcd_config_uefi()

        #  To verify PCD config data
        self.verify_pcd_data(pcd_config)

        #  To generate PCAT txt file file and attach the text file
        pcd_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi show -dimm -pcd Config > 55812_pcd.txt")
        if not pcd_value:
            self._log.error("Command failed to generate pcd config text file")
            raise RuntimeError("Command failed to generate pcd config text file")

        #  To run boot status dimm command
        boot_reg_val = self.get_boot_status_register_uefi()

        #  To verify boot status register value
        if not ("BootStatus=Success") in boot_reg_val:
            self._log.error("Boot status is failed")
            raise RuntimeError("Boot status is failed ")
        else:
            self._log.info("Boot status is succeeded...")

        #  To run provisioning dimm command
        dimm_val = self.get_dimm_info_uefi()

        #  To verify health status of DIMM
        if "Healthy" and "Disabled" not in dimm_val:
            self._log.error("HealthyState is not Healthy and lockstate is not Disabled")
            raise RuntimeError("Dimms are not Healthy and lockstate is not Disabled ")
        else:
            self._log.info("Dimms are Healthy and LockState is Disabled...")

        # To Run system capability command in uefi shell
        system_capability = self.ipmctl_system_capability_uefi()

        #  To verify the system capability values
        if "Unknown" in system_capability:
            self._log.error("DCPMM attributes are not having correct values")
            raise RuntimeError("DCPMM attributes are not having correct values")
        else:
            self._log.info("DCPMM attributes having correct values...")

        # To Run topology command in uefi Shell
        topology_val = self.ipmctl_show_topology_uefi()

        #  To dispaly the topology values
        topology_val = '\n'.join(map(str, topology_val))
        self._log.info("DCPMM topology values{}".format(topology_val))

        # To Run firmware command in uefi Shell
        firmware_val = self.ipmctl_show_firmware_uefi()

        #  To dispaly the firmare values
        firmware_val = '\n'.join(map(str, firmware_val))
        self._log.info("DCPMM topology values{}".format(firmware_val))

        # To Run diagnostic security command in uefi Shell
        list_security_val = self.ipmctl_diagnostic_security_uefi()
        list_security_val = self.get_diagnostic_security_val(list_security_val)

        #  To Execute the security check diagnostic on installed DCPMMs
        if ("State=Disabled") in list_security_val:
            self.ipmctl_diagnostic_help_uefi()

        # To Execute the quick check diagnostic on a single DCPMM uefi Shell
        dimm_list = self.get_dimm_id_uefi()
        diagnostic_check_val = self.ipmctl_diagnostic_check_uefi(dimm_list)
        diagnostic_check_val = '\n'.join(map(str, diagnostic_check_val))
        self._log.info("The DCPMM host mailbox is reporting acceptable values...{}".format(diagnostic_check_val))

        #  To verify the diagnostic security  information
        if not ("State=Ok") and ("The quick health check succeeded") in diagnostic_check_val:
            self._log.error("A security state is required to execute diagnostics")
            raise RuntimeError("A security state is required to execute diagnostics")
        else:
            self._log.info("The security check diagnostic test is successfully completed...")

        # To Execute the quick check diagnostic on a single DCPMM uefi Shell
        qucik_check_val = self.ipmctl_diagnostic_quick_check_uefi()
        list_quick_val = self.get_diagnostic_quick_val(qucik_check_val)
        self._log.info("The quick diagnostic values...{}".format(list_quick_val))

        #  To Execute the Config check diagnostic on all DCPMMs uefi Shell
        qucik_config_val = self.ipmctl_diagnostic_config_check_uefi()
        list_config_val = self.get_config_val(qucik_config_val)

        #  To Execute  diagnostic on all DCPMMs via uefi Shell
        diagnostic_value = self.ipmctl_diagnostic_uefi()
        diagnostic_value_str = "\n".join(map(str, diagnostic_value))

        #  To verify diagnostic results are consistent with those from the previous tests executed
        if all(
            data in diagnostic_value_str for data in list_quick_val) and all(
            data in diagnostic_value_str for data in list_config_val) and all(
                data in diagnostic_value_str for data in list_security_val):
            self._log.info("Diagnostic results are consistent with those from the previous tests executed")
        else:
            self._log.error("Diagnostic results are not consistent with those from the previous tests executed")
            raise RuntimeError("Diagnostic results are not consistent with those from the previous tests executed")

        #  To run system NFIT command in uefi shell
        nfit_value = self.ipmctl_system_nfit_uefi()

        #  To verify NFIT value from NFIT.TXT file in uefi shell
        nfit_value_list = self.get_system_val(nfit_value)
        if self.NFIT_VAL == nfit_value_list:
            self._log.info("Diagnostic results of NFIT are consistent with those from the previous tests executed")
        else:
            self._log.error("Diagnostic results of NFIT are not consistent with those from the previous tests executed")
            raise RuntimeError("Diagnostic results of NFIT are not consistent with those from the previous tests "
                               "executed")

        #  To run system PCAT command in uefi shell
        pcat_value = self.ipmctl_system_pcat_uefi()

        #  To verify PCAT value from PCAT.TXT file in uefi shell
        pcat_value_list = self.get_system_val(pcat_value)
        if self.PCAT_VAL == pcat_value_list:
            self._log.info("Diagnostic results of PCAT are consistent with those from the previous tests executed")
        else:
            self._log.error("Diagnostic results of PCAT are not consistent with those from the previous tests executed")
            raise RuntimeError("Diagnostic results of PCAT are not consistent with those from the previous tests "
                               "executed")

        #  To run system PMTT command in uefi shell
        pmtt_value = self.ipmctl_system_pmtt_uefi()

        #  To verify PMTT value from PMTT.TXT file in uefi shell
        pmmt_value_list = self.get_system_acpi_val(pmtt_value)
        if self.PMTT_VAL == pmmt_value_list:
            self._log.info("Diagnostic results of PMTT are consistent with those from the previous tests executed")
        else:
            self._log.error("Diagnostic results of PMTT are not consistent with those from the previous tests executed")
            raise RuntimeError("Diagnostic results of PMTT are not consistent with those from the previous tests "
                               "executed")

        #  To generate PMTT txt file file and attach the text file
        pmtt_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi  show -system PMTT > 55812_PMTT.txt")
        if not pmtt_val:
            self._log.error("Command failed to generate PMTT text file")
            raise RuntimeError("Command failed to generate PMTT text file")

        #  To generate NFIT txt file file and attach the text file
        nfit_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi  show -system NFIT > 55812_NFIT.txt")
        if not nfit_val:
            self._log.error("Command failed to generate NFIT text file")
            raise RuntimeError("Command failed to generate NFIT text file")

        #  To generate PCAT txt file file and attach the text file
        pcat_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi  show -system PCAT > 55812_PCAT.txt")
        if not pcat_val:
            self._log.error("Command failed to generate PCAT text file")
            raise RuntimeError("Command failed to generate PCAT text file")

        #  To verify serial no entries from NFIT text file
        self.verify_serial_no_nfit(dimm_list, nfit_value)

        #  To verify PCAT expected capabilities from PCAT.TXT file
        self.verify_memory_capability_pcat(pcat_value)

        #  To Display the DCPMM Thermal  error log and check for unexpected
        thermal_val = self.ipmctl_thermal_error_uefi()

        #  To verify thermal thermal error in UEFI
        self.verify_thermal_media_error(thermal_val)

        #  To Display the DCPMM  Media error log and check for unexpected
        media_val = self.ipmctl_media_error_uefi()

        #  To verify thermal media error in UEFI
        self.verify_thermal_media_error(media_val)

        #  To reboot the system
        self._uefi_obj.warm_reset()
        time.sleep(self._reboot_timeout)
        self._log.info("Waiting for system to reboot...")

        if not self._os.is_alive():
            log_error = "SUT did not come to OS within {} seconds after a reboot from UEFI shell...".format(
                self._reboot_timeout)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("SUT came to OS after a reboot from UEFI shell")
        sut_file_path = self._copy_usb.copy_file_from_usb_to_sut(self._common_content_lib,
                                                                 self._common_content_configuration,
                                                                 self.usb_file_path)
        self._common_content_lib.copy_log_files_to_host(self.TC_ID, str(sut_file_path), ".txt")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRdiagnosticsCliUefi.main() else Framework.TEST_RESULT_FAIL)
