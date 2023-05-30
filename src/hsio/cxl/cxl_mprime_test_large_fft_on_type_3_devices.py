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
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import sys
import os


from src.provider.stressapp_provider import StressAppTestProvider
from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.cxl.cxl_mprime_test_blend_on_type_3_devices import CxlMprimeTestBlendOnType3Devices
from src.lib.dtaf_content_constants import TimeConstants, Mprime95ToolConstant


class CxlMprimeTestLargeFFTOnType3Devices(CxlMprimeTestBlendOnType3Devices):
    """
    hsdes_id :  16016844479 CXL mprime test(Large FFTs) on  Host Managed Device Memory for CXL Type3 devices 

    """
    CXL_BIOS_KNOBS = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), "cxl_common_bios_file.cfg")

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=CXL_BIOS_KNOBS):
        """
        Create an instance of CxlMprimeTestLargeFFTOnType3Devices.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlMprimeTestLargeFFTOnType3Devices, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlMprimeTestLargeFFTOnType3Devices, self).prepare()

    def execute(self):
        """
        Method covers
        The Linux implementation is called mprime
        running Large FFT type torture test.
        """
        return super(CxlMprimeTestLargeFFTOnType3Devices, self).execute(type_of_torture=3)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlMprimeTestLargeFFTOnType3Devices.main() else
             Framework.TEST_RESULT_FAIL)
