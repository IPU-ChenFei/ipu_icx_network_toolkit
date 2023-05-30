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
import time

from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.lib.content_configuration import ContentConfiguration
from src.lib.common_content_lib import CommonContentLib
from src.lib import content_exceptions


class BifurcationSlotMappingUtils(object):
    """
    This class implements common functions which can used across all test cases.
    """
    BIOS_NAME_DICT = {
        ProductFamilies.SPR: "ConfigIOU{}_{}",
        ProductFamilies.EMR: "ConfigIOU{}_{}",
        ProductFamilies.GNR: "Socket_{}_PciExpress_{}_Bifurcation"
    }
    PORT_MAPPING_TO_BIOS = {
        ProductFamilies.SPR: {
            '1': '0',  # Key- PXP Number(Python SV SLS) and Value- BIOS
            '2': '1',
            '3': '2',
            '4': '3',
            '5': '4'
        },
        ProductFamilies.EMR: {
            '1': '0',  # Key- PXP Value(Python SV SLS) and Value- BIOS
            '2': '1',
            '3': '2',
            '4': '3',
            '5': '4'
        },
        ProductFamilies.GNR: {
            '0': '2',
            '1': '3',
            '2': '1',
            '3': '4',
            '4': '9',
            '5': '8'
        }
    }
    BIOS_VALUE = {
        "x4x4x4x4": {ProductFamilies.SPR: "0x0", ProductFamilies.EMR: "0x0", ProductFamilies.GNR: "0x0"},
        "x4x4x_x8": {ProductFamilies.SPR: "0x1", ProductFamilies.EMR: "0x1", ProductFamilies.GNR: "0x1"},
        "x_x8x4x4": {ProductFamilies.SPR: "0x2", ProductFamilies.EMR: "0x2", ProductFamilies.GNR: "0x2"},
        "x_x8x_x8": {ProductFamilies.SPR: "0x3", ProductFamilies.EMR: "0x3", ProductFamilies.GNR: "0x3"},
        "x_x_x_x16": {ProductFamilies.SPR: "0x4", ProductFamilies.EMR: "0x4", ProductFamilies.GNR: "0x4"},
        "x2x2x4x_x8": {ProductFamilies.SPR: "0x5", ProductFamilies.EMR: "0x5", ProductFamilies.GNR: "0x5"},
        "x4x2x2x_x8": {ProductFamilies.SPR: "0x6", ProductFamilies.EMR: "0x6", ProductFamilies.GNR: "0x6"},
        "x_x8x2x2x4": {ProductFamilies.SPR: "0x7", ProductFamilies.EMR: "0x7", ProductFamilies.GNR: "0x7"},
        "x_x8x4x2x2": {ProductFamilies.SPR: "0x8", ProductFamilies.EMR: "0x8", ProductFamilies.GNR: "0x8"},
        "x2x2x4x4x4": {ProductFamilies.SPR: "0x9", ProductFamilies.EMR: "0x9", ProductFamilies.GNR: "0x9"},
        "x4x2x2x4x4": {ProductFamilies.SPR: "0xA", ProductFamilies.EMR: "0xA", ProductFamilies.GNR: "0xA"},
        "x4x4x2x2x4": {ProductFamilies.SPR: "0xB", ProductFamilies.EMR: "0xB", ProductFamilies.GNR: "0xB"},
        "x4x4x4x2x2": {ProductFamilies.SPR: "0xC", ProductFamilies.EMR: "0xC", ProductFamilies.GNR: "0xC"},
        "x2x2x2x2x_x8": {ProductFamilies.SPR: "0xD", ProductFamilies.EMR: "0xD", ProductFamilies.GNR: "0xD"},
        "x_x8x2x2x2x2": {ProductFamilies.SPR: "0xE", ProductFamilies.EMR: "0xE", ProductFamilies.GNR: "0xE"},
        "x2x2x2x2x4x4": {ProductFamilies.SPR: "0xF", ProductFamilies.EMR: "0xF", ProductFamilies.GNR: "0xF"},
        "x2x2x4x2x2x4": {ProductFamilies.SPR: "0x10", ProductFamilies.EMR: "0x10", ProductFamilies.GNR: "0x10"},
        "x2x2x4x4x2x2": {ProductFamilies.SPR: "0x11", ProductFamilies.EMR: "0x11", ProductFamilies.GNR: "0x11"},
        "x4x2x2x2x2x4": {ProductFamilies.SPR: "0x12", ProductFamilies.EMR: "0x12", ProductFamilies.GNR: "0x12"},
        "x4x2x2x4x2x2": {ProductFamilies.SPR: "0x13", ProductFamilies.EMR: "0x13", ProductFamilies.GNR: "0x13"},
        "x4x4x2x2x2x2": {ProductFamilies.SPR: "0x14", ProductFamilies.EMR: "0x14", ProductFamilies.GNR: "0x14"},
        "x2x2x2x2x2x2x4": {ProductFamilies.SPR: "0x15", ProductFamilies.EMR: "0x15", ProductFamilies.GNR: "0x15"},
        "x2x2x2x2x4x2x2": {ProductFamilies.SPR: "0x16", ProductFamilies.EMR: "0x16", ProductFamilies.GNR: "0x16"},
        "x2x2x4x2x2x2x2": {ProductFamilies.SPR: "0x17", ProductFamilies.EMR: "0x17", ProductFamilies.GNR: "0x17"},
        "x4x2x2x2x2x2x2": {ProductFamilies.SPR: "0x18", ProductFamilies.EMR: "0x18", ProductFamilies.GNR: "0x18"},
        "x2x2x2x2x2x2x2x2": {ProductFamilies.SPR: "0x19", ProductFamilies.EMR: "0x19", ProductFamilies.GNR: "0x19"}
    }

    def __init__(self, log, os_obj, cfg_opts):

        self._log = log
        self._os = os_obj
        self._cfg = cfg_opts
        self._content_config = ContentConfiguration(self._log)
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._product = self._common_content_lib.get_platform_family()

    def set_and_verify_bifurcation_bios_knob(self, sdp):
        """
        This method is to get the BIOS Name and value to set.

        :param sdp - silicon debug provider object
        :return: bool- True if Bios Setting worked else False
        """
        bifurcation_slots_dict = self._content_config.get_bifurcation_slots_details_dict()
        bios_path = ""

        for pxp_name, pxp_name_value in bifurcation_slots_dict.items():
            if self._common_content_lib.get_platform_family() == ProductFamilies.GNR:
                bios_path += self.BIOS_NAME_DICT[self._product].format(
                     pxp_name_value['socket'], self.PORT_MAPPING_TO_BIOS[self._product][pxp_name_value['pxp']]) + \
                             "={};".format(self.BIOS_VALUE[pxp_name_value['bifurcation']][self._product])
            else:
                bios_path += self.BIOS_NAME_DICT[self._product].format(
                    self.PORT_MAPPING_TO_BIOS[self._product][pxp_name_value['pxp']], pxp_name_value['socket']) +\
                             "={};".format(self.BIOS_VALUE[pxp_name_value['bifurcation']][self._product])
        try:
            import pysvtools.xmlcli.XmlCli as cli
            sdp.start_log('bios_log.log', 'w')
            cli.clb.AuthenticateXmlCliApis = "True"
            cli.CvProgKnobs(bios_path)
            sdp.pulse_pwr_good()
            self._common_content_lib.wait_for_os(reboot_timeout=self._content_config.get_reboot_timeout())
            time.sleep(30)
            out_put = cli.CvReadKnobs(bios_path)
            sdp.stop_log()
            with open('bios_log.log', 'r') as fp:
                var = fp.read()
            if out_put:
                raise content_exceptions.TestFail("Bios-Verification failed. Please check the Log")
        except:
            raise content_exceptions.TestFail("Failed during bios set")
        finally:
            self._log.info('bios setting log- {}'.format(var))
        return True
