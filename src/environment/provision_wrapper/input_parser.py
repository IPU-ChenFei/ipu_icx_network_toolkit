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
import os
import sys
import fnmatch
import json
import xml.etree.ElementTree as ET
import xmltodict

from utils import find_by_key, merge_dicts

# The list of configuration files which should not be parsed, ex. to avoid overriding (asterisks are supported).
CONFIGS_BLACKLIST = []


class Config:
    """
    Superclass that represents configuration file from input (XML or JSON).
    """
    parameters = {}

    def __init__(self, config_file):
        self.config_file = config_file

    @property
    def _is_config_allowed(self) -> bool:
        for config in CONFIGS_BLACKLIST:
            if fnmatch.fnmatch(os.path.basename(self.config_file), config):
                return False
        return True

    def parse(self) -> None:
        """ Dispatch input parameter class parser according to its type."""
        if not self._is_config_allowed:
            print('Skipping config: {}'.format(self.config_file))
            return

        _, filetype = os.path.splitext(self.config_file)
        if filetype == '.xml':
            config = XMLConfig(self.config_file)
            self.parameters = config.parse(node='anyType')
        elif filetype == '.json':
            config = JSONConfig(self.config_file)
            self.parameters = config.parse()


class XMLConfig(Config):
    """
    Subclass that represents XML configuration file.
    """
    def parse(self, node=None) -> str:
        msg = 'Parsing config: {}'.format(self.config_file)
        if node:
            msg += ' (node: {})'.format(node)
        print(msg)

        with open(self.config_file) as cfg:
            doc = xmltodict.parse(xml_input=cfg.read(), encoding='utf-8', xml_attribs=False)
        if node:
            return find_by_key(doc, node)
        return doc


class JSONConfig(Config):
    """
    Subclass that represents JSON configuration file.
    """
    def parse(self) -> dict:
        print('Parsing config: {}'.format(self.config_file))
        with open(self.config_file) as cfg:
            data = json.load(cfg)
        return data


class InputFilesParser:
    """
    Creates the union of all configuration files as a dictionary.
    Overrides oldest key value if exists.
    """

    files_separator = ';'
    input_parameters = {}

    def __init__(self, config_files: str) -> None:
        self.config_files = config_files

        print("===== Running configuration files parser =====")
        mpc_config_files = set()
        for config_file in self.config_files.split(self.files_separator):
            if os.path.basename(config_file).startswith('MultiProductComponentConfig'):
                mpc_config_files.add(config_file)

            config = Config(config_file)
            config.parse()
            merge_dicts(self.input_parameters, config.parameters)

        # Prepare MultiProductComponentConfig map with Artifactory links to packages
        mpc_files = len(mpc_config_files)
        if not mpc_files:
            print("MultiProductComponentConfig XML was not found.")
            self.mpc_config = {}
        elif mpc_files == 1:
            mpc_file = mpc_config_files.pop()
            print("MultiProductComponentConfig XML found: {}".format(os.path.basename(mpc_file)))
            self.mpc_config = self.create_mpc_dict(mpc_file)
        elif mpc_files > 1:
            print("ERROR: Found more than one ({}) MultiProductComponentConfig files.".format(mpc_files))
            sys.exit(5)

    @staticmethod
    def create_mpc_dict(mpc_config_path):
        mpc = {
            'ProductComponent': '',
            'Components': {}
        }

        try:
            tree = ET.parse(mpc_config_path)
            root = tree.getroot()
        except FileNotFoundError:
            print("ERROR: MultiProductComponentConfig XML file not found.")
            sys.exit(5)

        for component in root.findall('.//ComponentItem'):
            if component.find('IsMain').text == 'true':
                mpc['ProductComponent'] = component.find('BuildNumber').text
            else:
                mpc['Components'][component.find('Type').text] = {
                    'RemotePath': component.find('RemotePath').text,
                    'BuildNumber': component.find('BuildNumber').text
                }
        return mpc
