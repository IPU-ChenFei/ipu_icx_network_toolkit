import os
import re
from typing import Union, List, Pattern
import xml.etree.ElementTree as ET
from argparse import Namespace
from pathlib import Path

from pysvtools.fish_platform.platforms.EagleStream import _unlock_injectors as unlock_injectors
from pysvtools.fish_platform.platforms.EagleStream import memory

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.exceptions import OsCommandTimeoutException

from src.provider.sgx_provider import LinuxSGXDriver, SGXProvider
from src.lib import content_base_test_case, content_exceptions
from src.security.tests.sgx.sgx_constant import SGXConstant


sgx_phys_addr_re = re.compile("sgx: EPC section (0x[0-9a-fA-F]*)-0x[0-9a-fA-F]*")

correctable_err_log_checks: List[str]= ["[Mca]CheckMcBankErrorStatus returns TRUE", "[Mca]McaDetectAndHandle start",
                                        "[Mca]McaDetectAndHandle, state is 0x0", "[Mca]McaDetectAndHandle, state is 0x1",
                                        "[Mca]McaDetectAndHandle, severity = 0x2, Broadcast is 0x1", "[Mca]ProcessSocketMcBankError: Inside the function"]
correctable_err_log_re: Pattern = re.compile(r"\[Mca\]Sending CMCI for CPU 0x[0-9A-Fa-f] Bank 0x[0-9A-Fa-f], ((Package)|(Socket)) 0x[0-9A-Fa-f] Core 0x[0-9A-Fa-f]")

class SgxErrorInjectionBaseTest(content_base_test_case.ContentBaseTestCase):
    BIOS_CONFIG_FILE: str = [os.path.join(Path(__file__).parent.resolve(), "2gb_prmrr.cfg")]

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree, add_bios_cfg: Union[str, List[str]] = None):
        bios_cfg: List[str] = self.BIOS_CONFIG_FILE
        if add_bios_cfg:
            if type(add_bios_cfg) is list:
                bios_cfg.extend(add_bios_cfg)
            else:
                bios_cfg.append(add_bios_cfg)

        bios_cfg: str = SGXConstant(test_log).sgx_bios_knobs(bios_cfg)

        super(SgxErrorInjectionBaseTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path=bios_cfg)

        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("This test is not applicable for " + self.os.os_type)

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp: SiliconRegProvider = ProviderFactory.create(sil_cfg, test_log)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp: SiliconDebugProvider = ProviderFactory.create(si_dbg_cfg, test_log)
        self.sgx: LinuxSGXDriver = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)

        self.correctable_error = memory.ddr5_cecc_injection
        self.correctable_error_verify = memory.ddr5_cecc_injection_verify
        self.uncorrectable_error = memory.ddr5_uc_injection
        self.uncorrectable_error_verify = memory.ddr5_uc_injection_verify

    def prepare(self) -> None:
        """
        ContentBaseTestCase prepare overload
        checks that ITP is connected and SGX is enabled.
        Installs make, gcc, gcc-c++, PSW, and SGX SDK to compile semtv0.3a
        Gets SGX base physical address
        Compiles semtv0.3a test application
        :raises content_exceptions.TestSetupError: If anything is missing or fails
        """
        super(SgxErrorInjectionBaseTest, self).prepare()

        self._log.info("Checking for ITP")
        if not self._common_content_lib.is_itp_connected(self.sdp):
            raise content_exceptions.TestSetupError("ITP is not connected")

        pkgs: List[str] = ["make", "gcc", "gcc-c++"]
        self._log.info("Installing {}".format(pkgs))
        for p in pkgs:
            self.sgx._install_collateral.yum_install(p)

        self._log.info("Checking SGX is enabled")
        self.sgx.check_sgx_enable()

        self._log.info("Looking for SGX base physical address")
        self.sgx_phys_addr: Union[int, None] = self.get_sgx_base_phys_addr()
        if self.sgx_phys_addr is None:
            raise content_exceptions.TestSetupError("Failed to extract SGX Physical Address from dmesg")
        else:
            self._log.debug("Using {} as SGX base physical address".format(self.sgx_phys_addr))

        self._log.info("Checking PSW Installation")
        try:
            self.sgx.check_psw_installation()
        except content_exceptions.TestFail as e:
            raise content_exceptions.TestSetupError("Failed to setup/Install PSW: {}".format(e))

        self._log.info("Installing SDK")
        try:
            self.sgx.install_sdk()
        except content_exceptions.TestFail as e:
            raise content_exceptions.TestSetupError("Failed to install SDK: {}".format(e))

        self._log.info("Compiling test code")
        if not self.compile_semt_v0_3a():
            raise content_exceptions.TestSetupError("Failed to compile test code")

    def unlock_injectors(self) -> None:
        """Unlock memory error injectors"""
        self._log.info("Unlocking memory injectors")
        unlock_injectors()

    def run_semt(self, s: str="0", v: str="4096", timeout: Union[float, None]=60) -> str:
        """
        Runs the semtv0.3a test application asynchronously
        :param s: passed to -S
        :param v: page allocation size
        :param timeout: Optional, used to limit run time
        :raises content_exceptions.TestFail: If the command fails for any reason apart from timeout
        :returns Path: Path to the semt executable
        """

        semt_out_file: str = "semt_output.txt"
        if timeout is not None:
            semt_cmd: str = "timeout {} ./semt -S{} {} >& {}".format(timeout, s, v, semt_out_file)
        else:
            semt_cmd: str = "./semt -S{} {} >& {}".format(s, v, semt_out_file)

        self._log.info("Running " + semt_cmd)

        try:
            self.os.execute_async(semt_cmd, cwd=self.SEMT_PATH)
        except OsCommandTimeoutException as e:
            # Timeout doesn't really matter here since it just needs to run
            pass
        except Exception as e:
            raise content_exceptions.TestFail("Failed to run {} due to error: {}".format(semt_cmd, e))

        if self.os.execute("pgrep semt", self._command_timeout).cmd_failed():
            raise content_exceptions.TestFail("semt failed to start")

        return Path(os.path.join(self.SEMT_PATH, semt_out_file)).as_posix()

    def compile_semt_v0_3a(self) -> bool:
        """Copies semtv0.3a files to the SUT and then compiles the semtv0.3a test application"""
        self._log.info("Compiling semt")
        self.SEMT_PATH = self.sgx._install_collateral.copy_semt_files_to_sut()

        enclave_pkg_path = Path(os.path.join(self.SEMT_PATH, self.sgx.ENCLAVE_PATH)).as_posix()
        self._common_content_lib.execute_sut_cmd(self.sgx.ENCLAVE_CONFIG_FILE_CHANGE,
                                                 self.sgx.ENCLAVE_CONFIG_FILE_CHANGE,
                                                 self.sgx.EXECUTION_TIMEOUT, enclave_pkg_path)

        self._common_content_lib.execute_sut_cmd(self.sgx.MAKE_CLEAN_CMD,self.sgx.MAKE_CLEAN_CMD,
                                                 self.sgx.EXECUTION_TIMEOUT,self.SEMT_PATH)

        self._log.debug("Make output: {}".format(self.sgx.run_make_command(self.SEMT_PATH)))

        return True


    def get_sgx_base_phys_addr(self) -> Union[int, None]:
        """Fetches SGX base physical address from dmesg log
        :return: None if it cannot be found."""
        cmd: str = "dmesg | grep sgx"

        dmesg_output = self.os.execute(cmd, self._command_timeout)
        if dmesg_output.cmd_failed():
            self._log.error("{} failed with error code {}".format(cmd, dmesg_output.return_code))
            return None

        addr_matches: Union[List, None] = sgx_phys_addr_re.findall(dmesg_output.stdout)
        if addr_matches is None:
            self._log.error("Regex found no matches in {}".format(dmesg_output.stdout))
            return None

        # There can be multiple base addresses but we only need the lowest one
        addrs: List[int] = [int(a, 16) for a in addr_matches]

        return min(addrs)

    def correctable_error_check(self) -> bool:
        """Checks serial logs for the strings indicating a correctable error occurred"""
        self._log.info("Checking serial log")
        with open(self.serial_log_path, "r") as serial_log:
            serial_data = serial_log.read()
            if not all([serial_data.find(check) for check in correctable_err_log_checks]) or correctable_err_log_re.search(serial_data) is None:
                return False
        return True

    def uncorrectable_error_check(self) -> bool:
        self._log.info("Checking serial log for uncorrectable error")
        with open(self.serial_log_path, "r") as serial_log:
            serial_data = serial_log.read()
            if serial_data.find("--Logging Uncorrected Error") < 0:
                return False
        return True

    def cleanup(self, return_status) -> None:
        super(SgxErrorInjectionBaseTest, self).cleanup(return_status)
