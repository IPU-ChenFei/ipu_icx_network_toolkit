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
from src.lib.content_base_test_case import ContentBaseTestCase
from src.pnp.lib.pnp_constants import Config, PnpPath
from src.lib import content_exceptions
from typing import TYPE_CHECKING
import json
import os
from pathlib import Path

if TYPE_CHECKING:
    from src.pnp.lib.common import PnPBase

class WorkloadSetup(ContentBaseTestCase):
    """
    Class for doing PnP WorkLoad Setups
    """
    def __init__(self, test_log, arguments, cfg_opts, workload_details, pnp_base : 'PnPBase'):
        super(self.__class__, self).__init__(test_log, arguments, cfg_opts)
        #log = self._log
        #self._log = log
        self.pnp_lib = pnp_base.common_pnp_lib
        self.__wl_details = workload_details
        self.content_lib = pnp_base._common_content_lib

    def prepare_sut_for_workload_execution(self, workload):
        #Check for WL setup done
        if self.workload_setup_done(workload):
            return

        if Config.BIOS_FILE in self.__wl_details.keys():
            self.set_bios_knobs_and_reboot_and_verify()

        if workload == 'qat':
            self.qat_pre_execution_setup()
        elif workload == 'dlb':
            self.dlb_pre_execution_setup()
        elif workload == 'specjbb':
            self.specjbb_pre_execution_setup()
        elif workload == 'sst':
            self.sst_pre_execution_setup()

        #git checkout branch
        if Config.BRANCH in self.__wl_details.keys():
            self._log.info("Using branch '{}' for workload '{}'".format(self.__wl_details[Config.BRANCH],workload))
            self.pnp_lib.git_checkout(self.__wl_details[Config.BRANCH])
        else:
            #git checkout master
            pass

        #set Workload setup done flag
        self.set_flag_workload_setup_done(workload)

    def set_bios_knobs_and_reboot_and_verify(self):
        self._log.info("Setting BIOS Knobs")
        self.bios_util.load_bios_defaults()
        self.bios_util.set_bios_knob(bios_config_file=self.__wl_details[Config.BIOS_FILE])
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self.bios_util.verify_bios_knob(bios_config_file=self.__wl_details[Config.BIOS_FILE])
        

    def qat_pre_execution_setup(self):
        self._log.info("Preparing SUT for QAT Execution")

    def dlb_pre_execution_setup(self):
        self._log.info("Preparing SUT for DLB Execution")
        username = os.environ['sys_user']
        password = os.environ['atf_api']

        # Downloading DLB driver file from ubit-artifactory.
        self.content_lib.execute_sut_cmd('mkdir -p /root/dlb_driver', "Creating 'dlb_driver' directory in SUT.", 10)
        self.content_lib.execute_sut_cmd('rm -rf /root/dlb_driver/*', "rm -rf /root/dlb_driver/*", 10)

        with open(os.path.join(Path(os.path.join(__file__)).parent, 'artifactory.json'), 'r') as data:
            artifactory_links = json.load(data)
        dlb_link = artifactory_links['dlb']
        dlb_driver_file_name = dlb_link.split("/")[-1].split(".zip")[0]
        download_cmd = "curl -u " + str(username) + ":" + str(password) + " -X GET " + str(
            dlb_link) + " --output /root/dlb_driver/" + dlb_driver_file_name

        self.content_lib.execute_sut_cmd(download_cmd, "Downloadng DLB Driver file form ubit-artifactory.", 60)

        output = self.content_lib.execute_sut_cmd(f'unzip /root/dlb_driver/{dlb_driver_file_name} -d /root/dlb_driver/',
                                                  "Extract DLB Drivers files.", 60)
        if 'unzip:  cannot find zipfile directory' in output:
            error_msg = "Error extracting files."
            raise content_exceptions.TestSetupError(error_msg)
        else:
            self._log.info("Successfully extracted files!")

        insmod_cmd = 'insmod /root/dlb_driver/dlb/driver/dlb2/dlb2.ko'
        make_cmd = 'make -C /root/dlb_driver/dlb/driver/dlb2/'
        self.content_lib.execute_sut_cmd(make_cmd, make_cmd, 60)
        self.content_lib.execute_sut_cmd(insmod_cmd, insmod_cmd, 60)

        self._log.info("Check if DLB driver loaded in kernel.")
        grep_cmd = 'lsmod | grep "dlb2"'
        output = self.content_lib.execute_sut_cmd(grep_cmd, 'lsmod | grep "dlb2"', 10)
        if 'dlb2' in str(output):
            self._log.info("DLB driver loaded in kernel.")
        else:
            raise content_exceptions.TestSetupError("DLB driver not loaded in kernel.")
    
    def specjbb_pre_execution_setup(self):
        self._log.info("Preparing SUT for SPECJBB Execution")

        # SPECJBB achieves best performance when running with 1GB transparent huge pages.
        # Default OS will have THP enabeld but only 2MB huge pages are default ones.
        # So, one need to make 1GB huge pages as default via kernel parameters.
        self._log.info("Making 1GB huge pages as default via kernel parameters")
        cmd = "grubby --update-kernel=/boot/vmlinuz-$(uname -r) --args=\"default_hugepagesz=1G hugepagesz=1G\""
        self.content_lib.execute_sut_cmd(cmd, "Set Huge Pages to 1G", 30)

        #Reboot SUT
        self._log.info("Rebooting OS")
        self.content_lib.perform_os_reboot(self.content_lib._reboot_timeout)
        

        #Verify Huge Pages is set to 1G
        cmd = "cat /proc/meminfo | grep Hugepagesize"
        output = self.content_lib.execute_sut_cmd(cmd, "cat /proc/meminfo", 30)
        split = str(output).split(':')
        huge_page_size = split[1].strip()

        if huge_page_size != "1048576 kB":
            log_error = "Huge page size not set to 1G"
            raise content_exceptions.TestSetupError(log_error)
        
        self._log.info("SPECJBB Pre-execution Setup done Successfully")
        
        return True

    def sst_pre_execution_setup(self):
        self._log.info("Preparing SUT for SST Execution")
        cmd = 'grubby --update-kernel=ALL --args="cpu0_hotplug"'
        self.content_lib.execute_sut_cmd(cmd, 'grubby --update-kernel=ALL --args="cpu0_hotplug"', 30)

        self._log.info("Rebooting OS")
        self.content_lib.perform_os_reboot(self.content_lib._reboot_timeout)

        cmd_to_verify = 'cat /proc/cmdline | grep cpu0_hotplug'
        cmd_output = self.content_lib.execute_sut_cmd(cmd_to_verify, "cat /proc/cmdline", 30)

        if 'cpu0_hotplug' not in str(cmd_output):
            cmd_error = 'Error adding new kernel arguments.'
            raise content_exceptions.TestSetupError(cmd_error)

        self._log.info("SST Pre-execution Setup done Successfully.")

    def workload_setup_done(self, workload_name):
        """
        Checks for WL setup file on SUT

        Args:
            workload_name: Name of the workload
        
        Returns:
            True: If the setup is already done for the WL
            False: If the setup is not done
        """
        file = PnpPath.TEMP_DIR + workload_name
        if self.file_exists_on_sut(file):
            return True

        return False

    def set_flag_workload_setup_done(self, workload_name):
        """
        Sets flag for the WL indicating the setup is done

        Args:
            workload_name: Name of the workload
        """
        file = PnpPath.TEMP_DIR + workload_name
        cmd = "touch " + file
        self._common_content_lib.execute_sut_cmd(cmd, cmd, 30)

    def file_exists_on_sut(self, path):
        """
        This function checks whether a file exists on the SUT

        Args:
            path: Path to the file

        Returns:
            True: if file exists
            False: if the file does not exist
        """
        self.cmd = "eval \"[[ -f " + path + " ]] && echo \"1\"\" || echo \"0\""
        cmd_output = int(self._common_content_lib.execute_sut_cmd(self.cmd, self.cmd, 30))

        if cmd_output:
            return True

        return False
