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
import datetime

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.dtaf_content_constants import TimeConstants
from src.lib.install_collateral import InstallCollateral
from src.provider.validation_runner_provider import ValidationRunnerProvider


class VerifyStressStabilityRunnerLinPackLinux(ContentBaseTestCase):
    """
    HPQALM ID : H82206-PI_Stress_Stability_Runner_Linpack_L
    This class to verify stress and stability after running run-linpack file
    """
    TEST_CASE_ID = ["H82206", "PI_Stress_Stability_Runner_Linpack_L"]
    COMMAND_TIME = datetime.timedelta(seconds=TimeConstants.EIGHT_HOURS_IN_SEC)
    RUN_LIN_PACK_FILE_NAME = "run-linpack.py"
    LIN_PACK_COMMAND = "python {} -t {}".format(RUN_LIN_PACK_FILE_NAME, str(COMMAND_TIME))
    XTERM = "xterm"
    APPLICATION_INSTALL_LIST = ["openssl-devel","libcurl-devel", "protobuf-devel", "mesa-libGLU.x86_64"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for VerifyStressStabilityRunnerLinPackLinux

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyStressStabilityRunnerLinPackLinux, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Cae is Only Supported on Linux")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._vr_provider = ValidationRunnerProvider.factory(test_log, cfg_opts, self.os)

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
        super(VerifyStressStabilityRunnerLinPackLinux, self).prepare()
        self._install_collateral.yum_remove(self.XTERM)
        self._vr_provider.install_validation_runner()

    def execute(self):
        """"
        This method install validation runner tool and executing and validating LinPack

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        self._log.info(" Installing required packages one by one:{}".format(self.APPLICATION_INSTALL_LIST))
        for application in self.APPLICATION_INSTALL_LIST:
            self._install_collateral.yum_install(application)
        script_path = self._vr_provider.get_runner_script_path(self.RUN_LIN_PACK_FILE_NAME)
        self._vr_provider.run_runner_script(self.LIN_PACK_COMMAND, TimeConstants.EIGHT_HOURS_IN_SEC, script_path)

        return True

    def cleanup(self, return_status):
        # Installing Xterm package as we removed the package in the test case.

        self._install_collateral.yum_install(self.XTERM)
        super(VerifyStressStabilityRunnerLinPackLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyStressStabilityRunnerLinPackLinux.main()
             else Framework.TEST_RESULT_FAIL)
