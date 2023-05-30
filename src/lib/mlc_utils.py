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
import re
import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path


class MlcUtils(object):
    """
        This class contains MLC tool's utility functions which can be used across all test cases.
    """
    COLLATERAL_DIR_NAME = 'collateral'

    def __init__(self, log):
        self._log = log

    def generate_mlc_log_data_set(self, log_path, encoding_type='utf-8'):
        """
        Parse the MLC data log file and create data sets.

        :param: log path, encoding type(optional param)
        :return: Dictionaries of five filtered data set
        :raise: Exception if it occurs .
        """
        idle_latencies_data_set = None
        peak_memory_bw_data_set = None
        memory_bw_between_node_data_set = None
        loaded_latency_data_set = None
        cache_to_cache_data_set = None
        index_list = []
        flag = False
        try:
            with open(log_path, 'r', encoding=encoding_type) as fp:
                mlc_out_list = fp.readlines()
                # get the line indexes from the file to filter out the Data
                for line in mlc_out_list:
                    if re.findall("Measuring idle latencies", line):
                        index_list.append(int(mlc_out_list.index(line)))
                    if re.findall("Measuring Peak Injection Memory Bandwidths", line):
                        index_list.append(int(mlc_out_list.index(line)))
                    if re.findall("Measuring Memory Bandwidths", line):
                        index_list.append(int(mlc_out_list.index(line)))
                    if re.findall("Measuring Loaded Latencies", line):
                        index_list.append(int(mlc_out_list.index(line)))
                    if re.findall("Measuring cache-to-cache", line):
                        index_list.append(int(mlc_out_list.index(line)))

                all_reads_data = None
                three_one_data = None
                two_one_data = None
                one_one_data = None
                stream_triad_data = None
                hit_latency = None
                hitm_latency = None
                latency_list = []
                for index, line in enumerate(mlc_out_list):
                    if index_list[0] <= index <= index_list[1]:
                        #  Get the Idle Latency Data
                        if self.get_numa_node_data_set(mlc_out_list, line, index):
                            idle_latencies_data_set = self.get_numa_node_data_set(mlc_out_list, line, index)

                    if index_list[1] <= index <= index_list[2]:
                        #  Get the Peak Memory BW Data
                        all_reads_data_match = re.findall(r"\AALL Reads.*", line)
                        if all_reads_data_match:
                            all_reads_data = float(all_reads_data_match[0].split(":")[1].strip("\t"))
                        three_one_data_match = re.findall(r"\A3:1 Reads-Writes.*", line)
                        if three_one_data_match:
                            three_one_data = three_one_data_match[0].split(":")[2].strip("\t")
                        two_one_data_match = re.findall(r"\A2:1 Reads-Writes.*", line)
                        if two_one_data_match:
                            two_one_data = float(two_one_data_match[0].split(":")[2].strip("\t"))
                        one_one_data_match = re.findall(r"\A1:1 Reads-Writes.*", line)
                        if one_one_data_match:
                            one_one_data = float(one_one_data_match[0].split(":")[2].strip("\t"))
                        stream_triad_data_match = re.findall(r"\AStream-triad like.*", line)
                        if stream_triad_data_match:
                            stream_triad_data = float(stream_triad_data_match[0].split(":")[1].strip("\t"))

                    #  Write all the Peak Memory BW Data to the below Dictionary
                    peak_memory_bw_data_set = {"ALL Reads": all_reads_data, "3:1 Reads-Writes": three_one_data,
                                               "2:1 Reads-Writes": two_one_data, "1:1 Reads-Writes": one_one_data,
                                               "Stream-triad like": stream_triad_data}

                    if index_list[2] <= index <= index_list[3]:
                        #  Get the Memory BW between nodes Data
                        if self.get_numa_node_data_set(mlc_out_list, line, index):
                            memory_bw_between_node_data_set = self.get_numa_node_data_set(mlc_out_list, line, index)

                    if index_list[3] < index < index_list[4] - 1:
                        #  Get the Loaded Latencies Data
                        if flag:
                            value = float(mlc_out_list[index].split("\t")[1])
                            latency_list.append(value)
                        if "====" in line:
                            flag = True

                    #  Write all the Loaded Latencies Data to the below Dictionary
                    loaded_latency_data_set = {'Latency': latency_list}

                    if index_list[4] < index:
                        #  Get the Cache-to-cache transfer latency Data Set
                        hit_match = re.findall(r"\ALocal Socket L2->L2 HIT\s.*", line)
                        if hit_match:
                            hit_latency = float(hit_match[0].split("\t")[1])
                        hitm_match = re.findall(r"\ALocal Socket L2->L2 HITM.*", line)
                        if hitm_match:
                            hitm_latency = float(hitm_match[0].split("\t")[1])

                    #  Write all the Loaded Latencies Data to the below Dictionary
                    cache_to_cache_data_set = {'HIT latency': hit_latency, 'HITM latency': hitm_latency}

                return idle_latencies_data_set, peak_memory_bw_data_set, memory_bw_between_node_data_set, \
                    loaded_latency_data_set, cache_to_cache_data_set

        except Exception as ex:
            self._log.error("Exception occurred while running the 'generate_mlc_log_data_set' function")
            raise ex

    def get_numa_node_data_set(self, out_data_list, line, index):
        """
        Change the node data to float values from str.

        :param: out data list, line , index
        :return: idle_latencies_data_set
        :raise: ex
        """
        idle_latencies_data_set = None
        try:
            numa_node_match = re.findall(r"\ANuma node", line)
            if numa_node_match:
                node_zero_data = out_data_list[index + 1].split("\t")[1:-3]
                node_one_data = out_data_list[index + 2].split("\t")[1:-3]
                node_zero_data = self.get_node_data(node_zero_data)
                node_one_data = self.get_node_data(node_one_data)
                idle_latencies_data_set = {'Node 0': node_zero_data, 'Node 1': node_one_data}

            return idle_latencies_data_set
        except Exception as ex:
            self._log.error("Exception occurred while running the 'get_node_data'")
            raise ex

    def get_node_data(self, node_data):
        """
        Change the node data to float values from str.

        :param node_data: node data from the Numa Node Data
        :return: None .
        """
        try:
            for index in range(0, len(node_data)):
                if node_data[index] == '-':
                    node_data[index] = 0
                else:
                    node_data[index] = float(node_data[index])
            return node_data
        except Exception as ex:
            self._log.error("Exception occurred while running the 'get_node_data'")
            raise ex

    def verify_mlc_log_with_template_data(self, log_file_path, encoding_type='utf-8'):
        """
        Verify All the current Data Set with the Template one.

        :param: log file path, encoding type(optional param)
        :return: True in Success
        :raise: RuntimeError, ex
        """
        try:
            #  Generate the MLC log data Set from Template log file
            parent_path = Path(os.path.dirname(os.path.realpath(__file__)))
            mlc_template_log_path = os.path.join(parent_path, self.COLLATERAL_DIR_NAME, "ddr4_prefetchoff_mlc.log")

            template_idle_latency_data, template_peak_memory_bw_data, template_memory_bw_data, \
                template_loaded_latency_data, template_cache_to_cache_latency_data = self.generate_mlc_log_data_set(
                    mlc_template_log_path, 'utf-8')

            #  Generate the MLC log data Set from Current log file
            current_idle_latency_data, current_peak_memory_bw_data, current_memory_bw_data, \
                current_loaded_latency_data, current_cache_to_cache_latency_data = self.generate_mlc_log_data_set(
                    log_file_path, encoding_type)

            # Verify the Current Data set with the Template Data
            if not self.verify_each_data(template_idle_latency_data, current_idle_latency_data, 'Node 0') and \
                    self.verify_each_data(template_idle_latency_data, current_idle_latency_data, 'Node 1') and \
                    self.verify_each_data(template_peak_memory_bw_data, current_peak_memory_bw_data, 'ALL Reads') and \
                    self.verify_each_data(template_peak_memory_bw_data, current_peak_memory_bw_data,
                                          '3:1 Reads-Writes') and \
                    self.verify_each_data(template_peak_memory_bw_data, current_peak_memory_bw_data,
                                          '2:1 Reads-Writes') and \
                    self.verify_each_data(template_peak_memory_bw_data, current_peak_memory_bw_data,
                                          '1:1 Reads-Writes') and \
                    self.verify_each_data(template_peak_memory_bw_data, current_peak_memory_bw_data,
                                          'Stream-triad like') and \
                    self.verify_each_data(template_memory_bw_data, current_memory_bw_data, 'Node 0') and \
                    self.verify_each_data(template_memory_bw_data, current_memory_bw_data, 'Node 1') and \
                    self.verify_each_data(template_loaded_latency_data, current_loaded_latency_data, 'Latency') and \
                    self.verify_each_data(template_cache_to_cache_latency_data, current_cache_to_cache_latency_data,
                                          'HIT latency') and \
                    self.verify_each_data(template_cache_to_cache_latency_data, current_cache_to_cache_latency_data,
                                          'HITM latency'):
                self._log.error("Current MLC log Data is not matching with the Template Data")
                raise RuntimeError("Current MLC log Data is not matching with the Template Data")

            self._log.info("Successfully Current MLC data set matched with the Template MLC data set")
            return True
        except Exception as ex:
            self._log.error("Exception occurred while running the 'verify_mlc_log' function")
            raise ex

    def verify_each_data(self, template_data, current_data, key):
        """
        Verify the current Data Set with the Template one.

        :param: template data, current data, key
        :return: True in Success else False
        """
        ret_val = True
        #  Making the Template Data 50% less to match the TC condition
        template_data_list = [element * 0.5 for element in template_data[key]]
        for index in range(0, len(template_data_list)):
            #  Checking current data with the 50% of the Template Data
            template_data_list = [element * 0.5 for element in template_data[key]]
            if not (template_data_list[index]) <= current_data[key][index]:
                self._log.error("Current Data is not matching with the template ")
                ret_val = False

        return ret_val

    def verify_idle_latency_mlc(self, log_path, idle_latency_threshold_value, encoding_type="UTF-8"):
        """
        This function is used to verify the idle latency for the persistent memory

        :param log_path: Path of the log file to be parsed.
        :param idle_latency_threshold_value: Threshold value of idle latency
        :param encoding_type: Optional one, by default it will be 'utf-8'
        :return idle_latency_flag: True if success else False
        """
        with open(log_path, 'r', encoding=encoding_type) as fp:
            mlc_out_list = fp.readlines()
            idle_latency_flag = True
            for line in mlc_out_list:
                match = re.findall("Each iteration", line)
                if match:
                    latency_value = float(line.split('(\t')[1].split('\t')[0])
                    if latency_value > idle_latency_threshold_value:
                        idle_latency_flag = False
                        self._log.error("Idle latencies (in ns), greater than {} in log file {}".
                                        format(idle_latency_threshold_value, log_path))
                    else:
                        self._log.info("Idle latencies (in ns), less than {} in log file {}".
                                       format(idle_latency_threshold_value, log_path))
                match = re.findall("Err", line, re.IGNORECASE)
                if match:
                    idle_latency_flag = False
                    self._log.error("Error in the log file due to failure {}".format(log_path))

        return idle_latency_flag

    def verify_mlc_log(self, log_path, idle_latency, peak_injection_memory_bandwidth, memory_bandwidth):
        """
        Verify All the current Data with the given threshold values

        :param: log_path, idle latency, peak injection memory bandwidth, memory bandwidth
        :return result_list: True in Success else False
        """
        try:

            template_idle_latency_data, template_peak_memory_bw_data, template_memory_bw_data, \
                template_loaded_latency_data, template_cache_to_cache_latency_data = self.generate_mlc_log_data_set(
                    log_path)

            result_list = []
            idle_latency_flag = True
            peak_memory_bw_flag = True
            memory_bw_flag = True
            # Idle latencies(in ns)
            for key, value in template_idle_latency_data.items():
                for each_value in value:
                    if each_value > idle_latency:
                        idle_latency_flag = False
            if idle_latency_flag:
                self._log.info("Idle latencies (in ns) is less than {} (ns) in log file {}".format(idle_latency,
                                                                                                   log_path))
            else:
                self._log.error("Idle latencies (in ns) is greater than {} (ns) in log file {}".format(idle_latency,
                                                                                                       log_path))
            result_list.append(idle_latency_flag)

            # Peak Injection Memory Bandwidths
            for key, value in template_peak_memory_bw_data.items():
                if float(value) < peak_injection_memory_bandwidth:
                    peak_memory_bw_flag = False
            if peak_memory_bw_flag:
                self._log.info("peak Injection Memory Bandwidths is greater than {} MB/sec in log file {}".
                               format(peak_injection_memory_bandwidth, log_path))
            else:
                self._log.error("peak Injection Memory Bandwidths is at least {} MB/sec in log file {}".format(
                    peak_injection_memory_bandwidth, log_path))
            result_list.append(peak_memory_bw_flag)

            # Measuring Memory Bandwidths between nodes within system
            for key, value in template_memory_bw_data.items():
                for each_value in value:
                    if each_value < memory_bandwidth:
                        memory_bw_flag = False
            if memory_bw_flag:
                self._log.info("Memory Bandwidths between nodes within system {} MB/sec in log file {}".format(
                    memory_bandwidth, log_path))
            else:
                self._log.error("Memory Bandwidths between nodes within system at least {} MB/sec in log file {}".
                                format(memory_bandwidth, log_path))
            result_list.append(memory_bw_flag)
            return all(result_list)
        except Exception as ex:
            self._log.error("Exception occurred while running the 'verify_mlc_log' function")
            raise ex
