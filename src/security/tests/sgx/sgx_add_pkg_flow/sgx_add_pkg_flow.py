import os
import sys
from argparse import Namespace
from typing import Union, List
import xml.etree.ElementTree as ET

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.sgx_provider import SGXProvider, LinuxSGXDriver
from src.lib import content_base_test_case, content_exceptions
from src.multisocket.lib.multisocket import MultiSocket

class SgxAddPkgFlow(content_base_test_case.ContentBaseTestCase):
    """
    Test ID: 18015174651
    Add Package Flow (MSFT Flow)
    Test Pre-requisites:
        * SGX-enabled CPU
        * 2-socket system with both sockets populated
    """

    UPI_DIS_BIOS_CONFIG_FILE: str = "link_disable_with_sgx.cfg"
    UPI_EN_BIOS_CONFIG_FILE: str = "link_enable_pkg_dis.cfg"
    TEST_CASE_ID: List[str] = ["18015174651", "Add Package Flow (MSFT Flow)"]

    def __init__(self, test_log: str , arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        super(SgxAddPkgFlow, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path=self.UPI_DIS_BIOS_CONFIG_FILE)

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp: SiliconRegProvider = ProviderFactory.create(sil_cfg, test_log)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp: SiliconDebugProvider = ProviderFactory.create(si_dbg_cfg, test_log)
        self.sgx: LinuxSGXDriver = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)

        if self.os.os_type == OperatingSystems.LINUX:
            if MultiSocket.get_socket_num_linux(self.os) != 2:
                raise content_exceptions.TestNAError("This test only works on 2 socket systems")
        elif self.os.os_type == OperatingSystems.WINDOWS:
            MultiSocket.check_socket_num_win(self.os, 2)
        else:
            raise content_exceptions.TestNotImplementedError(f"Test not implemented for {self.os.os_type}")

    def prepare(self) -> None:
        super(SgxAddPkgFlow, self).prepare()

        self._log.info("Verifying SGX is enabled")
        self.sgx.check_sgx_enable()

        self.sgx.install_mp_registration()

    def execute(self) -> bool:
        self._log.info("Verifying MP Registration")
        if not self.sgx.verify_mp_registration():
            content_exceptions.TestFail("Failed to verify MP registration with UPI disabled")

        self._log.info("Enabling UPI")
        self.bios_util.set_bios_knob(bios_config_file=self.UPI_EN_BIOS_CONFIG_FILE)
        self.perform_graceful_g3()

        self._log.info("Verifying MP registration again")
        if not self.sgx.verify_mp_registration():
            content_exceptions.TestFail("Failed to verify MP registration with UPI enabled")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxAddPkgFlow.main() else Framework.TEST_RESULT_FAIL)
