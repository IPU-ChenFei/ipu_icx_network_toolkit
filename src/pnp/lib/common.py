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
from src.lib.content_base_test_case import ContentBaseTestCase
import src.lib.content_exceptions as content_exceptions
from src.pnp.lib.pnp_configuration import PnPConfiguration
from dtaf_core.lib.dtaf_constants import Framework
from src.pnp.lib.pnp_utils import CommonPnPLib
from src.provider.cpu_info_provider import CpuInfoProvider
from src.pnp.lib.pnp_constants import PnpPath
import sys

class PnPBase(ContentBaseTestCase):
    """
    Base class extension for PnPBase which holds common arguments
    and functions.
    """
    PNP_TMP_DIR = PnpPath.TEMP_DIR
    PNP_SETUP_FILE_NAME = "pnp_setup"
    PNP_GIT_CHECK_OUT_COMMIT = "git checkout {}"
    PNP_WLS_DIR = PnpPath.AUTOMATION_DIR + PnpPath.PNPWLS_REPO_DIR
    VAR_LOGS_PATH = "/var/log/"
    RUN_BASIC_SETUP = "./{} {}"
    RUN_INSTALL_DOCKER = "./{}"
    command_timeout = 100  # this timeout value is being used for installing git on SUT, cloning repo..

    # installing docker script and running basic setup script

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance for pnp_source_path and mlc_file.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(PnPBase, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)
        self.pnp_config = PnPConfiguration(test_log)
        self.system_location = self.pnp_config.get_system_location()
        self.commit_file = self.pnp_config.get_pnp_commit_id()
        self.git_username = self.pnp_config.get_pnp_git_username()
        self.deploy_token = self.pnp_config.get_pnp_deploy_token()
        self.basic_setup_file = self.pnp_config.get_basic_setup_script()
        self.install_docker_file = self.pnp_config.get_docker_script()
        self.PNP_SETUP_FILE_PATH = self.PNP_TMP_DIR + self.PNP_SETUP_FILE_NAME
        self.cmd = ""
        self.common_pnp_lib = CommonPnPLib(self)
        self._pnp_setup = self.do_pnp_setup_on_sut()
        self.pnp_base = self
        self.cpu_info = CpuInfoProvider.factory(self._log, cfg_opts, self.os)

    def get_pnp_workloads_directory(self):
        return self.PNP_WLS_DIR

    def sut_info(self):
        pass

    def get_pnp_scripts_git(self):
        """
        This function git pulls the pnp scripts or clone's it to the git lab updated scripts
        """
        self._log.info("Setting up PNP workloads Repository")
        self.cmd = "export http_proxy=http://proxy-{location}.intel.com:911 && export https_proxy=http://proxy-{" \
                   "location}.intel.com:912 && export ftp_proxy=http://proxy-{location}.intel.com:911 && export " \
                   "no_proxy=intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,.local,127.0.0.0/8," \
                   "134.134.0.0/16 && yum install git -y && git --version"

        self.cmd = self.cmd.replace("{location}", self.system_location)
        install_git = self.os.execute(self.cmd, self.command_timeout, "/root")
        regex = "git version *([0-9.]*)"
        match = re.findall(regex, install_git.stdout)
        if len(match) > 0:
            self._log.info("Git is installed in the SUT system")
        else:
            raise content_exceptions.TestFail("Git is not installed in the SUT system")

        cmd_output = self.os.execute("cd {} && git rev-parse --is-inside-work-tree".format(self.PNP_WLS_DIR),
                                     self.command_timeout, self.PNP_WLS_DIR)

        if "true" in cmd_output.stdout:
            self._log.info("PNP Workloads repository is present. Skipping Clone Repo.")
            cmd_output = self._common_content_lib.execute_sut_cmd("git checkout master && git pull origin master",
                                                                  "Git Pull Command",
                                                                  self.command_timeout, cmd_path=self.PNP_WLS_DIR)
            self._log.info(cmd_output)

        elif "no such file or directory" in cmd_output.stderr.lower():
            self._log.info("PNP Workloads repository is not present. Starting to Clone Repo.")
            self.os.execute("mkdir egs_pnp_automation", self.command_timeout, "/root")
            cmd_output = self._common_content_lib.execute_sut_cmd(
                "git clone https://{}:{}@github.com/intel-innersource/applications.validation.platforms.power-and-performance.server.base-workloads.git".format(self.git_username,
                                                                                                self.deploy_token),
                "git clone", self.command_timeout, cmd_path=PnpPath.AUTOMATION_DIR)
            self._log.info("PNP Workloads cloned to "+self.PNP_WLS_DIR)

        if not self.git_checkout(self.commit_file):
            raise content_exceptions.TestFail("Error during git checkout")

        if not self.os.check_if_path_exists(self.PNP_WLS_DIR, True):
            raise content_exceptions.TestFail("PNP workload repository is not cloned in the SUT system")

    def git_checkout(self, commit_id, branch="master"):
        """
        This function pulls the branch and checks out a particular commit in pnpwls repository

        Args:
            commit_id: git commit id
            branch: git branch

        Returns:
            True: If checkout was successful
            False: If checkout was unsuccessful
        """
        cmd_output = self._common_content_lib.execute_sut_cmd("git checkout "+ branch +" && git pull origin master",
                                                              "Git Pull Command",
                                                              self.command_timeout, cmd_path=self.PNP_WLS_DIR)
        self._log.info(cmd_output)

        cmd_output = self.os.execute("git checkout " + commit_id, 
                                                                self.command_timeout, cwd=self.PNP_WLS_DIR)

        if "error" in cmd_output.stderr or "fatal" in cmd_output.stderr:
            self._log.info("Failed to checkout commit ID: " + commit_id)
            return False

        self._log.info("Checkout commit ID: " + commit_id)
        return True

    def pnp_basic_setup(self):
        """
        This function executes the command for the basic setup of PnP system
        """
        run_basic_setup = self._common_content_lib.execute_sut_cmd(
            self.RUN_BASIC_SETUP.format(self.basic_setup_file, self.system_location),
            "Basic Setup", self.command_timeout,
            cmd_path=self.PNP_WLS_DIR + '/' + "setup")

        if "Basic pnp setup script completed succssfully" in run_basic_setup:
            self._log.info("Basic PnP setup script executed successfully")
        else:
            raise content_exceptions.TestFail("basic pnp setup script is throwing error")

    def pnp_install_docker(self):
        """
        This function executes the command for the basic setup of PnP system
        """
        run_install_docker = self._common_content_lib.execute_sut_cmd(
            self.RUN_INSTALL_DOCKER.format(self.install_docker_file),
            "Docker Installation", self.command_timeout,
            cmd_path=self.PNP_WLS_DIR + '/' + "setup")

        if "Seems like docker engine is already installed and running on this system" in run_install_docker or "Docker engine is now installed and running" in run_install_docker:
            self._log.info("Docker is installed in the SUT system")
        else:
            raise content_exceptions.TestFail("Docker is not installed in the SUT system")

    def delete_var_logs(self):
        """
        This function executes commands and delete var logs from SUT system.
        """
        cmd_output = self._common_content_lib.execute_sut_cmd("rm -rf {}* && ls {} | wc -l".format(self.VAR_LOGS_PATH, self.VAR_LOGS_PATH),
                                                              "delete & count no of files in {}".format(self.VAR_LOGS_PATH),
                                                              self.command_timeout, "/root")

        if int(cmd_output) == 0:
            self._log.info("Successfully deleted /var/logs/")
        else:
            raise content_exceptions.TestFail("Facing issue to delete the /var/logs")

    def set_flag_pnp_setup_done_on_sut(self):
        """
        Creates a file which indicates that PNP setup is done on SUT
        :return:
        """
        # os.check_if_path_exists
        cmd = "mkdir -p " + self.PNP_TMP_DIR
        self._common_content_lib.execute_sut_cmd_no_exception(cmd, cmd, self.command_timeout, ignore_result="Yes")
        cmd = "touch " + self.PNP_SETUP_FILE_PATH
        self._common_content_lib.execute_sut_cmd(cmd, cmd, self.command_timeout)

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
        cmd_output = int(self._common_content_lib.execute_sut_cmd(self.cmd, self.cmd, self.command_timeout))

        if cmd_output:
            return True

        return False

    def is_pnp_setup_done(self):
        """
        This function checks whether PNP Setup was already done in the SUT

        Returns:
            True : If PNP setup is already done on SUT
            False : If PNP setup is not done on SUT
        """
        if self.file_exists_on_sut(self.PNP_SETUP_FILE_PATH):
            self._log.info("PNP Setup is Done on SUT")
            return True
        
        self._log.info("PNP Setup is not Done on SUT")
        return False

    def do_pnp_setup_on_sut(self):  # type: () -> bool
        self.delete_var_logs()
        if not self.is_pnp_setup_done():
            self._log.info("Running PNP Setup")
            self.get_pnp_scripts_git()
            self.pnp_basic_setup()
            self.pnp_install_docker()
            self.set_flag_pnp_setup_done_on_sut()
            self._log.info("PNP Setup Complete")
        #handle errors for this and rename commit_file
        if not (self.git_checkout(self.commit_file)):
            return False
        return True

if __name__ == '__main__':
    print("This module does not have any tests to execute.")
    sys.exit(Framework.TEST_RESULT_FAIL)
