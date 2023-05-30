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

import os
import time
import re
from dtaf_core.lib.base_test_case import BaseTestCase

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.console_log import ConsoleLogProvider

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.iomca_emca_util import IomcaEmcaUtil
from src.ras.lib.ras_einj_util import RasEinjCommon
from dtaf_core.lib.dtaf_constants import ProductFamilies


class VerifyEmcaCsmiMorphingBase(BaseTestCase):
    """
    Glasgow_id : 58266 , 63548
    Verify basic SMI signaling- core CSMI via IFU eMCA gen 2
    This test verifies EMCA CSMI Morphing functionally is supported as a basis for corrected error SMI test cases

    :return:  True if pass, False if not
    """
    _HEXADECIMAL_CONSTANT = 16
    _INJECTION_TIMEOUT = 15
    _MEMORY_CORRECTABLE_ERROR_ADDRESS = 0x112345000
    _READ_ERROR_STRING = "bits[6:4] = 001: Memory Read Error"

    _FILE_NAME = "emca_csmi_morphing_check_log.txt"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file, console_log_path):
        """
        Create an instance of sut os provider, BiosProvider, ConsoleLogProvider,  AcPowerControlProvider
         BIOS util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        :param console_log_path: console log file path
        """
        super(VerifyEmcaCsmiMorphingBase, self).__init__(test_log, arguments, cfg_opts)

        self._cfg = cfg_opts
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        serial_log_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self._slog = ProviderFactory.create(serial_log_cfg, test_log)  # type: ConsoleLogProvider

        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)  # type: AcPowerControlProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        if self._cscripts.silicon_cpu_family in [ProductFamilies.ICX, ProductFamilies.SNR,
                                                 ProductFamilies.SPR]:
            self._cpxo_count = 28
        else:
            self._cpxo_count = 40
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider

        self._nvd = self._cscripts.get_cscripts_nvd_object()
        self._sv = self._cscripts.get_cscripts_utils().getSVComponent()

        self._content_cfg = ContentConfiguration(self._log)
        self._itp_halt_time = self._content_cfg.itp_halt_time_in_sec()
        self._ei = self._cscripts.get_cscripts_utils().get_ei_obj()

        self._ras = self._cscripts.get_cscripts_utils().get_ras_obj()
        self._error = self._cscripts.get_cscripts_utils().get_error_obj()

        self.serial_console_log_path = console_log_path

        self._ras_einj_obj = RasEinjCommon(self._log, self._os, cfg_opts, self._common_content_lib,
                                           self._content_cfg, self._ac_power)

        self._reboot_timeout_in_sec = self._content_cfg.get_reboot_timeout()
        self._ac_power_time_out_in_sec = self._content_cfg.ac_timeout_delay_in_sec()
        self._os_time_out_in_sec = self._content_cfg.os_full_ac_cycle_time_out()

        self._command_timeout = self._content_cfg.get_command_timeout()
        self.log_file_path = self.get_ecma_csmi_check_log_path()

        self._product = self._cscripts.silicon_cpu_family

    def emca_csmi_detect(self):
        """
        This Method can be used to verify MSR bits 0x17E.
        The source of the SMI will be M2M and can be verified by reading MSR 0x17E.
        This MSR is only written in the EMCA gen 2 mode.

        :return: Returns True if verified , False or else.
        :raise: RuntimeError if itp command fails to execute.
        """
        try:
            check_msr = self._sdp.msr_read(0x17E)
            self._log.info("The source of the SMI will be M2M and can be verified by reading MSR 0x17E."
                           "(This MSR is only written in the EMCA gen 2 mode.)")
            count = 0
            for each in check_msr:
                if count < self._cpxo_count:
                    if each == 0:
                        self._log.error("MSR value is not Set Appropriately!")
                        return False
                    if each != 0:
                        count = count + 1
                else:
                    break
            self._log.info("MSR value read successfully!")
            return True
        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex

    def get_ecma_csmi_check_log_path(self):
        """
        # Here We get the Path for emca csmi morphing check log file

        :return: log_file_path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(cur_path, self._FILE_NAME)
        return path


    def get_emcal1diraddr(self):
        """
        This address is EMCA L1 DIR address which can be searched from the PuTTY serial logs
        when SUT boots to the OS or EFI shell.
        This Method is used to get the EMCAL1DirAddr value from serial logs.

        :return Returns the value of EMCAL1DirAddr if passed, else zero.
        :raise RuntimeError if there is any error while collecting the logs
        """
        emcal1diraddr = 0
        self._os.reboot(int(self._reboot_timeout_in_sec))
        self._os.wait_for_os(self._os_time_out_in_sec)
        _init = _now = time.time()
        while self._reboot_timeout_in_sec > _now - _init:
            console_log_path = os.path.join(self._slog.logpath_local, self.serial_console_log_path)
            console_data = open(console_log_path).readlines()
            for each in console_data:
                if re.match("EmcaL1DirAddr = ", each):
                    print("here")
                    emcal1diraddr = re.match("EmcaL1DirAddr = (\w+)", each).group(1)
                    self._log.info("EmcaL1DirAddr Value = {}".format(emcal1diraddr))
                    return emcal1diraddr
            else:
                _now = time.time()
                continue
        self._log.error('Timeout to get EmcaL1DirAddr from COM driver!')
        return emcal1diraddr

    def verify_emca_csmi_morphing(self):
        """
        Verify basic SMI signaling- core CSMI via IFU eMCA gen 2
        This test verifies EMCA CSMI Morphing functionally is supported as a basis for corrected error SMI test cases

        :return:  True if pass, False if not
        """
        try:

            emca_mci_ctl2_dict = {ProductFamilies.ICX: 'memss.mc0.ch0.imc0_mc_ctl2',
                                  ProductFamilies.SNR: 'memss.mc0.ch0.imc0_mc_ctl2',
                                  ProductFamilies.SPR: 'memss.mc0.ch0.imc0_mc_ctl2',
                                  ProductFamilies.SKX: 'imc0_m2mem_mci_ctl2',
                                  ProductFamilies.CLX: 'imc0_m2mem_mci_ctl2',
                                  ProductFamilies.CPX: 'imc0_m2mem_mci_ctl2'
                                  }
            viral_control_dict = {ProductFamilies.ICX: 'punit.viral_control_cfg',
                                  ProductFamilies.SNR: 'punit.viral_control_cfg',
                                  ProductFamilies.SPR: 'punit.viral_control_cfg',
                                  ProductFamilies.SKX: 'pcu_cr_viral_control_cfg',
                                  ProductFamilies.CLX: 'pcu_cr_viral_control_cfg',
                                  ProductFamilies.CPX: 'pcu_cr_viral_control_cfg'
                                  }
            mci_status_shadow_dict = {ProductFamilies.ICX: 'memss.m2mem0.mci_status_shadow',
                                      ProductFamilies.SNR: 'memss.m2mem0.mci_status_shadow',
                                      ProductFamilies.SPR: 'memss.m2mem0.mci_status_shadow',
                                      ProductFamilies.SKX: 'imc0_m2mem_mci_status_shadow',
                                      ProductFamilies.CLX: 'imc0_m2mem_mci_status_shadow',
                                      ProductFamilies.CPX: 'imc0_m2mem_mci_status_shadow'
                                      }
            # opening the Cscripts Log File and Appending the Data
            self._sdp.start_log(self.log_file_path, "w")
            iomca_emca_utils_obj = IomcaEmcaUtil(self._log, self._cfg, self._cscripts, self._common_content_lib)
            self._log.info("Getting the EMCAl1DirAddr Value!")
            emca_l1_dir_address_integer_value = int(self.get_emcal1diraddr(),
                                                    self._HEXADECIMAL_CONSTANT)  # 16 represents hexa decimal
            emca_l1_dir_address_value = hex(emca_l1_dir_address_integer_value)
            self._log.info("EMCAL1DirAddr Value = {}".format(emca_l1_dir_address_value))
            if iomca_emca_utils_obj.is_emca_gen2_enabled():
                self._sv.refresh()
                self._log.info("Getting the Memory Read Error Value")
                self._cscripts.get_by_path(self._cscripts.UNCORE, emca_mci_ctl2_dict[
                    self._cscripts.silicon_cpu_family]).show()
                self._log.info(self._cscripts.get_by_path(self._cscripts.UNCORE, emca_mci_ctl2_dict[
                    self._cscripts.silicon_cpu_family]).show())
                self._cscripts.get_by_path(self._cscripts.UNCORE, viral_control_dict[
                    self._cscripts.silicon_cpu_family]).show()
                self._log.info(self._cscripts.get_by_path(self._cscripts.UNCORE, viral_control_dict[
                    self._cscripts.silicon_cpu_family]).show())
                self._ras.checkEMCA2Cap()
                self._log.info("Perform functional EMCA CSMI Morphing test")
                self._log.info("Halting system ...")
                self._sdp.halt()
                time.sleep(float(self._itp_halt_time))
                self._log.info("setting reset break = 1 and smm entry break = 1")
                self._sdp.itp.cv.resetbreak = 1
                self._sdp.itp.cv.smmentrybreak = 1
                self._sdp.go()
                time.sleep(float(self._itp_halt_time))
                self._log.info("Verify no memory errors are logged at this point!")
                self._error.dumpMemErrors()
                self._log.info("Injecting Memory Correctable error!")
                self._ei.injectMemError(self._MEMORY_CORRECTABLE_ERROR_ADDRESS, errType="ce")
                time.sleep(self._INJECTION_TIMEOUT)
                if self.emca_csmi_detect():
                    self._log.info("Error will be logged in the M2M bank.")
                    self._error.dumpMemErrors()
                    if self._cscripts.silicon_cpu_family in [ProductFamilies.CLX, ProductFamilies.SKX,
                                                             ProductFamilies.CPX]:
                        self._cscripts.get_sockets()[0].uncore0.showsearch("mci_status")
                    if self._cscripts.silicon_cpu_family in [ProductFamilies.ICX, ProductFamilies.SNR,
                                                             ProductFamilies.SPR]:
                        self._cscripts.get_sockets()[0].uncore.showsearch("mci_status")

                    self._cscripts.get_by_path(self._cscripts.UNCORE, mci_status_shadow_dict[
                        self._cscripts.silicon_cpu_family]).show()
                    self._log.info(self._cscripts.get_by_path(self._cscripts.UNCORE, mci_status_shadow_dict[
                        self._cscripts.silicon_cpu_family]).show())
                    self._log.info("(MSB--> LSB) Making sure that the {}".format(self._READ_ERROR_STRING))
                    mcacod_desc = self._cscripts.get_by_path(self._cscripts.UNCORE, mci_status_shadow_dict[
                        self._cscripts.silicon_cpu_family]).mcacod.description
                    self._log.info("Mcacod Description -> {}".format(mcacod_desc))
                    self._log.info("Parsing mcacod description for Memory Read Error!")
                    readerrormatchedstring = ""
                    for each_line in mcacod_desc[0].split("\n"):
                        if self._READ_ERROR_STRING in each_line:
                            readerrormatchedstring = each_line
                    if readerrormatchedstring == "":
                        self._log.info("Memory Read Error Not Detected!")
                        return False
                    self._log.info("The {} Detected".format(self._READ_ERROR_STRING))
                    self._log.info("Halting system ...")
                    self._sdp.halt()
                    time.sleep(float(self._itp_halt_time))
                    self._log.info("setting smm exit break = 1")
                    self._sdp.itp.cv.smmexitbreak = 1
                    self._sdp.go()
                    if emca_l1_dir_address_value != 0:
                        self._ras.dumpEMCA2logs(emca_l1_dir_address_value)
                    else:
                        self._log.error("Could not get EMCAl1DirAddr Value!")
                        return False
                    self._log.info("Clear the smmexit break and release the system.")
                    self._sdp.itp.cv.smmentrybreak = 0
                    self._sdp.itp.cv.smmexitbreak = 0
                    self._sdp.stop_log()
                    self._sdp.reset_target()
                    self._sdp.halt()
                    self._sdp.go()
                    return True
                else:
                    self._log.error("Did Not Encounter Memory Read Error.")
                    return False
            else:
                self._log.error("EMCA gen 2 is not enabled.")
                return False

        except Exception as ex:
            log_error = "Unable to Perform EMCA CSMI Morphing due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise ex
