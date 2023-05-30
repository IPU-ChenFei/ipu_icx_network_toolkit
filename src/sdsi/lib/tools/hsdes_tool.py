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
"""Provides an interface to interact with HSDES to fetch article information.

    Typical usage example:
        self.hsdes_tool = HSDESTool(self._log)
        self.artifactory_tool.download_tool_to_sut(self.artifactory_tool.STRESSAPP_TOOL_LINUX, self.STRESS_DIR)
        self._log.info(f"Article Title: {self.hsdes_tool.get_test_title(test_id)}")
        self._log.info(f"Family Affected: {self.hsdes_tool.get_test_family_affected(test_id)}")
        self._log.info(f"Domain Affected: {self.hsdes_tool.get_test_domain_affected(test_id)}")
        self._log.info(f"Article Collaborators: {self.hsdes_tool.get_test_collaborators(test_id)}")
"""
from logging import Logger

import requests
import urllib3
from requests_kerberos import HTTPKerberosAuth


class HSDESTool:
    """Class to interact with HSDES API"""
    ARTICLE_URL = 'https://hsdes-api.intel.com/rest/article/{}'
    HEADERS = {'Content-type': 'application/json'}
    PROXIES = {'http': 'child-prc.intel.com:913',
               'https': 'child-prc.intel.com:913'}

    def __init__(self, log: Logger) -> None:
        """Initialize the hsdes tool.

        Args:
            log: logger to use for test logging.
        """
        self._log = log
        self._article_cache = {}
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _get_article_data(self, test_id: int) -> dict:
        """Fetch the article data from HSDES. Info is cached for the session to reduce web requests.

        Args:
            test_id: The article ID of the article to fetch data from.
                     To view article data structure, visit: https://hsdes-api.intel.com/rest/doc/#/

        Return:
            dict: The article information dict from HSDES.
        """
        if test_id not in self._article_cache.keys():
            res = requests.get(self.ARTICLE_URL.format(test_id), verify=False, auth=HTTPKerberosAuth(),
                               headers=self.HEADERS, proxies=self.PROXIES)
            self._article_cache[test_id] = res.json()['data'][0]
        return self._article_cache[test_id]

    def get_test_title(self, test_id: int) -> str:
        """Fetch the article title from HSDES.

        Args:
            test_id: The article ID of the article to fetch title from.

        Return:
            str: The article title
        """
        return self._get_article_data(test_id)['title']

    def get_test_collaborators(self, test_id: int) -> str:
        """Fetch the article collaborators from HSDES.

        Args:
            test_id: The article ID of the article to fetch collaborators from.

        Return:
            str: The article collaborators
        """
        return self._get_article_data(test_id)['collaborators']

    def get_test_family_affected(self, test_id: int) -> str:
        """Fetch the article family_affected from HSDES.

        Args:
            test_id: The article ID of the article to fetch family_affected from.

        Return:
            str: The article family_affected
        """
        return self._get_article_data(test_id)['family_affected']

    def get_test_domain_affected(self, test_id: int) -> str:
        """Fetch the article domain_affected from HSDES.

        Args:
            test_id: The article ID of the article to fetch domain_affected from.

        Return:
            str: The article domain_affected
        """
        return self._get_article_data(test_id)['domain_affected']
