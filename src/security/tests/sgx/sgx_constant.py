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
from dtaf_core.lib.registry import MetaRegistry


@six.add_metaclass(MetaRegistry)
class SGXConstant(object):
    """Defines the SGX constants"""
    WAIT_TIME_DELAY = 60
    PRMRR_KNOB_PROMPT = "PRMRR Size"
    PRMRR_KNOB_NAME = "PrmrrSize"
    SGX_LOGICAL_INTEGRITY = "logical_integrity"
    SGX_INTEGRITY = "SGX_INTEGRITY"
    SGX_CRYPTOGRAPHIC_INTEGRITY = "cryptographic_integrity"
    PRIMARY_BIOS_CONFIG_FILE = "collateral/{}/sgx_enable_through_bios.cfg"
    PRIMARY_BIOS_CONFIG_FILE_LI = "collateral/{}/sgx_enable_through_bios_li.cfg"
    BIOS_CONFIG_FILE_SGX_ADDDC_CONFIG_FILE = "collateral/{}/sgx_adddcen.cfg"
    BIOS_CONFIG_FILE_PRM_SIZE_TW0_GIGA = "collateral/{}/sgx_prm_size_2g.cfg"
    BIOS_CONFIG_FILE_PMR_SIZE_FOUR_GIGA = "collateral/{}/sgx_prm_size_4g.cfg"
    BIOS_CONFIG_FILE_PRM_SIZE_EIGHT_GIGA = "collateral/{}/sgx_prm_size_8g.cfg"
    BIOS_CONFIG_FILE_PRM_SIZE_SIXTEEN_GIGA = "collateral/{}/sgx_prm_size_16g.cfg"
    BIOS_CONFIG_FILE_PRM_SIZE_THRITY_TW0 = "collateral/{}/sgx_prm_size_32g.cfg"
    BIOS_CONFIG_FILE_PRM_SIZE_SIXTY_FOUR = "collateral/{}/sgx_prm_size_64g.cfg"
    BIOS_CONFIG_FILE_PRM_SIZE_ONE_TWENTY_EIGHT = "collateral/{}/sgx_prm_size_128g.cfg"
    BIOS_CONFIG_FILE_PRM_SIZE_TWO_FIFTY_SIX_GIGA = "collateral/{}/sgx_prm_size_256g.cfg"
    BIOS_CONFIG_FILE_PRM_SIZE_FIVE_TWELVE_GIGA = "collateral/{}/sgx_prm_size_512g.cfg"

class SGXSPR(SGXConstant):

    class RegisterConstants(object):
        CPUID_EAX = 0x12  # CPUID_LEAF
        MSR_FEATURE_CONTROL = 0x3a  # MSR_IA32_FEATURE_CONTROL
        PRMRR_MASK = 0x1F5  # PRMRR_MASK
        MCHECK_ERROR = 0xA0  # MSR_MCHECK_ERROR

    class MSRMCHECK(object):
        MCHECK_STATUS_VALUE = 0x0

    class MSRTMECapabilitiesBits(object):
        TME_CAPABILITIES_BIT = {"1": "1"}

    class MSRTMEActivateBits(object):
        TME_ACTIVATE_BIT = {"49": "1"}

    class EAXCpuidBits(object):
        EAX_CPUID_BITS = {"0": "1", "1": "1"}

    class EnableBits(object):
        ENABLE_BITS = {"0": "1", "17": "1", "18": "1"}

    class MSRIAFeatureControlBits(object):
        FEATURE_CONTROL_BITS = {"0": "1", "17": "1", "18": "1"}

    class PRMRRMaskBits(object):
        PRMRR_MASK_BITS = {"11": "1"}
