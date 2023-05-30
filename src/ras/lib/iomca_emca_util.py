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


class IomcaEmcaUtil(object):
    """
    IomcaEmca Util class, provides below functionality
    1. Check eMCA gen2 enabled
    """

    list_14nm_silicon_family = [ProductFamilies.SKX, ProductFamilies.CLX, ProductFamilies.CPX]
    iomca_en_product_reg_path_dict = {ProductFamilies.CPX: "iio_iiomiscctrl_b3d05f0.enable_io_mca",
                                      ProductFamilies.SKX: "iio_iiomiscctrl_b3d05f0.enable_io_mca",
                                      ProductFamilies.CLX: "iio_iiomiscctrl_b3d05f0.enable_io_mca",
                                      ProductFamilies.ICX: "ubox.ncevents.ncevents_cr_uboxerrctl2_cfg.enable_io_mca",
                                      ProductFamilies.SPR: "ubox.ncevents.ncevents_cr_uboxerrctl2_cfg.enable_io_mca"}

    def __init__(self, log, cfg_opts, csp = None, common_content_lib = None):
        self._log = log
        self._csp = csp
        self._cfg = cfg_opts
        self._common_content_lib = common_content_lib
        self._product = self._common_content_lib.get_platform_family()

        if self._common_content_lib is None:
            raise RuntimeError("The common_content_lib object should be not NULL...")

        if self._product != ProductFamilies.SPR and self._csp is None:
            raise RuntimeError("The cscript object should be not NULL...")

    @staticmethod
    def is_emca_gen2_enabled_using_sv(pythonsv, log):
        """
        This Function Verifies whether emca gen2 is enabled or Not

        :return: True is emca gen2 is enabled else False
        """
        mapmcetomsmi = pythonsv.get_by_path(pythonsv.UNCORE, "memss.m2mem0.mci_ctl2.mapmcetomsmi")
        log.info("Getting the value of mapmcetomsmi : {}".format(mapmcetomsmi))
        mapcmcitocsmi = pythonsv.get_by_path(pythonsv.UNCORE, "memss.m2mem0.mci_ctl2.mapcmcitocsmi")
        log.info("Getting the value of mapcmcitocsmi : {}".format(mapcmcitocsmi))

        if mapmcetomsmi[0] == "0x01L" and mapcmcitocsmi[0] == "0x01L" or \
                mapmcetomsmi[0] == 0x1 and mapcmcitocsmi[0] == 0x1:
            log.info("eMCA gen 2 Config has been enabled")
            return True
        else:
            log.error("eMCA gen 2 Config has not been enabled")
            return False

    def is_emca_gen2_enabled(self):
        """
        Function to checkeamca_gen2 enabled.

        :raise : RuntimeError if any exception from cscripts.
        :return: True of emca gen2 is enabled else False
        """
        try:
            if self._product == ProductFamilies.SPR:
                return self._common_content_lib.execute_pythonsv_function(self.is_emca_gen2_enabled_using_sv)

            if self._product in self.list_14nm_silicon_family:
                mapmcetomsmi = self._csp.get_by_path(self._csp.UNCORE, "imc0_m2mem_mci_ctl2.mapmcetomsmi")
                self._log.info("Getting the value of mapmcetomsmi : {}".format(mapmcetomsmi))
                mapcmcitocsmi = self._csp.get_by_path(self._csp.UNCORE, "imc0_m2mem_mci_ctl2.mapcmcitocsmi")
                self._log.info("Getting the value of mapcmcitocsmi : {}".format(mapcmcitocsmi))
            else:
                mapmcetomsmi = self._csp.get_by_path(self._csp.UNCORE, "memss.m2mem0.mci_ctl2.mapmcetomsmi")
                self._log.info("Getting the value of mapmcetomsmi : {}".format(mapmcetomsmi))
                mapcmcitocsmi = self._csp.get_by_path(self._csp.UNCORE, "memss.m2mem0.mci_ctl2.mapcmcitocsmi")
                self._log.info("Getting the value of mapcmcitocsmi : {}".format(mapcmcitocsmi))

            if mapmcetomsmi[0] == "0x01L" and mapcmcitocsmi[0] == "0x01L" or \
                    mapmcetomsmi[0] == 0x1 and mapcmcitocsmi[0] == 0x1:
                self._log.info("eMCA gen 2 Config has been enabled")
                return True
            else:
                self._log.error("eMCA gen 2 Config has not been enabled")
                return False
        except Exception as e:
            log_error = "An exception occurred:\n{}".format(str(e))
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def is_iomca_enabled(self):
        """
        Function to return if iomoca feature is enabled or not
        :return: Boolean
        """
        try:
            iomca_enable_status = False
            self._log.info("Verify if Iomca is enabled Successfully or not")
            #   Checking the iomca enable value
            iomca_enable_check_reg = self._csp.get_by_path(self._csp.UNCORE,
                                                           self.iomca_en_product_reg_path_dict[self._product])
            
            iomca_status = int(str(iomca_enable_check_reg[0]).replace("0x", "").replace("L", ""))
            
            #   Verifying iomca is enabled or not
            if iomca_status == 1:
                self._log.info("Iomca is Successfully Enabled")
                iomca_enable_status = True
            else:
                self._log.error("Iomca is not Enabled")
            return iomca_enable_status

        except Exception as e:
            self._log.error("An exception occurred:\n{}".format(str(e)))