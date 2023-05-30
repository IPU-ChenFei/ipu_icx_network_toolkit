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
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.processor.processor_cpuinfo.processor_cpuinfo_common import ProcessorCPUInfoBase
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import TimeConstants, LinPackToolConstant
from src.provider.validation_runner_provider import ValidationRunnerProvider
from src.lib import content_exceptions


class VerifyStressStabilityLinPackWith1sLinux(ProcessorCPUInfoBase):
    """
    HPQALM ID : H81706-PI_Processor_LinPackWith1S_Stress_L
    This class to check system can pass the linPack CPU stress testing.
    """
    TEST_CASE_ID = ["H81706-PI_Processor_LinPackWith1S_Stress_L"]
    EIST_DISABLE_BIOS_CONFIG_FILE = "disable_eist_bios_knob.cfg"
    EIST_ENABLE_BIOS_CONFIG_FILE = "enable_eist_bios_knob.cfg"
    COMMAND_TIME = datetime.timedelta(seconds=TimeConstants.EIGHT_HOURS_IN_SEC)
    RUN_LIN_PACK_FILE_NAME = "run-linpack.py"
    SET_RUNNER_CONFIG_COMMAND = "python set-runnerconfig.py"
    SET_SYSTEM_CONFIG = "python set-systemconfig.py"
    LIN_PACK_COMMAND = "python {} -t {}".format(RUN_LIN_PACK_FILE_NAME, str(COMMAND_TIME))
    XTERM = "xterm"
    NO_OF_SOCKET = 1
    COMMAND_TO_UPDATE_CONFIG_FILE = ["sed 's/export MPI_PROC_NUM=4/export MPI_PROC_NUM=1/g' runme_intel64 > "
                                     "runme_intel64.org ; mv -f runme_intel64.org runme_intel64; "
                                     "chmod +777 runme_intel64",
                                     "sed 's/export MPI_PER_NODE=4/export MPI_PER_NODE=1/g' runme_intel64 > "
                                     "runme_intel64.org ; mv -f runme_intel64.org runme_intel64; "
                                     "chmod +777 runme_intel64",
                                     "sed 's/export NUMMIC=1/export NUMMIC=0/g' runme_intel64 > "
                                     "runme_intel64.org ; mv -f runme_intel64.org runme_intel64; "
                                     "chmod +777 runme_intel64"
                                     ]
    COMMAND_TO_EXECUTE_FOR_AVX2 = "echo always > /sys/kernel/mm/transparent_hugepage/enabled;" \
                                        "source /opt/intel/impi/2018.1.163/bin64/mpivars.sh intel64;" \
                                        "export HPL_HOST_ARCH=3;./runme_intel64 -n {} -p 1 -q 1 -b 192"
    COMMAND_TO_EXECUTE_FOR_AVX3 = "echo always > /sys/kernel/mm/transparent_hugepage/enabled;" \
                                        "source /opt/intel/impi/2018.1.163/bin64/mpivars.sh intel64;" \
                                        "export HPL_HOST_ARCH=9;./runme_intel64 -n {} -p 1 -q 1 -b 384"
    VALIDATION_SIGNATURE = " PASSED"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for VerifyStressStabilityLinPackWith1sLinux

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyStressStabilityLinPackWith1sLinux, self).__init__(test_log, arguments, cfg_opts,
                                                                      self.EIST_ENABLE_BIOS_CONFIG_FILE,
                                                                      self.EIST_DISABLE_BIOS_CONFIG_FILE)
        self._cfg = cfg_opts
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._vr_provider = ValidationRunnerProvider.factory(test_log, cfg_opts, self.os)
        self._number_of_cycle = self._common_content_configuration.get_no_of_cycles_to_execute_linpack()

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
        super(VerifyStressStabilityLinPackWith1sLinux, self).prepare()
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Cae is Only Supported on Linux")

        if self._common_content_lib.get_platform_family() == ProductFamilies.SPR:
            self.sut_folder_path = self._install_collateral.install_linpack_mpi()
        else:
            self._install_collateral.yum_remove(self.XTERM)
            self._vr_provider.install_validation_runner()

    def execute_linpack_avx(self, cmd_path):
        """
        This method is to execute LinPack Test for EGS
        """
        for each_change in self.COMMAND_TO_UPDATE_CONFIG_FILE:
            self._common_content_lib.execute_sut_cmd(sut_cmd=each_change, cmd_str=each_change, execute_timeout=
            self._command_timeout, cmd_path=cmd_path+LinPackToolConstant.path_to_change_config_file)

        # execute linpack avx2 test
        cmd_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd=self.COMMAND_TO_EXECUTE_FOR_AVX2.format(
            self._number_of_cycle), cmd_str=self.COMMAND_TO_EXECUTE_FOR_AVX3.format(self._number_of_cycle),
                                                               execute_timeout=self._command_timeout*3, cmd_path=
                                                               cmd_path + LinPackToolConstant.path_to_change_config_file
                                                               )
        self._log.info("Out put for AVX2: {}".format(cmd_out_put))
        if not self.VALIDATION_SIGNATURE in cmd_out_put:
            raise content_exceptions.TestFail("Test is Failed for AVX2")
        self._log.info("Test is passed for AVX2")

        # execute linpack avx3 test
        cmd_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd=self.COMMAND_TO_EXECUTE_FOR_AVX3.format(
            self._number_of_cycle), cmd_str=self.COMMAND_TO_EXECUTE_FOR_AVX3.format(self._number_of_cycle),
                                                               execute_timeout=self._command_timeout*3, cmd_path=
                                                               cmd_path + LinPackToolConstant.path_to_change_config_file
                                                               )
        self._log.info("Out put for AVX3: {}".format(cmd_out_put))
        if not self.VALIDATION_SIGNATURE in cmd_out_put:
            raise content_exceptions.TestFail("Test is Failed for AVX3")
        self._log.info("Test is passed for AVX3")

    def execute(self):
        """"
        This method install validation runner tool and execute set_runner_config, set_system_config,
        run_linpack.

        :return: True or False
        :raise: if non-zero errors raise content_exceptions.TestFail
        """
        if int(self.get_cpu_info()[self._NUMBER_OF_SOCKETS]) != self.NO_OF_SOCKET:
            raise content_exceptions.TestNAError("Failed to execute on this SUT because of unexpected number of socket")
        self._log.info("SUT is supporting one socket")
        if self._common_content_lib.get_platform_family() == ProductFamilies.SPR:
            # calling method to execute linpack test on EGS
            self.execute_linpack_avx(self.sut_folder_path)
        else:
            script_path = self._vr_provider.get_runner_script_path(self.RUN_LIN_PACK_FILE_NAME)
            self._vr_provider.run_runner_script(self.SET_RUNNER_CONFIG_COMMAND, self._command_timeout, script_path)
            self._vr_provider.run_runner_script(self.SET_SYSTEM_CONFIG, self._command_timeout, script_path)

            self._vr_provider.run_runner_script(self.LIN_PACK_COMMAND, TimeConstants.EIGHT_HOURS_IN_SEC, script_path)

        return True

    def cleanup(self, return_status):
        # Installing Xterm package as we removed the package in the test case.
        self._install_collateral.yum_install(self.XTERM)
        super(VerifyStressStabilityLinPackWith1sLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyStressStabilityLinPackWith1sLinux.main()
             else Framework.TEST_RESULT_FAIL)

