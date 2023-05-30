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
from src.ras.tests.esmm.esmm_common import EsmmSaveCommon


class VerifySpuriousSmiHandlingFlowSupported(EsmmSaveCommon):
    """
    Glasgow_id : G58337-_74_02_01_verify_spurious_smi_handling_flow_supported
    This test verifies Spurious SMI Handling flow support

    """
    TEST_CASE_ID = ["G58337", "_74_02_01_verify_spurious_smi_handling_flow_supported"]
    BIOS_CONFIG_FILE = "esmm_save_state_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifySpuriousSmiHandlingFlowSupported object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifySpuriousSmiHandlingFlowSupported, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def prepare(self):
        # type: () -> None
        """
        Creates a new VerifySpuriousSmiHandlingFlowSupported object and we are calling a Prepare function
        Prepare Function does the Following tasks:
            1. Set the bios knobs to its default mode.
            2. Set the bios knobs as per the test case.
            3. Reboot the SUT to apply the new bios settings.
            4. Verify the bios knobs that are set.
        :return: None
        """
        super(VerifySpuriousSmiHandlingFlowSupported, self).prepare()

    def execute(self):
        """
        This Method is Used to execute below:
        1.Verifies spurious smi handling flow is supported

        :return: True or False
        """
        smi_handling_flow_status = False
        try:
            self.SDP.itp.halt()
            self.SDP.itp.threads[0].port(0xb2, 1)
            self.SDP.itp.cv.smmentrybreak=1
            self.SDP.itp.go()
            self.SV._sv.refresh()
            smi_handling_flow = self.SV._sv.sockets.uncores.virtual_msr_smm_cfg_options.cfg_option.show()
            if smi_handling_flow == 1:
                self.log.info("Successfully verified Spurious SMI Handling flow")
                smi_handling_flow_status = True
            else:
                self.log.error("Failed to verify Spurious SMI Handling flow")
            self.SDP.itp.halt()
            self.SDP.itp.smmentrybreak=0
            self.SDP.itp.go()
        except Exception as e:
            self.log.error("Failed to verify spurious SMI handling flow due to the Exception '{}'".format(e))
        finally:
            self.SDP.itp.go()
        return smi_handling_flow_status


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifySpuriousSmiHandlingFlowSupported.main() else Framework.TEST_RESULT_FAIL)
