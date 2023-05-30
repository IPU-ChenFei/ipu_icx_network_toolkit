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
"""Provides an interface to interact with artifactory to install test collateral utilities

    Typical usage example:
        self.artifactory_tool = ArtifactoryTool(test_log, self.os)
        self.artifactory_tool.download_tool_to_sut(self.artifactory_tool.STRESSAPP_TOOL_LINUX, self.STRESS_DIR)
"""
import os
from logging import Logger

import requests
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.sdsi.lib.tools.sut_os_tool import SutOsTool

class ArtifactoryInstallError(RuntimeError):
    """Raise if a tool fails to install from artifactory."""

class ArtifactoryTool:
    """Class to install tools from artifactory."""
    ARTIFACTORY_URL = "https://ubit-artifactory-ba.intel.com/artifactory/list/dcg-dea-srvplat-local/{}"
    STRESSAPP_TOOL_LINUX = "Automation_Tools/SPR/Linux/stressapptest"

    def __init__(self, log: Logger, sut_os: SutOsProvider) -> None:
        """Initialize the artifactory tool.

        Args:
            log: logger to use for test logging.
            sut_os: OS provider used for test content to interact with SUT.
        """
        self._sut_os_tool = SutOsTool(log, sut_os)
        self._log = log

    def download_tool_to_host(self, tool_path: str) -> str:
        """Performs the artifactory tool download to the host.

        Args:
            tool_path: The artifactory tool path of the tool to download. This class contains constant paths for
                        usage. Ex: download_tool_to_host(ArtifactoryTool.STRESSAPP_TOOL_LINUX)

        Return:
            str: The host path of the installed tool.

        Raises:
            ArtifactoryInstallError: If the tool fails to download from artifactory.
        """
        tool_name = os.path.basename(tool_path)
        install_folder = 'C:\\Automation'
        host_tool_directory = os.path.join(install_folder, tool_path)

        self._log.info(f"Requesting {tool_name} tool from artifactory.")
        res = requests.get(self.ARTIFACTORY_URL.format(tool_path))
        if res.status_code != 200:
            error_msg = f'Failed to install tool from artifactory, response code: {res.status_code}'
            self._log.error(error_msg)
            raise ArtifactoryInstallError(error_msg)

        self._log.info(f"Installing {tool_name} tool from artifactory.")
        os.makedirs(os.path.join(install_folder, os.path.dirname(tool_path)), exist_ok=True)
        with open(host_tool_directory, 'wb') as tool_file:
            [tool_file.write(chunk) for chunk in res.iter_content(chunk_size=512)]
        return host_tool_directory

    def download_tool_to_sut(self, tool_path: str, sut_path: str) -> str:
        """Download the tools from artifactory to the given SUT path

        Args:
            tool_path: The artifactory tool path of the tool to download. This class contains constant paths for
                       usage. Ex: download_tool_to_sut(ArtifactoryTool.STRESSAPP_TOOL_LINUX, '/root')
            sut_path: The SUT path to install the requested tool.

        Return:
            str: The sut path of the installed tool.

        Raises:
            ArtifactoryInstallError: If the tool fails to download from artifactory.
        """
        host_tool_path = self.download_tool_to_host(tool_path)
        tool_name = os.path.basename(host_tool_path)
        sut_tool_path = sut_path + "/" + tool_name
        self._log.info(f"Copying {tool_name} tool from host to SUT.")
        self._sut_os_tool.copy_local_file_to_sut(host_tool_path, sut_path)
        self._sut_os_tool.execute_cmd(f"sudo chmod 777 {sut_tool_path}")
        self._log.info(f"Tool {tool_name} installed to {sut_tool_path}.")
        return sut_tool_path
