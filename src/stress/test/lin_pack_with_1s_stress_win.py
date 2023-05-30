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

from src.processor.processor_cpuinfo.processor_cpuinfo_common import ProcessorCPUInfoBase
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import TimeConstants
from src.provider.validation_runner_provider import ValidationRunnerProvider
from src.lib import content_exceptions


class VerifyStressStabilityLinPackWith1sWin(ProcessorCPUInfoBase):
    """
    HPQALM ID : H81718 
    This class to check system can pass the linPack CPU stress testing.
    """
    RUN_LIN_PACK_FILE_NAME = "run-linpack.py"
    COMMAND_TIME = datetime.timedelta(seconds=TimeConstants.EIGHT_HOURS_IN_SEC)
    NO_OF_SOCKET = 1

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for VerifyStressStabilityLinPackWith1sWin

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyStressStabilityLinPackWith1sWin, self).__init__(test_log, arguments, cfg_opts,
                                                                    eist_enable_bios_config_file=None,
                                                                    eist_disable_bios_config_file=None)

        if self.os.os_type != OperatingSystems.WINDOWS:
            raise NotImplementedError("This test case is only supported on Windows platform... Exiting..")

        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._vr_provider = ValidationRunnerProvider.factory(test_log, cfg_opts, self.os)
        self._runner_path = None

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.
        6. Install runner tool

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()

        self._log.info("Loading default bios settings")
        self.bios_util.load_bios_defaults()

        # Power cycle to make the bios settings default.
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)

        # Install validation runner tool in SUT
        self._vr_provider.install_validation_runner()

    def execute(self):
        """"
        This method install validation runner tool and run_linpack.

        :return: True or False
        :raise: if non-zero errors raise content_exceptions.TestFail
        """
        if int(self.get_cpu_info()[self._NUMBER_OF_SOCKETS]) != self.NO_OF_SOCKET:
            raise content_exceptions.TestNAError("Failed to execute on this SUT.. Expected number of socket is "
                                                 "{} but the platform has {}".format(
                self.NO_OF_SOCKET, int(self.get_cpu_info()[self._NUMBER_OF_SOCKETS])))

        self._log.info("SUT is supporting one socket")

        script_path = self._vr_provider.get_runner_script_path(self.RUN_LIN_PACK_FILE_NAME)

        self._log.info("Started executing validation runner on the SUT..")

        self._vr_provider.run_runner_script("python {} -t {}".format(script_path, str(self.COMMAND_TIME))
                                            , TimeConstants.EIGHT_HOURS_IN_SEC, cwd=None)
        return True

    def cleanup(self, return_status):
        """ DTAF cleanup"""
        super(VerifyStressStabilityLinPackWith1sWin, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyStressStabilityLinPackWith1sWin.main()
             else Framework.TEST_RESULT_FAIL)

