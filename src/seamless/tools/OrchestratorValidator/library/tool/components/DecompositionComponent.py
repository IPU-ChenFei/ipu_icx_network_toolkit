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

from mmap import ACCESS_READ

from ..ColorPrint import ColorPrint
from ..Converter import Converter
from .IComponent import IComponent
from ..LibException import ComponentException, LibException
from ..exceptions import WrongFileException, MissingFileException
from ..structures import Buffer
from ..utils import validate_file


class DecompositionComponent(IComponent):
    class Tags:
        file = 'file'
        outputSuffix = 'output_suffix'

    file_dep_path = None
    file_name = None
    output_suffix = None

    def __init__(self, xml_node, **kwargs):
        kwargs['is_decomposition_node'] = True
        self._init_properties(xml_node, kwargs)
        self._set_parent_child()
        self.decomposition_xml_node = xml_node  # this is used by ExportManifestFunction
        if self._skip_calculates:
            # Decomposition node should parse children and not load input file in case of full decomposition
            super().__init__(xml_node, **kwargs)
            self._parse_children(xml_node, **kwargs)
            return
        self.output_suffix = self._parse_attribute(xml_node, self.Tags.outputSuffix, False, None)
        self.file_dep_path = self._parse_attribute(xml_node, self.Tags.file, False, None)
        if self.file_dep_path is None:
            # If we don't specify file input for decomposition then we will use this node for other purposes
            # (e.g. decomposing some binary data that we get later)
            self.enabled = True
            super().__init__(xml_node, **kwargs)
            return
        self.file_name = self.calculate_value(self.file_dep_path, allow_calculate=True)
        if not isinstance(self.file_name, str):
            raise ComponentException(f"'{self.Tags.file} must resolve to a string value'")
        if not self.file_name:
            # if path is empty then we skip decomposition
            return
        try:
            validate_file(self.file_name)
        except LibException as ex:
            if self.is_gui:
                self.error_message = str(ex)
                return
            self.error_message = str(ex)
            raise ComponentException("Cannot open file: '{}' ".format(self.file_name))
        with open(self.file_name, "rb") as f:
            buffer = Buffer(f.fileno(), 0, access=ACCESS_READ)
            self._validate_file_size(xml_node, buffer)
            kwargs['buffer'] = buffer
            try:
                super().__init__(xml_node, **kwargs)
            except ComponentException as ex:
                path_split = self.file_dep_path.rsplit('.')[0]
                ColorPrint.debug(f"{ex}")
                raise WrongFileException(f"Incorrect file {self.file_name} in {path_split}", self.name)
            finally:
                buffer.close()

    def _validate_file_size(self, xml_node, buffer):
        declared_size = xml_node.attrib.get('size', None)

        if declared_size:
            size_limit = Converter.string_to_int(declared_size)
            file_size = buffer.max_size

            if size_limit != file_size:
                raise ComponentException(
                    f"Decomposition file size is not equal to expected size. Expected size is {size_limit} and "
                    f"{self.file_name} size is: {file_size}")

    def _get_child(self, child_name):
        if self.buffer is None and not self._skip_calculates:
            path_split = self.file_dep_path.rsplit('.')[0] if self.file_dep_path else ''
            raise MissingFileException(f'File for decomposition was not set in {path_split}', self.name)
        return super()._get_child(child_name)

    def _is_enabled(self):
        if self.enabled is None:
            return bool(self.file_name)
        return self.enabled

    def _copy_to(self, dst):
        raise ComponentException("Using in dependency expressions is not supported: " + self.name)

    def _parse_basic_attributes(self, xml_node):
        super()._parse_basic_attributes(xml_node)
        if self.buffer is not None:
            self.buffer.seek(0)
