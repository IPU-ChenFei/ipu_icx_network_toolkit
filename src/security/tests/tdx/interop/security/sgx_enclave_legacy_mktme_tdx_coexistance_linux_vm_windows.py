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
    :Linux TD Guest, Linux Legacy Guest, Windows Mk-tme Guest and SGX Enclave Coexistance:

    With TD, Legacy, MK-Tme guests launched, launch SGX enclave and verify all guests are alive.
"""
import sys
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.security.tests.sgx.sgx_hydra_test.sgx_hydra_test_windows import SgxHydraTestWindows
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class SgxHydraLegacyMktmeLinuxTdGuestWindows(WindowsTdxBaseTest, SgxHydraTestWindows):
    """
            This test verifies the coexistence of an SGX enclave, Linux legacy VM, mk-tme enabled VM
            and a Linux Ubuntu TD guest on the SUT.  Paths to SGX PSW and FVT packages from BKC must be updated in
            content_configuration.xml file.  These are between the <SGX_APP><WINDOWS><PSW_SGX_APP_INSTALLER>
            and <SGX_APP><WINDOWS><SGX_FVT_ZIP> tags.

            :Scenario: Launch a Linux TD guest, Linux legacy VM, mk-tme enabled VM and a SGX enclave on the SUT.
            Verify system and guest VMs are alive.

            :Phoenix ID: 14015392671

            :Test steps:

                :1:  Enable TDX and SGX.

                :2:  Install SGX SW collateral (PSW and FVT stacks).

                :3:  Create and launch a Linux TD guest, Linux Legacy VM and mk-tme VM.

                :4:  Launch SGX sample enclave hydra test.

                :5: Verify all VM guests are still alive.

            :Expected results: all guests and SUT should be alive.

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
        super(SgxHydraLegacyMktmeLinuxTdGuestWindows, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self) -> None:
        # call prepare() of both parent classes.
        WindowsTdxBaseTest.prepare(self)
        SgxHydraTestWindows.prepare(self)

        self.setup_sgx_packages()
        self.time_duration = self.tdx_properties[self.tdx_consts.TDX_SGX_HYDRA_TEST_TIME]

    def execute(self) -> bool:
        self._log.info("Get all VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()
        self.clean_linux_vm_tdx_apps()

        # launch ubuntu td guest
        td_key = 0
        td_key, td_vm_name = self.create_vm_name(td_key, legacy=False, vm_os="LINUX")
        self.launch_ubuntu_td_guest(td_key, td_vm_name)

        # launch ubuntu legacy guest
        legacy_key = td_key+1
        legacy_key, legacy_vm_name = self.create_vm_name(legacy_key, legacy=True, vm_os="LINUX")
        self.launch_legacy_ubuntu_guest(legacy_key, legacy_vm_name)

        # launch mktme guest
        mktme_key = legacy_key+1
        mktme_key, mktme_vm_name = self.create_vm_name(mktme_key, legacy=True)
        mktme_vm_name = mktme_vm_name.replace("LEGACY", "MKTME")
        self.launch_mktme_guest(mktme_key, mktme_vm_name)

        # run SGX hydra test
        SgxHydraTestWindows.execute(self)

        # test whether VMs is active
        for vm_name in [td_vm_name, legacy_vm_name]:
            vm_ip_address = self.get_vm_ipaddress_for_linux_guest(vm_name)
            ret_val = self.test_linux_vm_folder_accessible(vm_name, vm_ip_address)
            if ret_val is True:
                self._log.info(f"{vm_name} guest alive after launching SGX Hydra Test")
            else:
                raise content_exceptions.TestFail(f"{vm_name} : VM is not accessible after launching SGX Hydra Test")

        ret_val = self.test_vm_folder_accessible(mktme_vm_name)
        if ret_val is True:
            self._log.info(f"{mktme_vm_name} guest alive after launching SGX Hydra Test")
        else:
            raise content_exceptions.TestFail(f"{mktme_vm_name} : VM is not accessible after launching SGX Hydra Test")

        return True

    def cleanup(self, return_status: bool) -> None:
        self.clean_linux_vm_tdx_apps()
        WindowsTdxBaseTest.cleanup(self, return_status)
        SgxHydraTestWindows.cleanup(self, return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxHydraLegacyMktmeLinuxTdGuestWindows.main() else Framework.TEST_RESULT_FAIL)
