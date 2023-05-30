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

from argparse import Namespace
from typing import Union, List
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

from src.lib import content_base_test_case, content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.provider.sgx_provider import LinuxSGXDriver, SGXProvider
from src.lib.dtaf_content_constants import TimeConstants

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.os_lib import OsCommandResult
from dtaf_core.lib.os_lib import LinuxDistributions
from dtaf_core.lib.exceptions import OsCommandTimeoutException

local_path: Path = Path(__file__).parent.resolve()

class SgxMaxBWTest(content_base_test_case.ContentBaseTestCase):
    """
    Test Case ID: 14016387385
    SGX Max BW Test
    Test Pre-requisites: SGX-enabled platform

    * Test creates a thread per logical processor, affinitizes the thread
    * Attempts to allocate the indicated EPC memory (cmd line argument in MB)
    * Writes a pattern using the memset routine to achieve the max write bandwidth/some reads
    """

    TEST_CASE_ID: List[str] = ["14016387385", "SGX Max BW Test"]
    SGX_W_LI_BIOS_PATH: str = [Path.joinpath(local_path.parent, "sgx_with_logical_integrity/sgx_with_li.cfg"),
                               Path.joinpath(local_path, "prm_size.cfg")]
    SGX_W_CI_BIOS_PATH: str = [Path.joinpath(local_path.parent, "sgx_with_cryptographic_integrity/sgx_with_ci_bios.cfg"),
                               Path.joinpath(local_path, "prm_size.cfg")]

    SGX_BW_TEST_DIR_NAME: str = "sgx_max_bw_test"
    SGX_BW_TEST_TIMEOUT: float = 21600
    SGX_BW_TEST_MEM: int = 500
    SGX_BW_TEST_CMD: str = f"./sgx_max_bw_test_16gb {SGX_BW_TEST_TIMEOUT} {SGX_BW_TEST_MEM}"

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        sgx_w_li_path: str = CommonContentLib.get_combine_config(self.SGX_W_LI_BIOS_PATH)
        super(SgxMaxBWTest, self).__init__(test_log, arguments, cfg_opts, sgx_w_li_path)

        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("This test is not applicable for " + self.os.os_type)
        else:
            os_sub_type: str = "{}_{}_KERNEL"
            if "intel-next" in self._common_content_lib.get_linux_kernel():
                os_sub_type = os_sub_type.format(LinuxDistributions.RHEL, "NXT")
            else:
                os_sub_type = os_sub_type.format(LinuxDistributions.RHEL, "BASE")

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp: SiliconRegProvider = ProviderFactory.create(sil_cfg, test_log)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp: SiliconDebugProvider = ProviderFactory.create(si_dbg_cfg, test_log)
        self.sgx: LinuxSGXDriver = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._install_collateral: InstallCollateral = InstallCollateral(self._log, self.os, self._cfg)

        self.BW_TEST: str = self._common_content_configuration.get_security_sgx_params(self.os.os_type, "SGX_BW_TEST", os_sub_type)

    def prepare(self) -> None:
        super(SgxMaxBWTest, self).prepare()

        self._log.info("Verifying SGX is enabled")
        self.sgx.check_sgx_enable()

        self._log.info("Installing Requirements")
        self.sgx.install_requirements()
        self.sgx.install_sdk()
        self.sgx.install_psw()

        self._log.info("Copying BW test files")
        self.bw_test_path: str = self._install_collateral.download_and_copy_zip_to_sut(self.SGX_BW_TEST_DIR_NAME, self.BW_TEST)
        make_res: OsCommandResult = self.os.execute("make", timeout=self._command_timeout, cwd=self.TEST_PATH)
        self._log.info("Building test")
        if make_res.cmd_failed():
            raise content_exceptions.TestSetupError(f"Test failed to make with error code {make_res.return_code}.\nstderr:\n{make_res.stderr}")

    def execute(self) -> bool:
        self._log.info("Running test with local integrity")
        self._run_bw_test()

        self._log.info("Setting up BIOS for SGX with CI")
        sgx_w_ci_bios_path: str = CommonContentLib.get_combine_config(self.SGX_W_CI_BIOS_PATH)
        self.bios_util.set_bios_knob(sgx_w_ci_bios_path)
        self.perform_graceful_g3()

        self._log.info("Running BW test with Cryptographic Integrity")
        self._run_bw_test()

        return True

    def _run_bw_test(self) -> None:
        """Runs Max Contention Test
        :raises content_exceptions.TestFail: If Command fails for any reason"""

        # During testing, I observed a minimum run time of about 11 minutes
        # I padded it to 15 minutes to be safe. This value shouldn't be too
        # long since hanging can indicate failure
        extra_time: float = 15 * TimeConstants.ONE_MIN_IN_SEC
        timeout: float = self.SGX_BW_TEST_TIMEOUT + extra_time

        try:
            test_res: OsCommandResult = self.os.execute(self.SGX_BW_TEST_CMD, timeout=timeout, cwd=self.bw_test_path)
        except OsCommandTimeoutException:
            raise content_exceptions.TestFail(f"Test timed out. This may indicate a failure. Please check the log: {self.SGX_BW_LOG_PATH}")
        else:
            if test_res.cmd_failed():
                raise content_exceptions.TestFail(f"BW Test failed with return code {test_res.return_code}.\nstderr:\n{test_res.stderr}")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxMaxBWTest.main() else Framework.TEST_RESULT_FAIL)
