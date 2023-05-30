#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
INTEL CONFIDENTIAL
Copyright 2020-2021 Intel Corporation All Rights Reserved.

The source code contained or described herein and all documents related to the source code
("Material") are owned by Intel Corporation or its suppliers or licensors. Title to the Material remains
with Intel Corporation or its suppliers and licensors. The Material contains trade secrets and
proprietary and confidential information of Intel or its suppliers and licensors. The Material is
protected by worldwide copyright and trade secret laws and treaty provisions. No part of the
Material may be used, copied, reproduced, modified, published, uploaded, posted, transmitted,
distributed, or disclosed in any way without Intel's prior express written permission.

No license under any patent, copyright, trade secret or other intellectual property right is granted to
or conferred upon you by disclosure or delivery of the Materials, either expressly, by implication,
inducement, estoppel or otherwise. Any license under such intellectual property rights must be
express and approved by Intel in writing.
"""
import sys
import json
from posixpath import join as urljoin

import urllib3
import requests
from requests_ntlm import HttpNtlmAuth

from utils import serialize_description, deserialize_description, get_controller_ip, pprint_dict
from src.lib.tools_constants import SysUser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CommandCenterAPIClient:
    def __init__(self, cc_url):
        self.cc_url = cc_url
        self.auth = HttpNtlmAuth(SysUser.User, SysUser.PWD)
        self.proxies = {
                'http': 'http://proxy-chain.intel.com:911',
                'https': 'https://proxy-chain.intel.com:912',
                'ftp': 'http://proxy-chain.intel.com:911'
            }
        self.controller_ip = get_controller_ip()

    def api_get(self, method_url):
        try:
            full_url = urljoin(self.cc_url, method_url)
            print('Calling CommandCenter API [GET]: {}'.format(full_url))
            response = requests.get(url=full_url, auth=self.auth, verify=False, proxies=self.proxies)
            response.raise_for_status()
            return json.loads(response.text.encode('utf8'))
        except (Exception, requests.exceptions.HTTPError) as err:
            print(err)
            sys.exit(5)

    def api_patch(self, method_url, data=None):
        try:
            full_url = urljoin(self.cc_url, method_url)
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

            print('Calling CommandCenter API [PATCH]: {}'.format(full_url))
            response = requests.patch(url=full_url, auth=self.auth, verify=False,
                                      proxies=self.proxies, headers=headers, data=data)
            response.raise_for_status()
            return response.status_code
        except (Exception, requests.exceptions.HTTPError) as err:
            print(err)
            sys.exit(5)

    def get_description(self):
        test_setup = self.api_get(method_url='testSetups?controller={ip}'.format(ip=self.controller_ip))
        description = test_setup.get('Description')
        return deserialize_description(description)

    def update_description(self, provisioned_versions):
        update_required = False
        cc_versions = self.get_description()
        print('CommandCenter product versions: {}'.format(pprint_dict(cc_versions)))
        print('Provisioned product versions: {}'.format(pprint_dict(provisioned_versions)))

        for component, version in provisioned_versions.items():
            if component in cc_versions:
                if version != cc_versions[component]:
                    print('Component\'s {} version has been changed, '
                          'updating {} with {}'.format(component, cc_versions[component], version))
                    update_required = True
                    cc_versions[component] = version
                else:
                    print("Component\'s {} version has not been changed.".format(component))
            else:
                print("Component {} was added to description.".format(component))
                update_required = True
                cc_versions[component] = version

        if update_required:
            update_status = self.api_patch(method_url='testSetups?controller={ip}'.format(ip=self.controller_ip),
                                           data=serialize_description(cc_versions))
            if update_status == 200:
                print('Description updated successfully (return code: 200)')

    def remove_component(self, component):
        cc_versions = self.get_description()
        removed_component = cc_versions.pop(component, None)

        if removed_component:
            update_status = self.api_patch(method_url='testSetups?controller={ip}'.format(ip=self.controller_ip),
                                           data=serialize_description(cc_versions))
            if update_status == 200:
                print('Component {} removed successfully (return code: 200)'.format(component))
        else:
            print('Component {} was not found in CommandCenter description.'.format(component))
