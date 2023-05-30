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
from ...Converter import Converter
from .IFunction import IFunction
from ...LibException import ComponentException


class UpdateValueFunction(IFunction):
    nodeTag = "node"
    newValueTag = "new_value"

    node_path = None
    new_value_path = None
    new_value = None

    def build(self, buffer):
        if not self._is_enabled():
            return

        node_to_update = self.calculate_value_from_path(self.node_path)
        cur_offset = buffer.tell()

        if self.new_value:
            node_to_update.parse_string_value(self.new_value)
            new_value = node_to_update.value
        if self.new_value_path:
            new_value = self.calculate_value(self.new_value_path, allow_calculate=True)
            node_to_update._set_value(new_value)

        node_to_update._write_bytes(node_to_update.get_bytes(), buffer, node_to_update.offset)
        buffer.seek(cur_offset)

        if node_to_update.parent:
            new_value = Converter.to_bytes(new_value, node_to_update.size, byte_order=node_to_update.byte_order)
            self.__class__._set_value_for_parent(node_to_update, node_to_update.parent, new_value)

    @staticmethod
    def _set_value_for_parent(node_to_update, parent, new_value):
        if parent.value and parent.offset is not None:
            offset_delta = node_to_update.offset - parent.offset
            parent_val = parent.value
            parent.value = parent_val[:offset_delta] + new_value + \
                           parent_val[offset_delta + node_to_update.size:]

        if parent.parent:
            UpdateValueFunction._set_value_for_parent(node_to_update, parent.parent, new_value)

    def _parse_children(self, xml_node, **kwargs):
        node = self._parse_node(xml_node, self.nodeTag)
        new_value = self._parse_node(xml_node, self.newValueTag)
        self.node_path = self._parse_attribute(node, self.calculateTag)
        self.new_value_path = None
        self.new_value = None

        if self.calculateTag in new_value.attrib:
            self.new_value_path = new_value.attrib[self.calculateTag]

        if self.valueTag in new_value.attrib:
            self.new_value = new_value.attrib[self.valueTag]

        if self.new_value is None and self.new_value_path is None:
            raise ComponentException("Could not find required attributes for '%s': %s or %s" %
                                     (self.newValueTag, self.calculateTag, self.valueTag), self.name)

    def _build_layout(self):
        pass
