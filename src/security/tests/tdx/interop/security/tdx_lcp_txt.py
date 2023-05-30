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
    :Trusted Boot Interop with TDX and TXT with MLE2 Launch Control Policy:

    With a trusted boot with a Launch Control Policy, boot a TD guest successfully.
"""

import sys
import os
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.tdx.interop.security.txt_trusted_boot import TdxTrustedBoot
from src.lib.cbnt_constants import HashAlgorithms
from src.security.tests.cbnt_txt.txt_constants import LCPPolicyElements, Tpm2KeySignatures, TpmIndices, TXT, Tpm2Drive


class LCP:
    def __init__(self, file_name):
        self.elt = f"{file_name}.elt"
        self.lst = f"{file_name}.lst"
        self.dat = f"{file_name}.dat"
        self.pol = f"{file_name}.pol"


class TdxLcpTest(TdxTrustedBoot):
    """
            This recipe enables TXT and TDX together with a TXT launch control policy and verifies a TD guest can
            launch.

            :Scenario: Enable TXT and boot to a trusted MLE with tboot.  Enable TDX and reboot to OS.  Generate and
            install a launch control policy on the SUT.  Boot to the trusted environment and verify the LCP has been
            loaded, Then launch defined number of TD guests (per <NUM_OF_VMS> param in content_configuration.xml).
             Run workload on TD guest and verify there are no MCEs.

            :Phoenix ID: 22013231907

            :Test steps:

                :1:  Enable TXT on SUT and boot to trusted MLE

                :2:  Enable TDX and boot to OS.

                :3:  Generate a list type CBnT launch control policy with 1 MLE SHA256 element.

                :4:  Provision the system with the LCP and boot to OS.

                :5:  Launch a TD guest.

                :6:  Run mprime on TD guest.

            :Expected results: TD guest should boot and should not yield MCEs.

            :Reported and fixed bugs:

            :Test functions:

        """

    LAST_IMAGE_IN_GRUB = "x86_64.img"

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TdxLcpTest, self).__init__(test_log, arguments, cfg_opts)
        self.txt = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        self.platform_family = self._common_content_lib.get_platform_family()
        self.path_to_idef = None
        self.path_to_idef_bak = None
        self.lcp = LCP("mle_tdx")

    def execute(self) -> bool:
        hash_file_name = "mle_hash"
        efi_partition = "/boot/efi/"
        IDEF_FILE = "ExamplePO_Sha256.iDef"
        # generate all the policy and dat files
        self._log.info("Generating LCP.")
        hash_string = self.execute_os_cmd(f"grep logging /boot/efi/EFI/{self.os.os_subtype.lower()}/grub.cfg | awk "
                                          f"-F\' \' \'{{print $NF}}\'").split("\n")[0]
        self.execute_os_cmd(f"lcp2_mlehash --create --cmdline \"{hash_string}\" /boot/tboot.gz > {hash_file_name}")
        self.txt.create_lcp_elt(elt_type=LCPPolicyElements.MLE, out=self.lcp.elt, tpm_version=TXT.TPM2, min_ver='0',
                                ctrl='2', mle_hash=hash_file_name, alg=HashAlgorithms.SHA256)
        self.txt.create_lcp2_list(out=self.lcp.lst, elements=[self.lcp.elt], sig_alg=None,
                                  list_ver=self.platform_family)
        self.txt.create_policy(cbnt_product_version=self.platform_family, pol=self.lcp.pol, data=self.lcp.dat,
                               lcp2_lists=[self.lcp.lst], sign="rsa-3072-sha256", masks=[],
                               policy_type='list', ctrl='2', rev='2', alg=HashAlgorithms.SHA256, min_ver='0')
        self._log.info(f"Created LCP files {self.lcp.dat}, {self.lcp.pol}, {self.lcp.lst}, {self.lcp.elt}.")

        # copy .dat to /boot
        self._log.info(f"Staging {self.lcp.dat} file into grub menu.")
        self._log.debug(f"Copying {self.lcp.dat} into /boot/")
        self.os.execute(f"cp {self.lcp.dat} /boot/", self.command_timeout)
        self.txt.modify_linux_grub_file(self.LAST_IMAGE_IN_GRUB, False, new_phase=f"module2 /{self.lcp.dat}")
        self.txt.modify_linux_grub_file(self.LAST_IMAGE_IN_GRUB, False,
                                        new_phase=f"echo \"loading {self.lcp.dat} ...\"")

        self._log.info(f"Processing iDef file to provision {self.lcp.pol}.")
        # copy .pol to host to update to iDef and stage to TPM2ProvTools directory
        self.path_to_idef = self.execute_os_cmd(f"find {efi_partition} -name \'{IDEF_FILE}\'")
        self.path_to_idef_bak = f"{self.path_to_idef}.bak"
        local_copy_of_idef = f"{os.getcwd()}\\{IDEF_FILE}"
        local_copy_of_idef_bak = f"{local_copy_of_idef}.bak"
        local_copy_of_idef_pol = f"{os.getcwd()}\\{self.lcp.pol}"
        self.execute_os_cmd(f"cp {self.path_to_idef} {self.path_to_idef_bak}")  # create backup copy of lcp
        self.os.copy_file_from_sut_to_local(f"/root/{self.lcp.pol}", f"{os.getcwd()}\\{self.lcp.pol}")
        self.os.copy_file_from_sut_to_local(self.path_to_idef, local_copy_of_idef)
        self.os.copy_file_from_sut_to_local(self.path_to_idef_bak, local_copy_of_idef_bak)
        self.txt.generate_file_for_tpm2_provisioning(local_copy_of_idef_pol, local_copy_of_idef_bak,
                                                     local_copy_of_idef)
        self.os.copy_local_file_to_sut(local_copy_of_idef, self.path_to_idef)

        self._log.info(f"Booting to UEFI shell to provision PO index.")
        # boot to UEFI shell to provision
        self.uefi.enter_uefi_shell()  # boot to UEFI shell
        self.txt.provision_tpm2(self.uefi_drive, TpmIndices.PO, HashAlgorithms.SHA256)
        self._log.info(f"Booting to SUT OS to verify trusted boot will work with LCP.")
        self.perform_graceful_g3()

        # boot to OS
        if self.txt.validate_linux_mle():
            if self.execute_os_cmd(f"txt-stat | grep \'v2 LCP policy data found\'") == "":
                raise content_exceptions.TestFail(f"System booted trusted, but could not find LCP was loaded in "
                                                  f"txt-stat.")
            self._log.debug("Successfully completed trusted boot amd verified LCP, starting TD guest and workload.")
            return super(TdxLcpTest, self).execute()
        raise content_exceptions.TestFail("Failed to boot trusted.")

    def cleanup(self, return_status: bool):
        super(TdxLcpTest, self).cleanup(return_status)
        self._log.info("Copying over clean PO policy for cleanup")
        self.execute_os_cmd(f"cp {self.path_to_idef_bak} {self.path_to_idef}")
        self.txt.modify_linux_grub_file(targeted_phrase=f"module2 /{self.lcp.dat}", deletion=True)
        self.txt.modify_linux_grub_file(targeted_phrase=f"echo \"loading {self.lcp.dat} ...\"", deletion=True)
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell")
        self.txt.provision_tpm2(self.uefi_drive, TpmIndices.PO, hashalg=HashAlgorithms.SHA256)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxLcpTest.main() else Framework.TEST_RESULT_FAIL)
