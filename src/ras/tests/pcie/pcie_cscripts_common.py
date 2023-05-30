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
import os
import re
import time
import pandas as pd
from dtaf_core.lib.dtaf_constants import ProductFamilies, OperatingSystems
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from src.lib import content_exceptions
from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.ras.lib.ras_smm_common import RasSmmCommon
from src.ras.lib.ras_common_utils import RasCommonUtil
from src.ras.lib.ras_einj_util import RasEinjCommon
from src.lib.content_configuration import ContentConfiguration
from src.lib.content_base_test_case import ContentBaseTestCase
from src.pcie.lib.pcie_telemetry import PcieTelemetry


class PcieCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Pcie Test Cases
    """
    _REGEX_CMD_FOR_CORRECTABLE_ERROR = r"Correctable\serror\sdetected"
    _REGEX_CMD_FOR_NON_FATAL_ERROR = r"Uncorrectable\serror\sdetected"
    _REGEX_CMD_FOR_FATAL_ERROR = r"Uncorrectable\serror\sdetected"
    _FILE_NAME = "cscripts_log_file.log"
    _PCIE_UNCORRECTABLE_ERROR_STRING = "Uncorrectable error detected in uncerrsts.completion_time_out_status"
    PORT_INFO_DICT = {}
    _PCIE_PORT_INFO = {}
    _DEVCTRL2_COMPLTOVAL = 0xE
    _XP_TO_PCIE_TIMEOUT_SELECT = 0x2
    _SOCKET_NUMBER = 0
    cto_set_for_port_reg = {ProductFamilies.ICX: "pcie.pxps.ports.cfg.erruncsts.cte",
                            ProductFamilies.SNR: "pcie.ports.conf.uncerrsts.completion_time_out_status",
                            ProductFamilies.SPR: "pcie.pxps.ports.cfg.erruncsts.cte"}

    _CHECK_PORT_REGEX = "\|\s+(\d+)\s+\|\s+(\S+)\s+\|\s+(\S+)\s+\|"
    _INJECT_CORRECTABLE_ERROR_TO_SOCKET0 = 0
    _INJECT_CORRECTABLE_ERROR_TO_PORT0 = 0
    _PCIE_CORRECTABLE_ERROR_STRING = "Correctable error detected in corerrsts.receiver_error_status"
    _PCIE_ERROR_COUNTER_VALUE = [0x00000000, 0x00000001, 0x00000002]
    _IEH_GLOBAL_SYSEVTSTS_PATH = "ieh_global.gsysevtsts"
    _DETECT_PCIE = "slot"
    _PCIE_COL_NAME = "slot/down"

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file
    ):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), bios_config_file)
        super(PcieCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)
        self.log_file_path = self.get_cscripts_log_file()
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self._common_content_configuration = ContentConfiguration(self._log)

        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._ei = self._cscripts.get_cscripts_utils().get_ei_obj()
        self._pcie = self._cscripts.get_cscripts_utils().get_pcie_obj()
        self._product = self._cscripts.silicon_cpu_family
        self._wait_for_dmi_link_down = self._common_content_configuration.dmi_link_down_delay()
        self._wait_for_pcie_cto_timeout_reconfig_in_sec = \
            self._common_content_configuration.wait_for_pcie_cto_timeout_reconfig()

        self._smm = RasSmmCommon(self._log, self._cscripts, self._sdp)
        self._ras_common = RasCommonUtil(self._log, self._os, cfg_opts, self._common_content_configuration,
                                         bios_util=self._bios_util)

        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)

        self._ras_einj_util = RasEinjCommon(self._log, self._os, cfg_opts, self._common_content_lib,
                                            self._common_content_configuration, self._ac_power)
        self.PCIE_SOCKET = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        self.SOCKET_LIST = self._common_content_configuration.get_socket_slot_pcie_errinj()
        self._pcie_telemetry = PcieTelemetry(self._log, self._os, cfg_opts)

        # self.portno, self.portdata = self.get_error_inj_pcie_port_num()
        self.portdata = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()
        self.PORT_LIST = self._common_content_configuration.get_pxp_port_pcie_errinj()
        self.ei_inject_pcie_uncorr_dict = {
            ProductFamilies.ICX: "self._ei.injectPcieError({}, '{}', 'uce')".format(self.PCIE_SOCKET,
                                                                                    self.portdata),
            ProductFamilies.SPR: "self._ei.injectPcieError({}, '{}', 'uce')".format(self.PCIE_SOCKET,
                                                                                    self.portdata),
            ProductFamilies.SNR: "self._ei.injectPcieError({}, '{}', 'uce', False)".format(self.PCIE_SOCKET,
                                                                                           self.portdata.split(".")[1])
        }
        self.ei_inject_pcie_corr_dict = {
            ProductFamilies.ICX: "self._ei.injectPcieError({}, '{}', 'ce')".format(self.PCIE_SOCKET,
                                                                                   self.portdata),
            ProductFamilies.SPR: "self._ei.injectPcieError({}, '{}', 'ce')".format(self.PCIE_SOCKET,
                                                                                   self.portdata),
            ProductFamilies.SNR: "self._ei.injectPcieError({}, '{}', 'ce')".format(self.PCIE_SOCKET,
                                                                                   self.portdata.split(".")[1])
        }
        self._ctes_verify_dict = {
            ProductFamilies.ICX: "self._cscripts.get_sockets()[{}].uncore.pcie.pxps.port0.cfg.erruncsev.ctes".format(
                self.PCIE_SOCKET),
            ProductFamilies.SPR: "self._cscripts.get_sockets()[{}].uncore.pi5.{}.cfg.erruncsev.ctes"
                .format(self.PCIE_SOCKET, self.portdata),
            ProductFamilies.SNR: "self._cscripts.get_sockets()[{}].uncore.pcie.port0.conf.uncerrsev."
                                 "completion_time_out_severity".format(self.PCIE_SOCKET)
        }
        self._ctes_set_dict = {
            ProductFamilies.ICX: "self._cscripts.get_sockets()[{}]."
                                 "uncore.pcie.pxps.port0.cfg.erruncsev.ctes = 1".format(self.PCIE_SOCKET),
            ProductFamilies.SPR: "self._cscripts.get_sockets()[{}]."
                                 "uncore.pi5.{}.cfg.erruncsev.ctes.write(1)".format(self.PCIE_SOCKET, self.portdata),
            ProductFamilies.SNR: "self._cscripts.get_sockets()[{}]."
                                 "uncore.pcie.port0.conf.uncerrsev."
                                 "completion_time_out_severity = 1".format(self.PCIE_SOCKET)
        }

    def get_cscripts_log_file(self):
        """
        Get the Path for Cscripts log file

        :return: log_file_path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(cur_path, self._FILE_NAME)

    def verify_injection_port_address(self):
        """
        This Method is Used to Verify if the port address for injection is valid or not.

        :raise: content_exceptions.TestSetupError if port address is not valid for  error injection
        """
        sec_bus_reg_path_dict = {ProductFamilies.SPR: "pi5.{}.cfg.secbus".format(self.portdata),
                                 ProductFamilies.ICX: "pi4.{}.cfg.secbus".format(self.portdata)}
        product_family = self._common_content_lib.get_platform_family()

        sec_bus_output = self._cscripts.get_by_path(self._cscripts.UNCORE, socket_index=self.PCIE_SOCKET,
                                                    reg_path=sec_bus_reg_path_dict[product_family])
        self._log.info(" Card Bus: {} is : {}".format(sec_bus_reg_path_dict[product_family],
                                                      sec_bus_output))
        if not sec_bus_output:
            self._log.info(" PCIe Card  is not enumerated ")
            raise content_exceptions.TestSetupError(
                "Card Enumeration failed  {}".format(sec_bus_reg_path_dict[product_family]))

    def verify_no_current_ieh_errors(self):
        """
        This Method is Used to Verify if there are any Previous Errors and Ideally there should not be any errors.

        :raise: RunTimeError if there are any Previous Ieh Errors
        """
        self._log.info("Verify if there are any Previous errors ...")
        errors = self._cscripts.get_by_path(self._cscripts.UNCORE, self._IEH_GLOBAL_SYSEVTSTS_PATH,
                                            self.PCIE_SOCKET).get_value()
        if errors == 0x0:
            self._log.info("There are No Previous Errors and Can Proceed with the Test Case")
        else:
            log_error = "There are Previous IEH Errors"
            self._log.error(log_error)
            raise Exception(log_error)

    def inject_ieh_global_mask_pcie_correctable_error(self, mask=True):
        """
        Inject Pcie Correctable Error by Halting the System and Verify if error is Successfully Injected
        or not - if masked=True - check ieh status shows no errors
        Note: registers are sticky - so a pwrgood reset is required between tests

        :param mask: True if checking for masked errors
        :type mask: Bool
        :return: True if error is detected and if mask check is verified
        :rtype: Bool
        """

        try:
            pcie_error_status = False
            self._smm.smm_entry()
            self._sdp.start_log(self.log_file_path, "w")
            self._log.info("Injecting Correctable Error using cscripts")
            for socket, port in (zip(self.SOCKET_LIST, self.PORT_LIST)):
                self._sdp.start_log(self.log_file_path, "w")
                self._log.info("injecting error-" + self.ei_inject_pcie_corr_dict[self._cscripts.silicon_cpu_family].
                               format(socket, port))
                eval(self.ei_inject_pcie_corr_dict[self._cscripts.silicon_cpu_family].format(socket, port))
                self._sdp.stop_log()
                self._log.info("Verify if error is Successfully Injected")
                error_status = self._cscripts.get_by_path(self._cscripts.UNCORE, self._IEH_GLOBAL_SYSEVTSTS_PATH,
                                                          socket).get_value()
                with open(self.log_file_path, "r") as log_file:
                    log_file_list = log_file.readlines()
                    regex_cmd = re.findall(self._REGEX_CMD_FOR_CORRECTABLE_ERROR, "".join(log_file_list))
                    if mask:
                        if error_status == 0x0 and len(regex_cmd) > 0:
                            self._log.info("PCIE Correctable error was Successfully Injected and Masked")
                            pcie_error_status = True
                        else:
                            self._log.error("PCIE Correctable Error is Not Injected")
                    else:
                        if error_status != 0 and len(regex_cmd) > 0:
                            self._log.info("PCIE Correctable error was Successfully Injected")
                            pcie_error_status = True
                        else:
                            self._log.error("PCIE Correctable Error is Not Injected")
        except Exception as ex:
            self._log.error("Unable to Inject PCIE Correctable Error due to the exception '{}'".format(ex))
            raise ex
        finally:
            self._smm.smm_exit()
            return pcie_error_status

    def injecting_pcie_non_fatal_error_and_mask(self, mask=True):
        """
        Inject Ieh Pcie Non Fatal Error by Halting the System and Verify if error is Successfully Injected or not
           if masked=True - check ieh status shows no errors
           Note: registers are sticky - so a pwrgood reset is required between tests

        :param mask: True if checking for masked errors
        :type mask: Bool
        :return: True if error is detected and if mask check is verified
        :rtype: Bool
        """
        try:
            pcie_error_status = False
            self._smm.smm_entry()
            for socket, port in (zip(self.SOCKET_LIST, self.PORT_LIST)):
                self._sdp.start_log(self.log_file_path)
                self._log.info("Injecting Non Fatal Error using Cscripts")
                eval(self.ei_inject_pcie_uncorr_dict[self._cscripts.silicon_cpu_family].format(socket, port))
                self._sdp.stop_log()
                self._log.info("Verifying if error is Successfully Injected or Not")
                error_status = self._cscripts.get_by_path(self._cscripts.UNCORE,
                                                          self._IEH_GLOBAL_SYSEVTSTS_PATH,
                                                          socket).get_value()
                with open(self.log_file_path, "r") as log_file:
                    regex_cmd = re.findall(self._REGEX_CMD_FOR_NON_FATAL_ERROR, "".join(log_file.readlines()))
                    if mask:
                        if error_status == 0x0 and len(regex_cmd) > 0:
                            self._log.info("PCIE Non Fatal error was Successfully Injected and Masked")
                            pcie_error_status = True
                        else:
                            self._log.error("PCIE Non Fatal Error is Not Injected")
                    else:
                        if error_status != 0x0 and len(regex_cmd) > 0:
                            self._log.info("PCIE Non Fatal error was Successfully Injected")
                            pcie_error_status = True
                        else:
                            self._log.error("PCIE Non Fatal Error is Not Injected")

        except Exception as ex:
            self._log.error("Unable to Inject PCIE Non Fatal Error due to the exception '{}'".format(ex))
            raise ex
        finally:
            self._smm.smm_exit()
            return pcie_error_status

    def inject_and_verify_ieh_pcie_fatal_error_and_mask(self, mask=True):
        """
        Set ctes severity=1 and Inject Ieh Pcie Fatal Error by Halting the System and Verify if error is Successfully
        Injected or not   if masked=True - check ieh status shows no errors
        Note: registers are sticky - so a pwrgood reset is required between tests

        :param mask: True if checking for masked errors
        :type mask: Bool
        :return: True if error is detected and if mask check is verified
        :rtype: Bool
        """
        try:
            pcie_error_status = False
            self._log.info("Halt the System ...")
            self._sdp.halt()
            for socket, port in (zip(self.SOCKET_LIST, self.PORT_LIST)):
                self._log.info("Check the status of completion timeout error severity for Fatal")
                ctes_status = eval(self._ctes_verify_dict[self._cscripts.silicon_cpu_family].format(socket))
                if ctes_status[0] == 0x0:
                    self._log.info("Set the completion timeout error severity to fatal")
                    eval(self._ctes_set_dict[self._cscripts.silicon_cpu_family].format(socket))
                    self._log.info("Verify the completion timeout error severity is set to fatal")
                    ctes_status = eval(self._ctes_verify_dict[self._cscripts.silicon_cpu_family].format(socket))
                    if ctes_status[0] == 0x1:
                        self._log.info("Completion timeout error severity set to fatal successfully")
                    else:
                        log_error = "Unable to set the completion timeout error severity set to fatal"
                        self._log.error(log_error)
                        raise Exception(log_error)
                self._log.info("completion timeout error severity is set to fatal")
                self._sdp.start_log(self.log_file_path, "w")
                self._smm.smm_entry()
                self._log.info("Inject the Fatal Error using CScripts")
                eval(self.ei_inject_pcie_uncorr_dict[self._cscripts.silicon_cpu_family].format(socket, port))
                self._sdp.stop_log()
                self._log.info("Verify if the Fatal error is Successfully Injected")
                error_status = self._cscripts.get_by_path(self._cscripts.UNCORE,
                                                          self._IEH_GLOBAL_SYSEVTSTS_PATH,
                                                          socket).get_value()
                with open(self.log_file_path, "r") as log_file:
                    regex_cmd = re.findall(self._REGEX_CMD_FOR_FATAL_ERROR, "".join(log_file.readlines()))
                    if mask:
                        if error_status == 0x0 and len(regex_cmd) > 0:
                            self._log.info("PCIE Fatal error was Successfully Injected and Masked")
                            pcie_error_status = True
                        else:
                            self._log.error("PCIE Fatal Error is Not Injected")
                    else:
                        if error_status != 0x0 and len(regex_cmd) > 0:
                            self._log.info("PCIE Fatal error was Successfully Injected")
                            pcie_error_status = True
                        else:
                            self._log.error("PCIE Fatal Error is Not Injected")

        except Exception as ex:
            self._log.error("Unable to Inject PCIE Fatal Error due to the Exception '{}'".format(ex))
            raise ex
        finally:
            self._smm.smm_exit()
            return pcie_error_status

    def set_iehs_mask_register(self, error_type):
        """
        This Method is Used to Enable the Iehs Mask register by iterating from ieh0 to ieh11 since iehs is failing to set the register .
        param error_type: Type of error on which the masking needs to be done.It could be 'correctable','non_fatal' or 'fatal'
        :return:None
        """
        set_ieh_mask_value = 0xffffffff
        ieh_list = ['ieh0', 'ieh1', 'ieh2', 'ieh3', 'ieh4', 'ieh5', 'ieh6', 'ieh7', 'ieh8', 'ieh9', 'ieh10', 'ieh11']
        ieh_error_mask_dict = {'correctable': 'gerrcormsk', 'non_fatal': 'gerrnonmsk', 'fatal': 'gerrfatmsk'}
        for value in ieh_list:
            try:
                ieh_register_path = "".join([value, '.', ieh_error_mask_dict[error_type]])
                self._log.info("Enable Iehs Mask for '{}' Errors".format(error_type))
                iehs_mask_value = self._cscripts.get_by_path(self._cscripts.UNCORE,
                                                             ieh_register_path, self.PCIE_SOCKET).get_value()
                if iehs_mask_value == 0:
                    self._cscripts.get_by_path(self._cscripts.UNCORE, ieh_register_path, self.PCIE_SOCKET
                                               ).write(set_ieh_mask_value)
                    iehs_mask_value = self._cscripts.get_by_path(self._cscripts.UNCORE,
                                                                 ieh_register_path, self.PCIE_SOCKET).get_value()
                    self._log.info(
                        "Iehs Mask was Enabled for '{}' Errors .{}={}".format(error_type, value, iehs_mask_value))
            except Exception as e:
                if 'pci_bus_map is missing our internal bus' in str(e):
                    self._log.info("Info:'{}' path is not accessible".format(value))
                else:
                    self._log.error("Failed to set ieh register  '{}'".format(e))

    def enable_ieh_mask(self, error_type):
        """
        This Method is Used to Enable the Mask by Changing the Register Access method and after Enabling the Mask
        Reverting the Access back to default.

        :return:
        """
        set_ieh_mask_value = 0xffffffff
        iehg_cor_error_mask_dict = {ProductFamilies.ICX: 'ieh_global.gcoerrmsk',
                                    ProductFamilies.SNR: 'ieh_global.gcoerrmsk',
                                    ProductFamilies.SPR: 'ieh_global.gerrcormsk',
                                    ProductFamilies.SKX: 'ieh_global.gcoerrmsk'
                                    }
        iehg_nonfatal_error_mask_dict = {ProductFamilies.ICX: 'ieh_global.gnferrmsk',
                                         ProductFamilies.SNR: 'ieh_global.gnferrmsk',
                                         ProductFamilies.SPR: 'ieh_global.gerrnonmsk',
                                         ProductFamilies.SKX: 'ieh_global.gnferrmsk'
                                         }
        iehg_fatal_error_mask_dict = {ProductFamilies.ICX: 'ieh_global.gfaerrmsk',
                                      ProductFamilies.SNR: 'ieh_global.gfaerrmsk',
                                      ProductFamilies.SPR: 'ieh_global.gerrfatmsk',
                                      ProductFamilies.SKX: 'ieh_global.gfaerrmsk'
                                      }
        iehs_cor_error_mask_dict = {ProductFamilies.ICX: 'iehs.gcoerrmsk',
                                    ProductFamilies.SNR: 'iehs.gcoerrmsk',
                                    ProductFamilies.SPR: 'iehs.gerrcormsk',
                                    ProductFamilies.SKX: 'iehs.gcoerrmsk'
                                    }
        iehs_non_fatal_error_mask_dict = {ProductFamilies.ICX: 'iehs.gnferrmsk',
                                          ProductFamilies.SNR: 'iehs.gnferrmsk',
                                          ProductFamilies.SPR: 'iehs.gerrnonmsk',
                                          ProductFamilies.SKX: 'iehs.gnferrmsk'
                                          }
        iehs_fatal_error_mask_dict = {ProductFamilies.ICX: 'iehs.gfaerrmsk',
                                      ProductFamilies.SNR: 'iehs.gfaerrmsk',
                                      ProductFamilies.SPR: 'iehs.gerrfatmsk',
                                      ProductFamilies.SKX: 'iehs.gfaerrmsk'
                                      }
        self._smm.smm_entry_for_masking_ieh()
        self._common_content_lib.set_ieh_register_access(csp=self._cscripts, access_type="pcicfg")
        self._log.info("Check Current Mask Value and Enable")
        self._sdp.halt()
        if error_type == "correctable":
            ieh_global_mask_value = self._cscripts.get_by_path(self._cscripts.UNCORE, iehg_cor_error_mask_dict[
                self._product], self.PCIE_SOCKET).get_value()
            if ieh_global_mask_value == 0x0:
                self._log.info("Enable the Ieh Global Mask for '{}' Errors".format(error_type))
                self._cscripts.get_by_path(self._cscripts.UNCORE, iehg_cor_error_mask_dict[
                    self._product], self.PCIE_SOCKET).write(set_ieh_mask_value)
                if self._cscripts.get_by_path(self._cscripts.UNCORE, iehg_cor_error_mask_dict[
                    self._product], self.PCIE_SOCKET).get_value() == set_ieh_mask_value:
                    self._log.info("IEH Global Mask was Enabled for '{}' Errors".format(error_type))
                else:
                    self._log.info("IEH Global Mask FAILED TO get Enabled for '{}' Errors".format(error_type))

            # Currently cscripts fails to update iehs mask registers consistently but updating ieh0,ieh1.....ieh11 works
            if (self._product == 'SPR'):
                self.set_iehs_mask_register(error_type)
            elif (self._product != 'SPR'):
                iehs_mask_value = self._cscripts.get_by_path(self._cscripts.UNCORE, iehs_cor_error_mask_dict[
                    self._product], self.PCIE_SOCKET).get_value()

                if iehs_mask_value == 0x0:
                    self._log.info("Enable Iehs Mask for '{}' Errors".format(error_type))

                    self._cscripts.get_by_path(self._cscripts.UNCORE, iehs_cor_error_mask_dict[
                        self._product], self.PCIE_SOCKET).write(set_ieh_mask_value)
                    self._log.info("Iehs Mask was Enabled for '{}' Errors".format(error_type))

        elif error_type == "non_fatal":
            ieh_global_mask_value = self._cscripts.get_by_path(self._cscripts.UNCORE, iehg_nonfatal_error_mask_dict[
                self._product], self.PCIE_SOCKET).get_value()
            if ieh_global_mask_value == 0x0:
                self._log.info("Enable the Ieh Global Mask for '{}' Errors".format(error_type))
                self._cscripts.get_by_path(self._cscripts.UNCORE, iehg_nonfatal_error_mask_dict[
                    self._product], self.PCIE_SOCKET).write(set_ieh_mask_value)
            self._log.info("IEH Global Mask was Enabled for '{}' Errors".format(error_type))
            if (self._product == 'SPR'):
                self.set_iehs_mask_register(error_type)
            elif (self._product != 'SPR'):
                iehs_mask_value = self._cscripts.get_by_path(self._cscripts.UNCORE, iehs_non_fatal_error_mask_dict[
                    self._product], self.PCIE_SOCKET).get_value()
                if iehs_mask_value == 0x0:
                    self._log.info("Enable Iehs Mask for '{}' Errors".format(error_type))
                    self._cscripts.get_by_path(self._cscripts.UNCORE, iehs_non_fatal_error_mask_dict[
                        self._product], self.PCIE_SOCKET).write(set_ieh_mask_value)
                self._log.info("Iehs Mask was Enabled for '{}' Errors".format(error_type))

        elif error_type == "fatal":
            ieh_global_mask_value = self._cscripts.get_by_path(self._cscripts.UNCORE, iehg_fatal_error_mask_dict[
                self._product], self.PCIE_SOCKET).get_value()
            if ieh_global_mask_value == 0x0:
                self._log.info("Enable the Ieh Global Mask for '{}' Errors".format(error_type))
                self._cscripts.get_by_path(self._cscripts.UNCORE, iehg_fatal_error_mask_dict[
                    self._product], self.PCIE_SOCKET).write(set_ieh_mask_value)
            self._log.info("IEH Global Mask was Enabled for '{}' Errors".format(error_type))
            if (self._product == 'SPR'):
                self.set_iehs_mask_register(error_type)
            elif (self._product != 'SPR'):

                iehs_mask_value = self._cscripts.get_by_path(self._cscripts.UNCORE, iehs_fatal_error_mask_dict[
                    self._product], self.PCIE_SOCKET).get_value()
                if iehs_mask_value == 0x0:
                    self._log.info("Enable Iehs Mask for '{}' Errors".format(error_type))
                    self._cscripts.get_by_path(self._cscripts.UNCORE, iehs_fatal_error_mask_dict[
                        self._product], self.PCIE_SOCKET).write(set_ieh_mask_value)
                self._log.info("Iehs Mask was Enabled for '{}' Errors".format(error_type))
        self._common_content_lib.set_ieh_register_access(csp=self._cscripts, access_type="tap2sb")
        self._smm.smm_exit()

    def set_timeout_pcie_cto(self):
        """
        This Function to Set timeouts on the system for pcie with cto

        return: True or False
        """
        try:
            pcie_timeout = False
            self._log.info("Setting timeouts on the system for pcie with cto")
            #   Setting timeout on the system for pcie with cto
            self._cscripts.get_sockets()[0].uncore.dmi.conf.devctrl2.compltoval = self._DEVCTRL2_COMPLTOVAL
            self._cscripts.get_sockets()[
                0].uncore.dmi.conf.ctoctrl.xp_to_pcie_timeout_select = self._XP_TO_PCIE_TIMEOUT_SELECT
            self._sdp.itp.resettarget()
            self._log.info("Wait for timeout for pcie with cto config")
            time.sleep(self._wait_for_pcie_cto_timeout_reconfig_in_sec)
            #   Waiting for os to up after timeout set for pcie with cto
            if self._os.is_alive():
                self._log.info("SUT is alive after pcie timeout set")
                pcie_timeout = True
            return pcie_timeout
        except Exception as ex:
            self._log.error("Exception occurred '{}'".format(ex))
            raise ex

    def get_corrected_error_threshold(self):
        """
        This method returns the value of XPCORERRTHRESHOLD that is set after setting
        UEFI-FW knobs

        :return: corrected error threshold register value
        :raises runtime error
        """
        xpcorerrthreshold_dict = {ProductFamilies.ICX: 'dmi.conf.xpcorerrthreshold',
                                  ProductFamilies.SNR: 'pcie.ports.conf.xpcorerrthreshold',
                                  ProductFamilies.SPR: 'pcie.ports.conf.xpcorerrthreshold',
                                  ProductFamilies.SKX: 'pxp_dmi_xpcorerrthreshold',
                                  }

        corrected_error_threshold_value = ""
        self._sdp.start_log(self._FILE_NAME)
        self._cscripts.get_by_path(self._cscripts.UNCORE, xpcorerrthreshold_dict[
            self._cscripts.silicon_cpu_family]).show()
        self._sdp.stop_log()

        logfile = os.path.abspath(self._FILE_NAME)
        log_file_header = open(logfile, "r")
        corrected_error_threshold_data = log_file_header.readlines()
        for each in corrected_error_threshold_data:
            if "error_threshold" in each:
                corrected_error_threshold_value = each.split(":")[0].strip()

        if corrected_error_threshold_value == "":
            self._log.error("Unable to get corrected_error_threshold_value or corrected_error_counter_value")
            raise RuntimeError("Failed to run {} in cscripts".format(xpcorerrthreshold_dict[
                                                                         self._cscripts.silicon_cpu_family]))

        return corrected_error_threshold_value

    def get_corrected_error_counter(self):
        """
        This method returns the value of XPCORERRCOUNTER that is set after setting
        UEFI-FW knobs

        :return: corrected error counter
        :raises runtime error
        """
        xpcorerrcounter_dict = {ProductFamilies.ICX: 'dmi.conf.xpcorerrcounter',
                                ProductFamilies.SNR: 'pcie.ports.conf.xpcorerrcounter',
                                ProductFamilies.SPR: 'pcie.ports.conf.xpcorerrcounter',
                                ProductFamilies.SKX: 'pxp_dmi_xpcorerrcounter'
                                }

        corrected_error_counter_value = ""
        self._sdp.start_log(self._FILE_NAME)
        self._cscripts.get_by_path(self._cscripts.UNCORE, xpcorerrcounter_dict[
            self._cscripts.silicon_cpu_family]).show()
        self._sdp.stop_log()

        logfile = os.path.abspath(self._FILE_NAME)
        log_file_header = open(logfile, "r")
        corrected_error_counter_data = log_file_header.readlines()
        for each in corrected_error_counter_data:
            if "receiver_error_mask" in each:
                corrected_error_counter_value = each.split(":")[0].strip()

        if corrected_error_counter_value == "":
            self._log.error("Unable to get ccorrected_error_counter_value")
            raise RuntimeError("Failed to run {} in cscripts".format(xpcorerrcounter_dict[
                                                                         self._cscripts.silicon_cpu_family]))
        return corrected_error_counter_value

    def get_rootcon_seceen_value(self):
        """
        This method returns the value of rootcon seceen that is set after setting
        UEFI-FW knobs

        :return: rootcon_seceen_value
        :raises runtime error
        """

        rootcon_seceen_dict = {ProductFamilies.ICX: 'dmi.conf.rootcon.seceen',
                               ProductFamilies.SNR: 'pcie.ports.conf.rootcon.seceen',
                               ProductFamilies.SPR: 'pcie.ports.conf.rootcon.seceen',
                               ProductFamilies.SKX: 'pxp_dmi_rootcon.seceen'
                               }

        rootcon_seceen_value = ""
        self._sdp.start_log(self._FILE_NAME)
        self._cscripts.get_by_path(self._cscripts.UNCORE, rootcon_seceen_dict[self._cscripts.silicon_cpu_family]).show()
        self._sdp.stop_log()

        logfile = os.path.abspath(self._FILE_NAME)
        log_file_header = open(logfile, "r")
        rootcon_seceen_data = log_file_header.readlines()
        for each in rootcon_seceen_data:
            if "seceen" in each:
                rootcon_seceen_value = each.split(":")[0].strip()

        if rootcon_seceen_value == "":
            self._log.error("Unable to get rootcon_seceen_value ")
            raise RuntimeError("Failed to run {} in cscripts".format(rootcon_seceen_dict[
                                                                         self._cscripts.silicon_cpu_family]))
        return rootcon_seceen_value

    def get_error_inj_pcie_port_num(self):
        """
        This method returns the pcie port no using pcie_topology() and pcie_port_map()

        :return: pcie_port no
        """
        try:
            self._sdp.start_log("pcie_topology.log")
            #   Doing pcie topology
            self._pcie.topology()
            self._sdp.stop_log()
            #   Getting the pcie topology log
            pcie_logfile = os.path.abspath("pcie_topology.log")
            pcie_file_handler = open(pcie_logfile, "r")
            pcie_dataframe_file_handler = open("pcie_dataframe_data.log", "w")
            root_port_list = []
            #   Reading the topology data and writing into the dataframe file
            pcie_port_topology = pcie_file_handler.readlines()
            for each in pcie_port_topology:
                if re.match("Port (\S+) MBAS=", each):
                    root_port_list.append(re.match("Port (\S+) MBAS=", each).group(1))
                if "|" in each:
                    pcie_dataframe_file_handler.write(each)
            pcie_dataframe_file_handler.close()

            self._sdp.start_log("pcie_port.log")
            #   Doing pcie port map
            self._pcie.port_map()
            self._sdp.stop_log()
            logfile = os.path.abspath("pcie_port.log")
            log_file_header = open(logfile, "r")
            pcie_port_data = log_file_header.readlines()
            #   Getting the port information dictionary
            for each in pcie_port_data:
                if re.match(self._CHECK_PORT_REGEX, each.strip()):
                    port_info = re.match(self._CHECK_PORT_REGEX, each.strip()).group(3)
                    value = re.match(self._CHECK_PORT_REGEX, each.strip()).group(1)
                    key = re.match(self._CHECK_PORT_REGEX, each.strip()).group(2)
                    self.PORT_INFO_DICT[key] = int(value)
                    self._PCIE_PORT_INFO[key] = port_info

            df = pd.read_csv("pcie_dataframe_data.log", delimiter="|", engine='python')
            df.to_csv('pcie.csv', index=False)
            pcie_csvfile = os.path.abspath("pcie.csv")
            #   Getting the pcie port dataframe
            pcie_port_df = pd.read_csv(pcie_csvfile, sep=",", delimiter=' *, *', encoding='utf8',
                                       engine='python')
            pcie_port_df.columns = [col.strip() for col in pcie_port_df.columns]
            pcie_port_df = pcie_port_df.drop(pcie_port_df.columns[0], 1)
            #   If the root_port_list is empty then the pcie card is not connected and will return 0
            if len(root_port_list) == 0:
                self._log.info("SUT has No PCIE Card attached")
                self._log.info("0 will default to DMI port!")
                return 0
            #   Getting the required pcie port number
            for each in root_port_list:
                pcie_values = pcie_port_df.loc[pcie_port_df['PCIe port'] == each]
                if self._DETECT_PCIE in pcie_values[self._PCIE_COL_NAME].values:
                    return self.PORT_INFO_DICT[each], self._PCIE_PORT_INFO[each]

        except Exception as ex:
            self._log.error("Exception occurred '{}'".format(ex))
            raise ex
        finally:
            self._sdp.go()

    def inject_and_verify_cscripts_pcie_error(self, error_type="ce", halt_first=True,
                                              check_einj_lock=True, show_error_regs=True):
        """
        This method injects PCI errors using CScripts while halted.

        :param:errType         : options are "uce", "ce", "both".  Leaving undefined will result in no error injected
        :param:haltFirst       : perform initial halt before any execution of script
        :param:checkEInjLock   : perform initial check to see if EInj capabilities are locked, and if so, unlock
        :param:showErrorRegs   : show memory error registers after error is injected
        :return: True/False
        raise runtime error
        """
        ret_value = False
        pcie_port_no, pcie_port_data = self.get_error_inj_pcie_port_num()

        #   Doing resetInjectorLockCheck
        self._ei.resetInjectorLockCheck(pcie_port_no)
        self._sdp.start_log("error_injection.log")
        #   Doing pcie error injection
        if self._cscripts.silicon_cpu_family in [ProductFamilies.CLX, ProductFamilies.SKX,
                                                 ProductFamilies.ICX, ProductFamilies.CPX,
                                                 ProductFamilies.SPR]:
            self._ei.injectPcieError(self._SOCKET_NUMBER, pcie_port_no, errType=error_type,
                                     haltFirst=halt_first,
                                     checkEInjLock=check_einj_lock, showErrorRegs=show_error_regs)

        elif self._cscripts.silicon_cpu_family == ProductFamilies.SNR:
            self._ei.injectPcieError(self._SOCKET_NUMBER, 'rlink', errType=error_type, haltFirst=halt_first,
                                     checkEInjLock=check_einj_lock, showErrorRegs=show_error_regs)

        self._sdp.stop_log()
        logfile = os.path.abspath("error_injection.log")
        #   Verifying pcie error message in the pcie log
        if self._PCIE_UNCORRECTABLE_ERROR_STRING in open(logfile).read():
            self._log.info("Successfully Found PCIE_UNCORRECTABLE_ERROR_STRING: {} "
                           .format(self._PCIE_UNCORRECTABLE_ERROR_STRING))
            ret_value = True

        return ret_value

    def is_cto_set_for_port(self):
        """
        Function to return if completion timeout set for the ports
        :return: Boolean
        """
        try:
            cto_set_status = False
            self._log.info("Verify if cto is set for the port Successfully or not")
            self._sdp.halt()
            #   Checking the cto value from registry
            cto_check_reg = self._cscripts.get_by_path(self._cscripts.UNCORE, self.cto_set_for_port_reg[self._product])

            cto_check_reg_list = str(cto_check_reg).split("\n")
            cto_check_reg_dict = {}
            #   Getting the registry values in a dictionary
            for value in cto_check_reg_list:
                cto_value = value.split("-")
                cto_check_reg_dict[cto_value[0]] = cto_value[1].strip()
            #   Verifying the registry value has come up as 1 if cto set for the port
            for key in cto_check_reg_dict.keys():
                if '1' in cto_check_reg_dict[key]:
                    self._log.info("CTO is successfully set for port")
                    cto_set_status = True
            if not cto_set_status:
                self._log.error("CTO is failed to set for port")
            self._sdp.go()
            return cto_set_status

        except Exception as e:
            self._log.error("An exception occurred:\n{}".format(str(e)))

    def inject_and_verify_cscripts_pcie_cto_error(self, errtype="ce"):
        """
        This Function provides pcie uncorrectable error with CTO

        :return : True/False
        :raises : RunTimeError
        """
        try:
            injected_pcie_error_successfully = False
            # self._sdp.go()
            self._log.info("Halt System to pcie uncorrectable error with CTO")
            #   Setting timeouts on the system for pcie with cto
            if self._product == ProductFamilies.ICX:
                self.set_timeout_pcie_cto()
            #   Doing halt
            self._sdp.halt()
            self._log.info("Inject PCIE Error")
            #   Injecting PCIE uncorrectable error
            self.inject_and_verify_cscripts_pcie_error(error_type=errtype)
            self._sdp.go()
            self._log.info("check whether the SUT is up or not")
            #   Checking the os is up or not after pcie error injection
            if self._os.is_alive():
                self._log.info("SUT is alive after pcie error injection")
            else:
                if not self._os.is_alive():  # Check to OS is alive
                    #   Going in a loop in order to os to come up
                    for iter_num in range(5):
                        self._log.info("SUT is not alive we will wait for reboot "
                                       "timeout for SUT to come up ...")
                        time.sleep(self._reboot_timeout)  # Waiting for os timeout
                        if self._os.is_alive():
                            break
            #   If Sut is not coming up then raise SystemError
            if not self._os.is_alive():
                self._log.error("SUT did not come-up even after waiting for specified time...")
                raise SystemError("SUT did not come-up even after waiting for specified time...")
            else:
                self._log.info("SUT is alive after pcie error injection")
                injected_pcie_error_successfully = self.is_cto_set_for_port()
            self._sdp.go()
            self._log.info("Collect all logs")
            self._common_content_lib.collect_all_logs_from_linux_sut()
            errortype = self._ras_einj_util.EINJ_PCIE_UNCORRECTABLE_NONFATAL
            check_os_log_success = self._ras_einj_util.einj_check_os_log(errortype)
            if not check_os_log_success:
                self._log.error("Failed to find the appropriate OS logs after error injection!")
                injected_pcie_error_successfully = False
            return injected_pcie_error_successfully
        except Exception as e:
            self._log.error("An exception occurred:\n{}".format(str(e)))

    def obtain_xpglberrsts(self, err_type="ce"):
        """
        This method returns the value of XPGLBERRSTS.pcie_aer_correctable_error or uncorrectable based on parameter
        pased

        :return: XPGLBERRSTS.pcie_aer_correctable_error else raise exception
        """
        pcie_aer_dict = {}
        if err_type == "ce":
            pcie_aer_dict = {ProductFamilies.ICX: 'dmi.conf.xpglberrsts.pcie_aer_correctable_error',
                             ProductFamilies.SNR: 'pcie.ports.conf.xpglberrsts.pcie_aer_correctable_error',
                             ProductFamilies.SPR: 'pcie.ports.conf.xpglberrsts.pcie_aer_correctable_error',
                             ProductFamilies.SKX: 'pxp_dmi_xpglberrsts.pcie_aer_correctable_error',
                             }

        pcie_aer_correctable_error_value = ""
        self._sdp.start_log("pcie_aer.log")
        self._cscripts.get_by_path(self._cscripts.UNCORE, pcie_aer_dict[
            self._cscripts.silicon_cpu_family]).show()
        self._sdp.stop_log()

        logfile = os.path.abspath("pcie_aer.log")
        log_file_header = open(logfile, "r")
        pcie_aer_error_data = log_file_header.readlines()
        for each in pcie_aer_error_data:
            if "pcie_aer_correctable_error" in each:
                pcie_aer_correctable_error_value = each.split(":")[0].strip()

        if pcie_aer_correctable_error_value == "":
            self._log.error("Unable to get XPGLBERRSTS.pcie_aer_correctable_error")
            raise RuntimeError("Failed to run {} in cscripts".format(pcie_aer_dict[
                                                                         self._cscripts.silicon_cpu_family]))

        return pcie_aer_correctable_error_value
