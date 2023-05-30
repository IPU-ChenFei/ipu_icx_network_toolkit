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
from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.cbnt_txt.txt_base.g58253_lcp202 import LCP202SHA1MLE
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.cbnt_constants import HashAlgorithms
from src.security.tests.cbnt_txt.txt_constants import TpmIndices, Tpm2Drive


class LCP219(TxtBaseTest):
    """
    Glasgow ID : 68782

    This test case tests LCP219 with a provisioned PO index with 1 TPM2 list of: RSA-3072-SHA256, SHA1 MLE ELEMENT. Then
    clears index of policy.
    1.Ensure that the system is in sync with the latest BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.
    """
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    TPM2_PCR_FOLDER = "/TPM_PCR_Tools"
    LAST_IMAGE_IN_GRUB = "x86_64.img"
    DEFAULT_NV_INDEX = "0x01C10106"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of LCP204

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(LCP219, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._lcp202 = LCP202SHA1MLE(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        Validating the system has TXT enabled and can boot to tboot without a policy provisioned
        :return:
        """
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob
        self._os.reboot(self._reboot_timeout)
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

    def execute(self):  # type: () -> bool
        """
        1. Creates policy using tboot lcp tools and stores policy on usb
        2. Generates appropriate index definition file for provisioning
        3. Generates PCRs for PCONF element
        3. Provisions TPM2 and writes location of data file into grub.cfg file
        :return: True if SUT boots trusted after provisioning, False if it cannot boot trusted
        """
        self._lcp202.execute()
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell to generate pcr list")
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self.clear_po_index_tpm2(usb_drive_list)
        return self.check_cleared_po_index_tpm2(usb_drive_list, self.DEFAULT_NV_INDEX)

    def cleanup(self, return_status):  # type: (bool) -> None
        super(LCP219, self).cleanup(return_status)
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
    sys.exit(Framework.TEST_RESULT_PASS if LCP219.main() else Framework.TEST_RESULT_FAIL)



