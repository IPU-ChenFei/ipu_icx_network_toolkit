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

import sys
import os
from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.cbnt_constants import HashAlgorithms
from src.security.tests.cbnt_txt.txt_constants import LCPPolicyElements, Tpm2KeySignatures, TpmIndices, TXT, Tpm2Drive


class LCP202SHA1MLE(TxtBaseTest):
    """
    Glasgow ID : 58253

    This test case tests LCP202 with a provisioned PO index with 1 TPM2 list of: RSA-3072-SHA256, SHA1 MLE ELEMENT.
    1.Ensure that the system is in sync with the latest BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.


    """
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    PRIVATE_KEY = "privkey3072.pem"
    PUBLIC_KEY = "pubkey3072.pem"
    LAST_IMAGE_IN_GRUB = "x86_64.img"
    LCP202 = os.getcwd() + "\\lcp202.pol"
    IDEF_FILE = os.getcwd() + "\\ExamplePO_Sha256.iDef"
    IDEF_FILE_BACKUP = os.getcwd() + "\\ExamplePO_Sha256.iDef.bak"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of LCP202SHA1MLE

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(LCP202SHA1MLE, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):  # type: () -> None
        """
        Validating the system has TXT enabled and can boot to tboot without a policy provisioned
        """
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob
        self._os.reboot(self._reboot_timeout)
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

    def execute(self):
        """
        1. Creates policy using tboot lcp tools and stores policy on usb
        2. Generates appropriate index definition file for provisioning
        3. Provisions TPM2 and writes location of data file into grub.cfg file
        :return: True if SUT boots trusted after provisioning, False if it cannot boot trusted
        """
        mle_element_name = "mle.elt"
        tboot_hash = "tboot_hash"
        privkey = "privkey3072.pem"
        pubkey = "pubkey3072.pem"
        self._linux_os.create_rsa_keys(self.PRIVATE_KEY, Tpm2KeySignatures.RSA3072, self.PUBLIC_KEY)
        self.generate_mle_hash(HashAlgorithms.SHA1, tboot_hash)
        self.create_lcp_elt(elt_type=LCPPolicyElements.MLE, out=mle_element_name, tpm_version=TXT.TPM2, min_ver='0',
                            ctrl='2', mle_hash=tboot_hash, alg=HashAlgorithms.SHA1)
        self.create_lcp2_list(out="lcp202.list", elements=[mle_element_name], sig_alg='rsa', list_ver=self.platform_family)
        self.sign_lcp2_list(out="lcp202.list", rev='2', private_key=privkey, public_key=pubkey,
                            sig_alg='rsa', hash_alg=HashAlgorithms.SHA256)
        self.create_policy(cbnt_product_version=self.platform_family, pol="lcp202.pol", data="lcp202.data",
                           lcp2_lists=["lcp202.list"], masks=[HashAlgorithms.SHA1, HashAlgorithms.SHA256],
                           policy_type='list', ctrl='2', rev='2', alg=HashAlgorithms.SHA256, min_ver='0',
                           sign="rsa-3072-sha256")
        self._log.debug("Copying lcp202.data into /boot/")
        self._os.execute("cp lcp202.data /boot/", self._command_timeout)
        self._os.copy_file_from_sut_to_local("/root/lcp202.pol", self.LCP202)
        path_to_idef = self._copy_usb.copy_file_from_usb_to_sut(self._common_content_lib,
                                                                self._common_content_configuration,
                                                                Tpm2Drive.TPM2_FOLDER +
                                                                Tpm2Drive.TPM2_PROVISIONING_FOLDER) + \
            "/ExamplePO_Sha256.iDef.bak"
        self._os.copy_file_from_sut_to_local(path_to_idef, self.IDEF_FILE_BACKUP)
        self.modify_linux_grub_file(self.LAST_IMAGE_IN_GRUB, False,
                                    new_phase="module2 /lcp202.data")
        self.modify_linux_grub_file(self.LAST_IMAGE_IN_GRUB, False,
                                    new_phase="echo \"loading lcp.data for lcp202\"")

        self.generate_file_for_tpm2_provisioning(self.LCP202,
                                                 self.IDEF_FILE_BACKUP,
                                                 self.IDEF_FILE)
        self._os.execute("mkdir lcp202", self._command_timeout)
        self._os.copy_local_file_to_sut(self.IDEF_FILE, "/root/lcp202/ExamplePO_Sha256.iDef")
        self._os.copy_local_file_to_sut(self.IDEF_FILE, "/root/lcp202/lcp202.iDef")
        self._copy_usb.copy_file_from_sut_to_usb(self._common_content_lib, self._common_content_configuration,
                                                 "/root/lcp202", "/" + Tpm2Drive.TPM2_FOLDER +
                                                 Tpm2Drive.TPM2_PROVISIONING_FOLDER)
        self._log.debug("Entering uefi shell to provision the tpm2 with the TC policy")
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell when attempting to provision TPM")
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self.provision_tpm2(usb_drive_list, TpmIndices.PO, HashAlgorithms.SHA256)
        if not self._os.is_alive():
            self._log.debug("SUT is down, applying power cycle to make the SUT up")
            self._log.debug("AC Off")
            self._ac_obj.ac_power_off(self._AC_TIMEOUT)
            self._log.debug("AC On")
            self._ac_obj.ac_power_on(self._AC_TIMEOUT)
            self._log.debug("Waiting for OS")
            self._os.wait_for_os(self._reboot_timeout)
        return self.verify_trusted_boot()

    def cleanup(self, return_status):  # type: (bool) -> None
        super(LCP202SHA1MLE, self).cleanup(return_status)
        self._log.info("Copying over any policy for cleanup")
        self._os.copy_local_file_to_sut(self.IDEF_FILE_BACKUP, "/root/lcp202/ExamplePO_Sha256.iDef")
        self._copy_usb.copy_file_from_sut_to_usb(self._common_content_lib, self._common_content_configuration,
                                                 "/root/lcp202", "/" + Tpm2Drive.TPM2_FOLDER +
                                                 Tpm2Drive.TPM2_PROVISIONING_FOLDER)
        self.modify_linux_grub_file(targeted_phrase="module2 /lcp202.data", deletion=True)
        self.modify_linux_grub_file(targeted_phrase="echo \"loading lcp.data for lcp202\"", deletion=True)
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell")
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self.provision_tpm2(usb_drive_list, TpmIndices.PO, hashalg=HashAlgorithms.SHA256)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LCP202SHA1MLE.main() else Framework.TEST_RESULT_FAIL)
