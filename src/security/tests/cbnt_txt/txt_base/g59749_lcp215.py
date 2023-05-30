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
from src.security.tests.cbnt_txt.txt_constants import TpmIndices, Tpm2Drive
from src.lib.bios_util import BootOptions


class LCP215(TxtBaseTest):
    """
    Glasgow ID : 59749

    This test case tests LCP215 with a provisioned PO index with 1 TPM2 empty list.
    Checks SINIT ACM Version, and ensures the lcp policy minver is larger than that. The system should fail to boot
    trusted.
    1.Ensure that the system is in sync with the latest BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.


    """
    PATH_TO_GRUB_FILE = "/boot/efi/EFI/redhat/"
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    PRIVATE_KEY = "privkey3072.pem"
    PUBLIC_KEY = "pubkey3072.pem"
    LAST_IMAGE_IN_GRUB = "x86_64.img"
    LCP215 = os.getcwd() + "\\lcp215.pol"
    IDEF_FILE = os.getcwd() + "\\ExamplePO_Sha256.iDef"
    IDEF_FILE_BACKUP = os.getcwd() + "\\ExamplePO_Sha256.iDef.bak"
    OS_DRIVE = "FS0:"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of LCP215

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(LCP215, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

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
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell when attempting to provision TPM")
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        sinit_acm_version = self.get_sinit_ACM_minver(usb_drive_list)
        if sinit_acm_version is -1:
            content_exceptions.TestError("Could not find sinit acm version")
        self._log.debug("AC Off")
        self._ac_obj.ac_power_off(self._AC_TIMEOUT)
        self._log.debug("AC On")
        self._ac_obj.ac_power_on(self._AC_TIMEOUT)
        self._log.debug("Waiting for OS")
        self._os.wait_for_os(self._reboot_timeout)
        above_sinit_acm_version_hex = hex(int(sinit_acm_version, 16) + 1)
        self.create_lcp2_list(out="lcp215.list", elements=[], sig_alg=None, list_ver=self.platform_family)
        self.create_policy(cbnt_product_version=self.platform_family, pol="lcp215.pol", data="lcp215.data",
                           lcp2_lists=["lcp215.list"], masks=[HashAlgorithms.SHA1, HashAlgorithms.SHA256],
                           policy_type='list', ctrl='2', rev='2', alg=HashAlgorithms.SHA256,
                           min_ver=str(above_sinit_acm_version_hex), sign="rsa-3072-sha256")
        self._os.execute("cp lcp215.data /boot/", self._command_timeout)
        self._os.copy_file_from_sut_to_local("/root/lcp215.pol", self.LCP215)
        path_to_idef = self._copy_usb.copy_file_from_usb_to_sut(self._common_content_lib,
                                                                self._common_content_configuration,
                                                                Tpm2Drive.TPM2_FOLDER +
                                                                Tpm2Drive.TPM2_PROVISIONING_FOLDER) + \
            "/ExamplePO_Sha256.iDef.bak"
        self._os.copy_file_from_sut_to_local(path_to_idef, self.IDEF_FILE_BACKUP)
        self.modify_linux_grub_file(self.LAST_IMAGE_IN_GRUB, False,
                                    new_phase="module2 /lcp215.data")
        self._log.debug("Backing up grub file as grub_file_before_neg.cfg")
        self._os.execute("cp " + self._GRUB_CONFIG_FILE_PATH + " " + self.PATH_TO_GRUB_FILE + "grub_file_before_neg.cfg"
                         , self._command_timeout)
        self.modify_linux_grub_file(self.LAST_IMAGE_IN_GRUB, False,
                                    new_phase="echo \"loading lcp.data for lcp215\"")
        self.generate_file_for_tpm2_provisioning(self.LCP215,
                                                 self.IDEF_FILE_BACKUP,
                                                 self.IDEF_FILE)
        self._os.execute("mkdir lcp215", self._command_timeout)
        self._os.copy_local_file_to_sut(self.IDEF_FILE, "/root/lcp215/ExamplePO_Sha256.idef")
        self._os.copy_local_file_to_sut(self.IDEF_FILE, "/root/lcp215/lcp215.idef")
        self._copy_usb.copy_file_from_sut_to_usb(self._common_content_lib, self._common_content_configuration,
                                                 "/root/lcp215", "/" + Tpm2Drive.TPM2_FOLDER +
                                                 Tpm2Drive.TPM2_PROVISIONING_FOLDER)
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell when attempting to provision TPM")
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self.provision_tpm2(usb_drive_list, TpmIndices.PO, HashAlgorithms.SHA256)
        self._log.debug("Applying power cycle to make the SUT up")
        self._log.debug("AC Off")
        self._ac_obj.ac_power_off(self._AC_TIMEOUT)
        self._log.debug("AC On")
        self._ac_obj.ac_power_on(self._AC_TIMEOUT)
        self.boot_choice_selection(BootOptions.RHEL)
        self.boot_choice_selection(BootOptions.UEFI)
        self._log.info("System failed to boot to RHEL like expected, now booted to UEFI.")
        provision_tpm2 = "Tpm2PoProv.nsh " + HashAlgorithms.SHA256 + " example"
        for usb_drive in usb_drive_list:
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive, None)
        self._uefi_util_obj.uefi_navigate_to_usb(provision_tpm2)
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("cp -q ExamplePO_Sha256.idef.bak "
                                                                  + "ExamplePO_sha256.idef", None)
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(provision_tpm2, "Completed Successfully")
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.OS_DRIVE, None)
        self._uefi_util_obj.uefi_navigate_to_usb("grub.cfg")
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("cp -q grub_file_before_neg.cfg grub.cfg")
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
        super(LCP215, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LCP215.main() else Framework.TEST_RESULT_FAIL)
