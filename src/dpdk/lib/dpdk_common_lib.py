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
import re

from src.lib import content_exceptions


class DpdkCommonLib:
    """
    Class is mainly used to parse generated output
    """

    RX_PACKET_STR = "RX-packets:"
    RX_TOTAL_STR = "RX-total:"
    TX_PACKET_STR = "TX-packets:"
    TX_TOTAL_STR = "TX-total:"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create an instance of DpdkCommonLib

        :param cfg_opts: Configuration Object of provider
        :param log: Log object
        :param os_obj: OS obj
        """
        self._log = log
        self._os = os_obj
        self._cfg_opts = cfg_opts
        self.sut_os = self._os.os_type

    def get_statistic_data(self, test_pmd_data, start_info_search, end_info_search):
        """
        This method is used to extract info between the given strings and parse it and return the statistics data in
        dictionary form.

        :param test_pmd_data: test pmd run data
        :param start_info_search: start string of search data
        :param end_info_search: end string of search data
        :raise: content exception if the packet details are found found
        :return: returns packet info in dictionary form
        """
        packets_info = {}
        packet_search_regex = r'(?<=' + start_info_search + ').*?(?=\\' + end_info_search + ')'
        packet_nos_regex = "{}\s+(\d+)"
        packets = [self.RX_PACKET_STR, self.RX_TOTAL_STR, self.TX_PACKET_STR, self.TX_TOTAL_STR]
        port_info = re.findall(packet_search_regex, test_pmd_data, flags=re.S)
        if not port_info:
            raise content_exceptions.TestFail("Search strings are not found")
        for each_data in packets:
            packet_num = re.search(packet_nos_regex.format(each_data), port_info[0])
            if not packet_num:
                raise content_exceptions.TestFail("Packet number details is not found")
            packets_info[each_data] = int(packet_num.group(1).strip())
        return packets_info

    def evaluate_packet_forward_statistics(self, pmd_test_data):
        """
        This method is used for comparing Rx-packet and Tx-packet data for port0 and port 1

        :param pmd_test_data: Poll mode driver test data
        :return: True if port1 and port 0 statistics are fine else False
        """
        port0_stat = "Forward statistics for port 0"
        port1_stat = "Forward statistics for port 1"
        all_port_stat = "Accumulated forward statistics for all ports"
        all_port_end_str = "Done."
        port01_end_str = 30 * "-"
        stat_result = []
        port0_packet_data = self.get_statistic_data(pmd_test_data, port0_stat, port01_end_str)
        self._log.debug("Port 0 forward statistic info is {}".format(port0_packet_data))
        port1_packet_data = self.get_statistic_data(pmd_test_data, port1_stat, port01_end_str)
        self._log.debug("Port 1 forward statistic info is {}".format(port1_packet_data))
        all_port_packet_data = self.get_statistic_data(pmd_test_data, all_port_stat, all_port_end_str)
        self._log.debug("All port forward statistic info is {}".format(all_port_packet_data))
        stat_result.append(port0_packet_data[self.RX_PACKET_STR] == port1_packet_data[self.TX_PACKET_STR])
        stat_result.append(port0_packet_data[self.RX_TOTAL_STR] == port1_packet_data[self.TX_TOTAL_STR])
        stat_result.append(port0_packet_data[self.TX_PACKET_STR] == port1_packet_data[self.RX_PACKET_STR])
        stat_result.append(port0_packet_data[self.TX_TOTAL_STR] == port1_packet_data[self.RX_TOTAL_STR])
        stat_result.append(all_port_packet_data[self.RX_PACKET_STR] == all_port_packet_data[self.TX_PACKET_STR])
        stat_result.append(all_port_packet_data[self.RX_TOTAL_STR] == all_port_packet_data[self.TX_TOTAL_STR])

        return all(stat_result)
