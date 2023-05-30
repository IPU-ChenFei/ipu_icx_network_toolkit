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


class CBnT(object):
    CBNT_PRODUCT_FAMILIES = ["ICX", "CPX", "JVL", "SPR"]


class HashAlgorithms(object):
    """ Enum for SHA Algorithms"""
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"
    SM2 = "sm2"

class LcpPolicyVersion:
    POLICY_3_0_VERSION = "3.0"
    POLICY_3_1_VERSION = "3.1"
    POLICY_3_2_VERSION = "3.2"

class TpmVersions(object):
    """Enum for TPM versions"""
    TPM2 = "TPM2"
    TPM1P2 = "TPM1.2"


class LinuxOsTypes(object):
    """Enum for Linux OS types"""
    RHEL = "RHEL"
    CENTOS = "CENTOS"


class RedhatVersion(object):
    """Enum for Redhat versions types"""
    RHEL_7_VERSION = ["7.6"]

    RHEL_8_VERSION = ["8.0", "8.1", "8.2", "8.3", "8.4", "8.5"]

