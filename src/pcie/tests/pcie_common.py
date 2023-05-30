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
from decimal import Decimal

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from src.ras.tests.pcie import pcie_cscripts_common


class PcieCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Pcie Test Cases
    """
    _KEY_DMI_SPEED = "speed"
    _KEY_DMI_WIDTH = "width"
    _KEY_DMI_VENDOR_ID = "vendor_id"
    _KEY_DMI_DEVICE_ID = "deviced_id"

    _CMD_TO_FETCH_PCIE_BUS_NUMBER = "lspci -mm | grep '{}'"
    _REGEX_TO_FETCH_PCIE_BUS_NUMBER = r"[0-9a-fA-F][0-9a-fA-F]:[0-9a-fA-F][0-9a-fA-F].[0-9].*{}"
    _CMD_TO_GET_PCIE_DEVICE_DETAILS = "lspci -s {} -vv"
    _REGEX_TO_GET_SPEED_AND_WIDTH = r"LnkSta.*Speed.*Width.*"
    _REGEX_LSPCI_SPEED = r"{}\s{}"
    _REGEX_LSPCI_WIDTH = r"{}\s{}"
    _KEY_PCIE_SPEED = "Speed"
    _KEY_PCIE_WIDTH = "Width"
    _KEY_PCIE_TYPE = "Type"
    _KEY_PCIE_CARD = "card"
    _KEY_PCIE_NAME = "Name"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SiliconDebugProvider and SiliconRegProvider

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(PcieCommon, self).__init__(test_log, arguments, cfg_opts)

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider

        self.pcie_topology_log_file = os.path.join(self.log_dir, "pcie_topology.log")

        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider

        self._pcie = self._cscripts.get_cscripts_utils().get_pcie_obj()
        self._pci = self._cscripts.get_cscripts_utils().get_pci_obj()
        self._product = self._cscripts.silicon_cpu_family

        self.number_of_sockets = self._cscripts.get_socket_count()
        self.bus_device_function_id_list = []

    def log_pcie_topology_data(self):
        """
        This method logs the pcie topology data which will have DMI device details

        :raises: RuntimeError - if any exception using cscripts..
        :return: None.
        """
        try:
            for each_socket in range(self.number_of_sockets):
                self._sdp.start_log(self.pcie_topology_log_file, "w")
                self._log.info("Get the pcie topology using cscripts!")
                self._pcie.topology(each_socket)
                self._sdp.stop_log()
                with open(self.pcie_topology_log_file, "r") as log_file:
                    log_file_list = log_file.readlines()
                    self._log.info("PCIE Topolgoy data for Socket='{}'".format(each_socket))
                    self._log.info("{}".format("".join(log_file_list)))
        except Exception as ex:
            self._log.error("Failed to log PCIE topology data due to the exception '{}'".format(ex))
            raise ex

    def get_device_id(self):
        """
        This method returns the device id using cscripts

        :return: device id as a list else empty list
        """
        try:
            device_id_dict = {ProductFamilies.ICX: "dmi.conf.did",
                              ProductFamilies.SNR: "dmi.conf.did",
                              ProductFamilies.SPR: "pi5.pxp0.pcieg4.dmi.cfg.did",
                              ProductFamilies.SKX: "pxp_dmi_did",
                              ProductFamilies.CLX: "pxp_dmi_did",
                              ProductFamilies.CPX: "pxp_dmi_did",
                              ProductFamilies.EMR: "pxp_dmi_did"
                              }

            reg_path = device_id_dict[self._product]
            self._log.info("Device ID: Executing cscript API get_by_path with reg_path = '{}'".format(reg_path))
            device_id = self._cscripts.get_by_path(self._cscripts.UNCORE, reg_path)
            self._log.info("PCIE DMI Device ID = '{}'".format(device_id))
            return device_id
        except Exception as ex:
            self._log.error("Unable to Get the Device identification number due to the exception '{}'".format(ex))
            raise ex

    def get_dmi_device_details_from_cscripts(self):

        link_width, link_speed = self.get_dmi_width_and_speed_using_cscripts()

        pcie_dmi_dict = {self._KEY_DMI_WIDTH: link_width,
                         self._KEY_DMI_SPEED: link_speed,
                         self._KEY_DMI_VENDOR_ID: self.get_vendor_id(),
                         self._KEY_DMI_DEVICE_ID: self.get_device_id()}

        return pcie_dmi_dict

    def get_vendor_id(self):
        """
        This method returns vendor id using cscripts.

        :return: vendor_id as a list else empty list
        """
        try:
            vendor_id_dict = {ProductFamilies.ICX: "dmi.conf.vid",
                              ProductFamilies.SNR: "dmi.conf.vid",
                              ProductFamilies.SPR: "pi5.pxp0.pcieg4.dmi.cfg.vid",
                              ProductFamilies.SKX: "pxp_dmi_vid",
                              ProductFamilies.CLX: "pxp_dmi_vid",
                              ProductFamilies.CPX: "pxp_dmi_vid",
                              ProductFamilies.EMR: "pi5.pxp0.pcieg4.dmi.cfg.vid"
                              }

            reg_path = vendor_id_dict[self._product]
            self._log.info("Vendor ID: Executing cscript API get_by_path with reg_path = '{}'".format(reg_path))
            vendor_id = self._cscripts.get_by_path(self._cscripts.UNCORE, reg_path)
            self._log.info("PCIE DMI Vendor ID = '{}'".format(vendor_id))
            return vendor_id
        except Exception as ex:
            self._log.error("Unable to Get the Vendor identification number due to the exception '{}'".format(ex))
            raise ex

    def get_dmi_width_and_speed_using_cscripts(self):
        """
        This method returns the link status data from cscripts

        :return: current link speed and negotiated width
        """
        try:
            speed = ""
            dmi_link_status_dict = {ProductFamilies.ICX: "dmi.conf.lnksts",
                                    ProductFamilies.SNR: "dmi.conf.lnksts",
                                    ProductFamilies.SPR: "pi5.pxp0.pcieg4.dmi.cfg.linksts",
                                    ProductFamilies.SKX: "pxp_dmi_lnksts",
                                    ProductFamilies.CLX: "pxp_dmi_lnksts",
                                    ProductFamilies.CPX: "pxp_dmi_lnksts",
                                    ProductFamilies.EMR: "pi5.pxp0.pcieg4.dmi.cfg.linksts"
                                    }

            dict_link_speed = {ProductFamilies.ICX: "current_link_speed",
                               ProductFamilies.SNR: "current_link_speed",
                               ProductFamilies.SPR: "cls",
                               ProductFamilies.SKX: "current_link_speed",
                               ProductFamilies.CLX: "current_link_speed",
                               ProductFamilies.CPX: "current_link_speed",
                               ProductFamilies.EMR: "cls"
                               }

            dict_link_width = {ProductFamilies.ICX: "negotiated_link_width",
                               ProductFamilies.SNR: "negotiated_link_width",
                               ProductFamilies.SPR: "nlw",
                               ProductFamilies.SKX: "negotiated_link_width",
                               ProductFamilies.CLX: "negotiated_link_width",
                               ProductFamilies.CPX: "negotiated_link_width",
                               ProductFamilies.EMR: "nlw"
                               }

            reg_path = dmi_link_status_dict[self._product]
            self._log.info("Negotiated_link_width and  Current_link_speed: Executing cscripts get_by_path "
                           "API using reg_path = '{}'".format(reg_path))

            reg_path_link_speed = reg_path + "." + dict_link_speed[self._product]
            reg_path_link_width = reg_path + "." + dict_link_width[self._product]

            link_speed = self._cscripts.get_by_path(self._cscripts.UNCORE, reg_path_link_speed)
            link_width = self._cscripts.get_by_path(self._cscripts.UNCORE, reg_path_link_width)

            self._log.info("Negotiated_link_width = {}".format(link_width))
            self._log.info("Current_link_speed = {}".format(link_speed))

            return link_width, link_speed
        except Exception as ex:
            self._log.error("Failed to get link width and link speed due to exception '{}'".format(ex))
            raise ex

    def verify_pcie_dmi_link_status(self):
        """
        This method checks pcie dmi link status .

        :return: Boolean
        """
        try:
            self._sdp.halt()

            # log PCIE topology data
            self.log_pcie_topology_data()

            # get dmi link config values from XML file
            pcie_dmi_config_dict = self._common_content_configuration.get_pcie_dmi_data(self._product)
            self._log.info("PCIE DMI device details from config file={}".format(pcie_dmi_config_dict))

            pcie_dmi_dict = self.get_dmi_device_details_from_cscripts()
            self._log.info("PCIE DMI Device details from CScripts={}".format(pcie_dmi_dict))

            # verify data from config file with data from cscripts
            device_id_config = int(pcie_dmi_config_dict[self._KEY_DMI_DEVICE_ID], 16)
            vendor_id_config = int(pcie_dmi_config_dict[self._KEY_DMI_VENDOR_ID], 16)

            link_width_config = pcie_dmi_config_dict[self._KEY_DMI_WIDTH]
            link_width_config = int(Decimal(re.findall(r'\d+', link_width_config)[0]))

            link_speed_config = pcie_dmi_config_dict[self._KEY_DMI_SPEED]
            link_speed_config = int(Decimal(re.findall(r'\d+', link_speed_config)[0]))

            device_id_cscripts = pcie_dmi_dict[self._KEY_DMI_DEVICE_ID]
            vendor_id_cscripts = pcie_dmi_dict[self._KEY_DMI_VENDOR_ID]
            link_width_cscripts = pcie_dmi_dict[self._KEY_DMI_WIDTH]
            link_speed_cscripts = pcie_dmi_dict[self._KEY_DMI_SPEED]

            self._log.info("Vendor ID: from Config: '{}' and "
                           "from cscripts: '{}'".format(hex(vendor_id_config), hex(vendor_id_cscripts)))
            self._log.info("Device ID: from Config: '{}' and "
                           "from cscripts: '{}'".format(hex(device_id_config), hex(device_id_cscripts)))
            self._log.info("Link Width: from Config: '{}' and "
                           "from cscripts: '{}'".format(hex(link_width_config), hex(link_width_cscripts)))
            self._log.info("Link Speed: from Config: '{}' and "
                           "from cscripts: '{}'".format(hex(link_speed_config), hex(link_speed_cscripts)))

            ret_val = True
            if device_id_config != device_id_cscripts:
                self._log.error("The device ID value from config is not matching with value from cscripts..")
                ret_val = False

            if vendor_id_config != vendor_id_cscripts:
                self._log.error("The vendor ID value from config is not matching with value from cscripts..")
                ret_val = False

            if link_width_config != link_width_cscripts:
                self._log.error("The Link Width value from config is not matching with value from cscripts..")
                ret_val = False

            if link_speed_config != link_speed_cscripts:
                self._log.error("The Link Speed value from config is not matching with value from cscripts..")
                ret_val = False

            self._log.info("PCIE DMI Link Status: all values are matching with config...")
            return ret_val
        except Exception as ex:
            log_error = "Failed to verify DMI device link status details due to the exception: '{}'".format(ex)
            self._log.error(log_error)
            raise content_exceptions.TestFail(log_error)
        finally:
            self._sdp.go()

    def get_pcie_bus_device_details_from_os(self, card_type):
        """
        This function returns the speed and width obtained using lspci command
        :return:
        """
        try:
            bus_device_function_id_list = []
            self._log.info("Fetch the Bus:Device.function Value for the card type: {}".format(card_type))

            cmd_line = self._CMD_TO_FETCH_PCIE_BUS_NUMBER.format(card_type)
            command_result = self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)

            self._log.info("Output from command {} is {}".format(cmd_line,command_result.strip()))

            pcie_device_list = re.findall(self._REGEX_TO_FETCH_PCIE_BUS_NUMBER.format(card_type), command_result)
            for each_device in pcie_device_list:
                bus_device_function_id_list.append(each_device.split(" ")[0])

            self._log.info("Available Bus:Device.function Values for the card type {} : {}".
                           format(card_type, ",".join(bus_device_function_id_list)))

            return bus_device_function_id_list

        except Exception as ex:
            log_error = "Failed to get PCIE Device details from lspci command due to the exception: '{}'".format(ex)
            self._log.error(log_error)
            raise content_exceptions.TestFail(log_error)

    def verify_pcie_enumeration(self):
        """
        This method compares speed and width of given pcie device from config

        :returns : Boolean
        """
        try:
            ret_value = False
            pcie_enumeration_config_list = self._common_content_configuration.get_pcie_enumeration_data(
                self._KEY_PCIE_CARD)
            self._log.info("PCIE Enumeration device details from config file={}".format(pcie_enumeration_config_list))

            for each_card in pcie_enumeration_config_list:
                pcie_enumeration_lspci_dict_list = self.get_pcie_bus_device_details_from_os(
                    each_card[self._KEY_PCIE_TYPE])

                self._log.info("PCIE Card Type : {} and Name : {}".format(
                    each_card[self._KEY_PCIE_TYPE], each_card[self._KEY_PCIE_NAME]))

                # verify speed and width from config file with data from lspci command
                for bus_device in pcie_enumeration_lspci_dict_list:
                    self._log.info("Check the Link Speed and Width for Bus:Device.id '{}'".format(bus_device))
                    command_result = self.os.execute(self._CMD_TO_GET_PCIE_DEVICE_DETAILS.format(bus_device),
                                                     self._command_timeout)

                    # Fetch the Expected Speed from lspci command output and compare
                    expected_speed = each_card[self._KEY_PCIE_SPEED]
                    self._log.info("Expected Link Speed is '{}'".format(expected_speed))
                    regex_cmd_for_speed = re.findall(self._REGEX_LSPCI_SPEED.format(self._KEY_PCIE_SPEED,expected_speed),
                                                     command_result.stdout.strip())
                    if regex_cmd_for_speed:
                        pcie_link_speed = expected_speed
                        ret_value = True
                        self._log.info("Pcie Link Speed at Bus:Device.id '{}' is '{}'".format(bus_device, pcie_link_speed))
                        self._log.info("Pcie Link Speed '{}' Matches with Expected Speed '{}' at Bus:Device.id '{}'".
                                       format(pcie_link_speed, expected_speed, bus_device))
                    else:
                        log_error = "Pcie Link Speed is Not as Expected Speed '{}' at Bus:Device.id '{}'"\
                            .format(expected_speed, bus_device)
                        self._log.error(log_error)

                    # Fetch the Expected Width from lspci command output and compare
                    expected_width = each_card[self._KEY_PCIE_WIDTH]
                    self._log.info("Expected Link Width is '{}'".format(expected_width))
                    regex_cmd_for_width = re.findall(self._REGEX_LSPCI_WIDTH.format(self._KEY_PCIE_WIDTH,expected_width),
                                                     command_result.stdout.strip())
                    if regex_cmd_for_width:
                        pcie_link_width = expected_width
                        ret_value = True
                        self._log.info("Pcie Link Width at Bus '{}' is '{}'".format(bus_device, pcie_link_width))
                        self._log.info("Pcie Link Width '{}' Matches with Expected Width '{}' at Bus:Device.id '{}'".
                                       format(pcie_link_width, expected_width, bus_device))
                    else:
                        log_error = "Pcie Link Width is Not as Expected Width '{}' at Bus:Device.id '{}'"\
                            .format(expected_width, bus_device)
                        self._log.error(log_error)

            if ret_value:
                self._log.info("Correct information of all PCIe cards like expected link width and speed is Verified.")
            return ret_value
        except Exception as ex:
            log_error = "Failed to due to the exception: '{}'".format(ex)
            self._log.error(log_error)
            raise content_exceptions.TestFail(log_error)
