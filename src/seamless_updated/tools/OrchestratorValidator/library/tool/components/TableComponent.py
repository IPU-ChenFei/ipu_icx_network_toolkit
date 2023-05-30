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
import copy

from .GroupComponent import GroupComponent
from .IComponent import IComponent
from ..LibException import ComponentException
from cffi.backend_ctypes import xrange


class TableComponent(IComponent):
    children_allowed = True
    countTag = "count"
    countPointerTag = "count_pointer"  # count_pointer helps with decomposition and isn't used in building
    sortTag = "sort"
    indicesTag = "indices"
    indices = None
    count_formula = None
    count_pointer_formula = None
    sort_value = None

    def __init__(self, xml_node, **kwargs):
        self.indices = []
        if self.countTag in xml_node.attrib:
            self.count_formula = xml_node.attrib[self.countTag]
        if self.countPointerTag in xml_node.attrib:
            self.count_pointer_formula = xml_node.attrib[self.countPointerTag]
        super().__init__(xml_node, **kwargs)
        if self.indicesTag in xml_node.attrib and not self._skip_calculates:
            self.parse_indices(xml_node.attrib[self.indicesTag])

    def validate(self):
        IComponent.validate(self)

        # Check if 'count' was specified
        if self.children_allowed and not self.count_formula:
            raise ComponentException("Use 'count' attribute to define table size.", self.name)

    def get_count(self):
        return self.calculate_value(self.count_formula, allow_calculate=True)

    def parse_indices(self, indices_formula):
        indices = self.calculate_value(indices_formula, allow_calculate=True)
        if type(indices) is not list:
            raise ComponentException(f"Indices attribute should be a list of indices, instead {indices} received",
                                     self.name)
        self.indices = [(index, None) for index in indices]
    
    def sort_indices(self, xml_node):
        for i in xrange(0, self.get_count()):
            sort_formula = xml_node.attrib[self.sortTag]
            if "{index}" in sort_formula:
                sort_formula = sort_formula.replace("{index}", str(i))
            if "{parent_index}" in sort_formula:
                sort_formula = sort_formula.replace("{parent_index}", str(self.get_table_index()))
            sort_value = self.calculate_value(sort_formula, allow_calculate=True)
            self.indices.append((i, sort_value))
        if self.indices:
            self.indices.sort(key=lambda x: x[1])

    def _parse_children(self, xml_node, **kwargs):
        self.children = []
        self.children_by_name = {}
        if self.sortTag in xml_node.attrib and not self._skip_calculates:
            self.sort_indices(xml_node)
        try:
            kwargs['parent'] = self
            for child_node in xml_node:
                if self._skip_calculates:
                    self.componentFactory.create_component(child_node, **kwargs)
                elif self.indices:
                    for indices in self.indices:
                        self.componentFactory.create_component(child_node, index=indices[0], **kwargs)
                else:
                    for i in xrange(self.get_count()):
                        self.componentFactory.create_component(child_node, index=i, **kwargs)

        except ComponentException as ex:
            self.trace_exception(ex)

    def _get_bytes(self):
        return self.value
