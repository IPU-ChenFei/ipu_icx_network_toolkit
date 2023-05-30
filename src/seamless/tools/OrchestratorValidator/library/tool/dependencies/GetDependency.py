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
from ..LibException import ComponentException
from ..exceptions import InvalidAttributeException
from ..LibException import DependencyException
from .Dependency import Dependency


class GetDependency(Dependency):
    tag = Dependency.Tags.getTag

    def execute(self, gui_trigger=False):
        if self.setting_property is None:
            self.src_setting_ref.copy_to(self.dst_setting_ref)
        else:
            new_value = self.src_setting_ref.get_property(self.setting_property)
            old_value = None

            try:
                old_value = self.dst_setting_ref.get_property(self.target_property.name)
            except (InvalidAttributeException, ComponentException):
                pass

            bit_count = self.get_bit_count()
            self.source_name = self.src_setting_ref.name
            self.destination_name = self.dst_setting_ref.name

            if self.calculate is not None:
                new_value = self.src_setting_ref.expr_engine.calculate_value(self.calculate, None, True)

            if bit_count is not None:
                self.source_name += ' [{}:{}]'.format(self.bit_low, self.bit_high)
                mask = ((1 << bit_count) - 1) << self.bit_low
                new_value = (mask & new_value) >> self.bit_low
            if old_value != new_value:
                if self.is_value_dependency():
                    self.dst_setting_ref._set_value(new_value)
                elif self.target_property == self.Targets.value_list:
                    self.dst_setting_ref.params.dict[self.Targets.value_list.value] = new_value
                elif self.target_property == self.Targets.enabled:
                    self.dst_setting_ref.enabled = bool(new_value)
                    self.dst_setting_ref.enabled_formula = str(bool(new_value))
                elif self.target_property == self.Targets.visible:
                    self.dst_setting_ref.visible = bool(new_value)
                else:
                    if not hasattr(self.dst_setting_ref, self.target_property.name):
                        raise DependencyException(f"{self.target_property.name} attribute is not supported")
                    setattr(self.dst_setting_ref, self.target_property.name, new_value)
                return [self.dst_setting_ref]
        return []
