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
from .IManifestFunction import IManifestFunction
from ...structures import ValueWrapper


class IOutputManifestsFunction(IManifestFunction):
    def __init__(self, xml_node, **kwargs):
        self.output: ValueWrapper = None
        super().__init__(xml_node, **kwargs)

    def _parse_children(self, xml_node, **kwargs):
        super()._parse_children(xml_node, **kwargs)
        output_node = self._parse_node(xml_node, self.Tags.Output)
        self.output = ValueWrapper(output_node, self)
