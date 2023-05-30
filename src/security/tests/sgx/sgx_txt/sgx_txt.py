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
from src.provider.sgx_provider import LinuxSGXDriver, SGXProvider
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems

local_path: Path = Path(__file__).parent.resolve()

class SgxOnTxt(content_base_test_case.ContentBaseTestCase):
    """
    Test ID: 18014073330
    Verify on a TXT enabled system that SGX works as expected
    Test Pre-requisites: SGX and TXT enabled CPU
    """

    TEST_CASE_ID: List[str] = ["18014073330", "Verify on a TXT enabled system that SGX works as expected"]
    SGX_BIOS_CONFIG_FILE: str = Path.joinpath(local_path.parent, "sgx_enable_through_bios.cfg")
    TBOOT_BIOS_CONFIG_FILE: str = Path.joinpath(local_path.parent.parent, "cbnt_txt", "txt_base", "security_txt_bios_knobs_enable.cfg")

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        bios_files: List[str] = [self.TBOOT_BIOS_CONFIG_FILE, self.SGX_BIOS_CONFIG_FILE]
        joined_bios_file: str = CommonContentLib.get_combine_config(bios_files)

        super(SgxOnTxt, self).__init__(test_log, arguments, cfg_opts, joined_bios_file)

        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError(f"This test is not applicable for {self.os.os_type}")

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp: SiliconRegProvider = ProviderFactory.create(sil_cfg, test_log)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp: SiliconDebugProvider = ProviderFactory.create(si_dbg_cfg, test_log)
        self.sgx: LinuxSGXDriver = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)

    def prepare(self) -> None:
        self.tboot: TxtBaseTest = TxtBaseTest(self._log, self._args, self._cfg)
        self.tboot.install_tboot_mercurial()
        self.tboot_index: str = self.tboot.get_tboot_boot_position()
        self.tboot.set_default_boot_entry(self.tboot_index)
        super(SgxOnTxt, self).prepare()
        self.tboot.verify_sut_booted_in_tboot_mode(self.tboot_index)

        self.sgx.check_sgx_enable()
        self.sgx.load_sgx_properites()
        self.sgx.check_psw_installation()

    def execute(self) -> bool:
        """Runs SGX app test
        :returns: True if SGX app test is successful"""
        return self.sgx.run_sgx_app_test()

    def cleanup(self, return_status) -> None:
        self.tboot.set_default_boot_entry(self.tboot._DEFAULT_ENTRY)
        self.perform_graceful_g3()
        self.tboot.cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxOnTxt.main() else Framework.TEST_RESULT_FAIL)
