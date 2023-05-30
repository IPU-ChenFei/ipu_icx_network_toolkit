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

from src.processor.processor_cpuinfo.processor_cpuinfo_common import ProcessorCPUInfoBase
import src.lib.content_exceptions as content_exception


class ProcessorBootWith1S(ProcessorCPUInfoBase):
    """
    HPQC ID: H81704-PI_Processor_BootWith1S_L and H81716-PI_Processor_BootWith1S_W

    Linux:
    check CPU information by cat /proc/cpuinfo or lscpu and Check the follow options:
    the current freqcency, the max frequency, socket number, core number,logical processor,
    support,L1,L2,L3 cache size

    All other info should match the physical Processor setting.( cpuinfo or lscpu command out infomration match with
    BIOS displayed output from path EDKII Menu/Socket Configuration/processor configuration)
    The current freq should be changed with EIST enabled under BIOS setup setting  and it should equal the
    base freq if EIST disabled.All other info should match the physical Processor setting.

    Windows:
    Check tHyper-he follow options:
    the current freqcency, the max frequency, socket number, core number,logical processor, virtualization,
    V support,L1,L2,L3 cache size

    The current freq should be changed with EIST enabled under BIOS setup setting and it should equal
     the max freq if EIST disabled.
    All other info should match the physical Processor setting.
    """
    TEST_CASE_ID = ["H81704","PI_Processor_BootWith1S_L", "H81716","PI_Processor_BootWith1S_W"]
    _EIST_DISABLE_BIOS_CONFIG_FILE = "disable_eist_bios_knob.cfg"
    _EIST_ENABLE_BIOS_CONFIG_FILE = "enable_eist_bios_knob.cfg"
    _EXPECTED_NUMBER_OF_SOCKETS = 1

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  ProcessorBootWith1S object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(ProcessorBootWith1S, self).__init__(test_log, arguments, cfg_opts,
                                                  self._EIST_ENABLE_BIOS_CONFIG_FILE,
                                                  self._EIST_DISABLE_BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """

        super(ProcessorBootWith1S, self).prepare()

    def execute(self):
        """
        1. Verify whether the system supports single socket.
        2. Verify the processor cpu information

        :return: True if test completed successfully, False otherwise.
        :raise: content_exception.TestFail
        """

        if int(self.get_cpu_info()[self._NUMBER_OF_SOCKETS]) != self._EXPECTED_NUMBER_OF_SOCKETS:
            raise content_exception.TestFail("Failed to execute the test case on this SUT because we would need "
                                             "single socket on the platform..")
        self._log.info("Successfully verified that SUT is supporting single socket...")

        return self.verify_processor_cpu_info()


if __name__ == '__main__':
    test_result = ProcessorBootWith1S.main()
    sys.exit(Framework.TEST_RESULT_PASS if test_result else Framework.TEST_RESULT_FAIL)
