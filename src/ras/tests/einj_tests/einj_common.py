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

from src.lib.install_collateral import InstallCollateral
from src.ras.lib.ras_einj_common import RasEinjCommon
from src.lib.content_base_test_case import ContentBaseTestCase
from src.ras.lib.ras_common_utils import RasCommonUtil


class EinjCommon(ContentBaseTestCase):
    """
    Glasgow_id : 59255, 59256, 59257, 59258, 59259, 59260.
    HPALM_id : 81562, 81563, 81554, 81555

    Common base class for functional einj mem - pcie test cases
    """

    def __init__(self, test_log, arguments, cfg_opts, config):
        """
        Creates a new Einj Common object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), config)
        super(EinjCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._ras_einj_obj = RasEinjCommon(self._log, self.os, self._common_content_lib,
                                           self._common_content_configuration, self.ac_power, cfg_opts)

        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._ras_common_obj = RasCommonUtil(self._log, self.os, cfg_opts, self._common_content_configuration)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        self._install_collateral.copy_mcelog_binary_to_sut()
        super(EinjCommon, self).prepare()
