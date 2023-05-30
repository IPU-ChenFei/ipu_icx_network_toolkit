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
class TPM(object):
    """TPM constants"""

    DTPM_MM_DID_VID = "FED40F00"
    DTPM_MM_VID_EXP_VAL = "0x001B15D1"
    FTPM_MM_DID_VID = "FED40034"
    FTPM_MM_DID_VID_EXP_VAL = "0xA13A8086"
    DTPM_ACCESS = "FED40000"
    FTPM_ACCESS = "FED40008"
    DTPM_MM_ACCESS_EXP_VAL = "0xA1"
    DTPM_MM_ACCESS_AL_EXP_VAL = "0x81"
    FTPM_MM_ACCESS_EXP_VAL = "0x83"

    TPM_REG_OFFSETS = dict(
        TPM_INTERFACE_ID=0x34,
        TPM_DEVICE_ID=0x36
    )

    PTT_ENABLED_REGISTER_VALUES = dict(TPM_INTERFACE_ID=0x8086, TPM_DEVICE_ID=0xA13A)
    NO_TPM_REGISTER_VALUES = dict(TPM_INTERFACE_ID=0xFFFF, TPM_DEVICE_ID=0xFFFF)


class TPMCLX(TPM):
    TPM_REG_OFFSETS = dict(
        TPM_INTERFACE_ID=0x34,
        TPM_DEVICE_ID=0x36
    )

    PTT_ENABLED_REGISTER_VALUES = dict(TPM_INTERFACE_ID=0x8086, TPM_DEVICE_ID=0xA13A)


class TPMICX(TPM):
    TPM_REG_OFFSETS = dict(
        TPM_INTERFACE_ID=0x34,
        TPM_DEVICE_ID=0x36
    )

    PTT_ENABLED_REGISTER_VALUES = dict(TPM_INTERFACE_ID=0x8086, TPM_DEVICE_ID=0xA13A)
