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
class XmlEntryCommonTags(object):
    """Common XML entry values used in content_configuration.xml/security/mktme section
    It contains the common entries/tag belong to Windows and Linux versions
    """
    MKTME_TOOL_PATH_HOST = "mktme_tool_path_host"


class XMLEntryWindows(XmlEntryCommonTags):
    """XML entry values defined only in content_configuration.xml/security/mktme/windows section"""
    AC_RESET = "ac_reset"
    VM_GUEST_USER = "vm_guest_user"
    VM_BOOT_TIME = "vm_boot_time"
    VM_OS = "vm_os"
    VM_TOOLS_BASE_LOC = "vm_tools_base_loc"
    VM_GUEST_IMAGE_PATH_SUT = "exported_vm_guest_image_path_sut"
    LEGACY_VM_IMAGE_PATH_SUT = "exported_legacy_vm_image_path_sut"
    VM_GUEST_IMAGE_DIR = "vm_guest_image_dir"
    VM_GUEST_USER_PWD = "vm_guest_user_pwd"


class XMLEntryLinux(XmlEntryCommonTags):
    """XML entry values defined only in content_configuration.xml/security/mktme/linux section"""
    pass


@six.add_metaclass(MetaRegistry)
class MKTMERegisterValues(object):
    pass


class SPRMKTMERegisterValues(MKTMERegisterValues):
    """SPR specific registers and constants."""

    class RegisterConstants(object):
        """This class contains only the register's address"""
        PRMRR_BASE = 0x2A0
        PRMRR_MASK = 0x1F5
        MSR_TME_CAPABILITY_ADDRESS = 0x981
        MSR_TME_EXCLUDE_MASK_ADDRESS = 0x983
        MSR_TME_EXCLUDE_BASE_ADDRESS = 0x984
        MSR_TME_ADDRESS = 0x982


@six.add_metaclass(MetaRegistry)
class WindowsConst(object):
    """Windows const class """

    def __init__(self, platform_family) -> None:
        self.XmlEntry = XMLEntryWindows()
        self.RegisterRef = MKTMERegisterValues.get_subtype_cls(platform_family + "MKTMERegisterValues", False)


@six.add_metaclass(MetaRegistry)
class LinuxConst(object):
    """Linux const class """
    def __init__(self, platform_family) -> None:
        self.XmlEntry = XMLEntryLinux()
        self.RegisterRef = MKTMERegisterValues.get_subtype_cls(platform_family + "MKTMERegisterValues", False)
