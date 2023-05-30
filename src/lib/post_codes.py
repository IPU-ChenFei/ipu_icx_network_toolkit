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

from src.lib.dtaf_content_constants import IntelPostCodes
from src.lib.dtaf_content_constants import DellPostCodes
from src.lib.dtaf_content_constants import HpePostCodes
from src.lib.dtaf_content_constants import PlatformType


class PostCodes(object):

    def __init__(self):
        self._intel_os_post_codes = [IntelPostCodes.PC_E3, IntelPostCodes.PC_00, IntelPostCodes.PC_4A]
        self._dell_os_post_codes = [DellPostCodes.PC_7E]
        self._hpe_os_post_codes = [HpePostCodes.PC_7E]
        self._msft_os_post_codes = [None]

        self._dict_os_pcs = {PlatformType.REFERENCE: self._intel_os_post_codes,
                             PlatformType.DELL: self._dell_os_post_codes,
                             PlatformType.HPE: self._hpe_os_post_codes,
                             PlatformType.MSFT: self._msft_os_post_codes}

    def get_os_post_codes(self, platform_type):
        if platform_type in self._dict_os_pcs.keys():
            return self._dict_os_pcs[platform_type]
        raise KeyError("Platform type '{}' is not supported".format(platform_type))
