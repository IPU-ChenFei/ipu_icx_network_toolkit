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
import sys
import time
from pathlib import Path

from dtaf_core.lib.dtaf_constants import Framework
from src.ras.lib.ras_numa_utils import RasNumaUtils

from src.ras.lib.ras_ethernet_util import RasEthernetUtils
from src.lib.dtaf_content_constants import TimeConstants

from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon

from src.lib import content_exceptions

from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class UpiPassthroughToAdjacentSocketBasic4s(HsioUpiCommon):
    """
    hsdes_id : 22014408767

    This test checks for proper reporting of UPI passthrough topology routing costs.
    """
    BIOS_CONFIG_FILE = "upi_enable_dfx_bios_knobs.cfg"
    UPI_DISABLE_PORT_2_BIOS_KNOBS = os.path.join(Path(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
                                              "upi_disable_port_2_bios_knobs.cfg")
    UPI_ENABLE_PORT_2_BIOS_KNOBS = os.path.join(Path(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
                                             "upi_enable_port_2_bios_knobs.cfg")
    CLEAR_LOG_DELAY_SEC = 3
    NUMASTAT_POLLING_DELAY_SEC = 30
    UPI_PASSTHROUGH_STRESS_TEST_RUN_TIME_SEC = 7200

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiPassthroughToAdjacentSocketBasic object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiPassthroughToAdjacentSocketBasic4s, self).__init__(test_log, arguments, cfg_opts,
                                                                    self.BIOS_CONFIG_FILE)
        self._io_pm_obj = IoPmCommon(self._log, arguments, cfg_opts, config=None)
        self._ras_ethernet_utils_obj = RasEthernetUtils(self._log, self.os, cfg_opts,
                                                        self._common_content_configuration)
        self._ras_numa_utils_obj = RasNumaUtils(self._log, self.os)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(UpiPassthroughToAdjacentSocketBasic4s, self).prepare()

    def run_ethernet_traffic_stress(self, num_ns='2',
                                    test_duration=TimeConstants.TWO_HOUR_IN_SEC):
        """
        This method is to run ethernet traffic. Assign IP addresses using network namespaces to isolate.
        start a iperf server on one NIC and pin to one NUMA node memory with numactl.
        Start a iperf client on the other NIC and pin the program to the other NUMA socket with numaclt.

        :param num_ns
        :param test_duration
        """
        ip_addr1 = self._common_content_configuration.get_sut_nic_endpoint1_ip_address_1()
        ip_addr2 = self._common_content_configuration.get_sut_nic_endpoint2_ip_address_1()
        netdev1 = self._common_content_configuration.get_sut_nic_endpoint1_netdev_1()
        netdev2 = self._common_content_configuration.get_sut_nic_endpoint2_netdev_1()

        self._io_pm_obj.iperf3_stop()
        self._ras_ethernet_utils_obj.cleanup_ethernet()
        self._ras_ethernet_utils_obj.prepare_sut_network_for_test(num_ns, netdev1, netdev2, ip_addr1, ip_addr2)
        self._ras_ethernet_utils_obj.run_ethernet_traffic(iper_serv_namespace='ns1', iper_clnt_namespace='ns2',
                                                          iper_srv_ip=ip_addr1, iper_tst_dur=test_duration,
                                                          iper_tst_threads='15', srv_node='0', clnt_node='0',
                                                          iperf_ver='iperf3')
        return True

    def poll_ethernet_traffic(self, test_duration=TimeConstants.TWO_HOUR_IN_SEC):
        """
        This method is to poll the ethernet Traffic for 2 hrs.

        :param test_duration - time duration to poll
        """
        start_time = time.time()
        numa_node0_initial = int(self._ras_numa_utils_obj.watch_numa_nodes()[0])
        self._log.info('this is numa_node0_initial {}'.format(numa_node0_initial))
        time.sleep(self.NUMASTAT_POLLING_DELAY_SEC)

        while time.time() - start_time < test_duration:
            numa_node0_final = int(self._ras_numa_utils_obj.watch_numa_nodes()[0])
            self._log.info('this is numa_node0_final {}'.format(numa_node0_final))
            if not numa_node0_initial < numa_node0_final:
                self._log.error('No node traffic detected !')
                self._io_pm_obj.iperf3_stop()
                self._ras_ethernet_utils_obj.cleanup_ethernet()
                return False
            time.sleep(self.CHECK_INTERVAL_SEC)
        return True

    def execute(self, stress=False, num_ns='2',
                test_duration=TimeConstants.TWO_HOUR_IN_SEC):
        """
        This method is to execute

        1. Check Port 2 is connected.
        2. Set the Bios to Disable Port 2.
        3. Check Port is disable or not.
        4. Check Numactl rout cost - i.e 31.
        4. Set the Bios to re-establish the Port.
        3. Verify the Port is re-established or not.
        """
        self._log.info("Checking upi port 2 connection")
        if not self.verify_upi_port_connection(upi_port_num=2):
            raise content_exceptions.TestFail("Port 2 is not connected- This is not expected")

        self._log.info("Port 2 is connected - This is expected")

        bios_knobs_file = {0: self.UPI_DISABLE_PORT_2_BIOS_KNOBS,
                           1: self.UPI_ENABLE_PORT_2_BIOS_KNOBS}
        for index in range(2):
            self.set_and_verify_bios_knobs(bios_knobs_file[index])
            self._log.info("Checking upi port After setting bios for - {}".format({0: "Port 2 disable",
                                                                                   1: "Port 2 enable"}[index]
                                                                                  ))
            port_connection_status = self.verify_upi_port_connection(upi_port_num=2)
            if port_connection_status and index == 0:
                raise content_exceptions.TestFail("Port 2 is connected - This is not expected")
            if (not port_connection_status) and index == 1:
                raise content_exceptions.TestFail("Port 2 is not connected - This is not expected")
            self._log.info("Port 2 is {} - This is expected".format({
                True: "connected", False: "not connected"}[port_connection_status]))

            self._log.info("Checking the route cost 2 hops")
            numact_route_cost_status = self.verify_numactl_route_cost(self.NUMACTL_ROUTE_COST_2_HOPS)
            if (not numact_route_cost_status) and index == 0:
                raise content_exceptions.TestFail("0<->2 and 1<->3 entries is not having a route cost of {}".format(
                    self.NUMACTL_ROUTE_COST_2_HOPS))
            elif numact_route_cost_status and index == 0:
                self._log.info("0<->2 and 1<->3 entries is having a route cost of {} as expected".format(
                    self.NUMACTL_ROUTE_COST_2_HOPS))

            if numact_route_cost_status and index == 1:
                raise content_exceptions.TestFail("0<->2 and 1<->3 entries is having a route cost of {} as unexpected"
                                                  "".format(self.NUMACTL_ROUTE_COST_2_HOPS))
            elif (not numact_route_cost_status) and index == 1:
                self._log.info("0<->2 and 1<->3 entries is not having a route cost of {} as expected".format(
                    self.NUMACTL_ROUTE_COST_2_HOPS))

            if stress and index == 0:
                self.run_ethernet_traffic_stress(num_ns=num_ns,
                                                 test_duration=test_duration)
                if not self.poll_ethernet_traffic(test_duration=test_duration):
                    raise content_exceptions.TestFail("No node traffic detected !")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiPassthroughToAdjacentSocketBasic4s.main() else Framework.TEST_RESULT_FAIL)
