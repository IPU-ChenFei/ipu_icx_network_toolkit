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

from dtaf_core.lib.dtaf_constants import OperatingSystems


class CollateralConstants(object):
    """
    This class defines the collateral archive details
    """
    # collateral archive types
    ZIP = "zip"
    TGZ = "tgz"
    TAR = "tar"
    TAR_GZ = "tar.gz"
    WHL = "whl"
    CONF = "conf"
    RPM = "rpm"

    # KEYS to collateral details
    RELATIVE_PATH = "relative_path"
    FILE_NAME = "file_name"
    TYPE = "type"
    SUPP_OS = "supported_os"
    SETUP_EXE = "setup_exe"

    # KEY to collateral dict
    COLLATERAL_CMDTOOL = "cmdtool"
    COLLATERAL_PCRTOOL = "pcrdump64"

    dict_collaterals = {
        # collateral_name --> {collateral_path, archive_type, "Supported OS":[], "optional_binary_name"}
        # archive_type --> "zip", "tgz", "tar", "tar.gz"
        COLLATERAL_CMDTOOL: {RELATIVE_PATH: "uefi", FILE_NAME: r"cmdtool.zip", TYPE: ZIP,
                             SUPP_OS: [OperatingSystems.LINUX, OperatingSystems.WINDOWS],
                             SETUP_EXE: None},
        COLLATERAL_PCRTOOL: {RELATIVE_PATH: "uefi", FILE_NAME: r"pcrdump64.zip", TYPE: ZIP,
                             SUPP_OS: [OperatingSystems.LINUX],
                             SETUP_EXE: None}
    }
