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
Common file for different tools used in HSIO PCIe stress testing.
    - Core polling
    - Test application polling
    - Status Scope log
    - MCE log
"""

import os
import re
import random
from time import sleep
from src.lib import content_exceptions
from datetime import datetime, timedelta
from src.provider.pcie_provider import PcieProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.content_base_test_case import ContentBaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from src.provider.stressapp_provider import StressAppTestProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

__this_dir__ = os.path.dirname(os.path.abspath(__file__))


class HsioStressCommon(ContentBaseTestCase):
    """
    Main thread should run this logger and keep polling the test thread.
    In the event of system crash, MCE and status scope logs will be captured.
    """
    MAX_BUFFER_TIME_SEC = 900  # seconds
    WAIT_SEC = 10
    PTG_FP_DID_LIST = ['0501']  # PTG_PHY_DID_LIST = ['0d52']
    AUTO = "auto"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        super(HsioStressCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._args = arguments
        self._cfg = cfg_opts
        self._initial_link_info = {}  # {bus1: (speed, width), bus2: (speed, width)}
        self._final_link_info = {}  # Link info after test.
        self.pcie_provider = PcieProvider.factory(self._log, self.os, cfg_opts, "os", uefi_obj=None)

        # Create Install Collateral Object for downloading tools from Artifactory to Host and then to SUT
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

        # Get PythonSV and Cscript Objects
        self.sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        # Don't initialize CScripts object first. Facing some problem starting PythonSV instance if we do this.
        # self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)

        # OS logging - DMESG
        self._check_os_log = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                               self._common_content_lib)
        # Stress provider
        self.sut_os = self.os.os_type
        self._cfg = cfg_opts
        self.itp = self.sdp.itp  # Silicon debug provide == itp
        self.stress_provider = StressAppTestProvider.factory(self._log, self._cfg, self.os)
        self.reset_itp_break_points()

        # Initialize variables -
        self.test_group = None  # Each test case will overwrite this before calling prepare.
        self.tool_path = None
        self.ptg_files = None
        self.ptg_executable_path = None
        self.emi_loader_path = None
        self.pmutil_path = None

    def detect_devices_by_did(self, did_list, return_type=list):
        """
        :param did_list: List of DIDs to look for. [did1, did2]
        :param return_type: valid values: list, dict.
                "dict" could be helpful for multifunction devices, key 'bdf' will hold all the bdf under a given bus.
                all keys and values are of type str.
                {<bus1>:
                    {'bdf': [<bdf1>, <bdf2>]},
                <bus2>:
                    {'bdf'}: [<bdf>]
                ...
                }
        """
        bus_list = {}
        for did in did_list:
            devices = str(self._common_content_lib.execute_sut_cmd(f"lspci -d :{did}", "Fetch BDF from DID", 3)).strip()
            if devices == "":
                continue
            devices = devices.split('\n')
            for device in devices:
                bdf = device.split(' ')[0]
                if bdf.count(":") == 2:
                    bus = bdf.split(":")[1]
                else:
                    bus = bdf.split(":")[0]

                if bus not in bus_list.keys():
                    bus_list[bus] = {"bdf": [bdf]}
                else:
                    bus_list[bus]["bdf"].append(bdf)

        if not bus_list:
            raise content_exceptions.TestFail(f"Could not find any known card! Or update the script with new DID. "
                                              f"Current DID list: {self.PTG_DID_LIST}")
        return return_type(bus_list)

    def prepare_ptg(self):
        """
        All configurations specific to PTG related tests.
        :return:
        """
        # Copy PTG files to SUT and get path
        self.tool_path = self._install_collateral.install_ptg()
        self.ptg_files = os.path.join(self.tool_path, "PTG-BKM", "PTG", "new_linear",
                                      "new_linear").replace("\\", "/")
        self.ptg_executable_path = os.path.join(self.tool_path, "PTG-BKM", "PTG",
                                                "ptg5_beta5_static").replace("\\", "/")
        self.emi_loader_path = os.path.join(self.tool_path, "PTG",
                                            "emi_loader").replace("\\", "/")  # For later.
        self._log.info(f"PTG tool copied to SUT - {self.tool_path}")
        # Copy PTG Wrapper to SUT.
        ptg_wrapper = "ptg_linux.py"
        self._install_collateral.copy_collateral_script(ptg_wrapper, self.ptg_executable_path)

    def prepare(self):
        """
        Checks if the configuration info has card that supports PTG.
        If no config is available, warns the user and checks if any other slot has required card.
        If card is found, holds the BDF and starts executing.
        Valid test_group:            # TODO- Always update this list after adding new test case.
            - "ptg"
            - "ptg_pm_harasser"
        """
        self._install_collateral.screen_package_installation()
        # Kernel arguments
        intel_iommu_on_str = "intel_iommu=on,sm_on"
        self._log.info(f"Kernel arguments will be updated for enabling IOMMU: {intel_iommu_on_str}")
        result_data = self._common_content_lib.execute_sut_cmd(
            f"grubby --update-kernel=ALL --args='{intel_iommu_on_str}'",
            "updating grub config file",
            self._command_timeout)
        self._log.debug("Updated the grub config file with stdout:\n{}".format(result_data))

        if self.test_group == "ptg":
            self.prepare_ptg()
        elif self.test_group == "ptg_pm_harasser":
            self.prepare_ptg()
            # Get PM-Utility
            self.pmutil_path = self._install_collateral.install_pmutility()

        super(HsioStressCommon, self).prepare()
        self.set_itp_break_points()  # Set breakpoints for stress tests.

    def trigger_wrapper(self, command, runtime):
        """
        Triggers the wrapper script with arguments as per test case.
        Starts polling the application and core status.
        :param command: List of tuples holding command, path info and application name. This information is used for
            polling application status.
            [(command1, executable_path1, app_name1), (command2, executable_path2, app_name2), ...]
        :param runtime: Test runtime in seconds.
        """
        buffer_time = min(runtime * 0.1, self.MAX_BUFFER_TIME_SEC)  # 10% of runtime or 15 minutes, whichever is lower.
        test_info = []  # To be used for polling application.
        if self.test_group == "ptg":
            for (test_cmd, test_path, test_app) in command:
                self._log.info(f"Executable path- {test_path} and command - {test_cmd}")
                self.os.execute_async(test_cmd, cwd=test_path)
                self._log.info("Test triggered. (Non-blocking execution)")
                test_info.append((test_app, test_cmd))
        elif self.test_group == "ptg_pm_harasser":
            for (test_cmd, test_path, test_app) in command:
                self._log.debug(f"Executable path- {test_path} and command - {test_cmd}")
                self.os.execute_async(test_cmd, cwd=test_path)
                test_info.append((test_app, test_cmd))
        # Start polling as a blocking thread.
        status = self.start_polling(test_info=test_info, runtime_sec=(runtime + buffer_time))
        return status

    def verify_ptg(self, test_type, execution_log):
        """
        Verify execution logs.
        :param test_type: "rd", "rdwr", "wr"
        :param execution_log:
        :return:
        """
        self._log.info("Proceeding to verify")
        log_files = []  # Hold sut_path and host_path
        log_filepath = os.path.join(self.ptg_executable_path, self.bw_file).replace("\\", "/")
        host_path = os.path.join(self.log_dir, self.bw_file)
        log_files.append((log_filepath, host_path))

        log_filepath = os.path.join(self.ptg_executable_path, execution_log).replace("\\", "/")
        host_path = os.path.join(self.log_dir, execution_log)
        log_files.append((log_filepath, host_path))

        self.copy_logs_to_host(log_files)
        result = self.parse_ptg_log(test_type, execution_log)
        return result

    def cleanup(self, return_status):
        """
        Copy log files from SUT to HOST.
        """
        super(HsioStressCommon, self).cleanup(return_status)

    def copy_logs_to_host(self, log_files):
        """
        Common. Copy logs from SUT to Host.
        :param log_files:
            list of tuples [(sut_path, host_path),
                            (sut_path, host_path)]
        """
        for (sut_path, host_path) in log_files:
            self._log.info(f"Copying log file from {sut_path} to {host_path}")
            self.os.copy_file_from_sut_to_local(source_path=sut_path, destination_path=host_path)

    def check_link_status(self, bus_list=None):
        """
        Common. If we are checking the first time, 'bus_list' argument is required!

        :param bus_list: list of bus numbers in hex (but without '0x' prefix)
                        'bus_list' can be something like [38,98]
        :return: None if checking first time
                True if initial link info matches link info after test
                False if initial link info does not match link info after test, indicating possible degrade in link.
        """
        self._log.info("Proceeding to check link status")
        if self._initial_link_info == {}:
            for bus in bus_list:
                (speed, width) = self.get_link_info(f"{bus}:00.0")
                self._initial_link_info[bus] = (speed, width)
            self._log.info("Initial link status: {self._initial_link_info}")
            return
        else:
            self._log.info("Checking for any link / width degrades")
            for bus in self._initial_link_info.keys():
                (speed, width) = self.get_link_info(f"{bus}:00.0")
                self._final_link_info[bus] = (speed, width)
            self._log.info(f"Final link status: {self._final_link_info}")
            if self._initial_link_info != self._final_link_info:
                return False
        return True

    def parse_ptg_log(self, test_type, execution_log):
        """
        PTG log parser. We only check if the bandwidth is non zero or valid.
        Due to various factors, the bandwidth could vary significantly; so we don't check if the bandwidth numbers
        meet the expected numbers.

        We parse the PTG Execution log for any known error messages.

        :param test_type: specify whether test is read only, write only or read-write
                        valid strings accepted - "rd", "wr", "rdwr"
        :param execution_log: execution log's file name.
        """
        self._log.info("Proceeding to parse PTG execution log")
        host_path = os.path.join(self.log_dir, execution_log)
        with open(host_path, "r") as f:
            data = f.read().lower()
            f.close()
        patterns = {
            "rd": ["reads:     0.00 mb/s      0.00 mb/s"],
            "wr": ["writes:     0.00 mb/s      0.00 mb/s"],
            "rdwr": ["reads:     0.00 mb/s      0.00 mb/s", "writes:     0.00 mb/s      0.00 mb/s"]
        }  # format: <test_type>: <list of strings to look for in the execution log>
        error_patterns = ['illegal pci base address', 'the card returned an error', 'error: no bus specified',
                          'you may need to try another test or re-flash/reset the card.']

        # Check if reads and writes are 0
        for pattern in patterns[test_type]:
            match = re.search(pattern, data)
            if match:
                self._log.info(f"Observed -> {pattern}")
                return False
        # Check for error strings
        for pattern in error_patterns:
            match = re.search(pattern, data)
            if match:
                self._log.info(f"Observed -> {pattern}")
                return False

        self._log.info("No known PTG errors seen. Bandwidth numbers are valid.")

        result = self.check_link_status()
        return result  # No errors, valid bandwidth and no link degrades!

    def set_itp_break_points(self):
        """
        This method is to set the break point.
        """
        self._log.info("Setting breakpoints...")
        self.itp.halt()
        try:
            self.itp.cv.resetbreak = 1
            self.itp.cv.machinecheckbreak = 1
            self._log.info("Breakpoints are set!")
        except:
            raise content_exceptions.TestFail("Failed to set breakpoints!")
        finally:
            self.itp.go()

    def reset_itp_break_points(self):
        """
        Removes breakpoints. Call before prepare phase.
        """
        self._log.info("Removing breakpoints...")
        self.itp.halt()
        try:
            self.itp.cv.resetbreak = 0
            self.itp.cv.machinecheckbreak = 0
            self._log.info("Breakpoints are removed!")
        except:
            raise content_exceptions.TestFail("Failed to reset breakpoints!")
        finally:
            self.itp.go()

    def start_polling(self, runtime_sec, test_info=None, buffer_time_sec=None, no_timeout=False):
        """
        Polls
            - Core Status (Does not require 'test_info')
            - Test application on SUT. (Needs 'test_info')

        Polling will be done here. Main thread blocker.

        :param no_timeout:
        :param buffer_time_sec: value in seconds to stop polling for application.
                    if None; the minimum of 10% runtime and 900 seconds (defined by self.MAX_BUFFER_TIME_SEC) is taken.
        :param runtime_sec: runtime in seconds
        :param test_info : List of tuples -> (<test applications name running on SUT>,
                                            <command for that test application>)
                                            Example: [
                                               ('ptg', 'python ptg_linux.py -f'),
                                                ('fio', 'fio --filename=/dev/nvme0n1')
                                                ]
        """
        if not buffer_time_sec:
            buffer_time_sec = min(runtime_sec * 0.1, self.MAX_BUFFER_TIME_SEC)  # Default buffer of 10 % or 15 minutes

        test_start = datetime.now()
        target_runtime = test_start + timedelta(seconds=runtime_sec)  # Actual expected runtime.
        app_polling_end = target_runtime - timedelta(seconds=buffer_time_sec)  # If application closes, return as fail
        core_polling_end = target_runtime + timedelta(
            seconds=buffer_time_sec)  # If application does not stop, return fail

        self._log.info(f"Test start time : {test_start}")
        self._log.info(f"Test runtime : {runtime_sec}")
        self._log.info(f"Expected test end time : {target_runtime}")

        self._log.info("Now polling core and application status.")
        while datetime.now() < core_polling_end:
            sleep(self.WAIT_SEC)
            # Poll test application status, if any.
            for (test_app, stress_test_command) in test_info:
                self._log.debug(f"Checking status of test application: {test_app} and command: {stress_test_command}")
                app_status = None
                try:
                    app_status = self.stress_provider.check_app_running(app_name=test_app,
                                                                        stress_test_command=stress_test_command)
                    self._log.debug(f"App running? : {app_status}")
                except Exception as e:
                    self._log.debug("Could not check status of application! Probably system has crashed.")
                    self._log.debug(f"App running? : {app_status}")
                    # Confirmation can come from checking core status, marking app_status as running to continue
                    app_status = True

                # If application has stopped, check if it stopped in expected time.
                if not app_status:
                    now = datetime.now()
                    if now < app_polling_end:  # Application stopped before runtime could be achieved.
                        self._log.info("Test stopped before runtime could be achieved.")
                        return app_status
                    else:  # elif now < core_polling_end:  # Application has stopped in expected range. Test complete.
                        self._log.info("Test application stopped on SUT in expected time.")
                        return True

            # Poll core status
            if self.itp.ishalted():
                self._log.debug("Polling core status")
                # use for else loop
                for counter in range(
                        2):  # Check status 30 times to avoid confusion with scenarios like error injection.
                    self._log.debug("Checking if cores are actually stuck... Can take around 5 minutes.")
                    counter += 1
                    sleep(random.randint(5, 12))
                    status = self.itp.ishalted()
                    if not status:
                        break  # No need to check further. We probably are running EI, or it was an isolated incident.
                else:
                    self._log.info("Capturing MCE and StatusScope logs")
                    # import pdb; pdb.set_trace()
                    self._common_content_lib.execute_pythonsv_function(self.capture_mce_log)
                    self._common_content_lib.execute_pythonsv_function(self.capture_status_scope)
                    self._log.info("MCE Status Scope Log collection completed.")
                    return False

        if no_timeout:
            self._log.info("Force closing the application(s)")
            for (test_app, stress_test_command) in test_info:
                self.stress_provider.kill_stress_tool(stress_tool_name=test_app,
                                                      stress_test_command=stress_test_command)
            return True
        else:
            self._log.info("Application did not stop in expected time! Marking test as fail.")
            return False

    @staticmethod
    def capture_mce_log(python_sv, log):
        """
        This method is to capture MCU Status Log.

        :param python_sv
        :param log
        """
        log.info("Capturing MCE logs")
        # UBOX
        log.info("Creating ubox object")
        server_ip_debug = python_sv.get_server_ip_debug_object()
        ubox = server_ip_debug.ubox
        log.info("Started UBOX log capture")
        ubox.Ubox().show_ww('MCA', source='reg')
        print(ubox.Ubox().show_ww('MCA', source='reg'))
        ubox.Ubox().show_mca_status(source='reg')
        print(ubox.Ubox().show_mca_status(source='reg'))
        log.info("ubox command execution completed")

        # MCE Errors
        log.info("Started MCE error log capture")
        log.info("Executing sv.sockets.uncore.ubox.ncevents.mcerrloggingreg.show()")
        python_sv.get_by_path(python_sv.SOCKETS, "uncore.ubox.ncevents.mcerrloggingreg").show()
        log.info("Executing sv.sockets.uncore.punit.mca_err_src_log.show()")
        python_sv.get_by_path(python_sv.SOCKETS, "uncore.punit.mca_err_src_log").show()
        log.info("Executing sv.sockets.uncore.punit.mc_status.show()")
        python_sv.get_by_path(python_sv.SOCKETS, "uncore.punit.mc_status").show()

        # CHA MCA Status
        cha = server_ip_debug.cha
        log.info("Started MCA status log capture")
        cha.Cha().show_mca_status(source='reg')
        log.info("MCA status execution completed")

        # MCU
        mcu = python_sv.get_mc_utils_obj()
        log.info("Started MCU error log CMD- mcu.show_errors()")
        mcu.show_errors()
        log.info("mcu.mcu.show_errors() execution completed")

    @staticmethod
    def capture_status_scope(python_sv, log):
        """
        This method is to capture Scope log.

        :param python_sv
        :param log
        """
        log.info("Capturing Status-Scope logs")
        analyzers = ['cha', 'pm', 'm2iosf', 'ubox', 'sys_cfg', 'pcie', 'ieh', 'm2mem']
        status_scope = python_sv.get_status_scope_obj()
        log.info("Executing command to initiate Status-Scope log capture")
        status_scope.run(collectors=['namednodes'], analyzers=analyzers)
        log.info("status_scope.run() command is completed")

    def get_link_info(self, bdf):
        """
        Fetches link speed and width from OS. (with pcie_provider)
        :returns <link speed>, <link width> or False, False if any of speed or width is not found.
        """
        try:
            link_speed = self.pcie_provider.get_link_status_speed_by_bdf(bdf)
            link_width = self.pcie_provider.get_link_status_width_by_bdf(bdf)
        except:
            self._log.error(f"ERROR trying to get link speed or width.")
            return False, False
        return link_speed, link_width
