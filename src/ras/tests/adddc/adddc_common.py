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

from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib.content_base_test_case import ContentBaseTestCase


class AdddcCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the ADDDC Functionality Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts, config):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(AdddcCommon, self).__init__(test_log, arguments, cfg_opts, config)

        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.
        :return: None
        """
        super(AdddcCommon, self).prepare()
