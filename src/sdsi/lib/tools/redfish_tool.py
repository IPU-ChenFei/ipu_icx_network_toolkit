#!/usr/bin/env python
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and propri-
# etary and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be ex-
# press and approved by Intel in writing.
"""Tool which provides functionality to interact with redfish API.

    Typical usage example:
        redfish_tool = RedFishTool(self._log, self._config)

        power_control_url = "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"
        power_on_cmd = r"{\"ResetType\": \"On\"}"

        redfish_tool.curl_post(power_control_url, power_on_cmd)
"""
import subprocess

from src.sdsi.lib.tools.automation_config_tool import AutomationConfigTool


# TODO REFACTOR THIS CLASS, REALLY POOR IMPLEMENTATION + DOCUMENTATION. USE REQUEST LIBRARY INSTEAD OF CURL COMMANDS.
class RedFishTool:
    """
    This provides an interface to interact with the Redfish API.
    """
    _CURL_POST_OPTIONS = " -X POST -H \"Content-Type: application/json\" -d \""
    _CURL_POST_WITHOUT_BODY = " -X POST"
    _CURL_PATCH = " -X PATCH -H \"Content-Type: application/json\" -d \""
    BMC_CFG_OPTS = 'suts/sut/silicon/bmc'
    BMC_CFG_NAME = "bmc"
    BMC_CRED = "credentials"
    BMC_IPV4 = "ipv4"
    BMC_USER = "@user"
    BMC_PWD = "@password"
    LOOP_COUNT = 5

    def __init__(self, test_log, config):
        """
        Create an instance of RedFishCommon
        :param test_log: Log object
        :param config: Configuration Object of provider
        """
        super(RedFishTool, self).__init__()
        self._log = test_log
        self._config = config

        automation_config_tool = AutomationConfigTool(self._log)  # type: AutomationConfigTool
        self.bmc_ip = automation_config_tool.get_config_value("Section0", "ipaddress")
        self.bmc_user = automation_config_tool.get_config_value("Section0", "username")
        self.bmc_pass = automation_config_tool.get_config_value("Section0", "password")

        self._base_url = " https://" + str(self.bmc_ip)
        self.curl_base_command = "curl -u {}:{} -k --insecure ".format(self.bmc_user, self.bmc_pass)

    def curl_get(self, url_string):
        """
        This method executes the get requests of Redfish APIs using curl command and returns the Output string

        :returns: output json response from API.
        """
        curl_command = self.curl_base_command + self._base_url + str(url_string)
        self._log.info("Execute the curl command : {}".format(curl_command))

        for count in range(self.LOOP_COUNT):
            result = subprocess.run(curl_command, stdout=subprocess.PIPE)
            if result.returncode == 0:
                break

        if result.returncode != 0:
            log_error = "Curl command '{}' failed with return code : {}".format(curl_command, result.returncode)
            self._log.error(log_error)
            self._log.error("Curl command error log = '{}".format(result.stderr))
            raise RuntimeError(log_error)
        else:
            self._log.info("Curl command '{}' executed successfully...".format(curl_command))
            self._log.debug("---------curl command result start----------")
            self._log.debug(str(result.stdout.decode('utf-8').strip("\r\n")))
            self._log.debug("---------curl command result end------------")

        return result.stdout

    def curl_post(self, url_string, request_body=""):
        """
        This method executes post Redfish APIs using curl command and returns the Output string

        :returns: output json response from API.
        """
        if request_body:
            curl_command = self.curl_base_command + self._base_url + str(url_string) + self._CURL_POST_OPTIONS + \
                           str(request_body)
        else:
            curl_command = self.curl_base_command + self._base_url + str(url_string) + self._CURL_POST_WITHOUT_BODY

        self._log.info("Execute the curl command : {}".format(curl_command))

        for count in range(self.LOOP_COUNT):
            result = subprocess.run(curl_command, stdout=subprocess.PIPE)
            if result.returncode == 0:
                break

        if result.returncode != 0:
            log_error = "Curl command '{}' failed with return code : {}".format(curl_command, result.returncode)
            self._log.error(log_error)
            self._log.error("StdError='{}'".format(result.stderr))
            raise RuntimeError(log_error)
        else:
            self._log.info("The curl command '{}' executed successfully..".format(curl_command))
            self._log.info("Curl command result = " + str(result.stdout.decode('utf-8').strip("\r\n")))

        return result.stdout

    def curl_patch(self, url_string, request_body=""):
        """
        This method executes Patch Redfish APIs using curl command and returns the Output string

        :returns: output json response from API.
        """
        curl_command = self.curl_base_command + " -i " + self._base_url + url_string + self._CURL_PATCH + request_body
        self._log.info("Execute the curl command : {}".format(curl_command))

        for count in range(self.LOOP_COUNT):
            result = subprocess.run(curl_command, stdout=subprocess.PIPE)
            if result.returncode == 0:
                break

        if result.returncode != 0:
            log_error = "The curl command '{}' failed with return code : {}".format(curl_command, result.returncode)
            self._log.error(log_error)
            self._log.error("StdOut='{}'".format(result.stderr))
            raise RuntimeError(log_error)
        else:
            self._log.info("The curl command '{}' executed successfully.".format(curl_command))
            self._log.info("The Curl command result = " + str(result.stdout.decode('utf-8').strip("\r\n")))

        return result.stdout
