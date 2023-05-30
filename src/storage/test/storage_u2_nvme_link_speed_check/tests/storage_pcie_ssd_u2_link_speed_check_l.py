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
from src.provider.storage_provider import StorageProvider  # type: StorageProvider
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from dtaf_core.providers.provider_factory import ProviderFactory

class StorageU2NvmeLinkSpeedCheckLinux(PcieCommon):
    """
    Glasgow ID/PhoenixID - EGS_PV_1287/16013616262 : Storage - U.2 NVME-Passthrough Link Speed Checks(RHEL)
               PhoenixID -             16013537636 : Storage - U.2 NVME-Passthrough Link Speed Checks(CentOS)
    To Check the Link Speed and Width for all Populated MCIO slots.
    """
    TEST_CASE_ID = ["EGS_PV_1287", "16013616262", "U.2 NVME-Passthrough Link Speed Checks(RHEL)",
                    "16013616262", "U.2 NVME-Passthrough Link Speed Checks(CentOS)"]

    STEP_DATA_DICT = {
        1: {'step_details': 'To get slot info of PCIe U.2 Card',
            'expected_results': 'Fetched slot info of PCIe U.2 card'},
        2: {'step_details': 'Check Populated PCIe U.2 Card has Link speed and width',
            'expected_results': 'Populated PCIe U.2 Card has Link speed and Width as expected'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a StorageU2NvmeLinkSpeedCheckLinux object

        :param test_log: Used for debug and info messages
        :param arguments
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StorageU2NvmeLinkSpeedCheckLinux, self).__init__(test_log, arguments, cfg_opts)
        self._log = test_log
        self._product_family = self._common_content_lib.get_platform_family()
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)

    def prepare(self):  # type: () -> None
        """
        This method is to execute prepare.
        """
        super(StorageU2NvmeLinkSpeedCheckLinux, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. To get slot info of PCIe U.2 Card.
        2. Check Populated PCIe U.2 card slot has Link Stat speed and Width.
        :return: True or False
        """
        self._test_content_logger.start_step_logger(1)
        slot_list = self._common_content_configuration.get_pcie_slot_mcio_check(self._product_family)
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.verify_required_slot_pcie_device(cscripts_obj=self._cscripts_obj, pcie_slot_device_list=slot_list,
                                                        lnk_stat_width_speed=True)
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True

    def cleanup(self, return_status):
        super(StorageU2NvmeLinkSpeedCheckLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageU2NvmeLinkSpeedCheckLinux.main() else
             Framework.TEST_RESULT_FAIL)
