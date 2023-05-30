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
# treaty provisions0. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import os
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.mktme.mktme_common import MktmeBaseTest


class MktmeKeyAssignmentMax(MktmeBaseTest):
    """
    Glasgow ID : G59527.2
    Phoenix ID : P18014070369
    This Test case enables Bios Knobs and executes .sh files to verify the output.
    """
    TEST_CASE_ID = ["G59527.2 - MKTME Key assignment Max",
                    "P18014070369 - MKTME Key assignment Max"]
    BIOS_CONFIG_FILE_MEMORY_INTERGITY_DISABLE = "../security_tme_mktme_bios_enable.cfg"
    BIOS_CONFIG_FILE_MEMORY_INTERGITY_ENABLE = "../security_tme_mktme_intergity_enable.cfg"
    CHMOD_CMD = "chmod -R 777 %s"
    KEY_ASSIGN_LOOP_SH_FILE = "sh key_assign_loop.sh"
    SUT_FOLDER_PATH = "mktmekeyassignment"
    MKTMEKEYASSIGNMENTMAXZIPFILE = "mktmekeyassignmentmax.zip"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of MktmeKeyAssignmentMax

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        if arguments.MEMORYINTERGITY == "enable":
            test_log.info("MKTME with enabling MEMORY INTERGITY bios knob")
            self.bios_config_file_memory_intergrity_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                          self.BIOS_CONFIG_FILE_MEMORY_INTERGITY_ENABLE)
            super(MktmeKeyAssignmentMax, self).__init__(test_log, arguments, cfg_opts,
                                                        self.bios_config_file_memory_intergrity_enable)

        else:
            test_log.info("MKTME with disable MEMORY INTERGITY bios knob")
            self.bios_config_file_memory_intergrity_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                          self.BIOS_CONFIG_FILE_MEMORY_INTERGITY_DISABLE)
            super(MktmeKeyAssignmentMax, self).__init__(test_log, arguments, cfg_opts,
                                                        self.bios_config_file_memory_intergrity_disable)


    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(MktmeKeyAssignmentMax, cls).add_arguments(parser)
        parser.add_argument("-mi", "--MEMORYINTERGITY", action="store", dest="MEMORYINTERGITY",
                            default=cls.bios_config_file_memory_intergrity_enable)

    def prepare(self):
        # type: () -> None
        """
        pre-checks if the sut is alive or not.
        """
        super(MktmeKeyAssignmentMax, self).prepare()

    def execute(self):
        """
        This function copies the two files (key_assign_test_rand.sh and key_assign_loop.sh) to sut machine and
        checks for the excepted values.

        :return: False if key_assign_loop.sh output is add_key: Required key not available or keyctl retcode 1
        """
        unzip_file_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.SUT_FOLDER_PATH,
                                                                              self.MKTMEKEYASSIGNMENTMAXZIPFILE)
        self._log.info("Unzip file path {}".format(unzip_file_path))
        self.os.execute(self.CHMOD_CMD % unzip_file_path, self._command_timeout)
        output = self._common_content_lib.execute_sut_cmd(self.KEY_ASSIGN_LOOP_SH_FILE, self.KEY_ASSIGN_LOOP_SH_FILE,
                                                          self._command_timeout, cmd_path=unzip_file_path)
        self._log.info("Key assign loop file output {}".format(output))
        self.verify_mktme_key_assignment(output)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeKeyAssignmentMax.main() else Framework.TEST_RESULT_FAIL)
