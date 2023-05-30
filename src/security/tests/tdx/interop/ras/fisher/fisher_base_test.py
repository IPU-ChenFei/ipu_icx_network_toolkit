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
"""
    :Fisher RAS Base Test Case:

    Launch Fisher RAS test suite for an extended period of time.  Calculate the failure rate if applicable and determine
    if it is acceptable.
"""
import six
import sys
import os

from abc import ABCMeta

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


@six.add_metaclass(ABCMeta)
class TdxRasFisherBaseTest(LinuxTdxBaseTest):
    """
           This is a base test for workload testing with TD guests as part of the TDX feature.

           The following parameters in the content_configuration.xml file should be populated before running a test.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.

            :Scenario: Launch the number of TD guests prescribed, initiate Fisher RAS test on the SUT, run for the
            necessary time to complete the test, then verify the SUT and the TD guests have not crashed.

            :Phoenix IDs:

            :Test steps:

                :1: Launch a TD guest.

                :2: Repeat step 1 for the prescribed number of TD guests.

                :3: On the TD host, launch the Fisher RAS test.

                :4: Run until Fisher RAS test completes.

                :5: If applicable, calculate the error ratio.

            :Expected results: Each TD guest should boot and the workload suite should run to completion with no
            errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """Create an instance of TdxBaseTest

        :param cfg_opts: Configuration Object of provider
        :type cfg_opts: str
        :param test_log: Log object
        :type arguments: Namespace
        :param arguments: None
        :type cfg_opts: Namespace
        :return: None
        """
        super(TdxRasFisherBaseTest, self).__init__(test_log, arguments, cfg_opts)

        self.bios_knobs = []
        self.workload_name = ""  # overwritten by inheriting test class
        self.run_time = 0.0  # overwritten by inheriting test class
        self.fisher_command = ""  # overwritten by inheriting test class
        self.pass_ratio = 0.8  # default pass ratio
        self.free_mem = 0.0  # stressapptest must have amount of memory free to test provided

    def prepare(self):
        super(TdxRasFisherBaseTest, self).prepare()
        self._log.debug("Setting BIOS knobs for RAS Fisher testing..")
        knob_file = self.build_knob_file()
        self.check_knobs(knob_file=knob_file, set_on_fail=True)
        os.remove(knob_file)
        self._log.debug("Checking EINJ is initialized and error table is available.")
        einj_result = self.execute_os_cmd("dmesg | grep -i EINJ")
        if not self.tdx_properties[self.tdx_consts.INTEL_NEXT_KERNEL]:
            error_table_result = self.execute_os_cmd("ls -l /sys/kernel/debug/apei/einj")
        else:
            error_table_result = True
        if einj_result != "" and error_table_result != "":
            self._log.debug(f"EINJ and error table check passed.  Output: einj result: {einj_result}; error table "
                            f"in OS: {error_table_result}")
        self._log.debug("Checking error collector is running.")
        self.setup_error_collector()
        self.set_up_fisher()
        self.install_workload()

    def execute(self):
        num_vms = self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS]
        self._log.info(f"Creating and launching {num_vms} VMs.")
        for idx in range(0, num_vms):
            self._log.info(f"Starting TD guest {idx}.")
            self.launch_vm(key=idx, tdvm=True)
            self._log.info(f"Attempting to execute SSH command to VM key {idx}.")
            if not self.vm_is_alive(key=idx):
                raise content_exceptions.TestFail(f"VM {idx} could not be reached after booting.")
            self._log.debug(f"SSH was successful; VM {idx} is up.")

        # make directory and run fisher command
        self.execute_os_cmd("mkdir -p /home/fisher")
        directory_name = f"/home/fisher_{self.workload_name}"
        self.execute_os_cmd(f"rm -rf {directory_name}")
        self.execute_os_cmd(f"mkdir -p {directory_name}")
        run_time_plus_buffer = self.run_time * 60.0 * 60.0 * 1.25  # convert to seconds, add 25% timeout buffer
        self._log.info(f"Running Fisher test.  Command: {self.fisher_command}")
        results = self.execute_os_cmd(f"cd {directory_name}; {self.fisher_command}", run_time_plus_buffer)

        self._log.info("Fisher test is finished.  Parsing logs.")
        # clean up
        # collect log files and copy to SUT
        find_cmd = f"find {directory_name} -name 'fisher_*.log'"
        fisher_file_path = self.execute_os_cmd(find_cmd)
        if fisher_file_path == "":
            raise content_exceptions.TestFail("Could not find path to fisher log file!  Fisher test likely failed; "
                                              "try testing the command that was run manually.  "
                                              f"Command: {self.fisher_command}")

        fisher_file_name = fisher_file_path.split("/")[-1]
        local_path = f"{self.log_dir}\\{fisher_file_name}"
        self.os.copy_file_from_sut_to_local(fisher_file_path, local_path)

        # copy fisher logs to tdvm logs
        self.execute_os_cmd(f"mv -r {directory_name} {self.tdx_consts.TD_GUEST_LOG_PATH_LINUX}")

        # calculate error ratio if needed and determine results
        self.log_sanity_check(local_path)
        ratio = self.calculate_error_ratio(local_path)

        if ratio < self.pass_ratio:
            raise content_exceptions.TestFail(f"Pass to fail ratio did not meet cutoff value {self.pass_ratio} "
                                              f"requirement.  Actual ratio: {ratio}")
        else:
            self._log.info(f"Pass to fail ratio was met or exceeded cutoff value {self.pass_ratio}.  Actual ratio: "
                           f"{ratio}")
            return True

    def set_up_fisher(self):
        """Install Fisher on SUT."""
        result = self.os.execute("export no_proxy=*.intel.com;"
                                 "export PYTHONHTTPSVERIFY=0;"
                                 "export PIP_TRUSTED_HOST=intelpypi.intel.com;"
                                 "export PIP_INDEX_URL=https://intelpypi.intel.com/pythonsv/production;"
                                 "pip3 install pysvtools.fish-automation", self.command_timeout)
        fisher_version = self.execute_os_cmd("fisher --version")
        if "fisher" not in fisher_version:
            raise content_exceptions.TestSetupError(f"Fisher could not be installed! Command output: stderr: "
                                                    f"{result.stderr}")

    def install_workload(self):
        """Install various workloads.  Extra steps are needed for the below workload applications to be installed:
        stressapptest:  requires calculating memory free with a buffer subtracted due to app's inability to accurately
        detect free space.  Stresspptest GitHub issue: https://github.com/stressapptest/stressapptest/issues/46"""
        if self.workload_name == "":
            raise content_exceptions.TestSetupError("No workload name provided!")
        if self.workload_name == self.tdx_consts.WorkloadToolNames.STRESSAPPTEST:
            path = self.install_collateral.install_stress_test_app()
            self.free_mem = self.execute_os_cmd("free | grep Mem | awk -F' ' '{print $3}'")
            try:
                self.free_mem = int(self.free_mem) - 1000000  # remove 1GB memory buffer, see docstring
                self.free_mem = int(self.free_mem) / 1000  # convert to MB
            except ValueError:
                raise content_exceptions.TestSetupError("Failed to retrieve the free amount of memory available on the "
                                                        f"SUT.  Free memory results: {self.free_mem}")
            if self.free_mem < 0:
                raise content_exceptions.TestSetupError("Not enough memory is free to run stressapptest.  Please check "
                                                        "SUT OS and free up memory.")
        elif self.workload_name == self.tdx_consts.WorkloadToolNames.STRESSNG:
            path = self.install_collateral.yum_install(self.tdx_consts.WorkloadToolNames.STRESSNG)
        elif self.workload_name == self.tdx_consts.WorkloadToolNames.MLC_INTERNAL:
            path = self.install_collateral.install_mlc()
            self.execute_os_cmd(f"chmod +x {path}/mlc")
            self.execute_os_cmd(f"ln -s {path}/mlc /usr/sbin/mlc_internal")
        elif self.workload_name == self.tdx_consts.WorkloadToolNames.SHA512SUM:
            path = None
            self.install_collateral.yum_install("coreutils")
        else:
            raise content_exceptions.TestSetupError("There is no install collateral procedure for workload "
                                                    f"{self.workload_name}!")
        # create executable shortcut
        if self.execute_os_cmd(f"find /usr/sbin -name \'{self.workload_name}\'") == "" and path is not None:
            self._log.debug("Installing short cut in /usr/sbin/.")
            self.execute_os_cmd(f"ln -s {path} /usr/sbin/{self.workload_name.lower()}")
        else:
            self._log.debug("Shortcut already exists for workload in /usr/sbin.")

    @staticmethod
    def calculate_error_ratio(file_path):
        """Calculate pass/fail ratio to determine if test passes.
        :param file_path: path to the"""
        for line in reversed(open(file_path).readlines()):
            if "PASS = " in line:
                data = line.split(":")[-1].strip()  # get rid of time stamp
                values = [int(s) for s in data.split() if s.isdigit()]
                if len(values) != 2:
                    raise content_exceptions.TestFail("More than 2 values found in results line from "
                                                      f"{file_path}. ")
                pass_count = int(values[0])
                fail_count = int(values[1])
                try:
                    results = pass_count / (fail_count + pass_count)
                except ZeroDivisionError:
                    raise content_exceptions.TestFail(
                        f"Zero was returned for pass/fail data found in fisher log {file_path}.  Check log file to "
                        f"verify if Fisher completed a cycle or other testing error.")
                return results
        raise content_exceptions.TestFail("No pass/fail data found in fisher log {}.  Check log file to verify if "
                                          "Fisher completed a cycle.  Run time might need to be "
                                          "increased.".format(file_path))

    def build_knob_file(self):
        """Build knob file to set Fisher RAS knobs with.
        :return: string pointing to built BIOS knob config file.
        :rtype: str"""
        _RAS_COLLATERAL_PATH = "collateral/"
        _RAS_FISHER_BIOS_KNOB = "fisher_base_knobs.cfg"
        self.bios_knobs.append(_RAS_FISHER_BIOS_KNOB)
        temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_fisher_knob_file.cfg")

        for knob_file in self.bios_knobs:
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), _RAS_COLLATERAL_PATH, knob_file)
            with open(full_path) as in_file:
                with open(temp_file, "w+") as out_file:
                    for line in in_file:
                        out_file.write(line)
        return temp_file

    def setup_error_collector(self):
        """Set up and verify a valid error collector is running."""
        self.install_collateral.yum_remove("rasdaemon")  # do not use rasdaemon per RAS team
        ec_running = False
        active_string = "active (running)"
        for ec in self.tdx_consts.LINUX_ERROR_COLLECTORS:
            if active_string not in self.execute_os_cmd(f"systemctl status {ec}"):
                self.execute_os_cmd(f"systemctl restart {ec}")
            if active_string in self.execute_os_cmd(f"systemctl status {ec}"):
                self._log.debug(f"Found error collector {ec} running.  Will use this for test.")
                ec_running = True
                break
        if not ec_running:
            raise content_exceptions.TestSetupError("Tried to bring up error collectors, but failed on all attempted.")

    def log_sanity_check(self, log_file: str):
        """Sanity checks for Fisher test.
        :param log_file: log file for Fisher RAS test to be examined."""
        command = self.fisher_command.split("--")
        for arg in command:
            if "cycles" in arg.split("="):
                option = int(arg.split("=")[-1])
                compare_value = self.get_run_cycles(log_file)
                break
            elif "runtime" in arg.split("="):
                option = self.run_time
                compare_value = self.get_run_time(log_file)
                break
        try:
            if option == compare_value:
                self._log.debug("Test appears to have run the expected number of cycles and/or run time.")
            else:
                raise content_exceptions.TestFail("Could not verify test ran the minimum run time/number of cycles.  "
                                                  f"Please check log file {log_file}.")
        except NameError:  # option or compare_value could not be determined from command string or log file
            raise content_exceptions.TestError("Could not determine the minimum run time/number of cycles.  "
                                               f"Please check log file {log_file}.")

    @staticmethod
    def get_run_time(file_path: str) -> int:
        """Get run time from Fisher log file.
        :param file_path: file path to Fisher log file."""
        for line in reversed(open(file_path).readlines()):
            if " total run time" in line:
                data = line.split("total run time:")[-1].strip()  # get rid of time stamp
                hours_run = data.split(":", 1)[0]
                return int(hours_run)
        raise content_exceptions.TestFail(f"No time run data found for Fisher test.  Please check log file "
                                          f"{file_path}.")

    @staticmethod
    def get_run_cycles(file_path: str) -> int:
        """Get number of cycles run from Fisher log file.
        :param file_path: file path to Fisher log file."""
        for line in reversed(open(file_path).readlines()):
            if " RUNNING CYCLE " in line:
                data = line.split("total run time:")[-1].strip()  # get rid of time stamp
                cycles_run = data.split("=")[-1].strip()
                return int(cycles_run)
        raise content_exceptions.TestFail(f"No cycle run data found for Fisher test.  Please check log file "
                                          f"{file_path}.")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxRasFisherBaseTest.main() else Framework.TEST_RESULT_FAIL)
