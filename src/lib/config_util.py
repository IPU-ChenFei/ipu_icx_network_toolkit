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

import six
if six.PY2:
    import ConfigParser
if six.PY3:
    import configparser as ConfigParser


class ConfigUtil(object):
    """
    Parses the config file and returns value from specified section and key.
    """

    def __init__(self, config_file):
        self._config_file = config_file

    def get_key_value(self, section, key):
        """
        Will fetch the key value from the specified configuration file.

        :param section: Section name in configuration file.
        :param key: option of configuration file.
        :return: str - value of the section options that was passed.
        """
        cp = ConfigParser.SafeConfigParser()
        cp.read(self._config_file)
        value = cp.get(section, key)
        return value
