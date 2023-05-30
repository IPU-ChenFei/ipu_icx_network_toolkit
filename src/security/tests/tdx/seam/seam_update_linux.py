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
    :Update SEAM Module (Linux):

    Update the SEAM module in the TDX OS and verify the update was successful.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from src.lib import content_exceptions


class TdxSeamUpdate(LinuxTdxBaseTest):
    """
            This recipe tests the update of SEAM module for TDX OS.

            :Scenario: With TDX enabled, boot to Linux TDX OS.  Replace the SEAM module with a new version.  Reboot the
            SUT and verify the new SEAM module is used and a TD guest can be run.

            :Prerequisite:  SUT must be configured with the latest BKC applicable for the platform and must have an
            Linux TDX SW stack installed stack.

            :Phoenix ID: https://hsdes.intel.com/appstore/article/#/22012469121

            :Test steps:

                :1: Boot to OS with TDX enabled.

                :2: Record current SEAM module version.

                :3: Update the SEAM module and SEAMLDR to BKC version.

                :4: Reboot SUT back to TDX OS.

                :5: Verify SUT can boot and SEAM module has been updated.

                :6: Launch TD guest.

            :Expected results: SUT should boot to OS with TDX enabled.  SEAM module version should have changed.  TD
            guest should boot.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        # record starting SEAM data
        self._log.info("Gathering current SEAM version information.")
        starting_seam_data = self.get_seam_version()
        self._log.debug(f"Starting SEAM data: {starting_seam_data}")

        # get paths of new SEAM package on SUT
        self._log.info("Copying new SEAM module from host path to SUT.")
        self._log.debug(f"Copying SEAM module from {self.tdx_properties[self.tdx_consts.SEAM_MODULE_PATH_HOST]} "
                        f"on host.")

        # set up where to store new seam
        seam_zip_file_name = self.tdx_properties[self.tdx_consts.SEAM_MODULE_PATH_HOST].split("/")[-1]
        seamldr_zip_file_name = self.tdx_properties[self.tdx_consts.SEAM_LOADER_UPDATE_PATH].split("/")[-1]
        directory_name = self.tdx_consts.SEAM_MODULE_PATH + seam_zip_file_name.split(".zip")[0]
        backup_directory_name = f"{self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}bak/"
        self.execute_os_cmd(f"rm -rf {directory_name}")
        self.execute_os_cmd(f"mkdir -p {directory_name}")
        for file in [self.tdx_consts.SEAM_MODULE_PATH_HOST, self.tdx_consts.SEAM_LOADER_UPDATE_PATH]:
            try:
                self.os.copy_local_file_to_sut(self.tdx_properties[file],
                                               self.tdx_consts.SEAM_MODULE_PATH)
            except IOError:
                raise content_exceptions.TestFail(f"Could not find SEAM update package.  Please verify that the zip is "
                                                  f"in the location in the content_configuration.xml file.  File "
                                                  f"must be a zip file.  Looked in {self.tdx_properties[file]}")
        seam_module_path = self.tdx_consts.SEAM_MODULE_PATH + seam_zip_file_name
        seamldr_path = self.tdx_consts.SEAM_MODULE_PATH + seamldr_zip_file_name

        # unzip seam packages from lab host
        for file in [seam_module_path, seamldr_path]:
            self._log.info(f"Decompressing new SEAM module package {file} on SUT and preparing for installation.")
            self.execute_os_cmd(f"unzip -o {file} -d {self.tdx_consts.SEAM_MODULE_PATH}")

        # copy backup binaries on SUT to backup
        self._log.info("Backing up current SEAM data.")
        self.execute_os_cmd(f"mkdir -p {backup_directory_name}")
        self._log.info(f"Moving current SEAM packages to {backup_directory_name}")
        self.execute_os_cmd(f"mv {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}* {backup_directory_name}")

        # rename binaries and move to seam directory
        self._log.info(f"Copying new binaries into {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}")
        seamldr_path = self.execute_os_cmd(f"find {self.tdx_consts.SEAM_MODULE_PATH} -name {self.tdx_consts.SEAMLDR_FILE}")
        self._log.debug(f"New seamldr path: {seamldr_path}")
        so_path = self.execute_os_cmd(f"find {self.tdx_consts.SEAM_MODULE_PATH} -name {self.tdx_consts.SO_FILE}")
        self._log.debug(f"New so file path: {so_path}")
        sigstruct_path = self.execute_os_cmd(f"find {self.tdx_consts.SEAM_MODULE_PATH} -name {self.tdx_consts.SO_SIGSTRUCT_FILE}")
        self._log.debug(f"New sigstruct path: {sigstruct_path}")

        self.execute_os_cmd(f"mv {seamldr_path} {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}{self.tdx_consts.SeamLoaderFiles.SEAMLDR_NAME}")
        self.execute_os_cmd(f"mv {so_path} {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}{self.tdx_consts.SeamLoaderFiles.SO_NAME}")
        self.execute_os_cmd(f"mv {sigstruct_path} {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}{self.tdx_consts.SeamLoaderFiles.SO_SIGSTRUCT_NAME}")

        files_exist = self.execute_os_cmd(f"ls {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}{self.tdx_consts.SeamLoaderFiles.SO_SIGSTRUCT_NAME}") != "" and \
                      self.execute_os_cmd(f"ls {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}{self.tdx_consts.SeamLoaderFiles.SEAMLDR_NAME}") != "" and \
                      self.execute_os_cmd(f"ls {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}{self.tdx_consts.SeamLoaderFiles.SO_NAME}") != ""

        if not files_exist:
            self._log.error("Missing SEAM binary.  Reverting the binaries to previous copy.")
            self.execute_os_cmd(f"mv {backup_directory_name}/* {self.tdx_consts.SEAM_FW_PATH}")
            raise content_exceptions.TestFail("New SEAM module binaries failed to be installed. Please check the "
                                              " SEAM module packages information in the content_configuration.xml "
                                              "file.")

        # reboot SUT
        self._log.info("Rebooting SUT to apply changes.")
        self.reboot_sut()

        # get SEAM version from dmesg and verify version has updated
        self._log.info("Getting new SEAM version data.")
        ending_seam_data = self.get_seam_version()
        self._log.info("Ending SEAM data: {}".format(ending_seam_data))

        try:
            if starting_seam_data == ending_seam_data:
                raise content_exceptions.TestFail("SEAM version information did not change; was a different SEAM "
                                                  "module version used for update? \n Starting SEAM version "
                                                  "information: {} \n Ending SEAM version information"
                                                  ": {}".format(starting_seam_data, ending_seam_data))
            self._log.info("SEAM version information updated. Starting SEAM version information: {} \n"
                           "Ending SEAM version information: {}".format(starting_seam_data,
                                                                        ending_seam_data))
            # boot TD guest
            self._log.info("Test booting TD guest.")
            self.launch_vm(key=0, tdvm=True)
            if not self.vm_is_alive(key=0):
                raise content_exceptions.TestFail(
                    "Could not boot TD guest after updating seam module. Check log files for "
                    "errors.")
        finally:
            # save seam binaries used for test
            self._log.debug("Saving SEAM binaries into log directory.")
            self.execute_os_cmd(f"mkdir -p {self.tdx_consts.TD_GUEST_LOG_PATH_LINUX}/seam")
            self.execute_os_cmd(f"cp {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}/* {self.tdx_consts.TD_GUEST_LOG_PATH_LINUX}/seam")
            self._log.debug("Reverting to starting SEAM version.")
            self.execute_os_cmd(f"mv -f  {backup_directory_name}/* {self.tdx_consts.SeamLoaderFiles.SEAM_FW_PATH}")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxSeamUpdate.main() else Framework.TEST_RESULT_FAIL)
