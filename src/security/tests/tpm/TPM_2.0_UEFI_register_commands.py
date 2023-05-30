import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class TPMUEFIRegisterCommand(TxtBaseTest):
    expected_value0 = "0x001B15D1"
    expected_value1 = "0xA1"
    expected_value2 = "0x81"
    uefi_cmd1 = "mm FED40F00 -w 4 -n"
    uefi_cmd2 = "mm FED40000 -n"
    uefi_cmd3 = "mm FED40000 20"
    uefi_cmd4 = "mm FED40000 02"

    BIOS_BOOTMENU_CONFIGPATH = "suts/sut/providers/bios_bootmenu"
    UEFI_CONFIG_PATH = 'suts/sut/providers/uefi_shell'
    DELAY_TIME = 10.0
    ACTIVE_LOCALITY = "active locality"
    ACCESS_BIT = "access bit"
    TEST_CASE_ID = ["18014073387  TPM 2.0 - UEFI register commands"]
    step_data_dict = {1: {'step_details': 'type "mm FED40F00 -w 4 -n"',
                          'expected_results': ' 0x001B15D1'},
                      2: {'step_details': 'type"mm FED40000 -n"',
                          'expected_results': ' 0xA1'},
                      3: {'step_details': 'Type "mm FED40000 20".Type "mm FED40000 -n".',
                          'expected_results': ' 0x81'},
                      4: {'step_details': 'Type "mm FED40000 02".Type "mm FED40000 -n".',
                          'expected_results': '0xA1'}}

    def __init__(self, test_log, arguments, cfg_opts):
        super(TPMUEFIRegisterCommand, self).__init__(test_log, arguments, cfg_opts)

        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.platform_family = self._common_content_lib.get_platform_family()
        self.uefi_cmd_exec_delay = self._common_content_configuration.get_uefi_exec_delay_time()
        self._command_timeout = self._common_content_configuration.get_command_timeout()

    def prepare(self):
        # type: () -> None
        """
        Pre-validating whether sut is boot to uefi shell.

        :return: False if system did not boot to uefi shell.
        """
        super(TPMUEFIRegisterCommand, self).prepare()


    def validate_memory_flag(self, registry_value, tpm_access_val, comment_str):
        """
        Get value from uefi shell and compared with the expected value

        :param registry_value: Expected registry value
        :param tpm_access_val: value which is retrived from uefi shell
        :param comment_str: registry string
        :return: return True if the value matches with expected value.
        """
        tpm_val_flag = False
        for value in tpm_access_val:
            if "MEM" in value:
                tpm_val = str(value.split(":")[-1]).strip()
                if registry_value == tpm_val:
                    self._log.info(
                        "Value of TPM {} Memory information is excepted value '{}'".format(
                            comment_str, tpm_val))
                    tpm_val_flag = True
                else:
                    self._log.error(
                        "Value of TPM {} Memory information is not excepted value '{}'".format(
                            comment_str, tpm_val))
        return tpm_val_flag

    def execute(self):
        self._test_content_logger.start_step_logger(1)  # Step logger start for Step 1
        self._log.info("=====================Entering UEFI shell=======================")
        if not self._uefi_util_obj.enter_uefi_shell():
            raise RuntimeError("SUT did not enter to UEFI Internal Shell")
        time.sleep(self.DELAY_TIME)

        tpm_val_flag = []
        cmd_return_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(uefi_cmd1)
        self._log.info("cmd return value:{}".format(cmd_return_value))
        tpm_val_flag.append(
            self.validate_memory_flag(
                self.expected_value0,
                cmd_return_value,
                self.ACTIVE_LOCALITY))
        self._test_content_logger.end_step_logger(1, return_val=True)  # Step logger end for Step 1

        self._test_content_logger.start_step_logger(2)
        cmd_return_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(uefi_cmd2)
        self._log.info("cmd return value:{}".format(cmd_return_value))
        tpm_val_flag.append(
            self.validate_memory_flag(
                self.expected_value1,
                cmd_return_value,
                self.ACTIVE_LOCALITY))
        self._test_content_logger.end_step_logger(2, return_val=True)  # Step logger end for Step 2
        self._test_content_logger.start_step_logger(3)
        cmd_return_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(uefi_cmd3)
        self._log.info("cmd return value:{}".format(cmd_return_value))
        cmd_return_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(uefi_cmd2)
        self._log.info("cmd return value:{}".format(cmd_return_value))
        tpm_val_flag.append(
            self.validate_memory_flag(
                self.expected_value2,
                cmd_return_value,
                self.ACTIVE_LOCALITY))
        self._test_content_logger.end_step_logger(3, return_val=True)  # Step logger end for Step 3

        self._test_content_logger.start_step_logger(4)
        #cmd = "mm FED40000 02"
        cmd_return_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(uefi_cmd4)
        self._log.info("cmd return value:{}".format(cmd_return_value))
        #cmd = "mm FED40000 -n"
        cmd_return_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(uefi_cmd2)
        self._log.info("cmd return value:{}".format(cmd_return_value))
        tpm_val_flag.append(
            self.validate_memory_flag(
                self.expected_value1,
                cmd_return_value,
                self.ACTIVE_LOCALITY))
        self._test_content_logger.end_step_logger(4, return_val=True)  # Step logger end for Step 4
        return all(tpm_val_flag)


def cleanup(self, return_status):
    super(TPMUEFIRegisterCommand, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TPMUEFIRegisterCommand.main() else Framework.TEST_RESULT_FAIL)
