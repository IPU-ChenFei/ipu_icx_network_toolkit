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
from src.security.tests.cbnt_txt.txt_constants import LCPPolicyElements, TpmIndices, TXT, Tpm2Drive


class LCP201(TxtBaseTest):
    """
    Glasgow ID : 58252

    This test case tests LCP201 with a provisioned PO index with 1 TPM2 list of unsigned SHA256 PCONF ELEMENT.
    1.Ensure that the system is in sync with the latest BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.


    """
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    PCR_FILE_NAME = "pcrs.pcr"
    TPM2_PCR_FOLDER = "/TPM_PCR_Tools"
    LAST_IMAGE_IN_GRUB = "x86_64.img"
    LCP201 = os.getcwd() + "\\lcp201.pol"
    IDEF_FILE = os.getcwd() + "\\ExamplePO_Sha256.iDef"
    IDEF_FILE_BACKUP = os.getcwd() + "\\ExamplePO_Sha256.iDef.bak"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of LCP201SHA1PCONF

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(LCP201, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):  # type: () -> None
        """
        Validating the system has TXT enabled and can boot to tboot without a policy provisioned
        :return:
        """
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob
        self._os.reboot(self._reboot_timeout)
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

    def execute(self):
        """
        1. Creates policy using tboot lcp tools and stores policy on usb
        2. Generates appropriate index definition file for provisioning
        3. Generates PCRs for PCONF element
        3. Provisions TPM2 and writes location of data file into grub.cfg file
        :return: True if SUT boots trusted after provisioning, False if it cannot boot trusted
        """
        pconf_element_name = "pconf.elt"
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell to generate pcr list")
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self.generate_pcrs(HashAlgorithms.SHA256, usb_drive_list, self.PCR_FILE_NAME)
        if not self._os.is_alive():
            self._log.info("SUT is down, applying power cycle to make the SUT up")
            self._log.info("AC Off")
            self._ac_obj.ac_power_off(self._AC_TIMEOUT)
            self._log.info("AC On")
            self._ac_obj.ac_power_on(self._AC_TIMEOUT)
            self._log.info("Waiting for OS")
            self._os.wait_for_os(self._reboot_timeout)
        path_to_pcrs = self._copy_usb.copy_file_from_usb_to_sut(self._common_content_lib,
                                                                self._common_content_configuration,
                                                                Tpm2Drive.TPM2_FOLDER +
                                                                self.TPM2_PCR_FOLDER) + "/" + self.PCR_FILE_NAME
        self._os.copy_file_from_sut_to_local(path_to_pcrs, "pcrs.pcr")
        pcr_hash = self.capture_pcr_hash(pcr_file="pcrs.pcr", hash_alg=HashAlgorithms.SHA256, pcr_number=0)
        self.create_lcp_elt(elt_type=LCPPolicyElements.PCONF, out=pconf_element_name, min_ver="0", ctrl="2",
                            tpm_version=TXT.TPM2, pcr_number="0", alg=HashAlgorithms.SHA256,
                            pcr_hash=pcr_hash)
        self.create_lcp2_list(out="lcp201.list",  elements=[pconf_element_name], sig_alg='rsa', list_ver= self.platform_family)
        self.create_policy(cbnt_product_version=self.platform_family, pol="lcp201.pol", data="lcp201.data",
                           lcp2_lists=["lcp201.list"], masks=[HashAlgorithms.SHA1, HashAlgorithms.SHA256],
                           policy_type='list', ctrl='2', rev='2', alg=HashAlgorithms.SHA256, min_ver='0',
                           sign="rsa-2048-sha256")
        self._log.info("Copying lcp201.data into /boot/")
        self._os.execute("cp lcp201.data /boot/", self._command_timeout)

        self._os.copy_file_from_sut_to_local("/root/lcp201.pol", self.LCP201)
        path_to_idef = self._copy_usb.copy_file_from_usb_to_sut(self._common_content_lib,
                                                                self._common_content_configuration,
                                                                Tpm2Drive.TPM2_FOLDER +
                                                                Tpm2Drive.TPM2_PROVISIONING_FOLDER) + \
            "/ExamplePO_Sha256.iDef.bak"
        self._os.copy_file_from_sut_to_local(path_to_idef, self.IDEF_FILE_BACKUP)
        self.modify_linux_grub_file(self.LAST_IMAGE_IN_GRUB, False,
                                    new_phase="module2 /lcp201.data")
        self.modify_linux_grub_file(self.LAST_IMAGE_IN_GRUB, False,
                                    new_phase="echo \"loading lcp.data for lcp201\"")

        self.generate_file_for_tpm2_provisioning(self.LCP201,
                                                 self.IDEF_FILE_BACKUP,
                                                 self.IDEF_FILE)
        self._os.execute("mkdir lcp201", self._command_timeout)
        self._os.copy_local_file_to_sut(self.IDEF_FILE, "/root/lcp201/ExamplePO_Sha256.iDef")
        self._os.copy_local_file_to_sut(self.IDEF_FILE, "/root/lcp201/lcp201.iDef")
        self._copy_usb.copy_file_from_sut_to_usb(self._common_content_lib, self._common_content_configuration,
                                                 "/root/lcp201", "/" + Tpm2Drive.TPM2_FOLDER +
                                                 Tpm2Drive.TPM2_PROVISIONING_FOLDER)
        self._log.info("Entering uefi shell to provision the tpm2 with the TC policy")
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell for provisioning the tpm")
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
        super(LCP201, self).cleanup(return_status)
        self._log.info("Copying over any policy for cleanup")
        self._os.copy_local_file_to_sut(self.IDEF_FILE_BACKUP, "/root/lcp201/ExamplePO_Sha256.iDef")
        self._copy_usb.copy_file_from_sut_to_usb(self._common_content_lib, self._common_content_configuration,
                                                 "/root/lcp201", "/" + Tpm2Drive.TPM2_FOLDER +
                                                 Tpm2Drive.TPM2_PROVISIONING_FOLDER)
        self.modify_linux_grub_file(targeted_phrase="module2 /lcp201.data", deletion=True)
        self.modify_linux_grub_file(targeted_phrase="echo \"loading lcp.data for lcp201\"", deletion=True)
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell")
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self.provision_tpm2(usb_drive_list, TpmIndices.PO, hashalg=HashAlgorithms.SHA256)
        self._ac_obj.ac_power_off(self._AC_TIMEOUT)
        self._log.debug("AC On")
        self._ac_obj.ac_power_on(self._AC_TIMEOUT)
        self._log.debug("Waiting for OS")
        self._os.wait_for_os(self._reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LCP201.main() else Framework.TEST_RESULT_FAIL)
