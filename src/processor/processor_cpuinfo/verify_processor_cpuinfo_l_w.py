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


class VerifyProcessorCPUInfo(ProcessorCPUInfoBase):
    """
    HPALM : H79586-PI_Processor_CPUInfo_W
    HPQC ID: 80052 (Linux), 72512 (Windows) and 79586 (Windows)
    LINUX TC:
    check CPU information by cat /proc/cpuinfo or lscpu and Check the follow options:
      the current freqcency, the max frequency, socket number, core number,logical processor,
      virtualization,Hyper-V support,L1,L2,L3 cache size

    All other info should match the physical Processor setting.( cpuinfo or lscpu command out infomration match with
    BIOS displayed output from path EDKII Menu\Socket Configuration\processor configuration)
    The current freq should be changed with EIST enabled under BIOS setup setting  and it should equal the
    base freq if EIST disabled.All other info should match the physical Processor setting.

    Brand string is only populated properly on QS/Revenue material.

    WINDOWS TC:
    Open task manager and select performace bar, then click CPU item.
    Check the follow options:
      the current freqcency, the max frequency, socket number, core number,logical processor, virtualization,
      Hyper-V support,L1,L2,L3 cache size

    The current freq should be changed with EIST enabled under BIOS setup setting  and
    it should equal the max freq if EIST disabled.
    All other info should match the physical Processor setting.
    Brand string is only populated properly on QS/Revenue material.

    """
    TEST_CASE_ID = ["H79586,PI_Processor_CPUInfo_W"]
    _EIST_DISABLE_BIOS_CONFIG_FILE = "disable_eist_bios_knob.cfg"
    _EIST_ENABLE_BIOS_CONFIG_FILE = "enable_eist_bios_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  VerifyProcessorCPUInfo object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyProcessorCPUInfo, self).__init__(test_log, arguments, cfg_opts, self._EIST_ENABLE_BIOS_CONFIG_FILE,
                                                     self._EIST_DISABLE_BIOS_CONFIG_FILE)

    def prepare(self):
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(VerifyProcessorCPUInfo, self).prepare()

    def execute(self):
        """
        Execute Main test case.

        :return: True if test completed successfully, False otherwise.
        """
        return self.verify_processor_cpu_info()


# Execute this test with TestEngine when run as main.
if __name__ == '__main__':
    test_result = VerifyProcessorCPUInfo.main()
    sys.exit(Framework.TEST_RESULT_PASS if test_result else Framework.TEST_RESULT_FAIL)
