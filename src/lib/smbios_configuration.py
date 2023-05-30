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

from pathlib import Path
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from xml.etree import cElementTree as ElementTree
from src.lib.dmidecode_verification_lib import DmiDecodeVerificationLib


class XmlConfigAsList(list):
    """
    Class to create a list of dict elements
    """
    def __init__(self, element_list):
        super().__init__()
        for element in element_list:
            if element:
                # treat like dict
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlConfigAsDict(element))
                # treat like list
                elif element[0].tag == element[1].tag:
                    self.append(XmlConfigAsList(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)


class XmlConfigAsDict(dict):
    """
    Class to create a dict elements out of xml.
    """

    def __init__(self, parent_element):
        super().__init__()
        if parent_element.items():
            self.update(dict(parent_element.items()))
        for element in parent_element:
            if element:
                # like dict - we assume that if the first two tags in a series are different, then they are all
                # different.
                if len(element) == 1 or element[0].tag != element[1].tag:
                    temp_dict = XmlConfigAsDict(element)
                else:
                    # here, we put the list in dictionary; the key is the tag name the list elements all share in
                    # common, and the value is the list itself
                    temp_dict = {element[0].tag: XmlConfigAsList(element)}
                if element.items():
                    # if the tag has attributes, add those to the dict
                    temp_dict.update(dict(element.items()))
                self.update({element.tag: temp_dict})
            elif element.items():
                self.update({element.tag: dict(element.items())})
            else:
                # finally, if there are no child tags and no attributes, extract the text
                self.update({element.tag: element.text})


class SMBiosConfiguration(object):
    """
    Parses the smbios config file and returns a dictionary of smbios tables
    """
    def __init__(self, log, os_obj, dmidecode_path=None):
        self._log = log
        self._os = os_obj
        self._dmidecode_path = dmidecode_path

        self._dmidecode_verification_lib = DmiDecodeVerificationLib(self._log, self._os)
        self._dmidecode_verification_lib.copy_smbios_config_file_if_not_exist(self._dmidecode_path)

    def get_smbios_table_dict(self):
        """
        Function to fetch the attribute values from the xml configuration file.

        :return: Value of the attribute in string type.
        """
        exec_os = platform.system()
        try:
            cfg_file_default = Framework.CFG_BASE
        except KeyError:
            err_log = "Error - execution OS " + str(exec_os) + " not supported!"
            self._log.error(err_log)
            raise err_log

        # Get the Automation folder config file path based on OS.
        cfg_file_automation_path = cfg_file_default[exec_os] + "smbios_configuration.xml"

        # First check whether the config file exists in C:\Automation folder else files not exists
        if os.path.isfile(cfg_file_automation_path):
            tree = ElementTree.parse(cfg_file_automation_path)
        else:
            err_log = "SMBIOS Configuration file '{}' does not exists, please populate the file and " \
                      "run test again..".format(cfg_file_automation_path)
            self._log.error(err_log)
            raise IOError(err_log)

        root = tree.getroot()
        xml_dict = XmlConfigAsDict(parent_element=root)
        return xml_dict
