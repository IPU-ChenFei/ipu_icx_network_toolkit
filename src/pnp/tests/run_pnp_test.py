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
from src.pnp.lib.common import PnPBase
from src.pnp.lib.wl_config import WorkloadConfig,TestcaseConfigs
from src.pnp.lib.pnp_constants import Config, Filename
from src.pnp.lib.pnp_utils import ResultParser
from dtaf_core.lib.dtaf_constants import Framework
from  src.pnp.lib.wl_setup import WorkloadSetup
import os
import sys
from pathlib import Path

class PnPTest(PnPBase):
    """
    Base class extension for StreamBaseTest which holds common arguments
    and functions.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance for pnp_source_path and stream file.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(self.__class__, self).__init__(test_log, arguments, cfg_opts)
        self._testcase = arguments.pnp_test
        self._workload = arguments.pnp_workload
        self.tc_config = {}
        self.linked_tc_configs = []

        #Workload details
        clustering_mode = self.common_pnp_lib.get_clustering_mode()
        wc = WorkloadConfig(self._workload, clustering_mode)
        self.__workload_details = wc.get_workload_details()
        self.workload_dir =self.__workload_details[Config.WORKLOAD_DIR]
        self.workload_config_file = self.__workload_details[Config.CONFIG_FILE]

        self.setup = WorkloadSetup(test_log, arguments, cfg_opts, self.__workload_details, self.pnp_base)
    
    @classmethod
    def add_arguments(cls, parser):
        super(PnPBase, cls).add_arguments(parser)
        parser.add_argument('-wl','--workload', action="store", dest="pnp_workload", required=True,
                            type=str, help="Name of the PnP Workload")
        parser.add_argument('-tc','--testcase', action="store", dest="pnp_test", required=True,
                            type=str, help="Name of the testcase for the PnP WorkLoad")

    def prepare(self):
        #Get testcase configs for the given testcase
        tc = TestcaseConfigs()
        self.__tc_config = tc.get_config_for_testcase(self.workload_config_file, self._testcase)
        if not self.__tc_config:
            self._log.error("Testcase '"+ self._testcase + "' not available in '" + 
                            self.workload_config_file + "'")
            return False
        
        #If the testcase has other related testcses, get config for the linked testcases
        self.__linked_tc_configs = tc.get_configs_for_linked_testcases(self.workload_config_file, self._testcase)

        #Set default timeout to 48Hrs if cmd_timeout is not provided
        if not self.__tc_config[Config.TIMEOUT]:
            self.__tc_config[Config.TIMEOUT] = 172800

        self.setup.prepare_sut_for_workload_execution(self._workload)

    def execute(self):  # type: () -> bool
        if not self._pnp_setup:
            self._log.error("PnP setup could not be completed")
            return False

        #Set command execution path and the run command 
        wl_path = self.get_pnp_workloads_directory() + self.workload_dir
        wl_run_cmd = self.__tc_config[Config.RUN_COMMAND]
        self._log.info("Run Command: " + wl_run_cmd)

        #Redirect output logs to a file
        wl_run_cmd += " 2>&1 | tee " + Filename.RUN_COMMAND_LOGS + " >/dev/null"

        #Run testcase for the workload
        testcase_log = self._common_content_lib.execute_sut_cmd(wl_run_cmd, wl_run_cmd,
                                                                   self.__tc_config[Config.TIMEOUT], 
                                                                   cmd_path=wl_path)
        self._log.info(testcase_log)

        #Copy run command logs file to HOST
        sut_log_file = wl_path + "/" + Filename.RUN_COMMAND_LOGS
        host_log_file = os.path.join(self.log_dir, Filename.RUN_COMMAND_LOGS)
        self.os.copy_file_from_sut_to_local(sut_log_file, host_log_file)
        self._log.info("Execution logs has been copied to logs directory")
        
        #smi interrupt log?
        #check testcase output is not empty
        result = ResultParser(host_log_file, self.__tc_config, self.__linked_tc_configs, self._log)
        kpi = result.extract_KPIs_from_output()

        result.dump_KPIs_in_test_log()
        result.generate_json_file_for_cc(self._cc_log_path)
        #if the value is <=0 
        return True

    '''
    def cleanup(self, true):
        self._log.info("Cleaning Up Done")
    '''

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PnPTest.main() else Framework.TEST_RESULT_FAIL)
