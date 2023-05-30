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

from ..ByteArrayComponent import ByteArrayComponent
from ...LibException import ComponentException, LibException
from ...exceptions import InvalidAttributeException
from ...structures import DataNode


class IFunction(ByteArrayComponent):
    inputTag = "input"
    dataTag = "data"

    input_data = []
    input_bytes = None
    decrypted = False

    def __init__(self, xml_node, **kwargs):
        super().__init__(xml_node, **kwargs)
        self.align_byte = self.AlignByte.Byte00

    def validate(self):
        pass

    def _parse_string_value(self, value):
        pass  # pragma: no cover

    def _parse_children(self, xml_node, **kwargs):
        input_node = xml_node.find(self.inputTag)

        if input_node is not None:
            self.input_data = self.parse_input_nodes(input_node)

    def parse_input_nodes(self, input_node):
        input_data = []
        for data_node in input_node.findall(self.dataTag):
            try:
                input_data.append(DataNode(data_node))
            except LibException as e:
                raise ComponentException("Failed to process input data: {}".format(e.args[0]),
                                         self.name)
        return input_data

    def parse_extra_node(self, xml_node, tag_name, value_tag=ByteArrayComponent.calculateTag):
        node = xml_node.find(tag_name)
        if node is not None:
            if value_tag not in node.attrib:
                raise ComponentException("'{}' node is missing '{}' attribute".
                                         format(tag_name, value_tag),
                                         self.name)
            return node.attrib[value_tag]

    def _build(self, buffer):
        self.get_input_bytes(buffer)

    def calculate_input_bytes(self, buffer, input_data):
        input_bytes = bytearray()
        raw_data = bytearray()
        for input_datum in input_data:
            if input_datum.value:
                value = self.calculate_value(formula=input_datum.value)
                if not isinstance(value, bytes) and not isinstance(value, bytearray):
                    raise ComponentException("Formula '{}' must return 'bytes' or 'bytearray', but returned '{}'"
                                             .format(input_datum.value, type(value).__name__), self.name)
                if input_datum.exclude_ranges:
                    value = self._mask_with_exclude_ranges(value, input_datum.exclude_ranges)
                if input_datum.start_index and input_datum.end_index:
                    start = self.calculate_value(formula=input_datum.start_index)
                    end = self.calculate_value(formula=input_datum.end_index)
                    value = value[start:end]
                input_bytes.extend(value)
            elif buffer is None:
                raise ComponentException(f"Buffer was not given - '{self.dataTag}' in '{self.inputTag}' must use "
                                         f"'{self.valueTag}' attribute", self.name)
            elif input_datum.path:
                input_component = self.calculate_value(formula=input_datum.path)
                if input_component.offset is not None:
                    input_component.build(buffer)
                input_component_bytes = input_component.get_bytes()
                if input_datum.exclude_ranges:
                    input_component_bytes = self._mask_with_exclude_ranges(input_component_bytes, input_datum.exclude_ranges)
                input_bytes.extend(input_component_bytes)
                if input_component.raw_data:
                    component_raw_data = input_component.raw_data
                    if input_datum.exclude_ranges:
                        component_raw_data = self._mask_with_exclude_ranges(component_raw_data, input_datum.exclude_ranges)
                    raw_data.extend(component_raw_data)
            else:
                start = self.calculate_value(formula=input_datum.start)
                end = self.calculate_value(formula=input_datum.end)
                buffer.seek(start)
                val = buffer.read(end - start)
                if input_datum.exclude_ranges:
                    val = self._mask_with_exclude_ranges(val, input_datum.exclude_ranges)
                input_bytes.extend(val)
                raw_data.extend(val)
        return input_bytes, raw_data

    def _mask_with_exclude_ranges(self, val, exclude_ranges_formula: [int, int]):
        exclude_ranges = self.calculate_value(formula=exclude_ranges_formula)
        IFunction.check_if_ranges_are_exclusive(exclude_ranges)
        val = bytearray(val)
        for start, end in exclude_ranges:
            if start > end:
                raise InvalidAttributeException(f'Exclude range limit cannot be smaller than its base. '
                                                f'Exclude base: "{start}", '
                                                f'exclude limit: "{end}"')
            if end > len(val):
                raise InvalidAttributeException(f'Exclude range limit cannot exceed data size. '
                                                f'Exclude limit: "{end}", '
                                                f'data size: "{len(val)}"')
            val[start:end] = [0xFF] * (end - start)
        return val

    @staticmethod
    def check_if_ranges_are_exclusive(range_tuples: []):
        if len(range_tuples) < 2:
            return
        sorted_ranges = sorted(range_tuples)
        lower_start, lower_end = sorted_ranges.pop()
        while len(sorted_ranges):
            higher_start, higher_end = lower_start, lower_end
            lower_start, lower_end = sorted_ranges .pop()
            if lower_end > higher_start:
                raise ComponentException(f"Exclude ranges are overlapping! {higher_start}:{higher_end} overlaps {lower_start}:{lower_end}")

    def get_input_bytes(self, buffer=None):
        if self.input_bytes is None or self.raw_data is None:
            self.input_bytes, self.raw_data = self.calculate_input_bytes(buffer, self.input_data)
        if self.decrypted and self.raw_data:
            return self.raw_data
        return self.input_bytes
