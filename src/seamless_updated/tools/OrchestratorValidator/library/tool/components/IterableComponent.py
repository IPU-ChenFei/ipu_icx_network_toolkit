#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
INTEL CONFIDENTIAL
Copyright 2020 Intel Corporation.
This software and the related documents are Intel copyrighted materials, and
your use of them is governed by the express license under which they were
provided to you (License).Unless the License provides otherwise, you may not
use, modify, copy, publish, distribute, disclose or transmit this software or
the related documents without Intel's prior written permission.

This software and the related documents are provided as is, with no express or
implied warranties, other than those that are expressly stated in the License.
"""

import re
import string
from copy import copy
from enum import Enum
from lxml.etree import SubElement #nosec

from .IComponent import IComponent
from ..Converter import Converter
from ..LibConfig import LibConfig
from ..dependencies.Dependency import Dependency
from ..LibException import ComponentException
from ..structures import Buffer


class IterableComponent(IComponent):
    entryTag = 'entry'
    entryLabel = 'Entry'
    iterableTag = 'iterable'
    indexTag = IComponent.ComponentProperty.Index.value

    class ComponentProperty(Enum):
        Size = "size"
        Data = "data"
        Indices = "indices"
        MaxSize = 'max_entry_count'
        ValuesArray = "values_array"

    maxSizeTag = ComponentProperty.MaxSize.value

    def __init__(self, xml_node, **kwargs):
        self.default_element = None
        self.defaultEntriesList = []
        self._data = None
        self.max_size = None
        self.children_by_index = {}
        self.starting_indices = set()
        self.starting_entries = set()
        super().__init__(xml_node, **kwargs)

    def _parse_additional_attributes(self, xml_node):
        max_size_formula = self._parse_attribute(xml_node, self.maxSizeTag, False, None)
        if max_size_formula is not None:
            self.max_size = self.calculate_value(max_size_formula)

    def build_layout(self, buffer, clear_build_settings: bool = False):
        raise ComponentException('Trying to build GUI only element', self.name)

    def build(self, buffer):
        raise ComponentException('Trying to build GUI only element', self.name)

    @property
    def indices(self):
        return sorted(self.children_by_index.keys())

    @property
    def data(self):
        self._load_data()
        return self._data

    @property
    def entries_count(self):
        return len(self.children)

    def _load_data(self):
        buffer = Buffer(-1, 100000)
        for entry in self.children:
            entry.build_layout(buffer)
        buffer.flush()
        for entry in self.children:
            entry.build(buffer)
        self._data = buffer[0:buffer.tell()]
        buffer.flush()

    def _get_property(self, component_property, _=False):
        if component_property == self.ComponentProperty.Data:
            return self.data
        if component_property == self.ComponentProperty.Size:
            return self.entries_count
        if component_property == self.ComponentProperty.Indices:
            return self.indices
        if component_property == self.ComponentProperty.MaxSize:
            return self.max_size
        if component_property == self.ComponentProperty.ValuesArray:
            return [[ch.value for ch in child.children] for child in self.children]

    def _copy_to(self, dst):
        super()._copy_to(dst)
        dst.children = self.children
        dst.children_by_name = self.children_by_name

    def _set_indexless_children(self, children: [IComponent]):
        """After adding all children with index specified, remaining entries should fill unused indexes"""
        index = 0
        for child_node in children:
            index = self._get_free_index(index)
            child_node.attrib[self.indexTag] = str(index)
            self._parse_entry_node(child_node)
            index += 1

    def _set_starting_indices(self):
        """Saves list of indices. Should only be called once children from plugin are parsed and haven't been edited by user."""
        self.starting_indices = set(self.children_by_index.keys())

    def _set_starting_entries(self):
        """Saves list of entries. Should only be called once children from plugin are parsed and haven't been edited by user."""
        self.starting_entries = copy(self.children_by_name)

    def _parse_children(self, xml_node, **kwargs):
        self.children = []
        self.children_by_name = {}
        if self.dependency_formula and Dependency.Tags.getTag in self.dependency_formula:
            return
        try:
            self._parse_default_node(xml_node)
            if self._skip_calculates:
                return
            indexless_children: [IComponent] = []
            for child_node in xml_node:
                if child_node.tag == self.defaultTag:
                    continue
                if child_node.tag == self.entryTag:
                    if self.indexTag in child_node.attrib:
                        self._parse_entry_node(child_node)
                    else:
                        indexless_children.append(child_node)
                else:
                    raise ComponentException(
                        f'Iterable children must be either "{self.entryTag}" or "{self.defaultTag}" '
                        f'- {child_node.tag} provided')
            self._set_indexless_children(indexless_children)
            self._set_starting_indices()
            self._set_starting_entries()
        except ComponentException as ex:
            self.trace_exception(ex)

    def _get_free_index(self, start: int = 0):
        """Gets lowest free index equal or greater than 'start'."""
        while not self.max_size or start < self.max_size:
            if start not in self.children_by_index:
                return start
            start += 1
        raise ComponentException(f'Number of entries exceeds max_size')

    def _parse_default_node(self, xml_node):
        defaults = xml_node.findall(self.defaultTag)
        if len(defaults) == 0:
            raise ComponentException(f'No default definition for {self.name} iterable', self.name)
        if len(defaults) > 1:
            raise ComponentException(f'There is more than one default definition for {self.name} iterable', self.name)
        default_node = defaults[0]
        self._fill_default_structure(default_node)
        self.default_element = self.componentFactory.create_component(default_node)
        self.default_element.initialize_defaults()

    def _parse_entry_node(self, child_node):
        index = child_node.attrib[self.indexTag]
        if index.isdigit():
            index = Converter.string_to_int(index)
            if index in self.children_by_index:
                raise ComponentException(f'Index with value {index} already used')
        else:
            raise ComponentException('Iterable entry index must be numeric value')
        if self.max_size and index >= self.max_size:
            raise ComponentException(f'Number of entries exceeds max_size {self.max_size}')
        if self.nameTag not in child_node.attrib:
            child_node.attrib[self.nameTag] = self.entryTag
            if self.labelTag not in child_node.attrib:
                child_node.attrib[self.labelTag] = f'{self.entryLabel}'
        self._validate_entry_structure(child_node, index)
        component = self.componentFactory.create_component(child_node, parent=self, index=index, iterable_descendant=True)
        self.children_by_index[index] = component

    def _get_child(self, child_name):
        if self.children_by_name is None:
            raise ComponentException("'{}' has no children".format(self.name), self.name)
        if child_name in self.children_by_name:
            return self.children_by_name[child_name]
        child_name_regex = re.search(rf'^{self.name}\[(\d+)\]$', child_name)
        index = int(child_name_regex.group(1)) if child_name_regex else None
        if index is not None and self.max_size is not None and index >= self.max_size:
            raise ComponentException(
                f'Trying to get configuration for non-existing index. Exceeded max_size: {index}', self.name)
        if index is not None and self.default_element:
            return self._add_entry_from_default(index)
        raise ComponentException(
            f"No '{child_name}' child. Choose one of: {', '.join(self.children_by_name.keys())}", self.name)

    def to_xml_node(self, parent, simple_xml: bool, create_groups: bool = False):
        if not self.is_setting_saveable or (self.xml_save_formula and not self.calculate_value(self.xml_save_formula)):
            return
        for index in sorted(self.starting_indices.union(self.children_by_index.keys())):
            entry = self.children_by_index.get(index, None)
            if entry is None:
                SubElement(parent, 'setting', {self.nameTag: f'{self.name}[{index}]:remove', self.valueTag: 'true'})
            else:
                entry_replaced = entry.from_default and index in self.starting_indices
                if entry_replaced:
                    SubElement(parent, 'setting', {self.nameTag: f'{entry.name}:replace', self.valueTag: 'true'})
                entry_added = entry.from_default and index not in self.starting_indices
                if not LibConfig.isFullDecomposition and (not simple_xml or (simple_xml and (entry_replaced or entry_added))):
                    SubElement(parent, 'setting', {self.nameTag: f'{entry.name}:label', self.valueTag: entry.label})
                setting_childes = [child for child in entry.descendants if child.node_tag != self.groupTag]
                for child in setting_childes:
                    if simple_xml and not child.has_non_defaults:
                        continue
                    child.to_xml_node(parent, simple_xml, create_groups)

    def _fill_default_structure(self, default_node):
        self.defaultEntriesList = []
        for node in default_node.iter():
            if node.tag == self.groupTag or node.tag == self.defaultTag:
                continue
            setting_name = self.get_name(node)
            # names generated can have additional number at the end which can vary between entries
            setting_name = setting_name.rstrip(string.digits)
            self.defaultEntriesList.append(setting_name)

    def _validate_entry_structure(self, entry_node, index):
        node_settings = [self.get_name(setting).rstrip(string.digits) for setting in entry_node.iter()
                         if setting.tag != self.groupTag and setting.tag != self.entryTag]
        if len(node_settings) != len(self.defaultEntriesList):
            raise ComponentException(f"Number of settings in {index} entry doesn't match number of default entries'",
                                     self.name)
        for mandatory_default_name in self.defaultEntriesList:
            if mandatory_default_name not in node_settings:
                raise ComponentException(f"Mandatory setting name: {mandatory_default_name} missing in"
                                         f" {index} entry of {self.name} iterable")
        return

    def make_component_iterable_descendant(self, component: IComponent, index: int):
        component.iterable_descendant = True
        component.iterable_root = self
        if not component.parent:
            component.parent = self
        component.iterable_index = index
        component.original_name = component.name
        if component.parent == self:
            component.name = f'{self.name}[{index}]'
        else:
            component.name = f'{self.name}[{index}].{component.original_name}'
        if hasattr(component, IComponent.childrenTag):
            for child in component.children:
                self.make_component_iterable_descendant(child, index)

    def _add_entry_from_default(self, index: int):
        entry = self.default_element.semideepcopy()
        entry.name = f'{self.entryTag}{index}'
        entry.label = f'{self.entryLabel}'
        entry.node_tag = self.entryTag
        if entry.map_name is None:
            entry.map_name = ""
        self.make_component_iterable_descendant(entry, index)
        self.children.append(entry)
        self.children_by_name[entry.name] = entry
        self.children_by_index[index] = entry
        return entry

    def add_new_entry(self):
        index = self._get_free_index()
        return self._add_entry_from_default(index)

    def remove_entry(self, index: int):
        try:
            element = self.children_by_index[index]
            self.remove_child(element.name)
            del self.children_by_index[index]
        except KeyError:
            raise ComponentException("Trying to remove non existing element")

    @property
    def has_non_defaults(self):
        if len(self.starting_entries) - len(self.children) != 0:
            return True
        if any(entry.from_default for entry in self.children):
            return True
        else:
            for entry in self.children:
                if any(entry_setting.has_non_defaults for entry_setting in entry.children):
                    return True

        return False

    def clear_children(self):
        self.children_by_index.clear()
        self.children_by_name.clear()
        self.children.clear()
