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

import struct
from distutils.version import LooseVersion

from .IComponent import IComponent
from ..LibException import ComponentException


class VersionComponent(IComponent):
    VER_SEPARATOR = '.'

    def __init__(self, xml_node, **kwargs):
        self.default_read_only_value = True
        super().__init__(xml_node, **kwargs)

    @staticmethod
    def _parse_string_value(value):
        ex = ComponentException("Invalid value for this type: '{}', should be string in version format no longer"
                                " than x.x.x.x and single version can't be greater than 65 535"
                                .format(str(type(value))))

        try:
            version = [int(x) for x in value.split(VersionComponent.VER_SEPARATOR)]
        except ValueError:
            raise ex

        if len(version) > 4 or any(x > 0xFFFF for x in version):
            raise ex

        if len(version) < 4:
            version += [0] * (4 - len(version))
        return struct.unpack("<Q", (struct.pack("<4H", version[0], version[1], version[2], version[3])))[0]

    def validate(self):
        super().validate()
        if self.value is not None and self.children:
            raise ComponentException("Object with defined value shouldn't have any children",
                                     self.name)

        if self.value is None and self.value_formula is None and self.dependency_formula is None and not self.children and not self.is_decomposition_node:
            raise ComponentException("Object has no value and no children", self.name)

    def get_val_string(self, value):
        if value is None:
            return None
        bytes_value = value.to_bytes(8, 'little')
        ver_parts = [str(val) for val in struct.unpack("4H", bytes_value)]
        return VersionComponent.VER_SEPARATOR.join(ver_parts)

    @property
    def comparison_value(self):
        return self.convert_string_value_for_comparison(self.get_value_string())

    @staticmethod
    def convert_string_value_for_comparison(value):
        """This method converts "1.2.3.4"-like string to object that can be properly compared with another one for
        being greater, lower or equal"""
        return LooseVersion(value)
