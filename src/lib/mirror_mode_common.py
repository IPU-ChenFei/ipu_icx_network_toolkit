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


class MirrorCommon(object):
    """
    This Class is Used as Common Class For all the Mirror Mode Functionality Test Cases
    """

    def __init__(self, log, csp, sdp):
        self._log = log
        self._cscripts = csp
        self._sdp = sdp
        self._product = self._cscripts.silicon_cpu_family

    def get_mirror_status_registers(self):
        """
        Verify if mirror mode registers have been set

        :return: True or False
        """
        try:
            self._log.info("Check whether Mirror mode is enabled")

            mirror_dic = {ProductFamilies.ICX: 'memss.m2mem0.mode',
                          ProductFamilies.SKX: 'imc0_m2mem_mode',
                          ProductFamilies.CLX: 'imc0_m2mem_mode',
                          ProductFamilies.CPX: 'imc0_m2mem_mode'
                          }

            mirror_mode_config_path = mirror_dic.get(self._product)
            self._sdp.halt()
            if mirror_mode_config_path:
                mirror_enabled = self._cscripts.get_field_value(scope=self._cscripts.UNCORE,
                                                                reg_path=mirror_mode_config_path,
                                                                field="mirrorddr4")
            else:
                raise RuntimeError("Test has not been implemented for" + self._product)
            return mirror_enabled
        except Exception as ex:
            log_error = "Unable to verify if Mirror Mode is Enabled"
            self._log.error(log_error)
            raise ex
        finally:
            self._sdp.go()

    def is_machine_in_mirror_mode(self):
        """
        This method is to check the status of mirror mode

        return: true if enable else False
        """
        try:
            mc_util_obj = self._cscripts.get_mc_utils_object()
            if self._cscripts.silicon_cpu_family == ProductFamilies.ICX:
                self._sdp.halt()
                if mc_util_obj.is_mirror_scrub_enabled():
                    self._log.info("Mirror Scrub is Enabled")
                    return True
                else:
                    self._log.error("Mirror Scrub is not Enabled")
                    return False
            else:
                demandscrubwrdis = self._cscripts.get_by_path(self._cscripts.UNCORE,
                                                              "imc0_m2mem_defeatures0.demandscrubwrdis")
                scrubcheckrddis = self._cscripts.get_by_path(self._cscripts.UNCORE,
                                                             "imc0_m2mem_defeatures0.scrubcheckrddis")
                self._log.info("Checking the status of Mirror Scrub")

                if demandscrubwrdis == 0 and scrubcheckrddis == 0:
                    pop_mc_list = mc_util_obj.mu.getPopMcList(socket=0, mc=0)
                    for pop_mc in pop_mc_list:
                        self._log.info("Reading register : imc%d_m2mem_defeatures0.scrubcheckrddis" % pop_mc.mc)
                        if pop_mc.sktObj.uncore0.readregister("imc%d_m2mem_defeatures0" % pop_mc.mc).scrubcheckrddis:
                            self._log.error("Mirror Scrub is not Enabled")
                            return False
                    self._log.info("Mirror Scrub is enabled")
                else:
                    self._log.error("Mirror Scrub is not Enabled")
                    return False

        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex

        finally:
            self._log.info("Resuming the device")
            self._sdp.go()

        return True
