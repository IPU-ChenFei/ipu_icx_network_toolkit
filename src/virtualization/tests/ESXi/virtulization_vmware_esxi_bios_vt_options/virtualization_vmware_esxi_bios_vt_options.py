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
import os
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.test_content_logger import TestContentLogger


class VirtualizationVmwareBiosVtOptions(VirtualizationCommon):
    """
    Phoenix ID: 18014072277
    The objective to this TC is to verify the BIOS knobs such as Vt-D, VMX and SRIOV and Operating System is booting without issues with this BIOS knobs enabled.

    1. Enable VT-d, VMX, SRIOV Bios knobs on ESXi sut.
    2. Verify all the above Bios knobs are enabled in BIOS settings
    4. Verify the Operating system booting fine with all these BIOS settings.
    """
    TEST_CASE_ID = ["P18014072277", "Virtualization_VMware_ESXi_Bios_VT_Options"]
    STEP_DATA_DICT = {
        1: {'step_details': "Set the default bios knob",
            'expected_results': "Default bios knob is set and verified successfully'"},
        2: {'step_details': "Set Bios knobs for VT-d, VMX and SRIOV",
            'expected_results': "Bios knobs Set successfully for Vt-d, VMX and SRIOV"},
        3: {'step_details': "Verify the Bios knob for VT-d, VMX and SRIOV",
            'expected_results': "Successfully verified the Bios knob for VT-d, VMX and SRIOV"},
    }
    BIOS_CONFIG_FILE = "virtualization_vmware_esxi_bios_vt_options.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareVtdPassthroughFunctionality object.

        """
        super(VirtualizationVmwareBiosVtOptions, self).__init__(test_log, arguments, cfg_opts,)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)

    def prepare(self):
        """
        Prepare executes the default bios setting for Vmware Esxi Os.
        """
        self._test_content_logger.start_step_logger(1)
        super(VirtualizationVmwareBiosVtOptions, self).prepare()
        self.bios_util.load_bios_defaults()
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        1. Set the bios Knob.
        2. Verify the bios settings for vmware esxi
        """
        self._test_content_logger.start_step_logger(2)
        self.bios_util.set_bios_knob(bios_config_file=self.bios_config_file)
        self._test_content_logger.end_step_logger(2, True)
        self.perform_graceful_g3()
        self._test_content_logger.start_step_logger(3)
        self.bios_util.verify_bios_knob(bios_config_file=self.bios_config_file)
        self._test_content_logger.end_step_logger(3, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareBiosVtOptions, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareBiosVtOptions.main()
             else Framework.TEST_RESULT_FAIL)
