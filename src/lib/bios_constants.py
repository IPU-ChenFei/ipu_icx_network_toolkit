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

from collections import OrderedDict

from dtaf_core.lib.private.cl_utils.adapter import data_types
from dtaf_core.lib.dtaf_constants import ProductFamilies


class BiosSerialPathConstants:

    CONTINUE_KNOB = "Continue"
    RESET_KNOB = "Reset"

    INTEL_SST_BIOS_PATH = {
        ProductFamilies.ICX: OrderedDict([(r"EDKII Menu", data_types.BIOS_UI_DIR_TYPE),
                             (r"Socket Configuration", data_types.BIOS_UI_DIR_TYPE),
                             (r"Advanced Power Management Configuration", data_types.BIOS_UI_DIR_TYPE),
                             (r"CPU P State Control", data_types.BIOS_UI_DIR_TYPE)]),
        ProductFamilies.CPX: OrderedDict([(r"EDKII Menu", data_types.BIOS_UI_DIR_TYPE),
                            (r"Socket Configuration", data_types.BIOS_UI_DIR_TYPE),
                            (r"Advanced Power Management Configuration", data_types.BIOS_UI_DIR_TYPE),
                            (r"CPU P State Control", data_types.BIOS_UI_DIR_TYPE)]),
        ProductFamilies.SPR: OrderedDict([(r"EDKII Menu", data_types.BIOS_UI_DIR_TYPE),
                            (r"Socket Configuration", data_types.BIOS_UI_DIR_TYPE),
                            (r"Advanced Power Management Configuration", data_types.BIOS_UI_DIR_TYPE),
                            (r"CPU P State Control", data_types.BIOS_UI_DIR_TYPE)]),
    }

    SATA_RST_CONFIGURATION = {
        ProductFamilies.SPR: OrderedDict([(r"EDKII Menu", data_types.BIOS_UI_DIR_TYPE),
                            (r"Platform Configuration", data_types.BIOS_UI_DIR_TYPE),
                            (r"PCH-IO Configuration", data_types.BIOS_UI_DIR_TYPE),
                            (r"SATA And RST Configuration", data_types.BIOS_UI_DIR_TYPE),
                            (r"Controller 1 SATA And RST Configuration", data_types.BIOS_UI_DIR_TYPE)])
    }

    INTEL_VROC_SATA_CONTROLLER = {
        ProductFamilies.SPR: OrderedDict([(r"EDKII Menu", data_types.BIOS_UI_DIR_TYPE),
                                          (r"Intel\(R\) VROC SATA Controller", data_types.BIOS_UI_DIR_TYPE)
                                          ]
                                         )
                                          }

    SYSTEM_INFORMATION_PATH = {
        ProductFamilies.SPR: OrderedDict([(r"EDKII Menu", data_types.BIOS_UI_DIR_TYPE),
                                          (r"System Information", data_types.BIOS_UI_DIR_TYPE)])}

    INTEL_VROC_NVME_CONTROLLER = {
        ProductFamilies.SPR: OrderedDict([(r"EDKII Menu", data_types.BIOS_UI_DIR_TYPE),
                                          (r"Intel\(R\) Virtual RAID on CPU", data_types.BIOS_UI_DIR_TYPE),
                                          (r"All Intel VMD Controllers", data_types.BIOS_UI_DIR_TYPE)
                                          ]
                                         )
    }

class IntelSSTTable:

    class ICX:

        INTEL_SST = "Intel SST-PP"
        CORE_COUNT = "Core Count"
        P1_RATIO = "Current P1 Ratio"
        PACKAGE_TDP = "Package TDP (W)"
        TJMAX = "Tjmax"

    class SPR:
        INTEL_SST = "Intel SST-PP"
        CORE_COUNT = "Core Count"
        P1_RATIO = "Current P1 Ratio"
        PACKAGE_TDP = "Package TDP (W)"
        TJMAX = "Tjmax"

