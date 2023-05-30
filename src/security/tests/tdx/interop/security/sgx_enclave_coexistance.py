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
from src.lib.content_exceptions import TestFail
from src.security.tests.tdx.tdvm.TDX050_launch_multiple_tdvm_linux import MultipleTDVMLaunch
from src.security.tests.sgx.sgx_sample_enclave_creation.sgx_sample_enclave_creation import SGXSampleEnclaveCreation


class SgxEnclaveTdGuest(SGXSampleEnclaveCreation):
    """
            This test verifies the coexistence of an SGX enclave and a TD guest on the SUT.  Paths to SGX PSW and FVT
            packages from BKC must be updated in content_configuration.xml file.  These are between the
            <SGX_APP><LINUX><RHEL_BASE_KERNEL><PSW_ZIP> and <SGX_APP><LINUX><RHEL_BASE_KERNEL><SGX_FVT_ZIP> tags.

            :Scenario: Launch a TD guest and a SGX enclave on the SUT.  Verify system and TD guest are alive.

            :Phoenix ID: 18014073883

            :Test steps:

                :1:  Enable TDX and SGX.

                :2:  Install SGX SW collateral (PSW and FVT stacks).

                :3:  Create and launch a TD guest.

                :4:  Launch SGX sample enclave.

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
        super(SgxEnclaveTdGuest, self).__init__(test_log, arguments, cfg_opts)
        self.launch_vms = MultipleTDVMLaunch(test_log, arguments, cfg_opts)
        try:
            self.launch_vms.tdx_properties[self.launch_vms.tdx_consts.MEM_INTEGRITY_MODE] = arguments.INTEGRITY_MODE.upper()
        except AttributeError:  # no argument given for memory integrity
            self._log.debug("No memory integrity setting given, leaving knob alone.")
            self.launch_vms.tdx_properties[self.launch_vms.tdx_consts.MEM_INTEGRITY_MODE] = None

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(SgxEnclaveTdGuest, cls).add_arguments(parser)
        parser.add_argument("--integrity-mode", "--im", action="store", dest="INTEGRITY_MODE", default=None)

    def prepare(self) -> None:
        self.launch_vms.os_preparation()  # verify python softlink is installed
        super(SgxEnclaveTdGuest, self).prepare()
        self.launch_vms.prepare()

    def execute(self) -> bool:
        self._log.info("Launching TD VMs.")
        self.launch_vms.execute()
        self._log.info("Setting up SGX sample enclave.")
        super(SgxEnclaveTdGuest, self).execute()
        self._log.info("SGX sample enclave launched, checking VM health.")
        for key, vm in enumerate(self.launch_vms.tdvms):
            if not self.launch_vms.vm_is_alive(key=key):
                raise TestFail(f"VM {key} no longer alive after launching SGX enclave.")
        self._log.info("TD guests are alive after launching SGX enclave.")
        return True

    def cleanup(self, return_status: bool) -> None:
        self.launch_vms.cleanup(return_status)  # override SGX clean up for TD guest clean up method


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxEnclaveTdGuest.main() else Framework.TEST_RESULT_FAIL)
