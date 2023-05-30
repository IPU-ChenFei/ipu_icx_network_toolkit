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
from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.einj_tests.einj_common import EinjCommon
from src.ras.lib.ras_ethernet_util import RasEthernetUtils
from src.ras.lib.ras_numa_utils import RasNumaUtils


class PcieUceAlternateSocketAccessNonFatalEthernetOSFirst(EinjCommon):
    """
    PM RAS Alternate/secondary socket CPU IO access +PTU + PCIe uncorrectable non-fatal error + OS log checks using
    ethernet OS 1st mode
    https://hsdes.intel.com/appstore/article/#/22013116982

    """

    _BIOS_CONFIG_FILE = "../io_power_management/alt_socket_biosknobs_os_1st.cfg"
    _OS_CMD_EXECUTE_TIMEOUT_IN_SEC = 30

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieUceNonfatalAlternateSocketAccessEthernet object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieUceAlternateSocketAccessNonFatalEthernetOSFirst, self).__init__(test_log, arguments, cfg_opts,
                                                                                  self._BIOS_CONFIG_FILE)
        self._log = test_log
        self._ras_numa_utils_obj = RasNumaUtils(self._log, self.os)
        self._ras_ethernet_utils_obj = RasEthernetUtils(self._log, self.os, cfg_opts,
                                                        self._common_content_configuration)
        self.injection_root_port = self._common_content_configuration.einj_pcie_default_address()
        self.sut_nic_driver_name = self._common_content_configuration.get_sut_nic_driver_module_name()
        self.sut_nic1_ip_addr1 = self._common_content_configuration.get_sut_nic_endpoint1_ip_address_1()
        self.sut_nic2_ip_addr1 = self._common_content_configuration.get_sut_nic_endpoint2_ip_address_1()
        self.sut_nic1_netdev1 = self._common_content_configuration.get_sut_nic_endpoint1_netdev_1()
        self.sut_nic2_netdev1 = self._common_content_configuration.get_sut_nic_endpoint2_netdev_1()
        self.injection_count = self._common_content_configuration.get_alt_socket_einj_injection_iteration_count()
        self.threshold_upi = self._common_content_configuration.get_sut_upi_minimum_hit_threshold_count()
        self.post_uce_inj_wait_secs = self._common_content_configuration.waiting_time_after_injecting_uncorr_error()
        self.test_run_time = self._common_content_configuration.ras_stress_test_execute_time()

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        return: None
        """

        super(PcieUceAlternateSocketAccessNonFatalEthernetOSFirst, self).prepare()

    def execute(self):
        """
        PCIe UCE-NF injection at runtime with PTU load and network performance tool running.
        eDPC enabled.

        To execute this test first set the desired number of error injections using "einj_injection_iteration_count" in
        the ras section of content_configuration.xml and then set a run-time for the stress that will last for the
        length of the injections. This time will vary due to system capabilities, injection tyoe and endpoint type.
        Set stress for longer than needed, the local cleanup function will stop it.

        :return: True or False based on Test Case fail or pass.
        """
        ip_addr1 = self.sut_nic1_ip_addr1
        ip_addr2 = self.sut_nic2_ip_addr1
        netdev1 = self.sut_nic1_netdev1
        netdev2 = self.sut_nic2_netdev1
        num_ns = '2'  # hard coded for this test at 2 namespaces, additional namespaces not needed for 2 NICs
        test_run_time_in_secs = self.test_run_time
        sut_nic_driver = self.sut_nic_driver_name
        injection_count = self.injection_count
        threshold_upi = self.threshold_upi
        injection_root_port = self.injection_root_port

        self._ras_ethernet_utils_obj.cleanup_ethernet(sut_nic_driver)
        self._log.info("Cleanup complete")
        self._ras_ethernet_utils_obj.prepare_sut_network_for_test(num_ns, netdev1, netdev2, ip_addr1, ip_addr2)
        self._log.info("SUT network preparation complete")
        self._ras_ethernet_utils_obj.prepare_sut_for_test()
        self._log.info("System prep complete")
        self._ras_numa_utils_obj.watch_numa_nodes()
        numa_node0_initial = (self._ras_numa_utils_obj.watch_numa_nodes()[0])
        numa_node1_initial = (self._ras_numa_utils_obj.watch_numa_nodes()[1])
        self._log.info('this is numa_node0_initial ' + str(numa_node0_initial))
        self._log.info('this is numa_node1_initial ' + str(numa_node1_initial))
        self._log.info("Initial Numa_other values are: node 0: = {}, node 1: = {} ".format(numa_node0_initial,
                                                                                           numa_node1_initial))
        self._ras_ethernet_utils_obj.run_ptu(test_run_time_in_secs)
        self._log.info("PTU started for {} seconds.".format(test_run_time_in_secs))
        self._ras_ethernet_utils_obj.run_ethernet_traffic(iper_serv_namespace='ns1', iper_clnt_namespace='ns2',
                                                          iper_srv_ip=ip_addr1, iper_tst_dur=test_run_time_in_secs,
                                                          iper_tst_threads='10', srv_node='0', clnt_node='1',
                                                          iperf_ver='iperf3')
        self._log.info("Iperf stress run started for {} seconds.".format(test_run_time_in_secs))
        self._ras_ethernet_utils_obj.check_running_stress()

        self._log.info("Beginning a sequence of {} PCIE correctable error injections to BDF {}".
                       format(injection_count, hex(injection_root_port)))
        if not self._ras_ethernet_utils_obj.inject_pcie_uncorrectable_errors(injection_count, 'ns1', netdev1,
                                                                             self.post_uce_inj_wait_secs, edpc_en=True):
            sys.exit(Framework.TEST_RESULT_FAIL)

        numa_node0_final = (self._ras_numa_utils_obj.watch_numa_nodes()[0])
        numa_node1_final = (self._ras_numa_utils_obj.watch_numa_nodes()[1])
        self._log.info('this is numa_node0_final ' + str(numa_node0_final))
        self._log.info('this is numa_node1_final ' + str(numa_node1_final))

        numa_delta_0 = (int(numa_node0_final) - int(numa_node0_initial))
        numa_delta_1 = (int(numa_node1_final) - int(numa_node1_initial))
        self._log.info('This is node0 delta ' + str(numa_delta_0))
        self._log.info('This is node1 delta ' + str(numa_delta_1))
        self._ras_numa_utils_obj.numa_compare_nodes(numa_delta_0, numa_delta_1, '0', '0', threshold_upi, injection_count
                                                    , '2')
        self._ras_ethernet_utils_obj.cleanup_ethernet(sut_nic_driver)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieUceAlternateSocketAccessNonFatalEthernetOSFirst.main()
             else Framework.TEST_RESULT_FAIL)
