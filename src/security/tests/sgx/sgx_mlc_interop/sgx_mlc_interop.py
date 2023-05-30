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
from pathlib import Path
from typing import Match, Union, List, Pattern
import xml.etree.ElementTree as ET
import sys
import os
from datetime import datetime
import time
import re

from src.lib import content_base_test_case, content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.provider.sgx_provider import LinuxSGXDriver, SGXProvider
from src.lib.dtaf_content_constants import TimeConstants

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.os_lib import OsCommandResult


mlc_img_name: str = "dcsorepo.jf.intel.com/pnpwls/mlc_internal"
container_id_re: Pattern[str] = re.compile(r"(?P<id>[0-9a-f]{12})\s*"+mlc_img_name)


class SgxMlcInterop(content_base_test_case.ContentBaseTestCase):
    """
    Test ID: 14014944283
    SGX Interop + MLC workload
    Test Pre-requisites: SGX-enabled CPU
    """

    TEST_CASE_ID: List[str] = ["14014944283", "SGX Interop + MLC workload"]
    BIOS_CONFIG_FILE: str = "../sgx_enable_through_bios.cfg"

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        bios_config_file = os.path.abspath(self.BIOS_CONFIG_FILE)

        super(SgxMlcInterop, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path=bios_config_file)

        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("This test is not applicable for " + self.os.os_type)

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp: SiliconRegProvider = ProviderFactory.create(sil_cfg, test_log)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp: SiliconDebugProvider = ProviderFactory.create(si_dbg_cfg, test_log)
        self.sgx: LinuxSGXDriver = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._install_collateral: InstallCollateral = InstallCollateral(self._log, self.os, self._cfg)

    def prepare(self) -> None:
        super(SgxMlcInterop, self).prepare()

        self._log.info("Verifying SGX is enabled")
        self.sgx.check_sgx_enable()

        self.sgx.check_psw_installation()
        self.sgx.install_sdk()
        self._log.info("Installing Hydra")
        self.hydra_path: str = Path(os.path.join(self._install_collateral.copy_and_install_hydra_tool(), "App")).as_posix()

        self.sgx.install_pnpwls_master()

    def execute(self) -> bool:
        test_len: float = 10 * TimeConstants.ONE_HOUR_IN_SEC
        sleep_len: float = 15 * TimeConstants.ONE_MIN_IN_SEC
        log_time: str = datetime.now().strftime("%Y%d%m_%H:%M:%S")
        hydra_out_path: str = Path(os.path.join(self.hydra_path, f"Hydra_output_{log_time}")).as_posix()

        self._log.info(f"Test will run for {test_len} seconds")
        self._log.info(f"Hydra output file location: {hydra_out_path}")

        test_start: float = time.time()

        self._log.info("Starting Hydra")
        self.os.execute_async(self.sgx.HYDRA_CMD.format(128, 128, 64, test_len, hydra_out_path), self.hydra_path)

        self._log.info("Starting MLC tool")
        self.sgx.execute_mlc_tool(run_async=True)

        # It can take a couple seconds for the script to get docker started
        time.sleep(20)

        self.mlc_cont_id = self._get_mlc_container_id()
        self._log.info(f"MLC Container ID: {self.mlc_cont_id}")

        run_time: float = 0
        while run_time < test_len:
            run_time = time.time() - test_start

            self._verify_hydra(hydra_out_path)
            self._verify_mlc()

            time.sleep(sleep_len)

        return True

    def _get_mlc_container_id(self) -> str:
        """Gets the container ID running the MLC tool
        :returns: ID of docker image running the MLC tool
        :raises content_exceptions.TestFail: If command fails or ID can't be found in the output
        """
        get_id_cmd: str = "docker ps"
        get_id_res: OsCommandResult = self.os.execute(get_id_cmd, timeout=self._command_timeout)
        if get_id_res.cmd_failed():
            raise content_exceptions.TestFail(f"{get_id_cmd} failed with return code {get_id_res.return_code}.\nstderr:\n{get_id_res.stderr}")
        else:
            match: Union[None, Match[str]] = container_id_re.search(get_id_res.stdout)
            if not match:
                raise content_exceptions.TestFail(f"Could not find container ID in {get_id_res.stdout}")
            else:
                return match.group("id")

    def _verify_hydra(self, hydra_out_path: str) -> None:
        """Checks that SGXHydra is still running
        :param hydra_out_path: Path to the Hydra output file
        :raises content_exceptions.TestFail: If any commands fails, hydra is no longer running, or
            if errors are found in the hydra output file
        """

        self._log.info("Checking on Hydra")
        hydra_live_res: OsCommandResult = self.os.execute(f"pgrep {self.sgx.SGX_HYDRA}", self._command_timeout)
        if hydra_live_res.cmd_failed():
            content_exceptions.TestFail("Hydra has died")
        else:
            self._log.info("Hydra PID(s):\n{}".format(hydra_live_res.stdout))

        hydra_read_res: OsCommandResult = self.os.execute(f"cat {hydra_out_path}", self._command_timeout, self.hydra_path)
        if hydra_read_res.cmd_failed():
            raise content_exceptions.TestFail(f"Failed to read hydra log file: {hydra_read_res.stderr}")
        else:
            hydra_log: str = hydra_read_res.stdout.lower()
            if hydra_log.find("error") > -1:
                raise content_exceptions.TestFail("Found errors in Hydra Log file")
            else:
                self._log.info("No errors found in Hydra log file")

    def _verify_mlc(self) -> None:
        """Checks that MLC tool is still running
        :raises content_exceptions.TestFail: If the check command fails or if MLC is not running"""

        self._log.info("Checking on MLC Tool")
        mlc_live_cmd: str = "docker ps"
        mlc_live_res: OsCommandResult = self.os.execute(mlc_live_cmd, timeout=self._command_timeout)
        if mlc_live_res.cmd_failed():
            raise content_exceptions.TestFail(f"{mlc_live_cmd} failed with return code {mlc_live_res.return_code}.\nstderr:\n{mlc_live_res.stderr}")
        elif mlc_live_res.stdout.find(mlc_img_name) < 0:
            raise content_exceptions.TestFail("MLC Tool appears to have stopped running")
        else:
            self._log.info("MLC Tool is still running")

    def cleanup(self, return_status):
        try:
            self.os.execute("pkill SGXHydra", timeout=self._command_timeout)
            self.os.execute(f"docker stop {self.mlc_cont_id}", timeout=self._command_timeout)
        except:
            # If the programs aren't running, that's fine
            pass

        super(SgxMlcInterop, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxMlcInterop.main() else Framework.TEST_RESULT_FAIL)
