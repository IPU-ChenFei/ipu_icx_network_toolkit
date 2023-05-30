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
import platform
import shutil
import sys
from xml.etree import ElementTree

import six

from src.lib.common_content_lib import CommonContentLib

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

if six.PY2:
    import ConfigParser as config_parser
if six.PY3:
    import configparser as config_parser

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from src.lib.dtaf_content_constants import CommonConstants
from src.lib.content_configuration import ContentConfiguration
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools


class RhelYumRepoSet(BaseTestCase):
    """
    Install RHEL OS Yum repo
    """
    C_DRIVE_PATH = "C:\\"
    YUM_REPO_FILE_NAME = r"intel-yum-rhel.repo"
    REPOS_FOLDER_PATH_SUT = "/etc/yum.repos.d"
    ENABLE_YUM_REPO_COMMAND = "yum repolist all"
    ACTUAL_REPO_COUNT = 4
    PROXY_STR = "proxy={}".format(CommonConstants.HTTP_PROXY)
    YUM_CONF_FILE_PATH = "/etc/yum.conf"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new RhelYumRepoSet object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath

        super(RhelYumRepoSet, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        self._common_content_configuration = ContentConfiguration(self._log)
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._config_parser = config_parser.ConfigParser()
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self._os, self._common_content_lib, cfg_opts)

    @classmethod
    def add_arguments(cls, parser):
        super(RhelYumRepoSet, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def proxy_setup(self):
        """
        Function to add the proxy into yum.conf file
        """
        yum_conf_result = self._os.execute("cat {}".format(self.YUM_CONF_FILE_PATH), self._command_timeout)

        if yum_conf_result.cmd_failed():
            self._log.error("stderr of {}:\n{}".format(self.YUM_CONF_FILE_PATH, yum_conf_result.stderr))
            raise RuntimeError

        self._log.debug("stdout of {} proxy file :\n{}".format(self.YUM_CONF_FILE_PATH, yum_conf_result.stdout))

        if self.PROXY_STR not in yum_conf_result.stdout:
            sed_cmd = self._os.execute(r"sed -i.bak '$ a\{}' {}".format(self.PROXY_STR, self.YUM_CONF_FILE_PATH),
                                       self._command_timeout)
            if sed_cmd.cmd_failed():
                self._log.error("stderr of {}".format(sed_cmd.stderr))
                raise RuntimeError

            yum_conf_result = self._os.execute("cat {}".format(self.YUM_CONF_FILE_PATH), self._command_timeout)

            if yum_conf_result.cmd_failed():
                self._log.error("stderr of {}:\n{}".format(self.YUM_CONF_FILE_PATH, yum_conf_result.stderr))
                raise RuntimeError

            self._log.debug("stdout of {} after adding proxy ::\n{}".format(self.YUM_CONF_FILE_PATH,
                                                                            yum_conf_result.stdout))

        self._log.info("Added the proxy in {}".format(self.YUM_CONF_FILE_PATH))

    def get_yum_repo_config(self):
        """
        This function to get the content configuration xml file path and return content configuration xml file root.

        :return: return configuration xml file root .
        """

        repo_config_file_src_path = None
        tree = ElementTree.ElementTree()
        repo_config_file_path = Path(os.path.dirname(os.path.realpath(__file__))).parent.parent
        for root, dirs, files in os.walk(str(repo_config_file_path)):

            for name in files:
                if name.startswith("yum_repo_configuration") and name.endswith(".xml"):
                    repo_config_file_src_path = os.path.join(root, name)

        if os.path.isfile(repo_config_file_src_path):
            tree.parse(repo_config_file_src_path)
        else:
            err_log = "Repo Configuration file does not exists, please check.."
            self._log.error(err_log)
            raise IOError(err_log)

        root = tree.getroot()

        return root

    def create_yum_repo_file_rhel(self, os_version):
        """
        Function to create a yum repo file for RHEL OS.
        """
        repo_options = {'name': "name", 'baseurl': "baseurl", 'enabled': "enabled", 'sslverify': "sslverify",
                        'gpgcheck': "gpgcheck"}

        rhel_os_ver = "RHEL-" + os_version

        url_attrib_list = []
        url_text_list = []

        root = self.get_yum_repo_config()

        for x in root.iter('base_url'):
            url_attrib_list.append(x.attrib)
            url_text_list.append(x.text)

        self._log.info(url_attrib_list)
        self._log.info(url_text_list)

        for index, repo_url in enumerate(url_text_list):

            if "epel" in url_attrib_list[index]['name'].lower():
                rhel_os_ver = os_version.split(".")[0]

            rhel_section = "rhel" + os_version + "_" + url_attrib_list[index]['name']
            self._config_parser.add_section(rhel_section)

            self._config_parser.set(rhel_section, repo_options["name"],
                                    "Red Hat Enterprise Linux " + os_version + " " + url_attrib_list[index]['name'])
            self._config_parser.set(rhel_section, repo_options["baseurl"], repo_url.format(rhel_os_ver))
            self._config_parser.set(rhel_section, repo_options["enabled"], "1")
            self._config_parser.set(rhel_section, repo_options["sslverify"], "0")
            self._config_parser.set(rhel_section, repo_options["gpgcheck"], "0")

        path = Path(os.path.dirname(os.path.realpath(__file__)))
        repo_file_path = os.path.join(str(path), self.YUM_REPO_FILE_NAME)

        with open(repo_file_path, "w+") as cfg_file:
            self._config_parser.write(cfg_file)

        if not os.path.isfile(repo_file_path):
            raise RuntimeError("repo file not found under {}".format(path))

        return repo_file_path

    def enable_yum_repo_in_rhel(self, repo_file_name):
        """
        This method is to enable yum repo in rhel

        :param repo_file_name: Corresponding repo file name
        """

        self._log.info("Enabling yum repo in rhel")

        """
        From SUT side preparations starts from here 
        """

        self._log.info("Deleting old yum repo files in rhel if available..")

        ls_repo_res = self._os.execute(r"ls *.repo", self._command_timeout, self.REPOS_FOLDER_PATH_SUT)
        self._log.debug("stdout of ls *.repo is :\n{}".format(ls_repo_res.stdout))
        if ls_repo_res.cmd_failed():
            self._log.debug("stderr of ls *.repo is :\n{}".format(ls_repo_res.stderr))

        sut_repo_file_path = []
        if len(ls_repo_res.stdout.strip().split()) != 0:
            for log_file in ls_repo_res.stdout.strip().split():
                if ".repo" in log_file.lower():
                    sut_repo_file_path.append(Path(os.path.join(self.REPOS_FOLDER_PATH_SUT, log_file)).as_posix())

        if len(sut_repo_file_path) != 0:
            for repo in sut_repo_file_path:
                rmrf_repo_res = self._os.execute(r"rm -rf {}".
                                                 format(repo.strip().replace("(", r"\(").replace(")", "\)")),
                                                 self._command_timeout, self.REPOS_FOLDER_PATH_SUT)

                if rmrf_repo_res.return_code != 0:
                    raise RuntimeError("rmrf command execution failed with error "
                                       ": {}...".format(rmrf_repo_res.stderr))
                self._log.debug("Successfully deleted the old file '{}'".format(repo.strip()))
        else:
            self._log.info("No .repo file(s) present under {}, proceeding further..".format(self.REPOS_FOLDER_PATH_SUT))

        """
        From Host to SUT copy repo starts from here
        """

        # proxy settings
        self.proxy_setup()

        self._os.copy_local_file_to_sut(repo_file_name, self.REPOS_FOLDER_PATH_SUT)
        self._log.info("Copied '{}' file to SUT folder '{}' successfully".format(repo_file_name,
                                                                                 self.REPOS_FOLDER_PATH_SUT))
        self._log.info("Successfully copied the .repo file to rhel")

        self._log.info("Executing yum repo list to check whether repo has enabled ...")
        cmd_opt = self._os.execute(self.ENABLE_YUM_REPO_COMMAND, self._command_timeout)

        if cmd_opt.cmd_failed():
            raise RuntimeError("{} stderr:\n{}".format(self.ENABLE_YUM_REPO_COMMAND, cmd_opt.stderr))

        list_of_repos = cmd_opt.stdout.strip().split("\n")
        self._log.debug("List of repos :\n{}".format(cmd_opt.stdout))
        enabled_repo_count = 0
        not_enabled_repos = []
        for repo in list_of_repos:
            if 'enabled' in repo:
                self._log.info("{} successfully.".format(repo))
                enabled_repo_count = enabled_repo_count + 1
            else:
                not_enabled_repos.append(repo)

        if enabled_repo_count < self.ACTUAL_REPO_COUNT:
            raise RuntimeError("Failed to enable the below repos : \n {}".format(not_enabled_repos))

        self._log.info("Successfully enabled YUM repos")

        return True

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        pass

    def execute(self):
        if (self._os.is_alive() == True):
            self._log.info("Booted Os And Entered Into OS Successfully")
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.TEST_REPO]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            self._os.copy_local_file_to_sut(zip_file_path, self.REPOS_FOLDER_PATH_SUT+"/test.repo")
            ret = self._os.execute("ls /etc/yum.repos.d/", 10)
            if(str(ret.stdout.strip()).find("test.repo")!=-1):
                self._log.info("REPO Configuration Made for RHEL")
                return True
            else:
                self._log.error("REPO Configuration FAILED for RHEL")
                return False
        else:
            self._log.error("System Not Alive")

        # os_version_cmd = "cat /etc/os-release | grep 'CPE_NAME'"
        # os_version = self._common_content_lib.execute_sut_cmd(os_version_cmd, "get os version", self._command_timeout)

        # # Sample String --- 'CPE_NAME = "cpe:/o:redhat:enterprise_linux:8.2:GA"'

        # os_len = len(os_version.strip("\n").split(':')[-2::][0].split("."))

        # if os_len == 2:
        #     os_version = '.0-'.join(os_version.strip("\n").split(':')[-2::]).replace('"', "")

        # os_version = '-'.join(os_version.strip("\n").split(':')[-2::]).replace('"', "")

        # repo_path = self.create_yum_repo_file_rhel(os_version)

        # return self.enable_yum_repo_in_rhel(repo_path)

    def cleanup(self, return_status):
        """Test Cleanup"""
        # self._common_content_lib.store_os_logs(self.log_dir)
        # # copy logs to CC folder if provided
        # if self._cc_log_path:
        #     self._log.info("Command center log folder='{}'".format(self._cc_log_path))
        #     self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        # super(RhelYumRepoSet, self).cleanup(return_status)
        pass

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RhelYumRepoSet.main() else Framework.TEST_RESULT_FAIL)
