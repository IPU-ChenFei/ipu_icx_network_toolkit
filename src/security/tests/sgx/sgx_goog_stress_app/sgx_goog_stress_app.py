from argparse import Namespace
from typing import Union, List
import xml.etree.ElementTree as ET
import sys
import time

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.sgx_provider import LinuxSGXDriver, SGXProvider
from src.provider.goog_stressapp_test_provider import GoogStressAppTestProvider, LinuxGoogStressAppTestProvider
from src.lib.dtaf_content_constants import TimeConstants

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.os_lib import OsCommandResult


class SgxGoogStressApp(ContentBaseTestCase):
    """
    Test ID: 18014072732
    Google StressAppTest (SAT)
    Test Pre-requisites: SGX-enabled CPU
    """

    TEST_CASE_ID: List[str] = ["18014072732", "Google StressAppTest (SAT)"]
    BIOS_CONFIG_FILE: str = "../sgx_enable_through_bios.cfg"

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        super(SgxGoogStressApp, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("This test is not applicable for " + self.os.os_type)

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp: SiliconRegProvider = ProviderFactory.create(sil_cfg, test_log)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp: SiliconDebugProvider = ProviderFactory.create(si_dbg_cfg, test_log)
        self.sgx: LinuxSGXDriver = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self.sat: LinuxGoogStressAppTestProvider = GoogStressAppTestProvider.factory(test_log, cfg_opts, self.os)

    def prepare(self) -> None:
        """
        Checks that SGX enabled
        Installs Google Stress App test on SUT
        Sets up Google Stress App test with test parameters
        Installs semt on SUT
        """
        super(SgxGoogStressApp, self).prepare()

        self._log.info("Checking that SGX is enabled")
        self.sgx.check_sgx_enable()

        self._log.info("Installing Google Stress App")
        self.sat.install_app()

        self.sat.run_time = 10 * TimeConstants.ONE_HOUR_IN_SEC
        self.sat.mbytes = 256
        self.sat.n_cpu_mem_threads = 18
        self.sat.more_cpu_stress = True

        self._log.info("Copying semt app")
        self.sgx.check_psw_installation()
        self.sgx.install_sdk()
        self.semt_app_loc: str = self.sgx._install_collateral.copy_semt_files_to_sut()

    def execute(self) -> bool:
        """
        Runs semt and Google stress app test
        and checks every sleep_time seconds that both are still running
        :raises content_exceptions.TestError: If any commands fail
        :raises content_exceptions.TestFail: If Google Stress App test log does not indicate success
        :returns: True if test passes
        """
        sleep_time: float = 15*TimeConstants.ONE_MIN_IN_SEC
        semt_cmd: str = "./semt -S2 1024 1024"

        self._log.info("Starting semt")
        self.os.execute_async(semt_cmd, cwd=self.semt_app_loc)

        self._log.info("Starting Google Stress App")
        self.sat.run_test()

        test_start: float = time.time()

        run_time: float = 0
        while run_time <= self.sat.run_time:
            self._log.info(f"Remaining run time {self.sat.run_time-run_time} seconds")

            self._log.info("Verifying that semt is still running")
            semt_ck: OsCommandResult = self.os.execute("pgrep semt", timeout=self._command_timeout)
            if semt_ck.cmd_failed():
                raise content_exceptions.TestError("Semt is no longer running.")
            self._log.info("Semt is still running.")

            self._log.info("Verifying that Google Stress App is still running")
            sat_ck: OsCommandResult = self.os.execute("pgrep stressapptest", timeout=self._command_timeout)
            if sat_ck.cmd_failed():
                # It's possible that the stress app stopped without issue before the clock ran out
                # So it doesn't make sense to error out just yet.
                self._log.info("Google Stress App test stopped running.")
                break
            self._log.info("Google Stress App test is still running.")

            run_time = time.time() - test_start

            time.sleep(sleep_time)

        self._log.info(f"Test ran for ~{run_time} seconds")
        self._log.info(f"Checking Stress App log")
        read_log_cmd: str = f"cat {self.sat.log_file}"
        read_log_res: OsCommandResult = self.os.execute(read_log_cmd, self._command_timeout)
        if read_log_res.cmd_failed():
            raise content_exceptions.TestError(f"{read_log_cmd} with return code {read_log_res.return_code}.\nstderr:\n{read_log_res.stderr}")
        else:
            sat_log: str = read_log_res.stdout
            if sat_log.find("Status: PASS") < 0:
                raise content_exceptions.TestFail(f"Stress app test log does not indicate success:\n{sat_log}")

        return True

    def cleanup(self, return_status):
        try:
            self.os.execute("pkill semt", timeout=self._command_timeout)
            self.os.execute("pkill stressapptest", timeout=self._command_timeout)
        except:
            # Doesn't matter if this fails.
            pass
        super(SgxGoogStressApp, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxGoogStressApp.main() else Framework.TEST_RESULT_FAIL)
