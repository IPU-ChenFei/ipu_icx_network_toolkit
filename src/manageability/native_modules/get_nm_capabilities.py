#!/usr/bin/env python
###############################################################################
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
###############################################################################

import os
import re


from montana.nativemodules import getnmcapabilities
from src.lib.common_content_lib import CommonContentLib


class GetNMCapabilities(object):
    """
    This Class is Used to get NM Capabilities.
    """
    _MIV_LOG_FILE = "MEpythonlog.csv"
    _DOMAIN = "numdomains"
    _REGEX_FOR_DOMAIN_ID = "Domain ID\s+:\s\d+"
    _REGEX_FOR_MAX_CONCURRENT_SETTINGS = "Max\sConcurrent\sSettings\s+:\s+\d+"
    _REGEX_FOR_MAX_PWR = "Max\s+:\s+\d+"
    _REGEX_FOR_MIN_PWR = "Min\s+:\s+\d+"
    _REGEX_FOR_MIN_CORRECTION_TIME = r"Min\sCorrection\sTime\s+:\s+\d+"
    _REGEX_FOR_MAX_CORRECTION_TIME = r"Max\sCorrection\sTime\s+:\s+\d+"
    _REGEX_FOR_MIN_STATS_PERIOD = r"Min\sStats\sPeriod\s+:\s+\d+"
    _REGEX_FOR_MAX_STATS_PERIOD = r"Max\sStats\sPeriod\s+:\s+\d+"
    _REGEX_FOR_DOMAIN_SCOPE = r"Domain\sScope\s+:\s+\d+"

    DOMAIN_ID = "Domain ID"
    MAX_CONCURRENT_SETTINGS = "Max Concurrent Settings"
    MAX_PWR = "Max"
    MIN_PWR = "Min"
    MIN_CORRECTION_TIME = "Min Correction Time"
    MAX_CORRECTION_TIME = "Max Correction Time"
    MIN_STATS_PERIOD = "Min Stats Period"
    MAX_STATS_PERIOD = "Max Stats Period"
    DOMAIN_SCOPE = "Domain Scope"

    def __init__(self, log, montana_log_path, os_obj):
        """
        Creates an Instance of GetNMCapabilities

        :param log: log_object
        :param montana_log_path: montana_log_file path available in log_dir of TC.
        :param os_obj: OS object for all OS related Operations.
        """
        self._log = log
        self.dtaf_montana_log_path = montana_log_path
        self._os = os_obj
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.miv_log_file = os.path.join(self.cwd, self._MIV_LOG_FILE)
        self.get_nm_obj = getnmcapabilities.getnmcapabilities()
        self._common_content_lib = CommonContentLib(self._log, self._os, None)
        self.nm_capabilities_list = []
        self._populate_nm_capabilities()

    def _populate_nm_capabilities(self):
        """
        This Method is Used to get the Device Details from Montana.
        """
        if os.path.isfile(self.miv_log_file):
            os.remove(self.miv_log_file)
        command = "python {} --{}".format(getnmcapabilities.__file__,self._DOMAIN)
        self._common_content_lib.execute_cmd_on_host(command, cwd=self.cwd)

        with open(self.miv_log_file, "r") as log_file:
            log_file_list = log_file.readlines()
            with open(self.dtaf_montana_log_path, "a") as montana_log:
                montana_log.write("".join(log_file_list))

            nm_data = "".join(log_file_list)
            domain_ids_list = re.findall(self._REGEX_FOR_DOMAIN_ID, nm_data)
            nm_domain_details_dict = {}
            for i in range(len(domain_ids_list)):
                each_domain_data = domain_ids_list[i].split(":")
                nm_domain_details_dict[each_domain_data[0].strip()] = each_domain_data[1].strip()

                max_pwr_list = re.findall(self._REGEX_FOR_MAX_PWR, nm_data)
                each_domain_data = max_pwr_list[i].split(":")
                nm_domain_details_dict[each_domain_data[0].strip()] = each_domain_data[1].strip()

                min_pwr_list = re.findall(self._REGEX_FOR_MIN_PWR, nm_data)
                each_domain_data = min_pwr_list[i].split(":")
                nm_domain_details_dict[each_domain_data[0].strip()] = each_domain_data[1].strip()

                domain_scope_list = re.findall(self._REGEX_FOR_DOMAIN_SCOPE, nm_data)
                each_domain_data = domain_scope_list[i].split(":")
                nm_domain_details_dict[each_domain_data[0].strip()] = each_domain_data[1].strip()

                max_concurrent_list = re.findall(self._REGEX_FOR_MAX_CONCURRENT_SETTINGS, nm_data)
                each_domain_data = max_concurrent_list[i].split(":")
                nm_domain_details_dict[each_domain_data[0].strip()] = each_domain_data[1].strip()

                max_correction_time_list = re.findall(self._REGEX_FOR_MAX_CORRECTION_TIME, nm_data)
                each_domain_data = max_correction_time_list[i].split(":")
                nm_domain_details_dict[each_domain_data[0].strip()] = each_domain_data[1].strip()

                min_correction_time_list = re.findall(self._REGEX_FOR_MIN_CORRECTION_TIME, nm_data)
                each_domain_data = min_correction_time_list[i].split(":")
                nm_domain_details_dict[each_domain_data[0].strip()] = each_domain_data[1].strip()

                max_stats_period_list = re.findall(self._REGEX_FOR_MAX_STATS_PERIOD, nm_data)
                each_domain_data = max_stats_period_list[i].split(":")
                nm_domain_details_dict[each_domain_data[0].strip()] = each_domain_data[1].strip()

                min_stats_period_list = re.findall(self._REGEX_FOR_MIN_STATS_PERIOD, nm_data)
                each_domain_data = min_stats_period_list[i].split(":")
                nm_domain_details_dict[each_domain_data[0].strip()] = each_domain_data[1].strip()

                self.nm_capabilities_list.append(nm_domain_details_dict)
                nm_domain_details_dict = {}

    def get_nm_capabilities_dict(self,domain_id):
        """
        This method returns NM Capabiltiies based on given Domain ID.

        :returns: dictionary
        """
        for each_dict in self.nm_capabilities_list:
            if each_dict[self.DOMAIN_ID]==str(domain_id):
                return each_dict

    def get_domain_scope(self,domain_id):
        """
        This method returns Domain scope for given domain id

        :return: domain scope value
        """
        return self.get_nm_capabilities_dict(domain_id)[self.DOMAIN_SCOPE]

    def get_max_power(self, domain_id):
        """
        This method returns Max Power for given domain id

        :return: domain scope value
        """
        return self.get_nm_capabilities_dict(domain_id)[self.MAX_PWR]

    def get_min_power(self, domain_id):
        """
        This method returns Min Power for given domain id

        :return: domain scope value
        """
        return self.get_nm_capabilities_dict(domain_id)[self.MIN_PWR]

    def get_max_concurrent_settings(self, domain_id):
        """
        This method returns max_concurrent_settings for given domain id

        :return: domain scope value
        """
        return self.get_nm_capabilities_dict(domain_id)[self.MAX_CONCURRENT_SETTINGS]

    def get_max_correction_time(self, domain_id):
        """
        This method returns max_correction_time for given domain id

        :return: domain scope value
        """
        return self.get_nm_capabilities_dict(domain_id)[self.MAX_CORRECTION_TIME]

    def get_min_correction_time(self, domain_id):
        """
        This method returns min_correction_time for given domain id

        :return: domain scope value
        """
        return self.get_nm_capabilities_dict(domain_id)[self.MIN_CORRECTION_TIME]

    def get_max_stats_period(self, domain_id):
        """
        This method returns max_stats_period for given domain id

        :return: domain scope value
        """
        return self.get_nm_capabilities_dict(domain_id)[self.MAX_STATS_PERIOD]

    def get_min_stats_period(self, domain_id):
        """
        This method returns min_stats_period for given domain id

        :return: domain scope value
        """
        return self.get_nm_capabilities_dict(domain_id)[self.MIN_STATS_PERIOD]
