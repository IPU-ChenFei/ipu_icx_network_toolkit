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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib.common_content_lib import CommonContentLib
from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.lib.test_content_logger import TestContentLogger
from src.lib.dtaf_content_constants import TimeConstants


class PartialMemoryMirroring(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix TC ID : P18014072989-Partial_Memory_Mirroring
    ICX: Verify inability to enable SGX reserved memory ranges when the system memory has been configured with partial
    mirroring RAS feature.
    From SPR onwards, SGX and partial Memory Mirroring can co-exist together.
    Operating System : Linux and Windows
    """
    TEST_CASE_ID = ["P18014072989", "Partial_Memory_Mirroring"]
    BIOS_CONFIG_FILE = "../sgx_tme.cfg"
    PARTIAL_MIRROR_MODE_CONFIG_FILE = "partial_mirror_mode_enable.cfg"
    step_data_dict = {
        1: {'step_details': 'Set BIOS knobs as Enable Total Memory Encryption (TME),'
                            ' and Enable SW Guard Extensions (SGX) and Partial Memory Mirror Mode',
            'expected_results': 'TME SGX amd Partial Memory Mirror Mode should be enabled in the BIOS'},
        2: {'step_details': 'Boot to the OS and verify SGX MSR & EAX value ',
            'expected_results': 'SGX MSR & EAX value is successfully verified'},
        3: {'step_details': 'Run Semt app or sgx Hydra and very it is running with Partiall Memory Mirror Mode',
            'expected_results': 'Semt app or sgx hydra ran successfully with Partial Memory Mirror Mode'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PartialMemoryMirroring

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.bios_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        self.partial_mirror_mode_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            self.PARTIAL_MIRROR_MODE_CONFIG_FILE)

        combined_bios = CommonContentLib.get_combine_config([self.bios_config_path, self.partial_mirror_mode_config_path])
        super(PartialMemoryMirroring, self).__init__(test_log, arguments, cfg_opts,
                                                     bios_config_file_path=combined_bios)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._log.debug("Bios config file: %s", self.bios_config_path)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)

    def prepare(self):
        # type: () -> None
        """preparing the setup
        1. Enabling SGX, Tme amd Partial Memory MirrorMode Bios knobs
        """
        self._test_content_logger.start_step_logger(1)
        self._log.info("Enabling SGX Tme and Partial Memory Mirror Mode bios knobs..")
        super(PartialMemoryMirroring, self).prepare()
        self._log.info("Sgx knob is enabled with Partial Memory Mirroring Mode..")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Verifying SGX EAX & MSR value
        2. Running Semt app for linux os and sgx hydra for windows os

        :return True if test case is passed
        """
        # check for eax and msr value for SGX
        self._test_content_logger.start_step_logger(2)
        self.sgx.check_sgx_enable()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Running Semt app/Sgx Hydra
        self._test_content_logger.start_step_logger(3)
        self.sgx.verify_sgx_content(time_duration=TimeConstants.TEN_MIN_IN_SEC)
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PartialMemoryMirroring.main() else Framework.TEST_RESULT_FAIL)
