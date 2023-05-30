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

from src.storage.test.storage_common import StorageCommon
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


class StorageNvmeSataFwUpdate(StorageCommon):
    """
    HPALM : H80273-PI_Storage_NVMe-SATA FW Update.
    GLASGOW ID : G56977.1-NVMe-SATA FW Update.

    Install Intel SSD DC tool to check update the FW with the latest FW
    """
    CMD_FW_SHOW = "isdct.exe show -intelssd 1"
    CMD_FW_LOAD = "isdct.exe load -force -intelssd 1"
    FW_STATUS = ["Status : The selected Intel SSD contains current firmware as of this tool release.",
                 "Status : Firmware updated successfully. Please reboot the system."]
    TEST_CASE_ID = ["H80273", "PI_Storage_NVMe-SATA FW Update", "G56977.1", "NVMe-SATA FW Update"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageNvmeSataFwUpdate object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StorageNvmeSataFwUpdate, self).__init__(test_log, arguments, cfg_opts)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.reboot_timeout = self._common_content_configuration.get_reboot_timeout()

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(StorageNvmeSataFwUpdate, self).prepare()

    def execute(self):
        """
        this method install the intel ssd data center tool and update latest the Firmware update

        :return: True or False
        :raise content_exceptions.TestFail
        """
        # installation of intel ssd data center tool
        intel_ssd_tool_path_sut = self.install_collateral.install_intel_ssd_dc_windows()

        # Display the Before FW update FirmwareUpdateAvailable information
        before_fw_update_fw_show = self._common_content_lib.execute_sut_cmd(self.CMD_FW_SHOW,
                                                                            "Display the before update Firmware "
                                                                            "Update info",
                                                                            self._command_timeout,
                                                                            cmd_path=intel_ssd_tool_path_sut)
        self._log.debug("Display the Before FW update FirmwareUpdateAvailable information in SUT:{}".format(
            before_fw_update_fw_show))
        # Update the Firmware Update in SUT
        fw_update = self.os.execute(self.CMD_FW_LOAD, self._command_timeout, intel_ssd_tool_path_sut)
        self._log.debug("Update the FirmwareUpdate Status in SUT:{}".format(fw_update.stdout))
        status_flag = False
        for line in fw_update.stdout.split("\n"):
            if line.strip() in self.FW_STATUS:
                status_flag = True
                break
        if not status_flag:
            raise content_exceptions.TestFail("Failed the Firmware Update")

        # Performs restart the SUT
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)

        # Display the after FW update FirmwareUpdateAvailable information
        after_fw_update_fw_show = self._common_content_lib.execute_sut_cmd(self.CMD_FW_SHOW,
                                                                           "Display the after update Firmware Update "
                                                                           "info",
                                                                           self._command_timeout,
                                                                           cmd_path=intel_ssd_tool_path_sut)
        self._log.debug(" Display the after FW update FirmwareUpdateAvailable information in SUT:{}".format(
                        after_fw_update_fw_show))

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageNvmeSataFwUpdate.main() else Framework.TEST_RESULT_FAIL)
