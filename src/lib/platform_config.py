#!/usr/bin/env python
##########################################################################
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
##########################################################################

from dtaf_core.lib.dtaf_constants import ProductFamilies


class PlatformConfiguration(object):
    """
    This Class is Used as Common Class for all Platform Configuration Details.
    """

    PCLS_ENABLE_VERIFICATION_DICT = {
        ProductFamilies.SPR: "memss.mc0.ch1.pcls_{}_cfg_data_info.pcls_enable",
        ProductFamilies.ICX: "memss.mc0.ch1.pcls_{}_cfg_data_info.pcls_enable",
        ProductFamilies.SNR: "memss.mc0.ch1.pcls_{}_cfg_data_info.pcls_enable",
    }

    MKTME_MAX_KEYS_DICT = { ProductFamilies.ICX: "0x003F",
                            ProductFamilies.SPR: "0x007F", }

    MEMORY_SNC_CONFIG = {
        ProductFamilies.SPR: "cha.cha0.ms2idi0.snc_config"}
    MEMORY_KTILK_SNC_CONFIG = {ProductFamilies.SPR: "upi.upi0.ktilk_snc_config"}
    MCE_EVENTS_CHECK_CONFIG = {ProductFamilies.SPR: "ubox.ncevents.mcerrloggingreg"}
    UPI_KTIREUT_PH_CSS = {ProductFamilies.SPR: "uncore.upi.upis.ktireut_ph_css"}

    CHECK_ACPI_ENABLE = {ProductFamilies.SPR: "core_pmsb.core_pmsbs.pma_debug2.acp_enabled"}
