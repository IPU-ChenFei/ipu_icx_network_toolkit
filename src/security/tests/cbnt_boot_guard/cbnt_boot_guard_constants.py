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

import six
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.lib.registry import MetaRegistry


@six.add_metaclass(MetaRegistry)
class CBnTConstants(object):
    """CBnT constants"""

    ADDRESS_TO_READ_PCH_VAL = "0xfed30200p"

    CPU_FUSE_BIT_DICT = {
        ProductFamilies.SPR: "punit.core_configuration_0.anchor_cove_en",
        ProductFamilies.ICX: "punit.core_configuration_0.anchor_cove_en",
        ProductFamilies.SKX: "pcu_cr_core_configuration_0.anchor_cove_en",
        ProductFamilies.CLX: "pcu_cr_core_configuration_0.anchor_cove_en",
        ProductFamilies.CPX: "pcu_cr_core_configuration_0.anchor_cove_en",
    }


class BootGuardConstants:
    """BootGuard constants"""

    class BootGuardProfiles:
        PROFILE0 = "Profile0"
        PROFILE3 = "Profile3"
        PROFILE4 = "Profile4"
        PROFILE5 = "Profile5"

    class BootGuardValues:
        """Expected values for each BootGuard Profile for BootGuard MSR."""
        BTG_P0_VALID = [0x00000000400000000]
        CBNT_BTG_P0_VALID = [0x0000000D00000000, 0x00000001D00000000]

        BTG_P4_VALID = [0x0000000700000051]
        CBNT_BTG_P4_VALID = [0x0000000F00000051, 0x00000001F00000051]

        BTG_P5_VALID = [0x000000070000007B, 0x000000070000007D, 0x0000000700000075]
        CBNT_BTG_P5_VALID = [0x0000000F0000007B, 0x0000000F0000007D, 0x00000001F0000007D, 0x0000000F00000075]

        BTG_P3_VALID = [0x000000070000006B, 0x000000070000006D, 0x000000070000006F]
        CBNT_BTG_P3_VALID = [0x0000000F0000006B, 0x0000000F0000006D, 0x00000001F0000006D, 0x0000000F0000006F]

        BTP_P3_WITHOUT_TPM_VALID = [0x0000000700000041]
        CBNT_BTG_P3_WITHOUT_TPM_VALID = [0x0000000F00000041, 0x00000001F00000041]

    BTG_SACM_INFO_MSR_ADDRESS = 0x13a
