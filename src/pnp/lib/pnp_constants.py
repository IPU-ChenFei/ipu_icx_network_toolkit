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


class Config(object):
    """Constants for PNP Config"""
    TCD_ID = "tcd_id"
    REGEX = "regex"
    TIMEOUT = "timeout"
    SCORE_UNIT_DIVISOR = "score_unit_divisor"
    SCORE_UNIT = "score_unit"
    RESULT_SOURCE = "result_source"
    SWITCH = "switch"
    CC_TEST = "cc_test"
    CC_PACKAGE_NAME = "cc_package_name"
    RUN_COMMAND = "run_command"
    SCORE = "score"
    RESULT_INDICATOR = "ResultIndicator"
    JSON_FILE_NAME = "results_data.json"
    METADATA = "Metadata"
    TITLE = "title"
    WORKLOAD_DIR = "WorkloadDir"
    CONFIG_FILE = "ConfigFile"
    BIOS_FILE = "BiosConfig"
    BRANCH =  "Branch"
    TEST_CASE = "pnp_test_case"
    PARENT_TEST_CASE = "parent_pnp_tc"
    CONFIG_FILE_QUAD = "ConfigFileQUAD"
    CONFIG_FILE_SNC4 = "ConfigFileSNC4"

class ClusteringMode(object):
    ERROR = -1
    SNC4 = 0
    SNC2 = 1
    QUAD = 2

class Filename(object):
    RUN_COMMAND_LOGS = "execution_logs.txt"
    WORKLOAD_CONFIG_FILE = "pnp_wl_configs.cfg"

class PnpPath(object):
    TEMP_DIR = "/tmp/bkc_pnp/"
    AUTOMATION_DIR = "/root/egs_pnp_automation/"
    PNPWLS_REPO_DIR = "applications.validation.platforms.power-and-performance.server.base-workloads"
