#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :TD Guest and SGX Enclave Coexistance:

    With TD guest launched, launch SGX enclave and verify TD guest is alive.
"""
import sys
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.security.tests.sgx.sgx_hydra_test.sgx_hydra_test_windows import SgxHydraTestWindows
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class SgxHydraTdGuestWindows(WindowsTdxBaseTest, SgxHydraTestWindows):
    """
            This test verifies the coexistence of an SGX enclave and a TD guest on the SUT.  Paths to SGX PSW and FVT
            packages from BKC must be updated in content_configuration.xml file.  These are between the
            <SGX_APP><WINDOWS><PSW_SGX_APP_INSTALLER><WINDOWS><SGX_FVT_ZIP> tags.

            :Scenario: Launch a TD guest and a SGX enclave on the SUT.  Verify system and TD guest are alive.

            :Phoenix ID: 22013146494

            :Test steps:

                :1:  Enable TDX and SGX.

                :2:  Install SGX SW collateral (PSW, HydraTest and sgx_sdk_build).

                :3:  Create and launch a TD guest.

                :4:  Launch SGXHydra Test in SUT

                :5: Verify TD guest is still alive.

            :Expected results: TD guest and SUT should be alive.

            :Reported and fixed bugs:

            :Test functions:

    """

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SgxHydraTdGuestWindows, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self) -> None:
        # call prepare() of both parent classes.
        WindowsTdxBaseTest.prepare(self)
        SgxHydraTestWindows.prepare(self)

        self.setup_sgx_packages()
        self.time_duration = self.tdx_properties[self.tdx_consts.TDX_SGX_HYDRA_TEST_TIME]

    def execute(self) -> bool:

        self._log.info("Get all tdx VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()

        key = 0
        key, vm_name = self.create_vm_name(key, legacy=False)

        # launch td guest
        self.launch_td_guest(key, vm_name)

        # run SGX hydra test
        SgxHydraTestWindows.execute(self)

        # test whether VM is active
        ret_val = self.test_vm_folder_accessible(vm_name)
        if ret_val is True:
            self._log.info("TD guests are alive after launching SGX Hydra Test")
        else:
            raise content_exceptions.TestFail("VM is not accessible after applying memory encryption")

        return True

    def cleanup(self, return_status: bool) -> None:
        WindowsTdxBaseTest.cleanup(self, return_status)
        SgxHydraTestWindows.cleanup(self, return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxHydraTdGuestWindows.main() else Framework.TEST_RESULT_FAIL)
