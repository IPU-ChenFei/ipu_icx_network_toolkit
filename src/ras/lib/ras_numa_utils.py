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
from dtaf_core.lib.dtaf_constants import Framework
import sys


class RasNumaUtils(object):
    """
    Targeted NUMA-specific functions to read/compare "other_node" hit counters for RAS I/O UPI tests

    """
    OS_NUMA_CMD_EXECUTE_TIMEOUT_IN_SEC = 30

    def __init__(self, log, os):
        self._log = log
        self._os = os

    def watch_numa_nodes(self, node_count='2'):
        """
        Get NUMA "other_node" hit counter
        :param node_count: number of numa nodes on system currently synonymous with CPU socket count
        :return: List with the node specific values for NUMA "other_node" hit counter
        """
        numa_result = self._os.execute("numastat", self.OS_NUMA_CMD_EXECUTE_TIMEOUT_IN_SEC)
        numa_cap = numa_result.stdout
        numa_val = numa_cap.split()
        other_node_index = numa_val.index('other_node')

        if node_count == '2':
            numa_nodes = [numa_val[(int(other_node_index + 1))], numa_val[(int(other_node_index + 2))]]

        elif node_count == '4':
            numa_nodes = [numa_val[(int(other_node_index + 1))], numa_val[(int(other_node_index + 2))],
                          numa_val[(int(other_node_index + 3))], numa_val[(int(other_node_index + 4))]]

        else:
            log_error = "You must specify a NUMA node count of 2, or 4"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        return numa_nodes

    def numa_compare_nodes(self, node0, node1, node2, node3, threshold, inj_count, node_count='2'):
        """
        Compare NUMA "other_node" hits (via UPI) to the minimum required threshold as specified in content_config.xml
        :param node0: "other_node" hit count for socket 0 from the watch_numa_2node function
        :param node1: "other_node" hit count for socket 1 from the watch_numa_2node function
        :param node2: "other_node" hit count for socket 1 from the watch_numa_2node function
        :param node3: "other_node" hit count for socket 1 from the watch_numa_2node function
        :param threshold: Minimum number of hits desired for pass criteria (100 per injection seems good)
        :param inj_count: The number of injections in the test. Used to scale up threshold as traffic should keep
        :param node_count: number of numa nodes on system currently synonymous with CPU socket count
        running between injections.
        :return: fail test if hit count is too low.
        """
        min_upi = (int(threshold) * int(inj_count))

        if node_count == '2':
            if int(node0) < min_upi and int(node1) < min_upi:
                self._log.error("Not enough UPI traffic has passed to meet the test-defined minimum of {} transfers"
                                .format(min_upi))
                sys.exit(Framework.TEST_RESULT_FAIL)
        if node_count == '4':
            if int(node0) < min_upi and int(node1) < min_upi and int(node2) < min_upi and int(node3) < min_upi:
                self._log.error("Not enough traffic has passed to indicate sufficient UPI traffic")
                sys.exit(Framework.TEST_RESULT_FAIL)
        else:
            self._log.info("Sufficient UPI transfer traffic appears to have passed during this test")

