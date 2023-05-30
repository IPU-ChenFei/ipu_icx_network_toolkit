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
import os
import sys
import socket
import re
from shutil import copy

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.dtaf_content_constants import TimeConstants, DynamoToolConstants, IOmeterToolConstants
from src.lib.content_base_test_case import ContentBaseTestCase
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


class StorageIOStressLinux(ContentBaseTestCase):
    """
    HPQC : H80242-PI_Storage_IOStress_L
    Drive stress IO on all the drives for one hour:
    1. Prepare a Windows OS host and install IOMeter tool, connect it LAN as target Linux SUT;
    2. Copy Dynamo tool into Linux target SUT and run ./dyname -i host_IP_address -m target_IP_address;
    3. On Windows Host system, run 'iometer -t xxx' under cmd shell (xxx is time number);

    """
    TEST_CASE_ID = ["H80242", "PI_Storage_IOStress_L"]
    CMD_FDISK = 'fdisk -l'
    IP_ADDRESS_SUT = "ip route get 1.2.3.4 | awk '{print $7}'"
    ROOT_PATH = "/root"
    SATA_DISK_INFO_REGEX = ".*\/dev\/sda:\s(\S+.\S+)"
    NVME_DISK_INFO_REGEX = ".*\/dev\/nvme0n1:\s(\S+.\S+)"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageIOStressLinux object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StorageIOStressLinux, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test is Supported only on Linux")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        """
        # type: () -> None
        Executing the prepare.
        """
        super(StorageIOStressLinux, self).prepare()

    def execute(self):
        """
        1. Copy Dynamo tool into Linux target SUT and run EXECUTE_DYNAMO_METER_CMD
        2. Run iometer.reg file in Host machine to accept Intel Open Source License.
        3. On Windows Host system, run EXECUTE_IOMETER_CMD

        :return: True or False
        :raise: content_exceptions.TestFail
        """
        fdisk_info = self._common_content_lib.execute_sut_cmd(self.CMD_FDISK, self.CMD_FDISK, self._command_timeout,
                                                              self.ROOT_PATH)
        self._log.debug("Disk information:{}".format(fdisk_info))
        # Check SATA DISK Details
        sata_disk_info = re.findall(self.SATA_DISK_INFO_REGEX, fdisk_info)
        self._log.debug("Disk /dev/sda size is : {}".format(sata_disk_info))
        # Check NVMe DISK Details
        nvme_disk_info = re.findall(self.NVME_DISK_INFO_REGEX, fdisk_info)
        self._log.debug("Disk /dev/nvme0n1 size is : {}".format(nvme_disk_info))

        if not sata_disk_info and not nvme_disk_info:
            raise content_exceptions.TestFail("Failed to verify disk information in {}".format(self.CMD_FDISK))
        # Copy Dynamo meter to sut
        sut_folder_path = self._install_collateral.install_dynamo_tool_linux()
        # Getting the HOST IP
        hostname = socket.gethostname()
        host_ip = socket.gethostbyname(hostname)
        self._log.debug("HOST IP:{}".format(host_ip))
        # Getting the SUT IP
        sut_ip = self._common_content_lib.execute_sut_cmd(self.IP_ADDRESS_SUT, self.IP_ADDRESS_SUT,
                                                          TimeConstants.FIFTEEN_IN_SEC, self.ROOT_PATH)
        self._log.debug("SUT IP:{}".format(sut_ip))
        # executing dynamo cmd in the sut
        self.os.execute_async( DynamoToolConstants.EXECUTE_DYNAMO_METER_CMD.format(host_ip, sut_ip), sut_folder_path)

        iometer_tool_path = os.path.join(self._common_content_lib.get_collateral_path(),
                                         IOmeterToolConstants.IOMETER_TOOL_FOLDER)
        bkc_config_file_path = self._common_content_configuration.get_iometer_tool_config_file()
        copy(bkc_config_file_path, iometer_tool_path)
        # Executing import iometer.reg command
        reg_output = self._common_content_lib.execute_cmd_on_host(IOmeterToolConstants.REG_CMD, iometer_tool_path)
        self._log.debug("Successfully run iometer org file: {}".format(reg_output))
        # Executing IOMETER Tool on host
        self._log.info("Executing iometer command:{}".format(IOmeterToolConstants.EXECUTE_IOMETER_CMD))
        io_output = self._common_content_lib.execute_cmd_on_host(IOmeterToolConstants.EXECUTE_IOMETER_CMD,
                                                                 iometer_tool_path)
        self._log.debug("Successfully run iometer tool: \n{}".format(io_output))
        return True

    def cleanup(self, return_status):
        """
        # type: (bool) -> None
        Executing the cleanup.
        """
        super(StorageIOStressLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageIOStressLinux.main() else Framework.TEST_RESULT_FAIL)
