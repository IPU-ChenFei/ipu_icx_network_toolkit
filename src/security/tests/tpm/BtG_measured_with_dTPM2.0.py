import os
import re
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.ac_power import AcPowerControlProvider
from src.lib import content_exceptions
from src.lib.bios_util import ItpXmlCli, BootOptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.cbnt_boot_guard.cbnt_boot_guard_constants import CBnTConstants
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_profile5 import BootGuardProfile5


class BtGMeasuredWithDTPM2(TxtBaseTest):
    WAIT_TIME = 60.0
    PCR_TOOL_DIR = ''
    enter_fs1 = 'fs1:'
    cmd = 'ShellDmpLog2.efi > sha256_pcr_values.txt'
    # cmd = 'ShellDmpLog2.efi'
    read_cmd = 'cat sha256_pcr_values.txt'
    TEST_CASE_ID = ['18014070619', 'BtG measured with dTPM 2.0']
    EVA_STRING = "EVA "
    STEP_DATA_DICT = {
        1: {'step_details': ' enable Boot Guard Profile 5 on the SUT.', 'expected_results': ''},
        2: {'step_details': 'Reboot the system to the UEFI shell', 'expected_results': ''},
        3: {'step_details': 'Ensure that SUT booted measured+verified by executing the last step of '
                            'https://hsdes.intel.com/appstore/article/#/18014070216',
            'expected_results': 'Results should match the expected results of '
                                'https://hsdes.intel.com/appstore/article/#/18014070216'},
        4: {'step_details': 'Using the ShellDmpLog2.efi utility, read the platform PCR data and save the results.',
            'expected_results': 'The file generates with non-zero PCR values.'},
        5: {'step_details': 'Check SHA256 EventLog and TPM SHA256 PCR', 'expected_results': 'true'}}

    def __init__(self, test_log, arguments, cfg_opts):
        super(BtGMeasuredWithDTPM2, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.mount_point = self._copy_usb.get_mount_point(self._common_content_lib, self._common_content_configuration)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_config = ContentConfiguration(self._log)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(
            si_dbg_cfg, test_log)
        self._cbnt_const = CBnTConstants()
        self._profile5_enable = BootGuardProfile5(test_log, arguments, cfg_opts)
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

    # def prepare(self):
    #     """
    #      enable Boot Guard Profile 5 on the SUT.
    #     """
    #     self._test_content_logger.start_step_logger(1)
    #     self._profile5_enable.prepare()
    #     self._profile5_enable.execute()
    #     self._test_content_logger.end_step_logger(1, return_val=True)

    def compare_pcr_eva_values(self, pcr_values_list, eva_values_list):
        pcr_values_list.sort()
        eva_values_list.sort()
        count = 0
        if len(eva_values_list) == len(pcr_values_list):
            for i in range(0, len(eva_values_list)):
                if eva_values_list[i] == pcr_values_list[i]:
                    count += 1
                else:
                    return False
            if count == len(eva_values_list):
                return True
            else:
                pass
        else:
            return False

    def execute(self):
        """
        Execute test case steps
        :return: True if Test case pass
        """
        self._test_content_logger.start_step_logger(2)
        # self._sdp.itp.unlock()
        # self._itp_xmlcli = ItpXmlCli(self._log, self._cfg)
        # self._itp_xmlcli.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)

        self._uefi_util_obj.enter_uefi_shell()

        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        time.sleep(1)
        # output_boot = self.get_pcrdump_from_uefi(self.cmd, self.PCR_TOOL_DIR)
        # print(output_boot)
        self._uefi_obj.execute(self.enter_fs1)
        self._uefi_obj.execute(self.cmd)
        read_return_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.read_cmd)
        # read_return_value = self.get_pcrdump_from_uefi(self.read_cmd, self.PCR_TOOL_DIR)
        print(type(read_return_value))
        print(read_return_value)
        self._log.info(read_return_value)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        listToStr = ''.join([str(elem.replace("\r", "")) for elem in read_return_value])
        eva_list = []
        pcr_list = []
        for i in range(8):
            eva = re.findall(f'(?<=EVA_VALUE\[0{i}])(.*?)(?=PCR_VALUE\[0{i}])', listToStr, re.DOTALL)
            eva_list.append(eva[0])
        eva_list = [x.strip('\n') for x in eva_list if x.strip() != '']
        print('eva:', eva_list)

        for i in range(8):
            if i == 7:
                break
            pcr = re.findall(f'(?<=PCR_VALUE\[0{i}])(.*?)(?=EVA_VALUE\[0{i + 1}])', listToStr, re.DOTALL)
            pcr_list.append(pcr[0])
        pcr_07 = re.findall(r'(?<=PCR_VALUE\[07])(.*?)(?=Tpm12*)', listToStr, re.DOTALL)
        pcr_list.append(pcr_07[0].replace('(', ''))
        pcr_list = [x.strip('\n') for x in pcr_list if x.strip() != '']
        print('pcr:', pcr_list)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        if not self.compare_pcr_eva_values(pcr_list, eva_list):
            raise content_exceptions.TestFail('EVA values is not different with PCR values')
        self._test_content_logger.end_step_logger(5, return_val=True)
        return True

    def cleanup(self, return_status):
        """
        Reverting to previous boot order if current boot order is not same as previous boot order
        """
        super(BtGMeasuredWithDTPM2, self).cleanup(return_status)


if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if BtGMeasuredWithDTPM2.main() else Framework.TEST_RESULT_FAIL)
