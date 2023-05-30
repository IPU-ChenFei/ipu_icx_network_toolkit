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
import src.lib.content_exceptions as content_exceptions

from src.lib.dtaf_content_constants import SandstoneTestConstants
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral


class StressStabilityCommon(ContentBaseTestCase):

    def __init__(self, test_log, arguments, cfg_opts):
        super(StressStabilityCommon, self).__init__(test_log, arguments, cfg_opts)

        self.sandstone_version_number = self._common_content_configuration.sandstone_version_number()
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def sandstone_pre_req(self):
        """
        Function to satisfy all the sandstone pre requisite.
        """
        self._common_content_lib.execute_sut_cmd(SandstoneTestConstants.PROXY_CHAIN, "Proxy chain",
                                                 self._command_timeout)
        self._log.info("Proxy has been set successfully.")
        self._common_content_lib.execute_sut_cmd(SandstoneTestConstants.DNF_UTILS, "dnf utils install",
                                                 self._command_timeout)
        self._log.info("DNF utils installed successfully.")
        self._common_content_lib.execute_sut_cmd(
            "dnf config-manager --add-repo={}".format(self.install_collateral.DOCKER_REPO), "add docker repo",
            self._command_timeout)
        self._log.info("Docker repo added successfully.")
        self._common_content_lib.execute_sut_cmd(SandstoneTestConstants.CONTAINERD_IO, "Docker container",
                                                 self._command_timeout)
        self._log.info("Docker installed successfully.")
        self._common_content_lib.execute_sut_cmd(SandstoneTestConstants.IPMI_TOOL, "IPMI Tool",
                                                 self._command_timeout)
        self._log.info("OpenIPMI tool installed successfully.")

        self.start_docker_service()

        self._common_content_lib.execute_sut_cmd(
            SandstoneTestConstants.PULL_SANDSTONE_REPO.format(self.sandstone_version_number), "pull sandstone repo",
            self._command_timeout)
        self._log.info("Sandstone repo pulled successfully.")

    def start_docker_service(self):
        """
        Function to start the docker.
        """
        self._common_content_lib.execute_sut_cmd(SandstoneTestConstants.STOP_FIREWALL_SUT, "Stop Firewall",
                                                 self._command_timeout)
        self._log.info("Firewall stopped successfully.")
        self._common_content_lib.execute_sut_cmd(SandstoneTestConstants.DAEMON_RELOAD, "Daemon Reload",
                                                 self._command_timeout)
        self._log.info("Deamon reload successful.")
        self._common_content_lib.execute_sut_cmd(SandstoneTestConstants.ENABLE_DOCKER, "Enable Docker",
                                                 self._command_timeout)
        self._log.info("Docker enabled successfully.")
        self._common_content_lib.execute_sut_cmd(SandstoneTestConstants.START_DOCKER, "Start Docker",
                                                 self._command_timeout)
        self._log.info("Docker started successfully.")

    def create_sandstone_log_dir_sut(self):
        """
        Function to create a sandstone log directory on sut on every new start of test
        """
        cmd_output = self.os.execute(r"rm -rf {}".format(SandstoneTestConstants.ROOT), self._command_timeout)
        if cmd_output.stderr == "":
            self._log.info("Removed the sandstone log directory if exist")
        else:
            log_err = "Failed to remove the sandstone log directory"
            self._log.error(log_err)
            raise content_exceptions.TestError(log_err)

        cmd_output = self.os.execute(r"mkdir -p {}".format(SandstoneTestConstants.ROOT), self._command_timeout)
        if cmd_output.stderr == "":
            self._log.info("Sandstone log directory is created {}".format(SandstoneTestConstants.ROOT))
        else:
            log_err = "Unable to create the sandstone log directory"
            self._log.error(log_err)
            raise content_exceptions.TestError(log_err)
