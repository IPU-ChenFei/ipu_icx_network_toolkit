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
class PTT(object):
    """PTT constants"""

    PTT_REG_BASE = 0xFED40000

    PTT_REG_OFFSETS = dict(
        PTT_INTERFACE_ID=0x34,
        PTT_DEVICE_ID=0x36
    )

    PTT_ENABLED_REGISTER_VALUES = dict(PTT_INTERFACE_ID=0x8086, PTT_DEVICE_ID=0xA13A)


class PTTCLX(PTT):

    PTT_REG_OFFSETS = dict(
        PTT_INTERFACE_ID=0x34,
        PTT_DEVICE_ID=0x36
    )

    PTT_ENABLED_REGISTER_VALUES = dict(PTT_INTERFACE_ID=0x8086, PTT_DEVICE_ID=0xA13A)


class PTTICX(PTT):

    PTT_REG_OFFSETS = dict(
        PTT_INTERFACE_ID=0x34,
        PTT_DEVICE_ID=0x36
    )

    PTT_ENABLED_REGISTER_VALUES = dict(PTT_INTERFACE_ID=0x8086, PTT_DEVICE_ID=0xA13A)
