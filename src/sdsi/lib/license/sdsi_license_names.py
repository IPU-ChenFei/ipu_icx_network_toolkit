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
"""Provides Constants for Feature names which can be requested through the SDSi API.

    Typical usage example:
        self.sdsi_agent.apply_lac_by_name(socket, [FeatureNames.DLB4.value, FeatureNames.SG40.value]))
"""
from enum import Enum


class FeatureNames(Enum):
    """Enum class containing license option names"""
    BASE = 'BASE'
    CSS4 = 'CSS4'
    CSS2 = 'CSS2'
    AMS4 = 'AMS4'
    AMS1 = 'AMS1'
    SG01 = 'SGX08'
    SG04 = 'SGX32'
    SG08 = 'SGX64'
    SG10 = 'SGX128'
    SG20 = 'SGX256'
    SG40 = 'SGX512'
    IAA1 = 'IAA1'
    IAA2 = 'IAA2'
    IAA4 = 'IAA4'
    VROCBT = 'VR01'
    VROCST = 'VR02'
    VROCPR = 'VR03'
    VROCDL = 'VR04'
    DSA1 = 'DSA1'
    DSA2 = 'DSA2'
    DSA4 = 'DSA4'
    QTC1 = 'QTC1'
    QTC2 = 'QTC2'
    QTC4 = 'QTC4'
    QTE1 = 'QTE1'
    QTE2 = 'QTE2'
    QTE4 = 'QTE4'
    QTP1 = 'QTP1'
    QTP2 = 'QTP2'
    QTP4 = 'QTP4'
    DLB1 = 'DLB1'
    DLB2 = 'DLB2'
    DLB4 = 'DLB4'
    SSPE = 'SSPE'
    SSCE = 'SSCE'
    SSBE = 'SSBE'
    SSTE = 'SSTE'
    TDXE = 'TDXE'
    TDXD = 'TDXD'
