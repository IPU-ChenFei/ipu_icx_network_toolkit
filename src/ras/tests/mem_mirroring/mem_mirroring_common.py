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

import os
import time

from dtaf_core.lib.base_test_case import BaseTestCase
from src.lib.content_base_test_case import ContentBaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.lib.mirror_mode_common import MirrorCommon
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.ras_mirror_mirroring_common_util import MemoryMirroringUtil
from src.ras.lib.ras_common_utils import RasCommonUtil
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.install_collateral import InstallCollateral


class MemMirroringBaseTest(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the MemMirroring Test Cases
    """
    _STEP_SIZE = 10
    _END_INDEX = 3
    _START_INDEX = 0
    _END_ADDR = 0x000100000100
    _START_ADDR = 0x000100000000
    _CORE_ADDR = 0x100000000
    _MIRROR_MODE = 0x1
    _CHECK_IN_ADDRESS_LIST = [0x000100000000, 0x000200000000, 0x000000010000, 0x000000100000, 0x000001000000,
                              0x000010000000, 0x001000000000, 0x000100010000, 0x000100100000, 0x000010100000]
    _MEM_LOG_FILE = "memory_mirroring_log_file.txt"
    _REGX_FOR_MIRROR_MAPPED = [r"\s*Mirror\s*"]
    _REGX_FOR_MIRROR_CHECK_ADDR = [r"Mirror.*1"]
    _REGEX_FOR_KLAXON_NO_ERRORS = [r"No\serrors\sfound"]
    _REGEX_FOR_UNCORR_ERR_ON_SECONDARY_CHANNEL = [r"ECC\sInjection\sin\sMirror\sMode.\sChannel.1",
                                                  r"Error\sinjected\ssuccessfully"]
    _REGEX_FOR_VALIDATING_UCE_MIRROR_FAILOVER = [r"Error\sis\sconsumed\sby\shost\smemory\sread\srequest",
                                                 r"ECC\sInjection\sin\sParMirr\sMode"]
    _MC_DIMM_INFO_REGEX = [r"(ECC / CAP Checking\s*\|\s*On\s*/\s*On\s*\|\s*On\s*/\s*On\s*\|\s*On\s*/\s*On\s*\|)",
                           r"(Directory Mode\s*\|\s*Off\s*\|\s*Off\s*\|\s*Off\s*\|)"]
    _UC_BOTH_CHANNEL_FOR_14NM = [0x0, 0x4, 0x0]
    _UC_BOTH_CHANNEL_FOR_10NM = [0x0, 0x304, 0x0]

    _UC_ON_PRI_CE_ON_CHANNEL_14NM = [0x1, 0xe, 0x0]
    _UC_ON_PRI_CE_ON_CHANNEL_10NM = [0x1, 0xe, 0x0]

    _CE_ON_PRIMARY_CHANNEL_10NM = [0x0, 0x0, 0x0]
    _CE_ON_PRIMARY_CHANNEL_14NM = [0x1, 0xa, 0x0]

    _UC_ON_PRIMARY_CHANNEL_14NM = [0x1, 0xc, 0x0]
    _UC_ON_PRIMARY_CHANNEl_10NM = [0x1, 0xc, 0x0]

    _MCE_LOG_COMMANDS_LIST = ["mcelog --daemon", "mcelog --client"]
    _VALIDATE_FAILOVER = {
        ProductFamilies.CPX: "imc0_m2mem_mci_misc_shadow.mirrorfailover",
        ProductFamilies.CLX: "imc0_m2mem_mci_misc_shadow.mirrorfailover",
        ProductFamilies.SKX: "imc0_m2mem_mci_misc_shadow.mirrorfailover",
        ProductFamilies.ICX: "memss.m2mem0.mci_misc_shadow.mirrorfailover",
        ProductFamilies.SPR: "memss.m2mem0.mci_misc_shadow.mirrorfailover"
    }
    _CHECK_CORR_ERR = {
        ProductFamilies.CPX: "imc0_m2mem_mci_misc_shadow",
        ProductFamilies.CLX: "imc0_m2mem_mci_misc_shadow",
        ProductFamilies.SKX: "imc0_m2mem_mci_misc_shadow",
        ProductFamilies.ICX: "memss.m2mem0.mci_misc_shadow",
        ProductFamilies.SPR: "memss.m2mem0.mci_misc_shadow"
    }
    _VALIDATE_CE_AND_UCE_ERR = {
        ProductFamilies.CPX: "imc0_m2mem_mci_misc_shadow.mirrorcorrerr",
        ProductFamilies.CLX: "imc0_m2mem_mci_misc_shadow.mirrorcorrerr",
        ProductFamilies.SKX: "imc0_m2mem_mci_misc_shadow.mirrorcorrerr",
        ProductFamilies.ICX: "memss.m2mem0.mci_misc_shadow.mirrorcorrerr",
        ProductFamilies.SPR: "memss.m2mem0.mci_misc_shadow.mirrorcorrerr"
    }
    _VALIDATE_ERR_TYPE = {
        ProductFamilies.CPX: "imc0_m2mem_mci_misc_shadow.errortype",
        ProductFamilies.CLX: "imc0_m2mem_mci_misc_shadow.errortype",
        ProductFamilies.SKX: "imc0_m2mem_mci_misc_shadow.errortype",
        ProductFamilies.ICX: "memss.m2mem0.mci_misc_shadow.errortype",
        ProductFamilies.SPR: "memss.m2mem0.mci_misc_shadow.errortype"
    }
    _DIMM_INFO = {
        ProductFamilies.SKX: "self._mc.skxdimminfo()",
        ProductFamilies.CLX: "self._mc.clxdimminfo()",
        ProductFamilies.CPX: "self._mc.cpxdimminfo()",
        ProductFamilies.ICX: "self._mc.dimminfo()",
        ProductFamilies.SPR: "self._mc.dimminfo()"
    }

    _CHECK_CHANNEL_FAILOVER = {
        ProductFamilies.CPX: "imc0_m2mem_mirrorfailover",
        ProductFamilies.CLX: "imc0_m2mem_mirrorfailover",
        ProductFamilies.SKX: "imc0_m2mem_mirrorfailover",
        ProductFamilies.ICX: "memss.m2mem0.mirrorfailover",
        ProductFamilies.SPR: "memss.m2mem0.mirrorfailover"
    }

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
        BIOS util and Config util,

        :param test_log: Log object
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(MemMirroringBaseTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

        self._cfg = cfg_opts

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        if self._cscripts.silicon_cpu_family == ProductFamilies.SPR:
            self.ras_obj = self._csp.get_ras_object()
        else:
            self.ras_obj = self._cscripts.get_cscripts_utils().get_ras_obj()

        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)
        self._mirror_common = MirrorCommon(self._log, self._cscripts, self._sdp)

        self._common_content_config = ContentConfiguration(self._log)

        self._reboot_timeout_in_sec = self._common_content_config.get_reboot_timeout()
        self._execute_cmd_timeout_in_sec = self._common_content_config.get_command_timeout()
        self.memory_mirroring_utils_obj = MemoryMirroringUtil(self._log, self._cscripts, self._sdp)
        self._mc = self._cscripts.get_dimminfo_object()
        if self._cscripts.silicon_cpu_family == ProductFamilies.CPX:
            self._klaxon = self._cscripts.get_klaxon_object()
        self._ei = self._cscripts.get_cscripts_utils().get_ei_obj()
        self._ras_common_obj = RasCommonUtil(self._log, self._os, cfg_opts, self._common_content_config, self._bios_util,
                                             self._cscripts, self._sdp)
        self._os_log_obj = OsLogVerifyCommon(self._log, self._os, self._common_content_config, self._common_content_lib)
        self._mce_log_cfg = InstallCollateral(self._log, self._os, cfg_opts)
        self._stress_app_execute_time = self._common_content_config.memory_stress_test_execute_time()

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs and verify it.

        :return: None
        """
        super(MemMirroringBaseTest,self).prepare()

    def get_mc_dimm_info(self, mc_dimm_info_regex):
        """
        This method is for getting the dimm information.

        return: True if all regex found else false
        raise: RuntimeError
        """
        try:
            self._log.info("Execute the mc.dimminfo command")
            if not self._sdp.is_halted():
                self._log.info("Halting the system for dimminfo execution:")
                self._sdp.halt()
                time.sleep(self._common_content_config.itp_halt_time_in_sec())
            #   Going to open the cscript log file to capture the mc_dimminfo output
            self._sdp.start_log(self._MEM_LOG_FILE, "w")
            eval(self._DIMM_INFO[self._common_content_lib.get_platform_family()])
            self._sdp.stop_log()

            #   Reading the log output of mc_dimminfo
            with open(self._MEM_LOG_FILE, "r") as dimminfo_log:
                self._log.info("Checking the mc_dimminfo log file")
                mc_dimminfo_log = dimminfo_log.read()  # Getting the mc_dimminfo log
                #   Calling the Memory mirror utils object method to verify dimminfo
                self._log.info("Extracting the Dimm info from : {}".format(mc_dimminfo_log))
                mc_dimm_check_status = self._common_content_lib.extract_regex_matches_from_file(mc_dimminfo_log,
                                                                                                mc_dimm_info_regex)
                if mc_dimm_check_status:
                    self._log.info("Validation of memory configurations from mc_dimminfo PASS")
                else:
                    self._log.error("Validation of memory configurations from mc_dimminfo Fail")
            return mc_dimm_check_status
        except Exception as ex:
            log_err = "An exception Occurred during executing dimm info {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)
        finally:
            self._log.info("Resume the Machine")
            self._sdp.go()

    def check_mirror_address(self):
        """
        This Method is to check the mirror Address.

        return:None
        raise: RuntimeError
        """
        try:
            flag = 0
            self._sdp.halt()
            product = self._common_content_lib.get_platform_family()
            if product in self._common_content_lib.SILICON_10NM_CPU:
                add_tran_obj = self._cscripts.get_add_tran_obj()
                self._log.info("Check the Mirror Address")
                ti = add_tran_obj.TranslationInfo()
                for addr_tran in self._CHECK_IN_ADDRESS_LIST:
                    ti.core_addr = addr_tran
                    self._sdp.start_log(self._MEM_LOG_FILE, "w")
                    add_tran_obj.core_address_to_dram_address(ti, verbose=1)
                    ti.show_results()
                    self._sdp.stop_log()
                    with open(self._MEM_LOG_FILE, 'r') as mirroring_log:
                        add_mapped_log = mirroring_log.read()
                        self._log.info(add_mapped_log)
                        address_mapped_status = self._common_content_lib.extract_regex_matches_from_file(
                            add_mapped_log, self._REGX_FOR_MIRROR_CHECK_ADDR)
                    if address_mapped_status:
                        self._CORE_ADDR = addr_tran
                        flag = 1
                        break
                if not flag:
                    log_err = "Memory Address is not Found in mirrored region"
                    self._log.error(log_err)
                    raise Exception(log_err)
        except Exception as ex:
            log_err = "An Exception occured during address Translation: {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)
        finally:
            self._sdp.go()

    def is_address_mapped_to_dimm_space(self, start_addr, end_addr):
        """
        This method is use to check the address is mapped to dimm space or not.

        :param: start_addr: starting address
        :param: end_addr: ending address
        :return: True if Mapped else False
        :raise: RuntimeError
        """
        try:
            if not self._sdp.is_halted():
                self._sdp.halt()
            self._sdp.start_log(self._MEM_LOG_FILE, 'w')
            self._ei.sa2da_table(start_addr=start_addr, end_addr=end_addr, step_size=self._STEP_SIZE)
            self._sdp.stop_log()
            with open(self._MEM_LOG_FILE, 'r') as mirroring_log:
                add_mapped_log = mirroring_log.read()
                self._log.info(add_mapped_log)
                address_mapped_status = self._common_content_lib.extract_regex_matches_from_file(
                    add_mapped_log, self._REGX_FOR_MIRROR_MAPPED)

                if address_mapped_status:
                    self._log.info("Addressed Mapped to dimm space from {} to {}".format(start_addr, end_addr))
                    ret_value = True
                else:
                    self._log.error("Address is not Mapped to dimm space between {} to {}".format(start_addr, end_addr))
                    ret_value = False
            return ret_value
        except Exception as ex:
            log_err = "An exception Occurred {}".format(ex)
            self._log.error(log_err)
        finally:
            self._sdp.go()

    def check_mirroring_error_was_detected(self, validation_list, fail_over=False):
        """
        This Method is to check injected error ie: correctable, uncorrectable, error type, mirror failure

        :param validation_list: list of expected register value.
        :param fail_over: This is to check the fail over if needed.
        return: True if error found else False
        raise: RuntimeError
        """
        try:
            ret_val = False
            product = self._common_content_lib.get_platform_family()
            if not self._sdp.is_halted():
                self._sdp.halt()
            self._sdp.start_log(self._MEM_LOG_FILE, "w")
            self._cscripts.get_by_path(self._cscripts.UNCORE, self._CHECK_CORR_ERR[product]).show()
            self._sdp.stop_log()
            with open(self._MEM_LOG_FILE, 'r') as mirroring_log:
                corr_err_log = mirroring_log.read()
                self._log.info(corr_err_log)

            if self._cscripts.get_by_path(self._cscripts.UNCORE, self._VALIDATE_CE_AND_UCE_ERR[product]) == \
                    validation_list[0]:
                self._log.info("Mirror Error register found Expected: {}".format(validation_list[0]))
                ret_val = True

            if self._cscripts.get_by_path(self._cscripts.UNCORE, self._VALIDATE_ERR_TYPE[product]) and \
                    validation_list[1] == validation_list[1]:
                self._log.info("Error Type Register Found Expected Value: {}".format(validation_list[1]))
                ret_val = ret_val and True

            if fail_over:
                if not self._cscripts.get_by_path(self._cscripts.UNCORE, self._VALIDATE_FAILOVER[product]) == \
                       validation_list[2]:
                    self._log.info("Mirror Fail over Register Found Expected value ")
                    ret_val = ret_val and True

            return ret_val
        except Exception as ex:
            log_err = "An Exception Occurred {}".format(ex)
            self._log.error(log_err)

        finally:
            self._sdp.go()

    def check_mci_status_register(self):
        """
        This function is to check the mci status register.

        :return : True if found else false.
        :raise : RuntimeError
        """
        try:
            ret_val = False
            product = self._common_content_lib.get_platform_family()
            self._sdp.start_log(self._MEM_LOG_FILE, "w")
            if product in self._common_content_lib.SILICON_10NM_CPU:
                self._cscripts.get_sockets()[0].uncore.showsearch("mci_status_shadow")
                self._cscripts.get_by_path(self._cscripts.UNCORE, "memss.m2mem0.mci_status_shadow").show()
            else:
                self._cscripts.get_by_path(self._cscripts.UNCORE, "imc0_m2mem_mci_status").show()
            self._sdp.stop_log()
            with open(self._MEM_LOG_FILE, 'r') as mirroring_log:
                err_decode_log = mirroring_log.read()
                self._log.info(err_decode_log)

            if product in self._common_content_lib.SILICON_10NM_CPU:
                if self._cscripts.get_by_path(self._cscripts.UNCORE, "memss.m2mem0.mci_status_shadow.corrcount"):
                    ret_val = True
            else:
                if self._cscripts.get_by_path(self._cscripts.UNCORE, "imc0_m2mem_mci_status.corrcount"):
                    ret_val = True

        except Exception as ex:
            log_err = "An Exception Occurred: {}".format(ex)
            self._log.error(log_err)

        return ret_val

    def smmentrybreak_mode_control(self, smmbreak_mode):
        """
        This method is to set or reset the smmentry break.

        :param: smmbreak_mode:- to set or reset the smmentry break.
        :return: None
        :raise: RuntimeError
        """
        try:
            self._sdp.halt()
            time.sleep(self._common_content_config.itp_halt_time_in_sec())
            self._sdp.itp.cv.smmentrybreak = smmbreak_mode
            self._sdp.go()

        except Exception as ex:
            log_err = "An exception Occurred: {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def ddr_channel_failure_detection(self):
        """
        This method is use to detect the ddr4 channel failure.

        return: True if detected else False.
        raise: RuntimeError
        """
        try:
            ret_val = False
            product = self._common_content_lib.get_platform_family()
            self._sdp.start_log(self._MEM_LOG_FILE, "w")

            if product in self._common_content_lib.SILICON_10NM_CPU:
                self._cscripts.get_sockets()[0].uncore.showsearch("mci_status_shadow")
                self._cscripts.get_by_path(self._cscripts.UNCORE, "memss.m2mem0.mci_status_shadow").show()
            else:
                self._cscripts.get_by_path(self._cscripts.UNCORE, "imc0_m2mem_mci_status").show()
            self._sdp.stop_log()
            with open(self._MEM_LOG_FILE, 'r') as mirroring_log:
                err_decode_log = mirroring_log.read()
                self._log.info(err_decode_log)

            if product in self._common_content_lib.SILICON_10NM_CPU:
                if self._cscripts.get_by_path(self._cscripts.UNCORE, "memss.m2mem0.mci_status_shadow.corrcount"):
                    ret_val = True
            else:
                if self._cscripts.get_by_path(self._cscripts.UNCORE, "imc0_m2mem_mci_status.corrcount"):
                    ret_val = True

            self._cscripts.get_by_path(self._cscripts.UNCORE, self._CHECK_CHANNEL_FAILOVER[product]).show()
            self._sdp.stop_log()
            with open(self._MEM_LOG_FILE, 'r') as mirroring_log:
                corr_err_log = mirroring_log.read()
                self._log.info(corr_err_log)
            if product in self._common_content_lib.SILICON_10NM_CPU:
                if self._cscripts.get_by_path(self._cscripts.UNCORE, self._CHECK_CHANNEL_FAILOVER[product] +
                                                                     ".ddr4chnlfailed") == 0x1:
                    ret_val = True
            else:
                if self._cscripts.get_by_path(self._cscripts.UNCORE, self._CHECK_CORR_ERR[product] +
                                                                     ".ddr4chnlfailed") == 0x2:
                    ret_val = True
            return ret_val
        except Exception as ex:
            log_err = "An Exception Occurred: {}".format(ex)
            self._log.error(log_err)

    def enable_interleave_bios_knobs(self, bios_config_file):
        """
        This method is to set the bios knobs and verify it.

        :param bios_config_file
        """
        if bios_config_file:
            bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), bios_config_file)
        self.bios_util.load_bios_defaults()
        self.bios_util.set_bios_knob(bios_config_file)  # To set the bios knob setting.
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        self.bios_util.verify_bios_knob(bios_config_file)

    def check_system_error(self, Error_sign):
        """
        This function is to run commands to check any unexplained errors exist.

        :return: True is any unexplained error has occurred else False
        """
        # log_file_path = "klaxon_mem_error_log.log"
        error_flag = False
        self._log.info("Checking the system errors")
        self._sdp.start_log(self.log_file_path, "w")  # Opening the Cscripts Log File to log the output
        self._klaxon.m2mem_errors()
        self._sdp.stop_log()  # CLosing the Cscripts Log File
        if self.parse_error(Error_sign):  # parsing error for checking if any error detected or not
            error_flag = True
        self._sdp.start_log(self.log_file_path, "w")  # Opening the Cscripts Log File to log the output
        self._klaxon.imc_errors()
        self._sdp.stop_log()  # CLosing the Cscripts Log File
        if self.parse_error(Error_sign):  # parsing error for checking if error detected or not
            error_flag = True

        return error_flag

    def parse_error(self, Error_Exp):
        """
        This function is to Parse cscript logs and checks whether there is any unexplained error exist

        :raise : OSError, IOError Exception is raised if any error has occurred during reading the cscript log file
        :return: True is any unexplained error has occurred else False
        """
        error_flag = False
        try:
            with open(self.log_file_path, "r") as log_file:  # Open the cscript lof file for checking any error
                log_details = log_file.read()
                expected_error = re.findall(Error_Exp, log_details)
                actual_experienced_error = [string for string in expected_error if string != ""]  # filter empty strings
                if actual_experienced_error:
                    for line in actual_experienced_error:
                        if int(line) > 0:
                            # Capture the error log information in test case log file
                            self._log.info("Start of m2mem errors details")
                            self._log.info("Output of failed log is: '{}'".format(log_details))
                            self._log.info("End of m2mem errors details")
                            error_flag = True
                            break

        except (OSError, IOError) as e:
            self._log.error("Error in reading file due to exception '{}'".format(e))
            raise e
        if error_flag:
            log_error = "System has experienced some unexplained errors"
            self._log.error(log_error)
        else:
            self._log.info("No unexplained errors detected ")
        return error_flag
