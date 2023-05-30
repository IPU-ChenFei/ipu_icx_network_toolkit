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

from dtaf_core.lib.dtaf_constants import ProductFamilies


class AerUtil(object):
    """
    AerUtil Util class, provides below functionality
    1. is aer enabled
    """

    def __init__(self, log, csp, sdp):
        self._log = log
        self._csp = csp
        self._sdp = sdp
        self._product = self._csp.silicon_cpu_family

    def is_aer_enabled(self):
        """
        Function to get the aer enabled or not
        :return: Boolean(True/False)
        """
        # TODO : Observed three registries(aebedm,  tpbedm , ptlpebdm ) are not implemented in Cscript. Sent mail to
        # TODO : Timothy & Miguel for help. Once we will get the solution need to modify again
        try:
            aer_enable_status_list = []
            self._log.info("Verifying if AER is enabled Successfully or not")

            if self._product == ProductFamilies.ICX:
                #   Defining register field and expected values
                erruncdetmsk = {'dlpedm': 0, 'sldedm': 0, 'ptlpedm': 0, 'fcedm': 0, 'ctedm': 0, 'caedm': 0, 'ucedm': 0,
                                'roedm': 0, 'mtlpedm': 0,
                                'ecrcedm': 0, 'uredm': 0, 'acsedm': 0, 'uiedm': 0, 'mcedm': 0}

                erruncmsk = {'dlpem': 0, 'uiem': 1, 'sldem': 0, 'ptlpem': 0, 'fcem': 0, 'ctem': 0, 'caem': 0, 'ucem': 0,
                             'roem': 0, 'mtlpem': 0, 'ecrcem': 0,
                             'urem': 0, 'acsem': 0, 'mcem': 0, 'aebem': 0, 'tpbem': 0, 'ptlpebm': 0}

                erruncsev = {'sldes': 0, 'ptlpes': 0, 'ctes': 0, 'caes': 0, 'uces': 0, 'ecrces': 0, 'ures': 0,
                             'acses': 0, 'mces': 0, 'aebes': 0, 'tpbes': 0,
                             'ptlpebs': 0, 'dlpes': 1, 'fces': 1, 'roes': 1, 'mtlpes': 1, 'uies': 1}

                erruncsts = {'dlpe': 0, 'slde': 0, 'ptlpe': 0, 'fce': 0, 'cte': 0, 'cae': 0, 'uce': 0, 'roe': 0,
                             'mtlpe': 0, 'ecrce': 0, 'ure': 0, 'acse': 0,
                             'uie': 0, 'mce': 0, 'aebe': 0, 'tpbe': 0, 'ptlpeb': 0}

                errcordetmsk = {'redm': 0, 'btlpedm': 0, 'bdllpedm': 0, 'rnredm': 0, 'rttedm': 0, 'anfedm': 0,
                                'ciedm': 0, 'hloedm': 0}

                errcormsk = {'rem': 0, 'btlpem': 0, 'bdllpem': 0, 'rnrem': 0, 'rttem': 0, 'anfem': 1, 'ciem': 0,
                             'hloem': 0}

                errcorsts = {'re': 0, 'btlpe': 0, 'bdllpe': 0, 'rnre': 0, 'rtte': 0, 'anfe': 0, 'cie': 0, 'hloe': 0}

                reg_dict_list = {'erruncdetmsk': erruncdetmsk, 'erruncmsk': erruncmsk, 'erruncsev': erruncsev,
                             'erruncsts': erruncsts, 'errcordetmsk': errcordetmsk,
                             'errcormsk': errcormsk, 'errcorsts': errcorsts}

                aer_reg_mapping_dict = {'erruncdetmsk': 'cbdma_0', 'erruncmsk': 'pcie.pxp0.ntb.iep.cfg',
                                        'erruncsev': 'cbdma_0',
                                        'erruncsts': 'pcie.pxp0.ntb.iep.cfg', 'errcordetmsk': 'cbdma_0',
                                        'errcormsk': 'adl_cci_dfd.dvp.dvp0_pktzr_dtf_pktstrm_ctrl0_reg',
                                        'errcorsts': 'cbdma_0'}

                self._sdp.halt()
                self._log.debug("--- Checking each register bit fields ---")
                for registry_name, bit_registry_pair in reg_dict_list.items():
                    #   Getting the AER registry Name
                    _AER_REG_NAME = aer_reg_mapping_dict[registry_name]
                    #   Iterating through the bit_id and bit_val from the default registry dictionary
                    icounter = 0
                    for bit_id, bit_val in bit_registry_pair.items():
                        #   Getting the registry values
                        if bit_id == 'tpbes':
                            _AER_REG_NAME = 'pcie.pxp0.ntb.iep.cfg'
                        elif bit_id == 'btlpem':
                            _AER_REG_NAME = 'cbdma_0'
                        if bit_id == 'rem':
                            aer_reg_val = self._csp.get_by_path(self._csp.UNCORE,
                                                        'adl_cci_dfd.dvp.dvp0_pktzr_dtf_pktstrm_ctrl0_reg.capturemask')
                        elif bit_id == 're':
                            aer_reg_val = self._csp.get_by_path(self._csp.UNCORE,
                                                    'adl_cci_dfd.dso.dso0_dtf_encoder_status_reg.dtfe_upstream_credit')
                        else:
                            aer_reg_val = self._csp.get_by_path(self._csp.UNCORE, "{}.{}.{}".format(
                                                                            _AER_REG_NAME, str(registry_name), str(bit_id)))
                        #   Validating the registry bit registry value with default bit registry value
                        if aer_reg_val[0] == bit_val:

                            self._log.debug("++++ Registers have been matched with default bit value ++++ %s" % aer_reg_val[0])
                            aer_enable_status_list.append(True)
                        else:
                            self._log.error("++++ Failed and Registers have mismatched/non-default bit value ++++ %s"
                                            % aer_reg_val[0])
                            aer_enable_status_list.append(False)
            else:
                self._log.error("Platform: {} not supported".format(self._product))

            return all(aer_enable_status_list)

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex
