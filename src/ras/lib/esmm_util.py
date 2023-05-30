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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.ras_smm_common import RasSmmCommon



class EsmmSaveUtil(object):
    """
    Esmm Save Util class, provides below functionality
    1. Check if Esmm Save enabled
    2. Check if is_long_and_blocked_flow_indication_enabled
    3. Check if Esmm Bios Write Protect Enabled
    """

    def __init__(self, log, sdp, csp, cfg_opts):
        self._log = log
        self._sdp = sdp
        self._csp = csp
        self._ras_common = RasSmmCommon(self._log, self._csp, self._sdp)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, self._log)
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)

    def is_esmm_save_state_enable(self):
        """
        Check if esmm save state is enabled for the system

        :return: true if esmm save states check is enabled, false if not enabled
        """

        _dict_esmm_enable = {
            ProductFamilies.CLX: "ubox_ncdecs_smm_feature_control_cfg_b0d08f1.smm_cpu_save_en",
            ProductFamilies.SKX: "ubox_ncdecs_smm_feature_control_cfg_b0d08f1.smm_cpu_save_en",
            ProductFamilies.SNR: "ubox.ncdecs.smm_feature_control_cfg.smm_cpu_save_en",
            ProductFamilies.ICX: "ubox.ncdecs.smm_feature_control_cfg.smm_cpu_save_en",
            ProductFamilies.SPR: "ubox.ncdecs.smm_feature_control_cfg.smm_cpu_save_en",
            ProductFamilies.CPX: "ubox_ncdecs_smm_feature_control_cfg_b0d08f1.smm_cpu_save_en",
        }
        ret_value = False
        try:
            esmm_save_status = self._csp.get_by_path(self._csp.UNCORE, _dict_esmm_enable[self._csp.silicon_cpu_family])
            if esmm_save_status == 0x1:
                self._log.info("esmm save state is enabled")
                ret_value = True
            else:
                self._log.error("esmm save state is not enabled")
        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex

        return ret_value

    def is_long_and_blocked_flow_indication_enabled(self):
        """
        Check if long and blocked flow indication is enabled for the system

        :return: true if long and blocked flow indication enable, false if not enable.
        """
        _dict_long_and_blocked_flow_indication = {
            ProductFamilies.CPX: "core0.thread0.ucode_smm_mca_cap.long_flow_indication",
            ProductFamilies.CLX: "core0.thread0.ucode_smm_mca_cap.long_flow_indication",
            ProductFamilies.SKX: "core0.thread0.ucode_smm_mca_cap.long_flow_indication",
            ProductFamilies.SNR: "cpu.module1.core0.thread0.msrs.ucode_cr_smm_mca_cap.long_flow_indication",
            ProductFamilies.ICX: "cpu.cores[0].thread0.core_msr.smm_mca_cap.long_flow_indication",
            ProductFamilies.SPR: "cpu.cores[0].thread0.core_msr.smm_mca_cap.long_flow_indication",
        }
        ret_val = False
        try:
            self._ras_common.enter_smm_mode()
            self._sdp.halt()
            long_flow_indication = self._csp.get_by_path(self._csp.SOCKET,
                                                         _dict_long_and_blocked_flow_indication[
                                                             self._csp.silicon_cpu_family])

            if long_flow_indication == 0x1:
                self._log.info("Long and Blocked Flow Indication is enabled")
                ret_val = True
            else:
                print("Long and Blocked Flow Indication is not enabled")
            self._sdp.go()

        except Exception as e:
            self._log.info("{}".format(str(e)))

        return ret_val

    def is_esmm_bios_write_protect_enable(self):
        """
        Check if esmm bios write protect is enabled for the system
        :return: true if esmm bios write protect enabled, false if not enabled
        """
        _dict_esmm_bios_write_protect_enable = {
            ProductFamilies.ICX: "ubox.ncdecs.smm_feature_control_cfg.smm_code_chk_en",
            ProductFamilies.SPR: "ubox.ncdecs.smm_feature_control_cfg.smm_code_chk_en",
            ProductFamilies.SKX: "ubox_ncdecs_smm_feature_control_cfg_b0d08f1.smm_code_chk_en",
            ProductFamilies.SNR: "ubox.ncdecs.smm_feature_control_cfg.smm_code_chk_en",
            ProductFamilies.CPX: "ubox_ncdecs_smm_feature_control_cfg_b0d08f1.smm_code_chk_en",
        }
        ret_value = False
        try:
            esmm_save_status = self._csp.get_by_path(self._csp.UNCORE,
                                                     _dict_esmm_bios_write_protect_enable[self._csp.silicon_cpu_family])
            if esmm_save_status == 0x1:
                self._log.info("esmm bios write protect is enabled")
                ret_value = True
            else:
                self._log.error("esmm bios write protect is not enabled")
        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex

        return ret_value

    def __loop_verify_smm_save_state_msrs(self, smm_save_state_msrs_list):
        """
        Loop through given list of smm save state msrs and ascertain it is readable for each socket
        :param smm_save_state_msrs_list: The given list of smm save state msrs to check
        :return: True if SMM dump state storage internal MSRs are available, False if not available
        """
        smm_save_state_storage_msrs_available = True

        try:
            self.core = self._common_content_configuration.get_memory_core()
            self.socket = self._common_content_configuration.get_memory_socket()
            self.thread = self._common_content_configuration.get_memory_thread()

            expected_smm_save_state_msrs_lowercase_list = [msr.lower() for msr in smm_save_state_msrs_list]
            self._log.info("Verify all SMM Dump State Storage MSRs are available for socket %s, core %d, thread %d" %
                          (self._csp.SOCKET, self.core, self.thread))
            self._product = self._common_content_lib.get_platform_family()
            msrs_reg_path_dict = {
                ProductFamilies.SPR: "core{}.thread{}".format(self.core, self.thread),
                ProductFamilies.SKX: "core{}.thread{}".format(self.core, self.thread),
                ProductFamilies.CLX: "core{}.thread{}".format(self.core, self.thread),
                ProductFamilies.CPX: "core{}.thread{}".format(self.core, self.thread),
            }
            #sv.socket0.core0.thread0.ucode_smram_cr0
            #Verifying msrs value after entering into smm mode

            for msr in expected_smm_save_state_msrs_lowercase_list:
                smm_dump_storage_msr_value = self._csp.get_by_path(scope=self._csp.SOCKET,reg_path=(msrs_reg_path_dict[self._product]
                                                                   + "." + msr), socket_index=self.socket)
                if not smm_dump_storage_msr_value >= 0:
                    self._log.error("FAIL: MSR " + str(msr) + " is not available for SMM Dump State Storage")
                    smm_save_state_storage_msrs_available = False
                    return smm_save_state_storage_msrs_available
                self._log.info("MSR " + str(msr) + " is available for SMM Dump State Storage")

        except Exception as e:
            self._log.error("An exception occurred:\n" + str(e))
            smm_save_state_storage_msrs_available = False

        return smm_save_state_storage_msrs_available

    def verify_smm_dump_state_storage_msrs_available(self, verify_non_smm_break_msrs=True, verify_smm_break_msrs=True):
        """
        This function Checks if SMM dump state storage internal MSRs are available for system to save data
        :param verify_non_smm_break_msrs: The given list of non smm break state msrs to check
        :param verify_smm_break_msrs: The given list of smm break state msrs to check
        :return: True if SMM dump state storage internal MSRs are available, False if not available
        """
        smm_dump_state_storage_msrs_available = True

        expected_smm_save_state_msrs_list = [
            'UCODE_SMRAM_CR0', 'UCODE_SMRAM_CR3', 'UCODE_SMRAM_EFLAGS', 'UCODE_SMRAM_EFER', 'UCODE_SMRAM_RIP',
            'UCODE_SMRAM_DR6', 'UCODE_SMRAM_DR7', 'UCODE_SMRAM_TR_LDTR', 'UCODE_SMRAM_GS_FS',
            'UCODE_SMRAM_DS_SS', 'UCODE_SMRAM_CS_ES', 'UCODE_SMRAM_IOMISCINFO', 'UCODE_SMRAM_IO_MEM_ADDR',
            'UCODE_SMRAM_RDI', 'UCODE_SMRAM_RSI', 'UCODE_SMRAM_RBP', 'UCODE_SMRAM_RSP', 'UCODE_SMRAM_RBX',
            'UCODE_SMRAM_RDX', 'UCODE_SMRAM_RCX', 'UCODE_SMRAM_RAX', 'UCODE_SMRAM_R8', 'UCODE_SMRAM_R9',
            'UCODE_SMRAM_R10', 'UCODE_SMRAM_R11', 'UCODE_SMRAM_R12', 'UCODE_SMRAM_R13', 'UCODE_SMRAM_R14',
            'UCODE_SMRAM_R15', 'UCODE_SMRAM_EVENT_CTL_HLT_IO', 'UCODE_SMRAM_SMBASE', 'UCODE_SMRAM_SMM_REVID',
            'UCODE_SMRAM_IEDBASE', 'UCODE_SMRAM_EPTP_ENABLE', 'UCODE_SMRAM_EPTP',
            'UCODE_SMRAM_CR4', 'UCODE_SMRAM_IO_RSI', 'UCODE_SMRAM_IO_RCX', 'UCODE_SMRAM_IO_RIP', 'UCODE_SMRAM_IO_RDI',
        ]

        expected_smm_break_save_state_msrs_list = [
            'UCODE_SMRAM_LDTR_BASE', 'UCODE_SMRAM_IDTR_BASE', 'UCODE_SMRAM_GDTR_BASE'
        ]

        try:
            self._ras_common.smm_entry_msrs()
            if verify_non_smm_break_msrs:
                self._log.info("Check MSRs that do not require SMM Break")
                if not self.__loop_verify_smm_save_state_msrs(expected_smm_save_state_msrs_list):
                    self._log.error("FAIL: All SMM Dump State Storage MSRs are available")
                    smm_dump_state_storage_msrs_available = False
                else:
                    self._log.info("PASS: All SMM Dump State Storage MSRs are available")

            if verify_smm_break_msrs:
                self._sdp.halt_and_check()
                self._log.info("Check MSRs that require SMM Break")
                if not self.__loop_verify_smm_save_state_msrs(expected_smm_break_save_state_msrs_list):
                    self._log.error("FAIL: All SMM Break Dump State Storage MSRs are not available")
                    smm_dump_state_storage_msrs_available = False
                else:
                    self._log.info("PASS: All SMM Break Dump State Storage MSRs are available")

                self._log.info("Unhalt all threads")
                self._sdp.go()
        except Exception as e:
            self._log.error("An exception occurred:\n" + str(e))
            smm_dump_state_storage_msrs_available = False

        finally:
            self._log.info("Unhalt all threads")
            self._sdp.go()
        return smm_dump_state_storage_msrs_available
