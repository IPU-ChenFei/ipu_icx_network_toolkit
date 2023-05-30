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
from src.ras.lib.ras_nvme_utils import RasNvmeUtils
from src.ras.lib.ras_numa_utils import RasNumaUtils


class PcieUceAlternateSocketAccessNvmeOSFirst(EinjCommon):
    """
    PM RAS Alternate/secondary socket CPU IO access +PTU + PCIe uncorrectable error + OS log checks using NVMe
    OS first version
    https://hsdes.intel.com/appstore/article/#/22013250923

    """

    _BIOS_CONFIG_FILE = "../io_power_management/alt_socket_biosknobs_os_1st.cfg"
    _OS_CMD_EXECUTE_TIMEOUT_IN_SEC = 30

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieUceNonfatalAlternateSocketAccessNvmeOSFirst object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieUceAlternateSocketAccessNvmeOSFirst, self).__init__(test_log, arguments, cfg_opts,
                                                                      self._BIOS_CONFIG_FILE)
        self._log = test_log
        self._ras_numa_utils_obj = RasNumaUtils(self._log, self.os)
        self._ras_nvme_utils_obj = RasNvmeUtils(self._log, self.os, cfg_opts,
                                                self._common_content_configuration)
        self.injection_root_port = self._common_content_configuration.einj_pcie_default_address()
        self.nvme_partition = self._common_content_configuration.get_nvme_partition_to_mount()
        self.injection_count = self._common_content_configuration.get_alt_socket_einj_injection_iteration_count()
        self.threshold_upi = self._common_content_configuration.get_sut_upi_minimum_hit_threshold_count()
        self.post_ce_inj_wait_secs = self._common_content_configuration.get_corr_err_inj_post_wait_time()
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

        super(PcieUceAlternateSocketAccessNvmeOSFirst, self).prepare()

    def execute(self):
        """
        PCIe UCE injection at runtime with PTU load and disc performance tool running.
        eDPC enabled.

        To execute this test first set the desired number of error injections using "einj_injection_iteration_count" in
        the ras section of content_configuration.xml and then set a run-time for the stress that will last for the
        length of the injections. This time will vary due to system capabilities, injection tyoe and endpoint type.
        Set stress for longer than needed, the local cleanup function will stop it.

        :return: True or False based on Test Case fail or pass.
        """
        unused_node = '0'  # A local parameter to send '0' to the two unused numa node inputs when using the
        # 4 node capable "numa_compare_nodes" method on a 2 socket system
        number_of_sockets = '2'  # Local parameter to set the method mentioned above into 2 socket mode

        self._ras_nvme_utils_obj.cleanup_nvme_test_specific_items(self.nvme_partition)
        self._log.info("Cleanup complete")
        self._ras_nvme_utils_obj.prepare_os_for_nvme_test(self.nvme_partition, self.nvme_partition)
        self._log.info("OS prep complete")
        if not self._ras_nvme_utils_obj.verify_test_req_progs_installed_on_sut():
            return False
        self._log.info("SUT NVMe test preparation complete")

        self._ras_numa_utils_obj.watch_numa_nodes()
        numa_node0_initial = (self._ras_numa_utils_obj.watch_numa_nodes()[0])
        numa_node1_initial = (self._ras_numa_utils_obj.watch_numa_nodes()[1])
        self._log.info('this is numa_node0_initial ' + str(numa_node0_initial))
        self._log.info('this is numa_node1_initial ' + str(numa_node1_initial))
        self._log.info("Initial Numa_other values are: node 0: = {}, node 1: = {} ".format(numa_node0_initial,
                                                                                           numa_node1_initial))
        self._ras_nvme_utils_obj.run_ptu(self.test_run_time)
        self._log.info("PTU started for {} seconds.".format(self.test_run_time))

        self._ras_nvme_utils_obj.run_bonnie_disk_traffic("0", self.injection_count, self.nvme_partition)
        self._log.info("bonnie++ R/W stress run started for {} seconds.".format(self.test_run_time))
        if not self._ras_nvme_utils_obj.check_running_stress():
            return False

        self._log.info("Beginning a sequence of {} PCIE uncorrectable error injections to BDF {}".
                       format(self.injection_count, hex(self.injection_root_port)))

        if not self._ras_nvme_utils_obj.inject_pcie_uncorrectable_errors(self.injection_count, self.nvme_partition,
                                                                       self.post_ce_inj_wait_secs, edpc_en=True):
            return False

        numa_node0_final = (self._ras_numa_utils_obj.watch_numa_nodes()[0])
        numa_node1_final = (self._ras_numa_utils_obj.watch_numa_nodes()[1])
        self._log.info('this is numa_node0_final ' + str(numa_node0_final))
        self._log.info('this is numa_node1_final ' + str(numa_node1_final))

        numa_delta_0 = (int(numa_node0_final) - int(numa_node0_initial))
        numa_delta_1 = (int(numa_node1_final) - int(numa_node1_initial))
        self._log.info('This is node0 delta ' + str(numa_delta_0))
        self._log.info('This is node1 delta ' + str(numa_delta_1))
        self._ras_numa_utils_obj.numa_compare_nodes(numa_delta_0, numa_delta_1, unused_node, unused_node,
                                                    self.threshold_upi, self.injection_count, number_of_sockets)
        self._ras_nvme_utils_obj.cleanup_nvme_test_specific_items(self.nvme_partition)
        self._log.info("Post-cleanup complete")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieUceAlternateSocketAccessNvmeOSFirst.main()
             else Framework.TEST_RESULT_FAIL)
