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
import re
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions


class RdtMBA2Base(ContentBaseTestCase):
    """
    This class contains RDT base functions for RDT MBA2.0 test cases.
    """

    SCRIPT_NAME = "case{}.py"
    SUT_SCRIPT_PATH = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtBase

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(RdtMBA2Base, self).__init__(test_log, arguments, cfg_opts)
        self.script_no = arguments.script_no
        self.SCRIPT_NAME = self.SCRIPT_NAME.format(self.script_no)

    @classmethod
    def add_arguments(cls, parser):
        super(RdtMBA2Base, cls).add_arguments(parser)

        parser.add_argument('--script_no', action="store", dest="script_no", type=str, default="",
                            help='script no which will be used for the MBA2.0 script run')

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        # super(RdtMBA2Base, self).prepare()
        # SUT path of the script

        self._log.info("start")
        # HOST path of the script
        script_folder_path = Path(os.path.abspath(__file__)).parents[1]
        script_file_host_path = os.path.join(script_folder_path, "Scripts")
        self._log.info("Complete Script file path on HOST : {}".format(script_file_host_path))
        # copy the scripts' folder to SUT
        files = [f for f in os.listdir(script_file_host_path) if os.path.isfile(os.path.join(script_file_host_path, f))]
        for file in files:
            cmp_file_path = os.path.join(script_file_host_path, file)
            self.os.copy_local_file_to_sut(cmp_file_path, "/root")
        self.SUT_SCRIPT_PATH = "/root/" + self.SCRIPT_NAME
        self._log.info("Successfully copied the script to SUT under : {}".format(self.SUT_SCRIPT_PATH))

    def execute(self):  # type: () -> bool
        """
        This method would execute the RDT script on the SUT

        :return: True on success
        """
        # Execute the script on SUT & Capture th resultsx
        self._log.info("*********** Execution starts for script {} **************".format(self.SCRIPT_NAME))
        result = self.os.execute("python {}".format(self.SUT_SCRIPT_PATH), 16000)
        self._log.info("STDOUT of the script : \n {}".format(result.stdout))
        self._log.error("STDERR of the script : \n {}".format(result.stderr))
        self._log.info("*********** Execution completed for script {} ************".format(self.SCRIPT_NAME))
        if result.cmd_failed():
            err_msg = "Execution for script {} failed due to :\n {}".format(self.SCRIPT_NAME, result.stderr)
            self._log.error(err_msg)
            raise content_exceptions.TestFail(err_msg)
        # checking the output of the script NO of Pass and Fail
        try:
            result_pass_fail_data = re.findall("Number of tests:.*", result.stdout)
            result_fail_count_data = re.findall(r"Failed:.\s\d+", result_pass_fail_data[0])
            no_of_failures_count = result_fail_count_data[0].split(":")[1].strip()
            if int(no_of_failures_count) != 0:
                raise content_exceptions.TestFail("Script execution failed as No of Failure count is: {}"
                                                  .format(no_of_failures_count))
        except Exception as ex:
            raise content_exceptions.TestFail("Exception occurred while parsing the Script Pass Fail data due to {}"
                                              .format(ex))
        self._log.info("Successfully executed the {} script".format(self.SCRIPT_NAME))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMBA2Base.main()
             else Framework.TEST_RESULT_FAIL)
