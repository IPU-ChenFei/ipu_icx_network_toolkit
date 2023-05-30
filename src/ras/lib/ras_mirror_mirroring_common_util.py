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


class MemoryMirroringUtil(object):
    """
    MemoryMirroringUtil Util class having the functionality for memory mirroring Test Cases.
    1. Check the mirror enable.
    2. Validation for memory configuration.
    3. DDR4 is enable or not.
    """
    _MEM_LOG_FILE = "memory_log_file.log"

    memory_en_product_reg_path_dict = { ProductFamilies.CPX: "iio_iiomiscctrl_b3d05f0.enable_io_mca",
                                        ProductFamilies.SKX: "iio_iiomiscctrl_b3d05f0.enable_io_mca",
                                        ProductFamilies.CLX: "iio_iiomiscctrl_b3d05f0.enable_io_mca",
                                ProductFamilies.ICX: "ubox.ncevents.ncevents_cr_uboxerrctl2_cfg.enable_io_mca",
                                        ProductFamilies.SPR: "ubox.ncevents.ncevents_cr_uboxerrctl2_cfg.enable_io_mca"}

    def __init__(self, log, csp, sdp=None):
        self._log = log
        self._csp = csp
        self._product = self._csp.silicon_cpu_family
        self._sdp = sdp

    def is_ddr_mirroring_enabled(self):
        """
        Function to return if mirroring is enabled by looking at m2mem0.mode.mirrorddr4

        :return: Boolean
        """
        mirroring_m2mem0_mode_dict = {ProductFamilies.CPX: "imc0_m2mem_mode",
                                      ProductFamilies.SKX: "imc0_m2mem_mode",
                                      ProductFamilies.CLX: "imc0_m2mem_mode",
                                      ProductFamilies.SPR: "memss.m2mem0.mode",
                                      ProductFamilies.ICX: "memss.m2mem0.mode"}
        mirroring_enable_status = False
        try:

            self._log.info("Verify if mirroring is enabled by Checking m2mem0.mode.mirrorddr4")
            self._sdp.start_log(self._MEM_LOG_FILE, "w")
            #  Checking the mirroring enable or not
            mirroring_enable_check_output = self._csp.get_by_path(self._csp.UNCORE,
                                                           mirroring_m2mem0_mode_dict[self._product]).show()
            self._sdp.stop_log()
            with open(self._MEM_LOG_FILE, "r") as mirroring_log:
                self._log.info("Checking the log file")
                mirroring_enable_log = mirroring_log.read()  # Getting the mc_dimminfo log
                self._log.info(mirroring_enable_log)
            if self._product == ProductFamilies.SPR:
                mirroring_enable_status = self._csp.get_by_path(self._csp.UNCORE,
                                                            mirroring_m2mem0_mode_dict[self._product]+ ".mirrorddr5")
            else:
                mirroring_enable_status = self._csp.get_by_path(self._csp.UNCORE,
                                                                mirroring_m2mem0_mode_dict[
                                                                    self._product] + ".mirrorddr4")
            if mirroring_enable_status:
                self._log.info("Mirroring is Successfully Enabled")
                mirroring_enable_status = True
            else:
                self._log.error("Mirroring is not Enabled")

        except Exception as e:
            self._log.error("An exception occurred:\n{}".format(str(e)))

        return mirroring_enable_status

    def get_mirror_status_registers(self):
        """
        Verify if mirror mode registers have been set

        :return: True or False
        """

        self._log.info("Check whether Mirror mode is enabled")

        mirror_dic = {ProductFamilies.ICX: 'memss.m2mem0.mode',
                      ProductFamilies.CLX: 'imc0_m2mem_mode',
                      ProductFamilies.CPX: 'imc0_m2mem_mode',
                      ProductFamilies.SPR: 'memss.m2mem0.mode',
                      ProductFamilies.SKX: 'imc0_m2mem_mode',
                      }

        mirror_mode_config_path = mirror_dic.get(self._product)

        if mirror_mode_config_path:
            mirror_enabled = self._csp.get_by_path(self._csp.UNCORE,
                                                   mirror_mode_config_path +
                                                   ".mirrorddr4")
        else:
            raise RuntimeError("Test has not been implemented for" + self._product)

        return mirror_enabled
