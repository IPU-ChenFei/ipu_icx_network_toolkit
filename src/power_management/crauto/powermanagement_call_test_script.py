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
import subprocess
import ipccli
from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions


class PowerManagementCallTest(ContentBaseTestCase):
    """
    phoenix IDs : 18016910205, 18016910039, 18016910125, 18016910130
                18016909855, 18016910135, 18016910143, 18016910207,
                18016910214, 18016910041, 18016910127, 18016909857,
                18016909864, 18016909866.

    The purpose of this Test Case is to call the CR Automaton Power Management ISS/Non- ISS Test Cases.
    """

    _BIOS_CONFIG_FILE = "powermanagement_iss.cfg"
    GENERATE_CPU_JSON_DATA_SCRIPT = r"cpu_json_data.py"
    xpiv_iss_path = r"c:/pythonsv/sapphirerapids/users/cr_tools/release/xpiv_iss"
    crowvalley_path = r"c:/pythonsv/crowvalley/crautomation/release"
    peci_path = r"c:/pythonsv/sapphirerapids/users/cr_tools/release/peci"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PowerManagementCallTest object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self.cmd = None
        self.iss_str = arguments.icp
        self.file_path = arguments.crauto_pypath
        self.test_name = arguments.test
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._BIOS_CONFIG_FILE)
        test_log.debug("Bios config file: %s", self.bios_config_file)

        super(PowerManagementCallTest, self).__init__(test_log, arguments, cfg_opts,
                                                      bios_config_file_path=self.bios_config_file)
        self._silicon_family = self._common_content_lib.get_platform_family()

    @classmethod
    def add_arguments(cls, parser):
        super(PowerManagementCallTest, cls).add_arguments(parser)

        parser.add_argument('--crauto_pypath', action="store", dest="crauto_pypath", type=str, default="", help='file name')
        parser.add_argument('-i', '--icp', help='modules from iss, crw, peci', default="", dest="icp", type=str)
        parser.add_argument('--test', help='test name', action="store", default="", dest="test", type=str)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PowerManagementCallTest, self).prepare()

    def execute(self):
        """
        Execution
        """
        try:
            python_exe_path = self._common_content_lib.get_python_path()

            if self.iss_str.lower() == 'iss':
                os.chdir(self.xpiv_iss_path)
                self.cmd = python_exe_path + " {}".format(self.file_path)
            elif self.iss_str.lower() == 'crw':
                os.chdir(self.crowvalley_path)
                self.cmd = python_exe_path + " {} --skipallchecks --disable_telemetry --username=root --password=password " \
                                             "--skipspdchecks --test {}".format(self.file_path, self.test_name)
            elif self.iss_str.lower() == 'peci':
                os.chdir(self.peci_path)
                self.cmd = python_exe_path + " {}".format(self.GENERATE_CPU_JSON_DATA_SCRIPT)
                itp = ipccli.baseaccess()
                itp.unlock()
                process = subprocess.run(self.cmd, shell=True,
                                         universal_newlines=True, input="yes")
                if not process.returncode:
                    print(process.stdout)
                    self.cmd = python_exe_path + " {}".format(self.file_path)
                    peci_process = subprocess.run(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                                  universal_newlines=True)
                    if not peci_process.returncode:
                        print(peci_process.stdout)
                        return True
                    else:
                        print(peci_process.stderr)
                        return False
                else:
                    print(process.stderr)
                    return False

            else:
                raise content_exceptions.TestError("Module not Found. Please verify the argument icp from the list ISS, "
                                                   "crowvalley, peci")

            process = subprocess.run(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                     universal_newlines=True)
            if not process.returncode:
                print(process.stdout)
                return True
            else:
                print(process.stderr)
                return False
        except Exception as ex:
            content_exceptions.TestFail("Filed due to {}".format(ex))


    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PowerManagementCallTest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementCallTest.main() else Framework.TEST_RESULT_FAIL)


