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

import os
import subprocess
import socket
import platform
from configobj import ConfigObj
from xml.etree.ElementTree import Element, tostring
import xmltodict

from dtaf_core.lib.dtaf_constants import Framework
import src.lib.content_exceptions as content_exceptions


class RedFishCommon(object):
    """
    This class implements common RedFish functions which can be used across all test cases.
    """
    _CURL_POST_OPTIONS = " -X POST -H \"Content-Type: application/json\" -d \""
    _CURL_POST_WITHOUT_BODY = " -X POST"
    _CURL_PATCH_OPTION = " -X PATCH -H \"Content-Type: application/json\" -d \""

    BMC_CFG_OPTS = 'suts/sut/silicon/bmc'
    BMC_CFG_NAME = "bmc"
    BMC_CRED = "credentials"
    BMC_IPV4 = "ipv4"
    BMC_USER = "@user"
    BMC_PWD = "@password"
    LOOP_COUNT = 5

    def __init__(self, test_log, cfg_opts):
        """
        Create an instance of RedFishCommon

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(RedFishCommon, self).__init__()
        self._log = test_log
        self._cfg_opts = cfg_opts

        self.bmc_ip = None
        self.bmc_debug_user = None
        self.bmc_password = None

        # populates bmp ip, user name and password
        try:
            if self.populate_bmc_details():
                self._log.info("BMC details populated from BMC config file.")
            elif self.populate_bmc_details_from_dtaf_config():
                self._log.info("BMC details populated from DTAF config file.")
            else:
                log_error = "Failed to populate the BMC config from either MIV config file " \
                            "or DTAF config file. Populate one of them and run test again."
                self._log.error(log_error)
                raise content_exceptions.TestSetupError(log_error)
        except Exception as ex:
            raise ex

        self._log.info("Found BMC IP: " + self.bmc_ip)
        self._base_url = " https://" + str(self.bmc_ip)
        self.curl_base_command = "curl -u {}:{} -k --insecure ".format(self.bmc_debug_user, self.bmc_password)

    def populate_bmc_details(self):
        host_name = socket.gethostname()
        config_file_name = host_name + ".cfg"
        exec_os = platform.system()
        miv_cfg_file_path = os.path.join(Framework.CFG_BASE[exec_os], config_file_name)
        if not os.path.exists(miv_cfg_file_path):
            log_error = "The MIV confilg file '{}' does not exists."
            self._log.error(log_error)
            return False
        try:
            cp = ConfigObj(miv_cfg_file_path)
            self.bmc_ip = cp["Section0"]["ipaddress"]
            self.bmc_debug_user = cp["Section0"]["username"]
            self.bmc_password = cp["Section0"]["password"]
            return True
        except Exception as ex:
            log_error = "The MIV config file '{}' configuration not correct. Please populate config correctly. " \
                        "Exception: '{}'".format(ex)
            self._log.error(log_error)
            return False

    def populate_bmc_details_from_dtaf_config(self):
        bmc_cfg_opts = self._cfg_opts.find(self.BMC_CFG_OPTS)
        if isinstance(bmc_cfg_opts, Element):
            cfg_dict = xmltodict.parse(tostring(bmc_cfg_opts))
            dict_bmc = dict(cfg_dict)
            self.bmc_ip = dict_bmc[self.BMC_CFG_NAME][self.BMC_IPV4]
            dict_bmc_cred = dict_bmc[self.BMC_CFG_NAME][self.BMC_CRED]
            self.bmc_debug_user = dict_bmc_cred[self.BMC_USER]
            self.bmc_password = dict_bmc_cred[self.BMC_PWD]
            return True
        else:
            log_error = "DTAF config file is not populated with BMC configuration."
            self._log.error(log_error)
            return False

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
        curl_command = self.curl_base_command + " -i " +  self._base_url + str(url_string) + self._CURL_PATCH_OPTION + \
                       str(request_body)
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
