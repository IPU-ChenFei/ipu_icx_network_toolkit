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

import sys
import time

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.dtaf_constants import Framework
from src.ras.lib.ras_ethernet_util import RasEthernetUtils
from src.ras.lib.ras_numa_utils import RasNumaUtils

from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class MlcIOAccessUpi16bCrcLlrError(IoPmCommon):
    """
    Glasgow_id : 70816 PM RAS - Linux-Second socket IO access+ MLC workload + UPI 16-bit CRC LLR error injections

    In this test case, we will be using MLC(memory latency Checker) to provide workload
    and inject a corrected UPI 16-bit CRC LLR error
    while the platform is under workload.

    test currently assumes that numactl and iperf3 is installed on OS already.
    and the interface names of the two test adapters have been provided in the content_configuration.xml file.
    """
    _BIOS_CONFIG_FILE = "mlc_io_upi_16b_crc_llr_err.cfg"
    EVENT_LOGGING_DELAY_SEC = 6
    CLEAR_LOG_DELAY_SEC = 3
    NUMASTAT_POLLING_DELAY = 30
    NUM_CYCLE = 225
    MLC_PATH_AND_LOADED_LATENCY_7200_SEC_POLL = "./mlc --loaded_latency -t7200"
    TEST_RUN_TIME_IN_SECS = 3600

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MlcIOAccessUpi16bCrcLlrError object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(MlcIOAccessUpi16bCrcLlrError, self).__init__(
            test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

        self._ras_numa_utils_obj = RasNumaUtils(self._log, self.os)
        self._ras_ethernet_utils_obj = RasEthernetUtils(self._log, self.os, cfg_opts,
                                                        self._common_content_configuration)
        self.sut_nic1_ip_addr1 = self._common_content_configuration.get_sut_nic_endpoint1_ip_address_1()
        self.sut_nic2_ip_addr1 = self._common_content_configuration.get_sut_nic_endpoint2_ip_address_1()
        self.sut_nic1_netdev1 = self._common_content_configuration.get_sut_nic_endpoint1_netdev_1()
        self.sut_nic2_netdev1 = self._common_content_configuration.get_sut_nic_endpoint2_netdev_1()

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
        super(MlcIOAccessUpi16bCrcLlrError, self).prepare()

    def execute(self):
        ip_addr1 = self.sut_nic1_ip_addr1
        ip_addr2 = self.sut_nic2_ip_addr1
        netdev1 = self.sut_nic1_netdev1
        netdev2 = self.sut_nic2_netdev1
        num_ns = '2'  # hard coded for this test at 2 namespaces, additional namespaces not needed for 2 NICs

        self.install_mlc_on_sut_linux()

        self.stop_mlc_stress()
        self.iperf3_stop()
        self._ras_ethernet_utils_obj.cleanup_ethernet()

        self._ras_ethernet_utils_obj.prepare_sut_network_for_test(num_ns, netdev1, netdev2, ip_addr1, ip_addr2)
        self._ras_ethernet_utils_obj.run_ethernet_traffic(iper_serv_namespace='ns1', iper_clnt_namespace='ns2',
                                                          iper_srv_ip=ip_addr1, iper_tst_dur=self.TEST_RUN_TIME_IN_SECS,
                                                          iper_tst_threads='15', srv_node='0', clnt_node='0',
                                                          iperf_ver='iperf3')

        self.start_mlc_stress(self.MLC_PATH_AND_LOADED_LATENCY_7200_SEC_POLL)
        numa_node0_initial = int(self._ras_numa_utils_obj.watch_numa_nodes()[0])
        self._log.info('this is numa_node0_initial {}'.format(numa_node0_initial))
        time.sleep(self.NUMASTAT_POLLING_DELAY)
        numa_node0_final = int(self._ras_numa_utils_obj.watch_numa_nodes()[0])
        self._log.info('this is numa_node0_final {}'.format(numa_node0_final))
        if not numa_node0_initial < numa_node0_final:
            self._log.error('No node traffic detected !')
            self.iperf3_stop()
            self._ras_ethernet_utils_obj.cleanup_ethernet()
            return False

        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        for i in range(self.NUM_CYCLE):
            self._log.info("Test on cycle {}".format(i + 1))
            self._log.info("Clearing OS logs .......")
            self._common_content_lib.clear_all_os_error_logs()
            time.sleep(self.CLEAR_LOG_DELAY_SEC)

            self._log.info("Checking if mlc still running...")
            if self.os.execute("pgrep mlc", self._command_timeout).return_code != 0:
                self._log.error("MLC closed unexpectedly!")
                return False
            self._log.info("Check finished, mlc still running")

            self.inject_and_check_upi_error_single_injection(cscripts_obj, init_err_count=i, socket=0, port=0, ignore_crc_cnt=True)

            time.sleep(self.EVENT_LOGGING_DELAY_SEC)
            event_check = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                        self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                                                                        self.LINUX_UPI_16B_CRC_LLR_ERR_SIGNATURE_JOURNALCTL)

            if not event_check:
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.stop_mlc_stress()
                self.iperf3_stop()
                self._ras_ethernet_utils_obj.cleanup_ethernet()
                return False

        self.stop_mlc_stress()
        self.iperf3_stop()
        self._ras_ethernet_utils_obj.cleanup_ethernet()
        return True


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if MlcIOAccessUpi16bCrcLlrError.main()
             else Framework.TEST_RESULT_FAIL)
