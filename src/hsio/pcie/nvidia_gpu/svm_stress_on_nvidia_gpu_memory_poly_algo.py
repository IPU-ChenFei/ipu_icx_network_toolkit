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

from src.hsio.pcie.nvidia_gpu.svm_stress_common import SVMStressCommon



class SVMStressOnNvidiaGPUMemoryPolyAlgo(SVMStressCommon):
    """
    HSD : 22013951413

    This test utilized an open source SVM benchmark to stress test the memory of the Nvidia GPU.  This will run SVM utilizing polynomial algorithm.

    Note: Should have a NVIDIA Graphic Card attached to SUT
    Also the stress runs for 160 iterations by default. We need 2 hours continuous stress, please anticipate the need
    to increase iterations if it finishes before 2 hours.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new SVMStressOnNvidiaGPUMemoryPolyAlgo object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(SVMStressOnNvidiaGPUMemoryPolyAlgo, self).__init__(test_log, arguments, cfg_opts)
        self.SVM_TEST_FILE = "testP.bat"


    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(SVMStressOnNvidiaGPUMemoryPolyAlgo, self).prepare()

    def execute(self):
        """
        1. Copy and extract GFX_nVidia_SVM.zip
        2. Run test.bat file
        3. Monitor stress on GPU for 2 hours
        4. Pass if os is alive

        :raise : content_exceptions.TestFail
        :return : True on Success
        """

        self._log.info("Running the stress on GPU by polynomial algorithm for 2 hours............................")
        return self.execute_svm_stress(self.SVM_TEST_FILE)

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        """
        super(SVMStressOnNvidiaGPUMemoryPolyAlgo, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SVMStressOnNvidiaGPUMemoryPolyAlgo.main()
             else Framework.TEST_RESULT_FAIL)
