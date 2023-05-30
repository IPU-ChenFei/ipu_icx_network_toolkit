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
import re

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.storage_provider import StorageProvider
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.lib import content_exceptions


class BonnieFioStressTestOnLinuxSUT(ContentBaseTestCase):
    """
    HPQALM ID : H82229-PI_Stress_Bonnie_FIO_L
    This class is to Test the SUT is stable or not after the bonnie and fio stress.
    """
    TEST_CASE_ID = ["H82229", "PI_Stress_Bonnie_FIO_L"]
    REGEX_TO_VALIDATE_FIO_OUTPUT = r'\serr=\s0'
    FIO_CMD = r'fio -filename=/dev/sda3 -direct=1 -iodepth 1 -thread -rw=randrw -rwmixread=70 -ioengine=psync -bs=4k ' \
              r'-size=300G -numjobs=50 -runtime=180 -group_reporting -name=randrw_70read_4k'
    BONNIE_CMD = r'./bonnie++ -d {} -s 1000 -r 500 -u root'
    MOUNT_POINT = ""

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for BonnieFioStressTestOnLinuxSUT

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(BonnieFioStressTestOnLinuxSUT, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Cae is Only Supported on Linux")
        self._usb_obj = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self.os)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._storage_provider = StorageProvider.factory(test_log, self.os, execution_env="os", cfg_opts=cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.
        6. Uninstalling xterm

        :return: None
        """
        super(BonnieFioStressTestOnLinuxSUT, self).prepare()
        self.execute_bonnie()

    def execute_bonnie(self):
        """
        This method is to install and execute the bonnie command.

        :raise content_exception
        """
        try:
            self._log.info("Mount the USB storage")
            mount_point = self._usb_obj.get_mount_point(self._common_content_lib, self._common_content_configuration)
            self._log.debug("Mount device : {} and Mount Point : {}".format(mount_point, self._usb_obj.USB_FILE_PATH))
            self._log.debug("Install the bonnie stress tool to SUT")
            bonnie_install_path = self._install_collateral.install_bonnie_to_sut()
            self._log.debug('Execute the bonnie command')
            result_output = self._common_content_lib.execute_sut_cmd(
                sut_cmd=self.BONNIE_CMD.format(self._usb_obj.USB_FILE_PATH.strip()),
                cmd_str=self.BONNIE_CMD.format(self._usb_obj.USB_FILE_PATH.strip()),
                execute_timeout=self._command_timeout, cmd_path=bonnie_install_path.strip())
            self._log.debug(result_output)
            self._log.info("Successfully Executed Bonnie Tool")
        except Exception as ex:
            raise content_exceptions.TestFail(ex)

    def execute(self):
        """"
        This method install fio tool and validate the fio log out put

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        self._install_collateral.install_fio(install_fio_package=True)
        self._log.info('Execute the fio command...')
        fio_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.FIO_CMD, cmd_str=self.FIO_CMD,
                                                                  execute_timeout=self._command_timeout)
        self._log.info("Fio tool command out put : {}".format(fio_cmd_output.strip()))
        reg_output = re.findall(self.REGEX_TO_VALIDATE_FIO_OUTPUT, fio_cmd_output.strip())
        if len(reg_output) == 0:
            raise content_exceptions.TestFail("Un-Expected Error Captured in Fio Output Log")
        self._log.info("No Error Found in Log as Expected")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BonnieFioStressTestOnLinuxSUT.main()
             else Framework.TEST_RESULT_FAIL)
