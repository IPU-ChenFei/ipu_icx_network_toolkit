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
from src.ras.lib.ras_einj_common import RasEinjCommon
from src.lib.mirror_mode_common import MirrorCommon


class PatrolScrubCommonUtils(object):
    """
    This Class is Used as Common Class For all the Patrol Scrub Functionality Test Cases
    """
    CE_ERROR_ERR_SIGNATURE_LIST = \
        ["ADDR 12346000",
         "scrub corrected error",
         "event severity: corrected"]

    UCE_ERROR_ERR_SIGNATURE_LIST = \
        ["ADDR 12345200",
         "Machine check events logged",
         "event severity: corrected",
         "Uncorrected DIMM memory error"]

    def __init__(self, log, csp, sdp, osobj, common_content_lib):
        self._log = log
        self._cscripts = csp
        self._sdp = sdp
        self._os = osobj
        self._common_content_lib = common_content_lib
        self._product = self._cscripts.silicon_cpu_family
        self._mirror_common = MirrorCommon(self._log, self._cscripts, self._sdp)

    def is_patrol_scrub_enabled(self):
        """
        Check platform patrols scrub status , return true if it is enabled

        :param self:

        """
        is_patrol_scrub_enabled_path_dict = {ProductFamilies.CLX: "pcu_cr_capid3_cfg",
                                             ProductFamilies.SKX: "pcu_cr_capid3_cfg",
                                             ProductFamilies.CPX: "pcu_cr_capid3_cfg",
                                             ProductFamilies.ICX: "punit.capid3_cfg",
                                             ProductFamilies.SPR: "punit.capid3_cfg",
                                             }

        patrolscrub_status = self._cscripts.get_field_value(scope=self._cscripts.UNCORE,
                                                            reg_path=is_patrol_scrub_enabled_path_dict[self._product],
                                                            field="disable_patrol_scrub", socket_index=0)

        patrolscrub_status = str(patrolscrub_status).replace("[0x", "").replace("]", "")

        if patrolscrub_status == 1:
            self._log.info("Patrol Scrub is Not Enabled on Platform")
            return False
        else:
            self._log.info("Patrol Scrub is Enabled on Platform")
            return True

    def set_patrol_scrub_start(self, pop_ch_list, start_scrub=1):
        """
        Set patrol start flag - This enables patrol scrub to start from address lo when enabled

        :param pop_ch_list:  memicals utility objects
        :param start_scrub: 0 or 1
        """

        self._log.info("Setting scrubctl.startscrub=" + str(start_scrub))

        for pop_ch in pop_ch_list:
            pop_ch.regs.set_access('mem')
            scrub_en_path_dict = {ProductFamilies.CLX: "imc" + str(pop_ch.mc) + "_scrubctl",
                                  ProductFamilies.CPX: "imc" + str(pop_ch.mc) + "_scrubctl",
                                  ProductFamilies.ICX: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                                      pop_ch.ch) + ".scrubctl",
                                  ProductFamilies.SNR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                                      pop_ch.ch) + ".scrubctl"
                                  }
            pop_ch.sktobj.uncore.get_by_path(scrub_en_path_dict[self._product]).startscrub.write(start_scrub)

    def set_patrol_scrub_enable(self, pop_ch_list, scrub_enable=1):
        """
        Enable patrol scrub start

        :param self:
        :param pop_ch_list:   populated memory channels list
        :param scrub_enable: 0 or 1
        """

        if scrub_enable:
            self._log.info("Enabling scrub")
        else:
            self._log.info("Disabling scrub")

        for pop_ch in pop_ch_list:
            pop_ch.regs.set_access('mem')
            scrub_en_path_dict = {ProductFamilies.CLX: "imc" + str(pop_ch.mc) + "_scrubctl",
                                  ProductFamilies.CPX: "imc" + str(pop_ch.mc) + "_scrubctl",
                                  ProductFamilies.ICX: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                                      pop_ch.ch) + ".scrubctl",
                                  ProductFamilies.SNR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                                      pop_ch.ch) + ".scrubctl"
                                  }
            path = scrub_en_path_dict[self._product]
            self._cscripts.get_by_path(self._cscripts.UNCORE, path).scrub_en.write(scrub_enable)
            self._log.info(str(path) + ".scrub_en=" + str(scrub_enable))

            self._log.info("setting mc" + str(pop_ch.mc) + " ch" + str(pop_ch.ch) + " to " + str(scrub_enable))

        results = None
        for pop_ch in pop_ch_list:
            # TODO - possible need to update access pop_ch.regs.set_access('mem')
            scrub_en_path_dict = {ProductFamilies.CLX: "imc" + str(pop_ch.mc) + "_scrubctl",
                                  ProductFamilies.CPX: "imc" + str(pop_ch.mc) + "_scrubctl",
                                  ProductFamilies.ICX: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                                      pop_ch.ch) + ".scrubctl",
                                  ProductFamilies.SNR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                                      pop_ch.ch) + ".scrubctl"
                                  }
            self._log.info(str(pop_ch.sktobj.uncore.get_by_path(scrub_en_path_dict[self._product]).scrub_en))
            if pop_ch.sktobj.uncore.get_by_path(scrub_en_path_dict[self._product]).scrub_en == scrub_enable:
                results = True
            else:
                results = False
        if not results:
            self._log.info("Unable to verify settings made - possibly platform is not unlocked?")
            return False
        else:
            return True

    def set_patrol_scrub_addr_lo(self, pop_ch_list, addresslo=0x100000):
        """
        Setup Patrol scrub address to start memory scrubbing when enabled

        :param self:
        :param pop_ch_list:  populated memory channels list
        :param addresslo: address to start scrub when enabled
        """
        self._log.info("Setting patrolscrub addresslo and address2lo to " + str(addresslo))

        for pop_ch in pop_ch_list:
            # TODO - possible need to update access pop_ch.regs.set_access('mem')
            scrub_addrlo_path_dict = {ProductFamilies.CLX: "imc" + str(pop_ch.mc) + "_scrubaddresslo",
                                      ProductFamilies.CPX: "imc" + str(pop_ch.mc) + "_scrubaddresslo",
                                      ProductFamilies.ICX: "memss.mc" + str(pop_ch.mc) + ".ch" + str(pop_ch.ch) +
                                                           ".scrubaddresslo",
                                      ProductFamilies.SNR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(pop_ch.ch) +
                                                           ".scrubaddresslo"
                                      }
            pop_ch.sktobj.uncore.get_by_path(scrub_addrlo_path_dict[self._product]).rankadd.write(addresslo)
            scrub_addr2lo_path_dict = {ProductFamilies.CLX: "imc" + str(pop_ch.mc) + "_scrubaddress2lo",
                                       ProductFamilies.CPX: "imc" + str(pop_ch.mc) + "_scrubaddress2lo",
                                       ProductFamilies.ICX: "memss.mc" + str(pop_ch.mc) + ".ch" + str(pop_ch.ch) +
                                                            ".scrubaddress2lo",
                                       ProductFamilies.SNR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(pop_ch.ch) +
                                                            ".scrubaddress2lo"
                                       }
            pop_ch.sktobj.uncore.get_by_path(scrub_addr2lo_path_dict[self._product]).baseadd.write(addresslo)

    def check_for_scrub_error(self, pop_ch_list):
        """

        :param pop_ch_list:   populated memory channels list
        :return: True if error found, otherwise False
        """
        patrol_scrub_error_found = False
        self._sdp.halt()
        self._log.info("Checking for patrol scrub error detected in registers(retry_rd_err_log.patspr")

        for pop_ch in pop_ch_list:
            pop_ch.regs.set_access('mem')

            rd_err_path_dict = {
                ProductFamilies.CLX: "imc" + str(pop_ch.mc) + "_c" + str(pop_ch.ch) + "_retry_rd_err_log",
                ProductFamilies.CPX: "imc" + str(pop_ch.mc) + "_c" + str(pop_ch.ch) + "_retry_rd_err_log",
                ProductFamilies.ICX: "memss.mc" + str(pop_ch.mc) + ".ch" + str(pop_ch.ch) + ".retry_rd_err_log",
                ProductFamilies.SNR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(pop_ch.ch) + ".retry_rd_err_log"
                }
            if pop_ch.sktobj.uncore.get_by_path(rd_err_path_dict[self._product]).patspr == 1:
                self._log.info("Error was detected by patrol scrubber at mc=" + str(pop_ch.mc) +
                               " ch=" + str(pop_ch.ch) + "\n")
                patrol_scrub_error_found = True
                break
        if not patrol_scrub_error_found:
            self._log.error(" No patrol scrub errors occurred in registers")

        self._sdp.go()
        return patrol_scrub_error_found

    def set_patrol_scrub_mode(self, pop_ch_list, sa_mode=1, tad_id=0, set_tad=False):
        """
        Function to enable SAMode(system address mode) - this test requires scrubbing is in this mode

        :param self:
        :param pop_ch_list:   populated memory channels list
        :param sa_mode: 1=Source Address Mode enabled
        :param tad_id: Target Address Decoder
        :param set_tad: setting Target Address Decoder to False
        """
        self._log.info("Setting system Address mode(SAMode)=" + str(sa_mode))

        for pop_ch in pop_ch_list:
            pop_ch.regs.set_access('mem')
            scrub_addrhi_path_dict = {ProductFamilies.CLX: "imc" + str(pop_ch.mc) + "scrubaddresshi",
                                      ProductFamilies.CPX: "imc" + str(pop_ch.mc) + "scrubaddresshi",
                                      ProductFamilies.ICX: "memss.mc" + str(pop_ch.mc) + ".ch" + str(pop_ch.ch) +
                                                           ".scrubaddresshi",
                                      ProductFamilies.SNR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(pop_ch.ch) +
                                                           ".scrubaddresshi"
                                      }
            pop_ch.sktobj.uncore.get_by_path(scrub_addrhi_path_dict[self._product]).ptl_sa_mode.write(sa_mode)
            if set_tad:
                pop_ch.sktobj.uncore.get_by_path(scrub_addrhi_path_dict[self._product]).tad_rule.write(tad_id)
                pop_ch.sktobj.uncore.get_by_path(scrub_addrhi_path_dict[self._product]).minimum_tad_rule.write(tad_id)
                pop_ch.sktobj.uncore.get_by_path(scrub_addrhi_path_dict[self._product]).maximum_tad_rule.write(tad_id)

            scrub_addr2hi_path_dict = {ProductFamilies.CLX: "imc" + str(pop_ch.mc) + "scrubaddress2hi",
                                       ProductFamilies.CPX: "imc" + str(pop_ch.mc) + "scrubaddress2hi",
                                       ProductFamilies.ICX: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                                           pop_ch.ch) + ".scrubaddresshi",
                                       ProductFamilies.SNR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                                           pop_ch.ch) + ".scrubaddresshi"
                                       }
            pop_ch.sktobj.uncore.get_by_path(scrub_addr2hi_path_dict[self._product]).ptl_sa_mode.write(sa_mode)
            if set_tad:
                pop_ch.sktobj.uncore.get_by_path(scrub_addr2hi_path_dict[self._product]).tad_rule.write(tad_id)
                pop_ch.sktobj.uncore.get_by_path(scrub_addr2hi_path_dict[self._product]).minimum_tad_rule.write(tad_id)
                pop_ch.sktobj.uncore.get_by_path(scrub_addr2hi_path_dict[self._product]).maximum_tad_rule.write(tad_id)
