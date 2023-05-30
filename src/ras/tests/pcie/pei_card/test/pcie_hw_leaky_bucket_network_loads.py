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

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.ras.lib.ras_ethernet_util import RasEthernetUtils
from src.ras.tests.pcie.pei_card.test.pcie_hw_leaky_bucket_basetest import PcieHWLeakyBucketBaseTest


class PcieHWLeakyBucketNetworkLoads(PcieHWLeakyBucketBaseTest):
    """
    Phoenix_id : 22012706805

    The objective of this test is to enable verification of Leaky Bucket flow in response to bad DLLP and bad TLP packets
    by way of injecting them with PEI 4.0 card while network is overloaded / run iperf traffic.
    Verify the Leaky Bucket Flow with various BER value for Leaky Bucket
    Configure the path of the ice (E810) driver in content configuration
    E.G <E810_network_adapter_driver_name>C:\Automation\E810_driver\ice-1.5.8.tar.gz</E810_network_adapter_driver_name>

     Requirements:

     1. BIOS config file path configured in system_configuration.xml
     2. Socket of PEI 4.0 card configured in content_configuration.xml
     3. pxp port of PEI 4.0 card configured in content_configuration.xml
     4. ethernet IP address for first network port configured in content_configuration.xml
     5. ethernet IP address for second network port configured in content_configuration.xml
     6. ethernet netmask for first network port configured in content_configuration.xml
     7. ethernet netmask for second network port configured in content_configuration.xml
     8. PEI 4.0 HW injector card

     Usage:

     Error type injection is controlled by the "test" parameter in the execute() method and is set to "badDLLP" by default
     To execute the test for bad TLP, set test="badTLP"

    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieHWLeakyBucketBaseTest object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieHWLeakyBucketNetworkLoads, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._ras_ethernet_utils_obj = RasEthernetUtils(self._log, self.os, cfg_opts,
                                                        self._common_content_configuration)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(PcieHWLeakyBucketNetworkLoads, self).prepare()
        self._log.info("Configure the PEI card in interposer mode")
        self.hw_injector.set_mode(self.pei_image_type.INTERPOSER)
        self.perform_graceful_g3()
        self._common_content_lib.clear_os_log()
        self._common_content_lib.clear_dmesg_log()
        self._install_collateral.load_intel_e810_network_adapter()
        self._install_collateral.install_iperf()

    def execute(self, err_type="badDLLP"):
        """
        This method checks the OS log for errors given a supported error type

        param: string err_type - one of the supported error types (i.e.: "badDLLP", "badTLP")
        return: True
        raise: TestFail
        """
        self._log.debug("Checking the PCIE Link speed")
        initial_gen = self.get_link_speed_detail()

        self._log.info("Identify the network device names for Columbiaville interfaces")
        eth_interface = self.extract_network_interface_from_dmesg(str_pattern=self._ras_ethernet_utils_obj.E810_network_interface_pattern)
        self._log.info("Network adapter interface - {}".format(eth_interface))

        eth_interface1_ip_addr = self._common_content_configuration.get_sut_nic_endpoint1_ip_address_1()
        eth_interface2_ip_addr = self._common_content_configuration.get_sut_nic_endpoint2_ip_address_1()
        eth_interface1_netmask = self._common_content_configuration.get_sut_nic_endpoint1_netmask()
        eth_interface2_netmask = self._common_content_configuration.get_sut_nic_endpoint2_netmask()

        self._log.info("Configure the first Network Adapter interface")
        self._ras_ethernet_utils_obj.assign_ip_address_to_interface(eth_interface1_ip_addr, eth_interface[0], net_mask=eth_interface1_netmask)
        self._ras_ethernet_utils_obj.set_interace_status(eth_interface[0], 1)

        self._log.info("Configure the second Network Adapter interface")
        self._ras_ethernet_utils_obj.network_namespace_create(1)
        self._ras_ethernet_utils_obj.namespace_move(1, eth_interface[1])
        self._ras_ethernet_utils_obj.assign_ip_address_to_interface(eth_interface2_ip_addr, eth_interface[1], net_mask=eth_interface2_netmask, ns_num=1)
        self._ras_ethernet_utils_obj.set_interace_status(eth_interface[1], 1, ns_num=1)

        self._log.info("Clearing OS logs")
        self._common_content_lib.clear_os_log()
        self._common_content_lib.clear_dmesg_log()

        self._log.info("Checking config register values before PEI error injection")
        self.check_config_registers()

        self._log.info("Checking leaky bucket lane error count is zero before overloading the network")
        if self.get_leaky_bucket_error_count(self.PCIE_SOCKET, self.PCIE_PXP_PORT) != 0:
            raise content_exceptions.TestFail("Lane error count was not zero before error injection")

        self._log.info("start iperf3 server and client")
        self._ras_ethernet_utils_obj.iperf_stop("iperf3")
        self._ras_ethernet_utils_obj.start_iperf_traffic(eth_interface2_ip_addr, iper_serv_namespace="ns1", iperf_ver="iperf3",
                                                         serv_bind_ip=eth_interface2_ip_addr, clnt_bind_ip=eth_interface1_ip_addr,
                                                         iper_log_file="iperf3_server.txt", iper_tst_dur=300)

        self._log.info("Checking leaky bucket lane error count is zero before error injection")
        if self.get_leaky_bucket_error_count(self.PCIE_SOCKET, self.PCIE_PXP_PORT) != 0:
            raise content_exceptions.TestFail("Lane error count was not zero before error injection")

        self._log.info("Checking iperf server is connected and data transfer started")
        self._ras_ethernet_utils_obj.check_iperf_server_status(iperf_log_file="iperf3_server.txt")

        self._log.info("Injecting errors")
        self.inject_pei_errors(err_type)

        self._log.info("Verify OS Log")
        self.check_os_errors_reported(err_type)

        self._log.info("Checking status register values after PEI error injection")
        self.check_status_registers_triggered()

        self._log.info("verify PCIE Link speed after PEI error injection.")
        self.check_link_degrade(initial_gen)

        self._log.info("Verify the network workload/iperf traffic was not interrupted")
        self._ras_ethernet_utils_obj.check_iperf_traffic_continuity(iperf_log_file="iperf3_server.txt")
        return True

    def cleanup(self, return_status):
        super(PcieHWLeakyBucketNetworkLoads, self).cleanup(return_status)
        self._ras_ethernet_utils_obj.iperf_stop("iperf3")
        self._ras_ethernet_utils_obj.cleanup_ethernet()
        self._log.info("Configure the PEI card in end point mode")
        self.hw_injector.set_mode(self.pei_image_type.ENDPOINT)
        self.perform_graceful_g3()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieHWLeakyBucketNetworkLoads.main() else Framework.TEST_RESULT_FAIL)
