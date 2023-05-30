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
# otherwise. Any license under such intellectual property rights must be
# express and approved by Intel in writing.
###############################################################################
import os
import six
if six.PY2:
    import ConfigParser as config_parser
if six.PY3:
    import configparser as config_parser


class BiosMapper(object):
    """
    Maps the bios knobs across platforms using unique names
    """
    NOT_APPLICABLE = "NOT_APPLICABLE"

    def __init__(self, product_family):
        self._product_family = product_family
        cur_path = os.path.dirname(os.path.realpath(__file__))
        self._bios_mapper_cfg_path = os.path.join(cur_path, "bios_mapper.cfg")
        self._cp = config_parser.ConfigParser()
        self._cp.read(self._bios_mapper_cfg_path)

    def get_bios_knob_name(self, knob_name):
        """
        :param: knob_name - bios knob name

        :return: returns unique name if exists, unqiue_name if knob is not applicable, else same knob value
        """
        list_bios_knobs = self._cp.sections()
        for mapper_knob_name in list_bios_knobs:
            if knob_name == mapper_knob_name:
                if self._cp.has_option(knob_name, self._product_family):
                    unique_knob_name = self._cp.get(knob_name, self._product_family)
                    if not unique_knob_name:
                        # if not value exists, returns same knob_name
                        return knob_name
                    if self.NOT_APPLICABLE == unique_knob_name:
                        return self.NOT_APPLICABLE
                    return unique_knob_name

        # no entry exists, just return same knob_name
        return knob_name

