#!/usr/bin/env python
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and propri-
# etary and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be ex-
# press and approved by Intel in writing.

from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies


def get_ecc_status(csp, sdp, common_content_lib, log):
    """
    Verify if ECC mode registers have been set

    :return: True or False
    """

    global sddc_enabled
    log.info("Check whether ECC is enabled")

    product = csp.silicon_cpu_family

    sddc_dic = {ProductFamilies.CPX: 'imc0_mcmtr', ProductFamilies.SNR: 'memss.mc%d.ch%d.mcmtr',
                ProductFamilies.ICX: 'memss.mc%d.ch%d.mcmtr', ProductFamilies.SPR: 'memss.mc%d.ch%d.mcmtr'
                }

    sddc_mode_config_path = sddc_dic.get(product)

    is_already_halted = sdp.is_halted()

    if sddc_mode_config_path:
        try:
            if not is_already_halted:
                sdp.halt()

            if product in common_content_lib.SILICON_10NM_CPU:
                log.info("Getting mc list from xnmMemicalsUtils object from CScripts...")
                mu_obj = csp.get_xnm_memicals_utils_object()
                ch_list = mu_obj.getPopChList() if product == ProductFamilies.SPR else mu_obj.get_pop_ch_list()
                for ch in ch_list:
                    sddc_mode_config_mc_ch_path = sddc_mode_config_path % (ch.mc, ch.ch)
                    socket_name = str(ch.sktobj.name)
                    socket_index = int(socket_name[-1])
                    log.info("Get field value of ECC mode for Register path '{}'".format(sddc_mode_config_mc_ch_path))
                    sddc_enabled = csp.get_field_value(scope=SiliconRegProvider.UNCORE,
                                                       reg_path=sddc_mode_config_mc_ch_path,
                                                       field="ecc_en",
                                                       socket_index=socket_index)
                    log.info("The register path = '{}' and sddc_enabled "
                             "value = '{}'".format(sddc_mode_config_mc_ch_path, sddc_enabled))
                    if not sddc_enabled:
                        break
            else:
                sddc_enabled = csp.get_field_value(scope=SiliconRegProvider.UNCORE,
                                                   reg_path=sddc_mode_config_path,
                                                   field="ecc_en")

            if sddc_enabled:
                log.info("ECC mode is enabled...")
            else:
                log.info("ECC mode is not enabled...")

        except Exception as ex:
            log_error = "Excpetion occured while checking get_ecc_status: '{}'".format(ex)
            log.error(log_error)
            raise ex
        finally:
            if not is_already_halted:
                sdp.go()
    else:
        raise RuntimeError("Test has not been implemented for" + product)

    return sddc_enabled
