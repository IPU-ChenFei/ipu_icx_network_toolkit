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

from src.lib.test_content_logger import TestContentLogger
from src.security.tests.sgx.sgx_prmrr_size.prmrr_common import SgxPrmBaseTest
from src.security.tests.sgx.sgx_constant import SGXConstant
from src.security.tests.sgx.sgx_common import SgxCommon


class SgxPrmSize64G(SgxPrmBaseTest):
    """
    Phoenix TC ID: P18015174679-PRM Size_Linux - 64G
    Phoenix TC ID: P16017338501-PRM Size_Windows - 64G
    Verify ability to boot with all supported PRM sizes and run basic SGX content: 64G
    """
    TEST_CASE_ID = ["P18015174679_Linux", "PRM_Size_64G", "P16017338501", "PRM_Size_64G_Windows"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable CI/LI bios knobs and PRMRR Size 64G and verify in BIOS',
            'expected_results': 'Enabled CI/LI bios knobs and PRMRR Size 64G and verified successfully in BIOS'},
        2: {'step_details': 'Verify SGX Enabled and run Hydra test for specified hours',
            'expected_results': 'SGX is Enabled successfully and Hydra test run for specified hours'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxPrmSize64G

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        
        bios_config_file = SgxCommon.get_bios_knob_cfg_complete_path(
            SGXConstant.BIOS_CONFIG_FILE_PRM_SIZE_SIXTY_FOUR, cfg_opts)
        super(SgxPrmSize64G, self).__init__(test_log, arguments, cfg_opts, bios_config_file=bios_config_file)
        self._log.debug("Bios config file: {}".format(bios_config_file))
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        self._test_content_logger.start_step_logger(1)
        super(SgxPrmSize64G, self).prepare()
        self._log.info("NUMA, TME, SGX, PRMRR Size 64G, UMA has been set in bios")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Verify EAX and MSR value for SGX and
        2. Run hydra app
        """
        self._test_content_logger.start_step_logger(2)
        super(SgxPrmSize64G, self).execute()
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxPrmSize64G.main() else Framework.TEST_RESULT_FAIL)
