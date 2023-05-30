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


class SmbusErrorUtil(object):
    """
    Smbus Errors Util class, provides below functionality
    1. Check if sbmbus error recovery enabled
    2. Smbus error injection
    3. Verify smb status
    """

    SMB_CMD_CFG_SPD_REG = "smb_cmd_cfg_spd%d"
    SMB_TSOD_CONFIG_CFG_SPD_REG = "smb_tsod_config_cfg_spd%d"
    SMB_STATUS_CFG_REG = "smb_status_cfg_spd%d"

    # registers for 14nm silicons
    PCU_CR_SMB_CMD_CFG_REG = "pcu_cr_smb_cmd_cfg_%d"
    PCU_CR_SMB_TSOD_CONFIG_CFG_REG = "pcu_cr_smb_tsod_config_cfg_%d"
    PCU_CR_SMB_STATUS_CFG_REG = "pcu_cr_smb_status_cfg_%d"

    list_14nm_silicon_family = [ProductFamilies.SKX, ProductFamilies.CLX, ProductFamilies.CPX]

    def __init__(self, log, sdp, csp):
        self._log = log
        self._sdp = sdp
        self._csp = csp

    def is_smbus_error_recovery_enabled(self, socket_index=0, mc=None):
        """
        Check if SMBus error recovery is enabled by BIOS
        :param socket_index: The given socket index to check
        :param mc: The given mc to check
        :return: True if SMBus error recovery is enabled, False if not
        """
        smb_rec = False

        try:
            self._log.info("Getting mc list from xnmMemicalsUtils object from CScripts...")
            self._sdp.halt()
            mu_obj = self._csp.get_xnm_memicals_utils_object()
            if self._csp.silicon_cpu_family in self.list_14nm_silicon_family:
                pop_ch_list = mu_obj.getPopChList(socket=socket_index, mc=mc)
            else:
                pop_ch_list = mu_obj.get_pop_ch_list(socket=socket_index, mc=mc)

            for pop_ch in pop_ch_list:
                if self._csp.silicon_cpu_family in self.list_14nm_silicon_family:
                    smb_cntl = pop_ch.sktObj.uncore0.readregister(self.PCU_CR_SMB_CMD_CFG_REG % pop_ch.ch)
                else:
                    smb_cntl = pop_ch.sktobj.uncore.punit.readregister(self.SMB_CMD_CFG_SPD_REG % pop_ch.ch)

                if smb_cntl.smb_sbe_en == 0 and smb_cntl.smb_sbe_smi_en == 0:
                    self._log.info("%s SMBus Error Recovery disabled" % pop_ch._name)
                else:
                    self._log.info("%s SMBus Error Recovery enabled" % pop_ch._name)
                    smb_rec = True
        except Exception as ex:
            self._log.error("An exception occurred:'{}'".format(ex))
        finally:
            self._sdp.go()

        return smb_rec

    def smb_error_injection(self, socket_index=0, mc=None):
        """
        Inject SMBus error and verify recovery
        :param socket_index: The given socket index to check
        :param mc: The given mc to check
        :return: True if SMBus error is recovered, False if not
        """
        smb_rec = False

        try:
            self._log.info("Getting mc list from xnmMemicalsUtils object from CScripts...")
            self._sdp.halt()
            mu_obj = self._csp.get_xnm_memicals_utils_object()
            if self._csp.silicon_cpu_family in self.list_14nm_silicon_family:
                pop_ch_list = mu_obj.getPopChList(socket=socket_index, mc=mc)
            else:
                pop_ch_list = mu_obj.get_pop_ch_list(socket=socket_index, mc=mc)

            for pop_ch in pop_ch_list:
                if self._csp.silicon_cpu_family in self.list_14nm_silicon_family:
                    tsod_cfg_orig = pop_ch.sktObj.uncore0.readregister(
                        self.PCU_CR_SMB_TSOD_CONFIG_CFG_REG % pop_ch.ch)
                else:
                    tsod_cfg_orig = pop_ch.sktobj.uncore.punit.readregister(
                        self.SMB_TSOD_CONFIG_CFG_SPD_REG % pop_ch.ch)

                dimm_orig = tsod_cfg_orig.group0_dimm_present

                self._log.info("group0_dimm_present value = 0x%x" % tsod_cfg_orig)

                self._log.info("Induce error by enabling TSOD polling on empty slot")
                tsod_cfg_orig.group0_dimm_present = 0x3

                if self._csp.silicon_cpu_family in self.list_14nm_silicon_family:
                    tsod_cfg_new = pop_ch.sktObj.uncore0.readregister(
                        self.PCU_CR_SMB_TSOD_CONFIG_CFG_REG % pop_ch.ch)
                else:
                    tsod_cfg_new = pop_ch.sktobj.uncore.punit.readregister(
                        self.SMB_TSOD_CONFIG_CFG_SPD_REG % pop_ch.ch)

                self._log.info("group0_dimm_present changed to = 0x%x" % tsod_cfg_new)
                self._log.info("Checking SMBus Error status bit...")
                if self.verify_smb_status(socket_index=socket_index):
                    tsod_cfg_new.group0_dimm_present = dimm_orig
                    self._log.info("group0_dimm_present value = 0x%x" % tsod_cfg_new)
                    smb_rec = True
        except Exception as ex:
            self._log.error("An exception occurred:'{}'".format(ex))
        finally:
            self._sdp.go()

        return smb_rec

    def verify_smb_status(self, socket_index=None, mc=None):
        """
        SMBus status to check error detection and recovery
        :param socket_index: The given socket index to check
        :param mc: The given mc to check
        :return: True if SMBus error is recovered, False if not
        """
        smb_err_rec = False
        try:
            self._log.info("Getting mc list from xnmMemicalsUtils object from CScripts...")
            self._sdp.halt()
            mu_obj = self._csp.get_xnm_memicals_utils_object()
            if self._csp.silicon_cpu_family in self.list_14nm_silicon_family:
                pop_ch_list = mu_obj.getPopChList(socket=socket_index, mc=mc)
            else:
                pop_ch_list = mu_obj.get_pop_ch_list(socket=socket_index, mc=mc)

            for pop_ch in pop_ch_list:
                if self._csp.silicon_cpu_family in self.list_14nm_silicon_family:
                    smb_status = pop_ch.sktObj.uncore0.readregister(self.PCU_CR_SMB_STATUS_CFG_REG % pop_ch.ch)
                else:
                    smb_status = pop_ch.sktobj.uncore.punit.readregister(self.SMB_STATUS_CFG_REG % pop_ch.ch)

                if smb_status.smb_sbe == 1:
                    self._log.info("%s SMBus Error detected on " % pop_ch._name)
                    self._log.info("%s Waiting for error to be recovered" % pop_ch._name)

                while smb_status.smb_sbe:
                    if self._csp.silicon_cpu_family in self.list_14nm_silicon_family:
                        smb_status = pop_ch.sktObj.uncore0.readregister(self.PCU_CR_SMB_STATUS_CFG_REG % pop_ch.ch)
                    else:
                        smb_status = pop_ch.sktobj.uncore.punit.readregister(self.SMB_STATUS_CFG_REG % pop_ch.ch)

                if smb_status.smb_sbe == 0:
                    self._log.info("%s SMBus Error Recovery completed" % pop_ch._name)
                    smb_err_rec = True
        except Exception as ex:
            self._log.error("An exception occurred:'{}'".format(ex))
        finally:
            self._sdp.go()

        return smb_err_rec
