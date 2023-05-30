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
    :Trusted Boot Interop with TDX and TXT:

    With a trusted boot, boot a TD guest successfully.
"""

import sys
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.workloads.TDX049_launch_tdvm_mprime import TDGuestMprime
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.cbnt_txt.txt_constants import ArtifactoryToolPaths
from src.lib.grub_util import GrubUtil
from src.lib.uefi_util import UefiUtil
from src.lib.os_lib import LinuxCommonLib
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.provider_factory import ProviderFactory


class TdxTrustedBoot(TDGuestMprime):
    """
            This recipe enables TXT and TDX together and verifies a TD guest can launch within a trusted MLE with tboot.

            :Scenario: Enable TXT and boot to a trusted MLE with tboot.  Then launch defined number of TD guests (per
            <NUM_OF_VMS> param in content_configuration.xml) Run workload on TD guest and verify there are no MCEs.

            :Phoenix ID: https://hsdes.intel.com/appstore/article/#/18014074009

            :Test steps:

                :1:  Enable TXT on SUT and boot to trusted MLE

                :2:  Enable TDX and boot to OS.

                :3:  Launch a TD guest.

                :4:  Run mprime on TD guest.

            :Expected results: TD guest should boot and should not yield MCEs.

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
        super(TdxTrustedBoot, self).__init__(test_log, arguments, cfg_opts)
        self.tdx_properties[self.tdx_consts.SMX_ENABLE] = True  # must have SMX enabled for TXT
        self.tdx_properties[self.tdx_consts.BIOS_SEAM_ENABLE] = True  # must use BIOS SEAMLDR
        self.tdx_properties[self.tdx_consts.DAM_ENABLE] = True  # must enable ITP for TXT registers
        self.txt = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        uefi_cfg = cfg_opts.find('suts/sut/providers/uefi_shell')
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider
        self.uefi = UefiUtil(self._log, self._uefi_obj, self._bios_boot_menu_obj, self.ac_power,
                             self._common_content_configuration, self.os, cfg_opts=self._cfg)
        self.tboot_index = None
        self.grub_obj = GrubUtil(self._log, self._common_content_configuration, self._common_content_lib)
        self.default_index = self.grub_obj.get_grub_boot_index().strip()
        self.linux_lib = LinuxCommonLib(test_log, self.os)
        self.artifactory_consts = ArtifactoryToolPaths
        self.tpm_prov_path = self.artifactory_consts.TPM2PROVTOOLS.value
        self.uefi_drive = None

    def prepare(self) -> None:
        temp_location = "/tmp/"
        efi_partition = "/boot/efi/"
        self.os_preparation()  # verify python soft link is installed
        for tool in self.artifactory_consts:
            path = self._artifactory_obj.download_tool_to_automation_tool_folder(tool.value)
            self.os.copy_local_file_to_sut(path, temp_location)  # stage TPM provisioning tools to /boot/efi
            self.execute_os_cmd(f"unzip -o {temp_location}{tool.value} -d {efi_partition}")
        uuid = self.linux_lib.get_uuid(efi_partition)
        self.uefi.enter_uefi_shell()  # boot to UEFI shell
        self.uefi_drive = self.uefi.get_uefi_path_for_disk(uuid)
        self.txt.verify_sha256_and_provision_tpm(self.uefi_drive)  # provision PO and Aux indices
        self.perform_graceful_g3()  # boot back to OS
        self._log.debug("Installing tboot.")
        self.txt.install_tboot_mercurial()
        self.tboot_index = self.txt.get_tboot_boot_position()  # bet the tboot index from grub menu entry
        self.txt.set_default_boot_entry(self.tboot_index)  # set tboot as default boot
        self._log.debug("Setting TXT knobs.")
        self.txt.enable_and_verify_bios_knob()  # enable and verify bios knobs
        self._log.debug("Running TDX mprime prepare.")
        super(TdxTrustedBoot, self).prepare()

    def execute(self) -> bool:
        if self.txt.validate_linux_mle():
            self._log.debug("Successfully completed trusted boot, starting TD guest and workload.")
            return super(TdxTrustedBoot, self).execute()
        raise content_exceptions.TestFail("Failed to boot trusted.")

    def cleanup(self, return_status: bool):
        super(TdxTrustedBoot, self).cleanup(return_status)
        self.grub_obj.set_grub_boot_index(self.default_index)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxTrustedBoot.main() else Framework.TEST_RESULT_FAIL)
