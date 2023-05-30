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
import re
import json
import socket
import xml.etree.ElementTree as ET
from fnmatch import fnmatch
from posixpath import join as urljoin
from src.lib.tools_constants import SysUser
import requests

# List of inline parameters which should be get from configuration files, example:
# CONFIG_PARAMS_MAP = {
#     'windows_installation': [
#         {'cfg_param': 'IPAddress', 'inline_param': 'dut_ip'},
#         {'cfg_param': 'CreationDate', 'inline_param': 'when_added'}
#     ]
# }

CONFIG_PARAMS_MAP = {
    'windows_installation': [],
    'linux_rhel_installation': [],
    'linux_fedora_installation': [],
    'linux_centos_installation': [],
    'esxi_installation': [],
    'ifwi_flashing': [],
    'bmc_banino_flashing': [],
    'bmc_redfish_flashing': [],
    'cpld_flashing': []
}

# Dictionaries helpers


def find_by_key(obj: dict, key: str) -> str:
    """ Get dictionary value by the given key. """
    if key in obj:
        return obj[key]
    for k, v in obj.items():
        if isinstance(v, dict):
            item = find_by_key(v, key)
            if item is not None:
                return item.get('string', item) if isinstance(item, dict) else item
        elif isinstance(v, list):
            for list_item in v:
                item = find_by_key(list_item, key)
                if item is not None:
                    return item


def pprint_dict(parameters: dict) -> str:
    """ Pretty print dictionary object. """
    return json.dumps(parameters, indent=4)


def get_config_params(task: str, parameters: dict) -> str:
    """ Get parameters from configuration files and append arguments to the tasks commandline. """
    cmd = []
    try:
        for parameter in CONFIG_PARAMS_MAP[task]:
            cfg_param = parameter.get('cfg_param')
            inline_param = parameter.get('inline_param')
            cmd.append('--{parameter} {value}'.format(parameter=inline_param.upper(),
                                                      value=find_by_key(parameters, cfg_param)))
    except KeyError:
        print('Undefined task: {} in CONFIG_PARAMS_MAP.'.format(task.upper()))
    return ' '.join(cmd)


def serialize(parameters: dict) -> str:
    """ Format dictionary entries as commandline arguments. """
    cmd = []
    for k, v in parameters.items():
        cmd.append('--{parameter} "{value}"'.format(parameter=k.upper(), value=v))
    return ' '.join(cmd)


def merge_dicts(dict1: dict, dict2: dict) -> None:
    """ Update dict1 with dict2 entries (default update method failed with nested keys). """
    for k in dict2:
        if k in dict1 and isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
            merge_dicts(dict1[k], dict2[k])
        else:
            dict1[k] = dict2[k]


# XML helpers


def get_manifest(input_parameters: dict) -> str:
    """ Get products manifest XML file with Artifactory data etc. """
    product_manifest_path = find_by_key(input_parameters, 'TestedComponentBuildsLocalPaths')

    if product_manifest_path:
        try:
            tree = ET.parse(product_manifest_path)
            root = tree.getroot()
        except FileNotFoundError:
            print('ERROR: Product\'s XML manifest file not found.')
            sys.exit(5)
    else:
        print('ERROR: Product\'s XML manifest path not found.')
        sys.exit(5)
    return root


def get_pkg(pkg_type: str, input_parameters: dict) -> str:
    """
    Get the OS or firmware package from XML manifest (SWPackage has specific XML tag attribute: SWpackage).
    Windows image has the type attribute: WIM.
    Handled pkg_type: win_os (Windows), os (other OSes, Linux), sft (software packages).
    """
    manifest = get_manifest(input_parameters)
    try:
        if pkg_type == 'win_os':
            return [image.attrib.get('artifactory') for image in manifest.iter('image')
                    if image.attrib.get('type') == 'wim' and image.attrib.get('tag') != 'SWpackage'][0]
        elif pkg_type == 'iso':
            return [image.attrib.get('artifactory') for image in manifest.iter('image')
                    if image.attrib.get('type') == 'iso' and image.attrib.get('tag') != 'SWpackage'][0]
        else:
            tag = ''
            if pkg_type == 'sft':
                tag = 'SWpackage'
            return [image.attrib.get('artifactory') for image in manifest.iter('image')
                    if image.attrib.get('tag') == tag][0]
    except IndexError:
        print('ERROR: Image package was not found in XML manifest.')
        sys.exit(5)


def get_project_pkg(project: str, input_parameters: dict) -> str:
    """ Get the flashing package from XML manifest. """
    manifest = get_manifest(input_parameters)
    try:
        pkg_path = [product.attrib.get('artifactory')
                    for product in manifest.findall("project[@name='{project}']".format(project=project))][0]
        pkg_archive = get_project_pkg_archive(pkg_path)
        return urljoin(pkg_path, pkg_archive)
    except IndexError:
        print('ERROR: Artifactory package path for {} was not found in XML manifest.'.format(project))
        sys.exit(5)


def get_project_pkg_archive(pkg_path: str) -> str:
    """ Find the flashing package in Artifactory (7z or zip). """
    url = '{}?list&deep=1&listFolders=1'.format(pkg_path.replace('/artifactory/', '/artifactory/api/storage/'))
    headers = {'X-JFrog-Art-Api': SysUser.ATF}
    proxies = {'http': 'http://proxy-ir.intel.com:912',
               'https': 'http://proxy-ir.intel.com:912',
               'ftp': 'http://proxy-ir.intel.com:912',
               'no_proxy': 'localhost,intel.com,10.0.0.0/8,10.64.0.0/10,100.64.0.0/12,100.80.0.0/16,10.244.0.0/16,10.96.0.0/12,10.45.128.26,10.45.128.27,10.45.128.28,10.45.128.10,10.45.128.41,10.45.128.42,10.45.128.43,10.45.128.44,10.45.128.45,10.45.128.46,10.45.128.8,10.45.128.4,10.45.128.34,10.45.128.40,10.45.128.101'}

    archives_list = []
    try:
        print('Calling Artifactory API (get firmware package): {}'.format(url))
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = json.loads(response.text.encode('utf8'))

        for package in result.get('files'):
            if any(fnmatch(package['uri'], pattern) for pattern in ['*.7z', '*.zip']):
                archives_list.append(package.get('uri').replace('/', ''))
    except (Exception, requests.exceptions.HTTPError) as err:
        print(err)
        sys.exit(5)

    if len(archives_list) == 0:
        print("ERROR: Firmware package (7z/zip) not found here: {}".format(pkg_path))
        sys.exit(5)
    elif len(archives_list) == 1:
        return archives_list[0]
    else:
        print("ERROR: More than one firmware package (7z/zip) found here: {}".format(pkg_path))
        sys.exit(5)


def get_mpc_data(mpc, product):
    try:
        component = mpc['Components'][product]
        remote_path = component['RemotePath']
        product_versions = {
            product: {
                'ver': component['BuildNumber'],
                'MainProduct': mpc['ProductComponent']
            }
        }
        return remote_path, product_versions
    except KeyError as e:
        print("ERROR: remote path or build number are missing "
              "in MultiProductComponentConfig XML (product: {}).".format(e))
        sys.exit(5)


def deserialize_description(description):
    parsed_description = {}
    setup_pattern = re.compile(r'(?P<component>\w+) v. (?P<component_version>[\w.-]+), '
                               r'MainProduct v. (?P<product_version>[\w.-]+)')

    for setup in description.split(';'):
        setup = setup.strip()
        if setup:
            description = setup_pattern.match(setup)
            component = description.group('component')
            component_version = description.group('component_version')
            product_version = description.group('product_version')

            parsed_description[component] = {
                'ver': component_version,
                'MainProduct': product_version
            }
    return parsed_description


def serialize_description(cc_versions):
    description = ''
    for component, version in cc_versions.items():
        description += '{component} v. {version}, MainProduct v. {product_version};\n'.format(
            component=component, version=version['ver'], product_version=version['MainProduct'])
    return json.dumps({'Description': description})


def get_controller_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def prepare_win_oneliner(config, provision_script):
    if config.mpc_config:
        product_location, product_version = get_mpc_data(config.mpc_config, 'WIM')
    else:
        product_location = get_pkg(pkg_type='win_os', input_parameters=config.input_parameters)
        product_version = None

    parameters = {'atf_path_os_pkg': product_location}
    oneliner = '{script} {inline_parameters}'.format(script=provision_script, inline_parameters=serialize(parameters))
    return oneliner, product_version


def prepare_fw_oneliner(config, provision_script, mpc_os_location, non_mpc_project, inline_param):
    if config.mpc_config:
        product_location, product_version = get_mpc_data(config.mpc_config, mpc_os_location)
    else:
        product_location = get_project_pkg(project=non_mpc_project, input_parameters=config.input_parameters)
        product_version = None
    parameters = {inline_param: product_location}
    oneliner = '{script} {inline_parameters}'.format(script=provision_script, inline_parameters=serialize(parameters))
    return oneliner, product_version


def prepare_os_oneliner_with_sft_pkg(config, provision_script, mpc_os_location, mpc_sft_location):
    if config.mpc_config:
        product_location, product_version = get_mpc_data(config.mpc_config, mpc_os_location)
        package_location, package_version = get_mpc_data(config.mpc_config, mpc_sft_location)
        merge_dicts(product_version, package_version)
    else:
        product_location = get_pkg(pkg_type='os', input_parameters=config.input_parameters)
        package_location = get_pkg(pkg_type='sft', input_parameters=config.input_parameters)
        product_version = None
    parameters = {'atf_path_os_pkg': product_location, 'atf_path_sft_pkg': package_location}
    oneliner = '{script} {inline_parameters}'.format(script=provision_script, inline_parameters=serialize(parameters))
    return oneliner, product_version


def prepare_cpld_fw_oneliner(config, provision_script):
    if config.mpc_config:
        product_location, product_version = get_mpc_data(config.mpc_config, 'PLDMain')
        package_location, package_version = get_mpc_data(config.mpc_config, 'PLDSecondary')
        merge_dicts(product_version, package_version)
    else:
        product_location = get_project_pkg(project='PLD_Main', input_parameters=config.input_parameters)
        package_location = get_project_pkg(project='PLD_Secondary', input_parameters=config.input_parameters)
        product_version = None
    parameters = {'atf_path_cpld_main_pkg': product_location, 'atf_path_cpld_secondary_pkg': package_location}
    oneliner = '{script} {inline_parameters}'.format(script=provision_script, inline_parameters=serialize(parameters))
    return oneliner, product_version


def prepare_os_iso_oneliner(config, provision_script, mpc_os_location):
    if config.mpc_config:
        product_location, product_version = get_mpc_data(config.mpc_config, mpc_os_location)
    else:
        product_location = get_pkg(pkg_type='iso', input_parameters=config.input_parameters)
        product_version = None

    parameters = {'atf_iso_path': product_location}
    oneliner = '{script} {inline_parameters}'.format(script=provision_script,
                                                     inline_parameters=serialize(parameters))
    return oneliner, product_version
