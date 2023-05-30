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

from .IComponent import IComponent
from ..LibException import ValueException, ComponentException, ValidateException
from ..Converter import Converter
from ..utils import to_hex, parse_json_str, get_item_from_structure, max_value, XmlAttrType, XmlAttr
from .IComponentParams import ComponentParams


class NumberComponent(IComponent):
    BitLowTag = "bit_low"
    BitHighTag = "bit_high"
    SignedTag = "signed"
    NullableTag = "nullable"

    def __init__(self, xml_node, **kwargs):
        super().__init__(xml_node, **kwargs)
        self.byte_order = self.littleOrder
        if self.params:
            if self.dependency_formula:
                dependency_dict = parse_json_str(self.dependency_formula)
                bit_low = get_item_from_structure(dependency_dict, self.BitLowTag)
                bit_high = get_item_from_structure(dependency_dict, self.BitHighTag)
                if bit_low is not None and bit_high is not None:
                    self.params.gen_value_min_max_from_bits(bit_low, bit_high)
                else:
                    self.params.gen_value_min_max(self.size, self.signed)
            else:
                self.params.gen_value_min_max(self.size, self.signed)
        if self.buffer is not None:
            try:
                self._set_value(int.from_bytes(self.value, self.littleOrder))
            except TypeError:
                raise ComponentException("Cannot convert '{}' value to int", self.value)
        self.default_value = self.value

    def validate(self):
        super().validate()
        if self.value is not None and self.children:
            raise ComponentException("Object with defined value shouldn't have any children", self.name)

        if self.value is None and self.value_formula is None and self.dependency_formula is None and not self.children and not self.nullable and not self.is_decomposition_node:
            raise ComponentException("Object has no value and no children", self.name)

    def display_func(self, val):
        if self.display_mode == 'dec':
            return str(val)
        if self.display_mode == 'hex':
            return to_hex(val, self.size)

    def _parse_additional_attributes(self, xml_node):
        super()._parse_additional_attributes(xml_node)
        signed = XmlAttr(name=self.SignedTag, is_required=False, default=False, attr_type=XmlAttrType.BOOL,
                         xml_node=xml_node)
        nullable = XmlAttr(name=self.NullableTag, is_required=False, default=False, attr_type=XmlAttrType.BOOL,
                           xml_node=xml_node)
        self.signed = signed.value
        self.nullable = nullable.value

    def _parse_string_value(self, value):
        if not value and self.nullable:
            self.value = None
            return
        if not value:
            raise ComponentException("Value cannot be empty", self.name)

        parsed_val = Converter.string_to_int(value)
        if not self.signed and parsed_val < 0:
            raise ValueException("Cannot set a negative value for a setting", parsed_val, self.name)

        if self.size is not None and parsed_val > max_value(self.size):
            raise ComponentException(
                "Value: " + value + " cannot be longer than the specified limit: " + self.display_func(max_value(self.size)),
                self.name)
        return parsed_val

    def _build_layout(self):
        if self.size is None:
            raise ComponentException("Size is not defined", self.name)

        super()._build_layout()

    def _get_bytes(self):
        if not isinstance(self.value, int):
            raise ComponentException("Invalid value for this type: '{}', should be int".format(str(type(self.value))),
                                     self.name)
        if self.size is None:
            raise ComponentException("Size is not defined but is required", self.name)
        return self.value.to_bytes(self.size, self.bigOrder, signed = self.signed)

    def _set_value(self, value):  # val: "str/int/bytearray/byte"
        int_value = value
        if isinstance(value, bytes) or isinstance(value, bytearray):
            int_value = int.from_bytes(value, self.byte_order)
        if isinstance(value, str):
            int_value = Converter.string_to_int(value)
        self._validate_min_max(int_value)
        super()._set_value(int_value)

    def _validate_min_max(self, value: int):
        if self.params and self.params.is_min_max_set():
            value_min = self.params.value_int(ComponentParams.ParamsAttr.ValueMin)
            value_max = self.params.value_int(ComponentParams.ParamsAttr.ValueMax)

            if value < value_min:
                raise ValidateException("Value is lower than the specified limit: " + self.display_func(value_min),
                                        value,
                                        min_max = value_min,
                                        component_name = self.name)
            if value > value_max:
                raise ValidateException("Value is higher than the specified limit: " + self.display_func(value_max),
                                        value,
                                        min_max = value_max,
                                        component_name = self.name)

    def get_val_string(self, val):
        if val is not None and val < 0:
            return str(val)
        if val is None and self.nullable:
            return ""
        return self.display_func(val)

