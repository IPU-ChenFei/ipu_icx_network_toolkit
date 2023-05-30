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
from enum import Enum
from collections import OrderedDict

from dtaf_core.lib.registry import MetaRegistry
from dtaf_core.lib.private.cl_utils.adapter import data_types


@six.add_metaclass(MetaRegistry)
class SecureBoot(object):
    """Secure Boot constants"""

    class CertTypes(Enum):
        """Types of certificates valid with Intel BIOS."""
        PK = "PK"
        KEK = "KEK"
        DB = "DB"
        DBT = "DBT"
        DBX = "DBX"

    class Cert:
        def __init__(self, cert_file_name, cert_file_type, cert_signature: str = None):
            self.file = cert_file_name
            self.type = cert_file_type
            self.signature = cert_signature
            self.installed = False

    ARTIFACTORY_SECURE_BOOT_CERTS = "secure-boot-test-certs.zip"
    ARTIFACTORY_LINUX_KERNEL_SIGNING_TOOLS = "sbsigntools-0.9.4-2.fc33.x86_64.rpm"

    SIGNATURE_GUID_CONTENT_CONFIG_LABEL = "SIGNATURE_GUID"

    EDKII_MENU_DIR = "EDKII Menu"
    SECURE_BOOT_CONFIG_DIR = "Secure Boot Configuration"
    CUSTOM_SECURE_BOOT_OPTIONS_DIR = "> Custom Secure Boot Options"
    SIGNATURE_GUID_LABEL = "Signature GUID"
    SECURE_BOOT_MODE_LABEL = "Secure Boot Mode"
    CUSTOM_MODE_OPTION = "Custom Mode"
    SECURE_BOOT_ENABLED = "Attempt Secure Boot"
    RESET_SECURE_BOOT_KEYS = "Reset Secure Boot Keys"

    OPTIONS_DIR = "{} Options"
    ENROLL_LABEL = "Enroll {}"
    ENROLL_FILE_LABEL = "Enroll {} Using File"
    ENROLL_SIG_LABEL = "Enroll Signature"

    SECURE_BOOT_PATH = OrderedDict([(EDKII_MENU_DIR, data_types.BIOS_UI_DIR_TYPE),
                                   (SECURE_BOOT_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE)])
    SAVE_CERT_OPTIONS = OrderedDict([("Commit Changes and Exit", data_types.BIOS_UI_DIR_TYPE)])
    ENROLL_SIGNATURE_OPTIONS = OrderedDict([(ENROLL_SIG_LABEL, data_types.BIOS_UI_DIR_TYPE)])
    SECURE_BOOT_DISABLE_OPTION = OrderedDict([(SECURE_BOOT_ENABLED, data_types.BIOS_UI_OPT_TYPE)])

