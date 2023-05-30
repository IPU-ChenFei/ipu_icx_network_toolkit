#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
INTEL CONFIDENTIAL
Copyright 2017-2020 Intel Corporation.
This software and the related documents are Intel copyrighted materials, and
your use of them is governed by the express license under which they were
provided to you (License).Unless the License provides otherwise, you may not
use, modify, copy, publish, distribute, disclose or transmit this software or
the related documents without Intel's prior written permission.

This software and the related documents are provided as is, with no express or
implied warranties, other than those that are expressly stated in the License.
"""


from ..Converter import Converter
from .ByteArrayComponent import ByteArrayComponent
from .IComponent import IComponent


class GroupComponent(ByteArrayComponent):

    def __init__(self, xml_node, **kwargs):
        super().__init__(xml_node, **kwargs)
        self.enabled_by_default = self.enabled

    def parse_string_value(self, value):
        old_val = self.enabled_formula
        new_enabled_value = bool(Converter.string_to_int(value))
        self.enabled = new_enabled_value
        self.enabled_formula = str(new_enabled_value)
        modified = [self] if old_val != self.enabled_formula else []
        if modified and not new_enabled_value:
            for subgroup in [child for child in self.children if child.node_tag == IComponent.groupTag and child.enabled_formula]:
                modified.extend(subgroup.parse_string_value(value))
        return modified

    def _should_omit_parsing(self, xml_node):
        super()._should_omit_parsing(xml_node)
        return False

    def _parse_additional_attributes(self, xml_node):
        super()._parse_additional_attributes(xml_node)
        self.settings_order = self._parse_attribute(xml_node, self.settingsOrderTag, False)
