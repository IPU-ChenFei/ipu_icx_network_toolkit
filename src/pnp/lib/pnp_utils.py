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
import re
import json
import os
from src.pnp.lib.pnp_constants import Config, ClusteringMode

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.pnp.lib.common import PnPBase
    from src.provider.cpu_info_provider import CpuInfoProvider

class ResultParser():
    """
    Class for PnP result Parsing, getting KPI's and generation of result_data.json 
    """
    REGEX = "regex"
    SCORE = "score"
    SCORE_UNIT = "score_unit"
    DIVISOR = "divisor"
    RESULT_INDICATOR = "ResultIndicator"
    LINKED_TEST_CASES = "linked_test_cases"
    TCD_ID = "tcd_id"
    METADATA = "Metadata"
    NAME = "name"
    JSON_FILE_NAME = "results_data.json"

    def __init__(self, logfile, tc_config, linked_tc_configs, log):
        """
        Create an instance for pnp_source_path and mlc_file.

        :param logfile: Workload output logfile
        :param tc_config: Config of the Testcase
        """
        self.logfile = logfile
        self.tc_config = tc_config
        self.linked_tc_configs = linked_tc_configs
        self._log = log
        self.kpi = {}

    def extract_KPIs_from_output(self):
        """
        """
        result_indicator = {}

        file = open(self.logfile, 'r')
        match = re.findall(self.tc_config[Config.REGEX], file.read())
        file.close()
        
        #If SCORE_UNIT_DIVISOR is not available, assign to 1
        if not self.tc_config[Config.SCORE_UNIT_DIVISOR]:
            self.tc_config[Config.SCORE_UNIT_DIVISOR] = 1

        #Check whether the value was found using the given regex
        if not match:
            self._log.error("KPI: '" +self.tc_config[Config.TITLE] + "' not found in output")
            result_indicator[Config.SCORE] = -1
        else:
            result_indicator[Config.SCORE] = round(float(match[-1])/self.tc_config[Config.SCORE_UNIT_DIVISOR],2)

        result_indicator[Config.SCORE_UNIT] = self.tc_config[Config.SCORE_UNIT]
        self.kpi[Config.RESULT_INDICATOR] = result_indicator
        
        #Extract KPI's if there are additional testcases linked to this particular testcase output
        if self.linked_tc_configs:
            metadata = {}
            for config in self.linked_tc_configs:
                result = {}
                #If SCORE_UNIT_DIVISOR is not available, assign to 1
                if not config[Config.SCORE_UNIT_DIVISOR]:
                    config[Config.SCORE_UNIT_DIVISOR] = 1

                file = open(self.logfile, 'r')
                match = re.findall(config[Config.REGEX], file.read())
                file.close()
                result[Config.TCD_ID] = config[Config.TCD_ID]

                #Check whether the value was forund using the given regex
                if not match:
                    self._log.error("KPI: '" +config[Config.TITLE] + "' not found in output")
                    result[Config.SCORE] = -1
                else:
                    result[Config.SCORE] = round(float(match[-1])/config[Config.SCORE_UNIT_DIVISOR],2)

                result[Config.SCORE_UNIT] = config[Config.SCORE_UNIT]
                metadata[config[Config.TITLE]] = result 
            
            self.kpi[Config.METADATA] = metadata
        return self.kpi

    def dump_KPIs_in_test_log(self):
        self._log.info("************************RESULTS*****************************")

        #If score_unit is NULL assign it to empty string
        if not self.kpi[Config.RESULT_INDICATOR][Config.SCORE_UNIT]:
            self.kpi[Config.RESULT_INDICATOR][Config.SCORE_UNIT] = ""

        kpi_score = self.tc_config[Config.TITLE] + " : " + \
                 str(self.kpi[Config.RESULT_INDICATOR][Config.SCORE]) + " " + \
                 self.kpi[Config.RESULT_INDICATOR][Config.SCORE_UNIT]
        self._log.info(kpi_score)

        if Config.METADATA in self.kpi.keys():
            linked_results = self.kpi[Config.METADATA]
            for title,result in linked_results.items():
                #If score_unit is NULL assign it to empty string
                if not result[Config.SCORE_UNIT]:
                    result[Config.SCORE_UNIT] = ""
                kpi_score = title + " : " + str(result[Config.SCORE]) + " " + \
                            result[Config.SCORE_UNIT]
                self._log.info(kpi_score)

        self._log.info("************************************************************")

    
    def generate_json_file_for_cc(self, path):
        json_result = {}
        json_path = os.path.join(path, self.JSON_FILE_NAME)
        result_indicator = self.kpi[self.RESULT_INDICATOR]
        metadata = []
        if self.METADATA in self.kpi.keys():
            test_result = self.kpi[self.METADATA]
            for tr in test_result.values():
                metadata.append(tr)
        json_result[self.RESULT_INDICATOR] = result_indicator
        if metadata:
            json_result[self.METADATA] = metadata

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=4)
        
        self._log.info(self.JSON_FILE_NAME + " is created in logs directory")

class CommonPnPLib():
    """
    Class for Common PnP Library functions
    """
    def __init__(self, pnp_base : 'PnPBase'):
        """
        """
        self.pnp_base = pnp_base
        self._log = pnp_base._log
        self._common_content_lib = pnp_base._common_content_lib
        self.os = pnp_base.os

    # This is a temporary quick fix and would be changed
    def get_clustering_mode(self):
        """
        This function returns the clustering mode of the SUT
        """
        cpu_info : 'CpuInfoProvider' = self.pnp_base.cpu_info
        cpu_info.populate_cpu_info()

        total_sockets = int(cpu_info.get_number_of_sockets())
        total_numa_nodes = int(cpu_info.get_numa_node())

        if total_numa_nodes == total_sockets:
            return ClusteringMode.QUAD
        elif total_numa_nodes == (total_sockets * 4):
            return ClusteringMode.SNC4
        elif total_numa_nodes == (total_sockets * 2):
            return ClusteringMode.SNC2

        return ClusteringMode.ERROR
    
    def git_checkout(self, branch="master"):
        """
        This function pulls the branch and checks out a particular commit in pnpwls repository

        Args:
            commit_id: git commit id
            branch: git branch

        Returns:
            True: If checkout was successful
            False: If checkout was unsuccessful
        """
        command_timeout = 30
        cmd_output = self._common_content_lib.execute_sut_cmd("git fetch", "git fetch", command_timeout, cmd_path=self.pnp_base.PNP_WLS_DIR)
        self._log.info(cmd_output)

        cmd_output = self.os.execute("git checkout " + branch,
                                     command_timeout, cwd=self.pnp_base.PNP_WLS_DIR)

        if "error" in cmd_output.stderr or "fatal" in cmd_output.stderr:
            self._log.info("Failed to checkout commit ID: " + branch)
            self._log.info(cmd_output.stderr)
            return False

        self._log.info(cmd_output.stdout)
        self._log.info("Using branch: " + branch)
        return True

