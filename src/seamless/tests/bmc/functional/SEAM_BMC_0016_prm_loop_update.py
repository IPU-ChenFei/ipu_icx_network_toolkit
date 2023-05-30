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
"""
    :Seamless BMC capsule stage test

    Attempts to send in a ucode capsule use to initiate the seamless update
"""
import sys
import time
from datetime import datetime
import random
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0016_prm_loop_update(SeamlessBaseTest):
    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0016_prm_loop_update, self).__init__(test_log, arguments, cfg_opts)
        self.expected_ver = arguments.expected_ver
        self.flow_type = arguments.flow_type
        self.start_workload = arguments.start_workload
        self.warm_reset = arguments.warm_reset
        self.prm_handler = arguments.prm_handler
        self.prm_path = arguments.prm_path
        self.capsule = arguments.capsule
        self.handler = arguments.handler
        self.min_delay = arguments.min_delay
        self.max_delay = arguments.max_delay
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.prm_handler_command = self._workload_path + "PRMTestFlow.ps1 " + self._powershell_credentials
        self.update_prm_handler_command = self._workload_path + "PRMUpdate.ps1 " + self._powershell_credentials
        self.cleanup_prm_handler_command = self._workload_path + "PRMCleanup.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.invocation_time = None
        self.update_time = None
        self.loop_count = arguments.loop
        self.total_iter = 0
        self.skip_reset = False
        self.activation = False
        self.sps_mode = arguments.sps_mode

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0016_prm_loop_update, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--flow_type', action='store', help="The type of flow for ucode update",
                            default="")  # (invoke, update)
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--prm_handler', action='store', help="The prm handler to be invoked/updated", default="p1")
        parser.add_argument('--prm_path', action='store', help='The prm tool path')
        parser.add_argument('--capsule', action='store', help='The capsule image')
        parser.add_argument('--handler', action='store', help='The prm handler to be invoked using OS wrapper tool',
                            default="")
        parser.add_argument('--loop', type=int, default=1, help="Add argument for # of loops")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--min_delay', action='store', help="Sets the minimum delay to wait between PRM runs in"
                                                                "seconds (default: 0).")
        parser.add_argument('--max_delay', action='store', help='Sets the maximum delay to wait between PRM runs in'
                                                                'seconds. If specified, delay will be random.')

    def check_capsule_pre_conditions(self):
        return True

    def evaluate_workload_output(self, output):
        return True

    def get_current_version(self, echo_version=True):
        version = None
        # TODO: tbd fucntion to read current prm status
        return version

    def invoke_prm_handler(self):
        time_start = datetime.now()
        output = self.run_powershell_command(command=self.prm_handler_command + " '-" + self.prm_handler + "'",
                                             get_output=True, echo_output=True)
        if 'Wrong input parameter' in output:
            raise RuntimeError('Input handler is incorrect')
        else:
            self.invocation_time = datetime.now() - time_start
            result = True
            self._log.info('PRM Handler invocation successful: check memory table for output')

        return result

    def invoke_prm_handler_os_wrapper(self):
        time_start = datetime.now()
        if self.handler == 'dummy':
            cmd = "rt_prm"
        elif self.handler == "addrtrans":
            cmd = "rt_addrtrans"
        else:
            raise RuntimeError("Input argument value for handler is incorrect")

        output = self.run_powershell_command(command=self.prm_handler_command + " " + cmd, get_output=True,
                                             echo_output=True)
        if 'Execution Failed' not in output:
            self.invocation_time = datetime.now() - time_start
            result = True
            self._log.info('PRM Dummy Handler invocation successful: check memory table for output')
        elif 'Execution Failed' not in output:
            self.invocation_time = datetime.now() - time_start
            result = True
            self._log.info('PRM Dummy Handler invocation successful: check memory table for output')
        else:
            self._log.error('PRM Invoke Handler failed ')
            raise RuntimeError("PRM Invoke Handler failed")

        return result

    def update_prm_handler(self):
        time_start = datetime.now()
        self.run_powershell_command(command=self.update_prm_handler_command + " " + self.capsule, get_output=True,
                                    echo_output=True)
        self.update_time = datetime.now() - time_start
        result = True
        self._log.info('PRM handler update executed: check memory tool for version')
        return result

    def update_prm_handler_os_wrapper(self):
        time_start = datetime.now()
        self.run_powershell_command(command=self.update_prm_handler_command + " 'up_prm'", get_output=True,
                                    echo_output=True)
        self.update_time = datetime.now() - time_start
        self._log.info('PRM handler update executed: check memory tool for version')
        # if 'PRM Handler Update Complete' in output:
        #     self.update_time = datetime.now() - time_start
        #     result = True
        #     self._log.info('PRM handler update executed: check memory tool for version')
        # else:
        #     result = False
        #     self._log.error('PRM handler update failed')
        #     raise RuntimeError("PRM handler update failed")
        return True

    def prm_cleanup(self):
        self._log.info("Clean previous PRM update")
        self.run_powershell_command(command=self.cleanup_prm_handler_command, get_output=True, echo_output=True)
        self._log.info("PRM cleanup complete, restarting the system")
        # self.warm_reset = True
        self.block_until_complete(None)
        result = True
        # TODO: uncomment following after windows OS change
        # if 'PRM Update is cleaned up. Please reboot' in output:
        #     self._log.info('PRM update cleanup was successful. Rebooting system')
        #     self.warm_reset = True
        #     output = self.block_until_complete(None)
        #     result = True
        # else:
        #     self._log.error("PRM cleanup failed")
        #     result = False
        #     raise RuntimeError("PRM cleanup failed")

        return result

    # Determine Delay
    def get_delay(self):
        # Convert to floats
        min_delay = None
        max_delay = None
        if self.min_delay is not None:
            min_delay = float(self.min_delay)
        if self.max_delay is not None:
            max_delay = float(self.max_delay)

        # Generate delay count
        random.seed(datetime.now())
        if min_delay is not None and max_delay is not None:
            return random.uniform(min_delay, max_delay)
        elif min_delay is not None:
            return min_delay
        elif max_delay is not None:
            return max_delay

        return 0

    def execute(self):
        result = False

        try:
            if self.start_workloads:
                self.summary_log.info("\tStart workloads: " + str(self.start_workloads))
                self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                self.begin_workloads()

            # time_start = datetime.now()

            if self.flow_type == 'update':
                for x in range(self.loop_count):
                    self._log.info('Start of iteration ' + str(x + 1))
                    # self.invoke_prm_handler_os_wrapper()
                    self.update_prm_handler_os_wrapper()
                    # self.invoke_prm_handler_os_wrapper()
                    self._log.info('End of iteration ' + str(x + 1) + ': Check PRM version in RW tool')
                    self.total_iter = x + 1
                    self._log.info('Rollback before next iteration: ')
                    result = self.prm_cleanup()

                    time.sleep(self.get_delay())

            elif self.flow_type == 'invoke':
                for x in range(self.loop_count):
                    self._log.info('Start of iteration ' + str(x + 1))
                    result = self.invoke_prm_handler_os_wrapper()
                    self._log.info('End of iteration ' + str(x + 1) + ': Check PRM version in RW tool')
                    self.total_iter = x + 1

                    time.sleep(self.get_delay())

            if result:
                result = True  # self.examine_post_update_conditions("PRM")
                self._log.info("\tPost update conditions checked")

        except RuntimeError as e:
            self._log.exception(e)

        if self.workloads_started:
            wl_output = self.stop_workloads()
            self._log.error("Evaluating workload output")
            if not self.evaluate_workload_output(wl_output):
                result = False
        return result

    def cleanup(self, return_status):
        super(SEAM_BMC_0016_prm_loop_update, self).cleanup(return_status)
        self._log.info("Invocation time: " + str(self.invocation_time))
        self._log.info("Update time: " + str(self.update_time))
        self._log.info("Total iterations passed: " + str(self.total_iter))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0016_prm_loop_update.main() else Framework.TEST_RESULT_FAIL)
