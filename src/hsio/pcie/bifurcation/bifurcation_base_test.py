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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.hsio.lib.bifurcation_slot_mapping_utils import BifurcationSlotMappingUtils
from src.pcie.tests.pi_pcie.pcie_common import PxpInventory
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.pcie_provider import PcieProvider
from src.hsio.cxl.cxl_common import CxlCommon
from src.lib import content_exceptions


class BifurcationBaseTest(ContentBaseTestCase):
    """
    Base Test of all Bifurcation Test.
    """
    SEC_BUS_REG_DICT = \
        {
            ProductFamilies.SPR: "uncore.pi5.{}.cfg.secbus",
            ProductFamilies.EMR: "uncore.pi5.{}.cfg.secbus",
            ProductFamilies.GNR: "io{}.uncore.pi5.{}.cfg.secbus"
        }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a BifurcationBaseTest object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(BifurcationBaseTest, self).__init__(test_log, arguments, cfg_opts)
        self._sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(self._sdp_cfg, self._log)  # type: SiliconDebugProvider
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self._slot_map_utils = BifurcationSlotMappingUtils(self._log, self.os, cfg_opts)
        self._product = self._common_content_lib.get_platform_family()
        self._pxp_inventory = PxpInventory(self._sdp, self._csp.get_cscripts_utils().get_pcie_obj(),
                                           r"C:\Automation\pxp_inventory.log")
        self._cfg = cfg_opts
        self._pcie_provider = None

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        self._slot_map_utils.set_and_verify_bifurcation_bios_knob(self._sdp)
        self._pcie_provider = PcieProvider.factory(self._log, self.os, self._cfg, "os", uefi_obj=None)

    def validate_speed_width_in_os(self, protocol=PxpInventory.IOProtocol.PCIE):
        """
        This method is to validate the Link Speed and Width in OS.

        :param protocol: "PCIE" or "CXL"
        """
        if self._pcie_provider is None:
            self._pcie_provider = PcieProvider.factory(self._log, self.os, self._cfg, "os", uefi_obj=None)
        bifurcation_slots_dict = self._pxp_inventory.get_slot_inventory(platform=self._product,
                                                                        silicon_reg_provider_obj=self._csp)[protocol]
        config_dict = self._common_content_configuration.get_bifurcation_slots_details_dict()
        soc_pxp_list = []
        bifurcation_list = []
        ret_val = False

        for each_key, value in config_dict.items():
            soc_pxp_list.append(each_key)
            bifurcation_list.append(value['bifurcation'])

        for each_pxp, bifurcation in zip(soc_pxp_list, bifurcation_list):
            socket_number = each_pxp.split('_')[0].replace('s', '')
            pxp_number = each_pxp.split('_')[1].replace('pxp', '')
            for each_soc, each_solts_details in bifurcation_slots_dict.items():
                if socket_number == each_soc:
                    for each_port, port_value in each_solts_details.items():

                        if port_value['width'] == '0':
                            self._log.info(
                                "No card is placed in socket- {} and port -{}, so skipping".format(socket_number,
                                                                                                   each_port))
                            continue

                        if "pxp{}".format(pxp_number) in each_port:

                            each_port = self.SEC_BUS_REG_DICT[self._product].format(each_port)
                            bus = self._csp.get_by_path(self._csp.SOCKET, each_port, int(socket_number))

                            if not bus:
                                self._log.info("No card is placed in -socket:{} and port-{}, so skipping".format(
                                    socket_number, each_port))
                                continue

                            if protocol == PxpInventory.IOProtocol.CXL:
                                if port_value['cxl_version'] in ["CXL 1.1"]:
                                    self._log.error("CXL Version - {} does not support Bifurcation".format(
                                        port_value['cxl_version']))
                                    continue

                                self.check_cxl_type_in_os(bus, port_value['cxl_type'])

                            width = self._pcie_provider.get_link_status_width_by_bdf(str(bus)[2:] + ':00.0')

                            speed = self._pcie_provider.get_link_status_speed_by_bdf(str(bus)[2:] + ':00.0')
                            ret_val = True
                            if port_value['width'] != width:
                                self._log.error("Width Captured from SLS - {}".format(port_value['width']))
                                self._log.error("Width Captured from OS- {}".format(width))
                                raise content_exceptions.TestFail("Width-{} Captured was not an expected for "
                                                                  "Socket- {} and Pxp- {}".format(width, each_soc,
                                                                                                  each_port))

                            self._log.info("Expected Width-{} was Captured for Socket- {} and Port- {}".format(
                                width, each_soc, each_port
                            ))
                            self._log.info("Width Captured from SLS - {}".format(port_value['width']))
                            self._log.info("Width Captured from OS- {}".format(width))

                            if PxpInventory.PCIeLinkSpeed.MAPPING[port_value['speed']] not in speed:
                                self._log.error("Speed Captured from SLS - {}".format(port_value['speed']))
                                self._log.error("Speed Captured from OS- {}".format(speed))
                                raise content_exceptions.TestFail("Speed-{} Captured was not an expected for "
                                                                  "Socket- {} and Pxp- {}".format(speed, each_soc,
                                                                                                  each_port))

                            self._log.info("Expected Speed-{} was Captured for Socket- {} and Port- {}".format(
                                speed, each_soc, each_port
                            ))
                            self._log.info("Speed Captured from SLS - {}".format(port_value['speed']))
                            self._log.info("Speed Captured from OS- {}".format(speed))

        if not ret_val:
            raise content_exceptions.TestFail("No Card was populated with required bifurcation. "
                                              "Please check the content config tag- <socket_pxp_name> and <bifurcation>"
                                              )

    def check_cxl_type_in_os(self, bus, cxl_type):
        """
        This method is to check the CXL Type in OS.

        :param bus
        :param cxl_type
        """

        lspci_output = self._common_content_lib.execute_sut_cmd(
            "lspci -s {}:00.0 -vvv".format(str(bus)[2:]),
            "bus details command execution",
            self._command_timeout)
        import re
        regex = r"CXLCap:\s(.*) Mem HW"
        cxl_cap_output = re.findall(regex, lspci_output)[0]

        if CxlCommon.CXL_TYPE_IN_OS[cxl_type] not in cxl_cap_output:
            raise content_exceptions.TestFail("Type of CXL Device was not found as expected")

    def validate_speed_and_width_in_os(self, protocol=PxpInventory.IOProtocol.PCIE):
        """
        This method is to validate the Link Speed and Width in OS.
        """
        if self._pcie_provider is None:
            self._pcie_provider = PcieProvider.factory(self._log, self.os, self._cfg, "os", uefi_obj=None)
        bifurcation_slots_dict = self._common_content_configuration.get_bifurcation_slots_details_dict()
        pxp_inventory_dict = self._pxp_inventory.get_pxp_inventory(positive_link_width_only=True)[protocol]

        ret_val = False
        for each_slot, each_solts_details in bifurcation_slots_dict.items():

            no_of_ports = each_solts_details['bifurcation'].count('x')
            for port_num in range(no_of_ports):
                if self._product == ProductFamilies.GNR:
                    if each_solts_details['pxp'] in ["pxp0", "pxp1", "pxp2", "pxp3"]:
                        io_die = 0
                    else:
                        io_die = 1
                    reg = self.SEC_BUS_REG_DICT[self._product].format(io_die,
                                                                      "pxp{}.rp{}".format(
                                                                          each_solts_details['pxp'], port_num))
                else:
                    reg = self.SEC_BUS_REG_DICT[self._product].format(
                        "pxp{}.pcieg5.port{}".format(each_solts_details['pxp'], port_num))

                port_flag = False
                for pxp_inventory_socket, pxp_inventory_port_list in pxp_inventory_dict.items():
                    if each_solts_details['socket'] == str(pxp_inventory_socket):
                        if "pxp{}.pcieg5.port{}".format(each_solts_details['pxp'], port_num) \
                                in pxp_inventory_port_list:
                            port_flag = True
                            break

                if not port_flag:
                    self._log.error(
                        "Socket- {} and Port- {} was not found with expected protocol. So, skipping..".format(
                            each_solts_details['socket'], "pxp{}.pcieg5.port{}".format(each_solts_details['pxp'],
                                                                                       port_num)))
                    continue

                if protocol == PxpInventory.IOProtocol.CXL:
                    self._sdp.start_log(self._sls_log, "w")
                    try:
                        self._sdp.halt()
                        cxl = self._csp.get_cxl_obj()
                        cxl.get_device_type(int(each_solts_details['socket']), "pxp{}.pcieg5.port{}".format(
                            each_solts_details['pxp'], port_num))
                        cxl.get_cxl_version(int(each_solts_details['socket']), "pxp{}.pcieg5.port{}".format(
                            each_solts_details['pxp'], port_num))
                    except:
                        self._log.error("Failed to get Cxl Device Type or Cxl Version")
                    finally:
                        self._sdp.go()
                        self._sdp.stop_log()
                    with open(self._sls_log, "r") as fp:
                        var = fp.read()

                    import re
                    cxl_type = re.findall(r"INFO: CXL.*(Type \d+)", var)[0]
                    cxl_version = re.findall(r"INFO: Device version.*(CXL \S+)", var)[0]
                    if cxl_version in ["CXL 1.1"]:
                        self._log.error("Bifurcation does not support to CXL version-{}, so skipping".format(
                            cxl_version))
                        continue

                if each_solts_details['port_{}'.format(port_num)]['speed'] != 'None':
                    ret_val = True
                    bus_output = self._csp.get_by_path(self._csp.SOCKET, reg,
                                                       int(each_solts_details['socket']))

                    if protocol == PxpInventory.IOProtocol.CXL:
                        self.check_cxl_type_in_os(str(bus_output), cxl_type)

                    width = self._pcie_provider.get_link_status_width_by_bdf(str(bus_output)[2:] + ':00.0')
                    if each_solts_details['port_{}'.format(port_num)]['width'] not in width:

                        raise content_exceptions.TestFail(
                            "Unexpected Width-{} was found for socket-{} and port - {}. Expected Width as per "
                            "config is-{} ".format(width, each_solts_details['socket'], reg[self._product],
                                                   width, each_solts_details['socket'], reg,
                                                   each_solts_details['port_{}'.format(port_num)]['width']))

                    self._log.info("Width-{} Found as Expected for socket - {} and port - {}".format(
                        width, each_solts_details['socket'], reg))

                    speed = self._pcie_provider.get_link_status_speed_by_bdf(str(bus_output)[2:] + ':00.0')
                    if each_solts_details['port_{}'.format(port_num)]['speed'] not in speed:
                        raise content_exceptions.TestFail(
                            "Unexpected Speed-{} was found for socket-{} and port-{}. "
                            "Expected Speed as per config-{}".format(
                                speed, each_solts_details['socket'], reg, each_solts_details[
                                    'port_{}'.format(port_num)]['speed']))

                    self._log.info("Speed-{} Found as Expected for socket - {} and port - {}".format(
                        speed, each_solts_details['socket'], reg))

                else:
                    if each_solts_details['port_{}'.format(port_num)]['speed'] == 'None':
                        self._log.error("No Card is placed under slot: socket-{} port-{}. So, skipping".format(
                            each_solts_details['socket'], reg))

        if ret_val is False:
            raise content_exceptions.TestFail("Expected slot bifurcation is not configured in "
                                              "tag bifurcation. Please check the content config tag- "
                                              "<socket_pxp_name> and <bifurcation>")
