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

import sys
import time
import re

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon, PxpInventory, LtssmTestType
from src.lib.dtaf_content_constants import LinuxCyclingToolConstant, PcieSlotAttribute, PcieAttribute
from src.lib import content_exceptions


class PcieEndPointLtssmBaseTest(PcieCommon):
    """
    HPQALM ID : H82136-G10527-PI-PCIe_Endpoint_LTSSM_Testing_L, H82138-PI-PCIe_Endpoint_LTSSM_Testing_W,
                H102286 -G10527.13-PI_PCIe_Endpoint_LTSSM_Testing_Gen5_W
    GLASGOW ID : 10527.12

    The purpose of this Test Case is to verify the functionality of all supported pcie link state transition
    for a specific adapter in all slot of the system.
    """
    TEST_CASE_ID = ["H82136", "G10527", "PI-PCIe_Endpoint_LTSSM_Testing_L"]

    def __init__(self, test_log, arguments, cfg_opts, bios_conf_path=None):
        """
        Creates a PcieEndPointLtssmBaseTest object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieEndPointLtssmBaseTest, self).__init__(test_log, arguments, cfg_opts,
                                                       self.BIOS_CONFIG_FILE
                                                       if bios_conf_path is None else bios_conf_path)
        self._sut_path = self._pcie_ltssm_provider.install_ltssm_tool()
        if self.os.os_type == OperatingSystems.WINDOWS:
            self.TEST_CASE_ID = ["H102286", "G10527", "PI_PCIe_Endpoint_LTSSM_Testing_Gen5_W",
                                 "PCI_Express_Endpoint_LTSSM_Testing","H82138" ,"PI-PCIe_Endpoint_LTSSM_Testing_W"]
        self.pxp_inventory = PxpInventory(self.sdp_obj, self.pcie_obj, self.PCIE_SLS_OUTPUT_LOG)
        self.LTSSM_TEST_NAME_LIST = self._common_content_configuration.get_ltssm_test_list()

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        super(PcieEndPointLtssmBaseTest, self).prepare()
        self.ltssm_prepare()

    def execute(self, tested_link_speed=None):
        """
        This method is to execute:
        1. Check Link and Width Speed.
        2. Test LTSSM Tool execution
        3. Check MCE Log in OS Log.

        :param tested_link_speed
        :return: True or False
        """
        csp = ProviderFactory.create(self.sil_cfg, self._log)

        if self._common_content_configuration.get_pcie_ltssm_auto_discovery():
            self._log.info("Auto-discovering PCIe endpoints for testing")
            for socket, ports in self.pxp_inventory.get_populated_ports_dict(tested_link_speed).items():
                if len(ports) < 1:
                    raise Exception("PCIe Auto-discovery did not detect any ports for the requested link speed: {}".
                                    format(tested_link_speed))
                for port in ports:
                    bdf = self.get_device_bdf(socket, port, self.get_pcie_controller_gen(tested_link_speed))
                    did = self.get_device_id(bdf)
                    for each_test in self.LTSSM_TEST_NAME_LIST:
                        if each_test != LtssmTestType.ASPML1 and self.is_aspm_supported(bdf):
                            self._log.info("Disabling ASPM for {} and port {}".format(each_test, port))
                            self.pcie_obj.aspm(socket, port, 0)
                        if each_test == LtssmTestType.ASPML1 and not self.is_aspm_supported(
                                bdf):
                            self._log.info("ASPM not supported on adapter {}, skipping".format(bdf))
                            return True
                        self._pcie_ltssm_provider.run_ltssm_tool(test_name=each_test,
                                                                 device_id=did,
                                                                 cmd_path=self._sut_path, skip_errors_on_failures=None,
                                                                 pxp_port=port, pxp_socket=socket)

                        #  Checking MCE Error after Testing
                        self.check_mce_error(socket, port)
        else:
            self._log.info("Using PCIe endpoints defined in content configuration for testing")
            pcie_slot_list = self._common_content_configuration.get_pcie_slot_to_check()
            pcie_device_info_list_from_config = self._common_content_configuration.get_required_pcie_device_details(
                product_family=self._product_family, required_slot_list=pcie_slot_list)
            each_slot_info_dict_list = []
            for each_slot_info_dict in pcie_device_info_list_from_config:
                # clear list and assigned pcie slot tag to list as argument require list.
                each_slot_info_dict_list.clear()
                each_slot_info_dict_list.append(each_slot_info_dict)
                self._log.info("Verifying PCIe device Link speed and Width for device: {}".format(each_slot_info_dict))
                pcie_device_info_dict = self.verify_required_slot_pcie_device(cscripts_obj=csp,
                                                                              pcie_slot_device_list=each_slot_info_dict_list,
                                                                              generation=self.get_pcie_controller_gen(tested_link_speed),
                                                                              lnk_stat_width_speed=True,
                                                                              lnk_cap_width_speed=False)[0]
                self._log.info("Device Link Speed and Width found as Expected")
                for bdf, device_details in pcie_device_info_dict.items():
                    for each_test in self.LTSSM_TEST_NAME_LIST:
                        if each_test == LtssmTestType.ASPML1 and not self.is_aspm_supported(
                                bdf):
                            self._log.info("ASPM not supported on adapter {}, skipping".format(bdf))
                            return True
                        self._pcie_ltssm_provider.run_ltssm_tool(test_name=each_test,
                                                                 device_id=device_details[PcieAttribute.DEVICE_ID],
                                                                 cmd_path=self._sut_path, skip_errors_on_failures=None,
                                                                 bdf=bdf)
                    break
                #  Checking MCE Error after Testing
                self.check_mce_error(PcieSlotAttribute.SLOT_NAME, PcieSlotAttribute.PCIE_DEVICE_NAME)

        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)

        return True

    def check_mce_error(self, *args):
        """
        Checks for MCE error and raises exception if error found

        :param *args
        """
        mce_error = self._pcie_util_obj.check_memory_controller_error()
        if mce_error:
            raise content_exceptions.TestFail("MCE error was Captured in Log.")
        self._log.debug("No MCE error was Captured in Os Log")
        self._log.info("LTSSM Testing got pass for {} and {}".format(*args))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieEndPointLtssmBaseTest.main() else Framework.TEST_RESULT_FAIL)
