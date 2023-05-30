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
from ..exceptions import InvalidAttributeException
from .Dependency import Dependency
from ..LibException import DependencyException, ComponentException


class SetDependency(Dependency):
    tag = Dependency.Tags.setTag

    def _set_referenced_setting(self, referenced_setting_ref):
        self.dst_setting_ref = referenced_setting_ref
        self.src_setting_ref = self.owner_setting_ref

    def execute(self, gui_trigger=False):
        if self.setting_property is None or (self.setting_property != self.owner_setting_ref.valueTag and
                                             self.setting_property != self.Targets.enabled.value and
                                             self.setting_property != self.Targets.visible.value):
            raise DependencyException(f"'{self.tag}' dependency must reference "
                                      f"'{self.owner_setting_ref.ComponentProperty.Value.value}' or " 
                                      f"'{self.Targets.enabled.value}' or "
                                      f"'{self.Targets.visible.value}' "
                                      f"property", self)
        else:
            if self.setting_property == self.Targets.enabled.value and self.dst_setting_ref.component_type != 'GroupComponent':
                raise DependencyException(f"'{self.tag}' dependency with '{self.Targets.enabled.value}' property must reference GroupComponent", self)
            if not gui_trigger and self.src_setting_ref.is_default():
                return []
            new_value = self.src_setting_ref.value
            old_value = None
            try:
                old_value = self.dst_setting_ref.get_property(self.setting_property)
            except (InvalidAttributeException, ComponentException):
                pass
            bit_count = self.get_bit_count()
            self.source_name = self.src_setting_ref.name
            self.destination_name = self.dst_setting_ref.name

            if self.calculate is not None:
                new_value = self.src_setting_ref.expr_engine.calculate_value(self.calculate, None, True)

            if bit_count is not None:
                self.destination_name += ' [{}:{}]'.format(self.bit_low, self.bit_high)
                mask = ((1 << bit_count) - 1) << self.bit_low
                new_value = (~mask & old_value) | ((new_value << self.bit_low) & mask)

            if old_value != new_value:
                if old_value is not None:
                    if self.is_duplicate:
                        new_name = self.get_bits_name(self.src_setting_ref)
                        if new_name:
                            self.source_name = new_name
                        new_name = self.get_bits_name(self.dst_setting_ref)
                        if new_name:
                            self.destination_name = new_name
                if self.setting_property == self.Targets.enabled.value:
                    self.dst_setting_ref.parse_string_value(str(int(new_value)))
                elif self.setting_property == self.Targets.visible.value:
                    self.dst_setting_ref.visible = bool(new_value)
                else:
                    self.dst_setting_ref._set_value(new_value)
                return [self.dst_setting_ref]
        return []
