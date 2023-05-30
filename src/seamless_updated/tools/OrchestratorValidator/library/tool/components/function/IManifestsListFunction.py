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
from ...LibException import ComponentException

import os


class IManifestsListFunction(IManifestFunction):
    def __init__(self, xml_node, **kwargs):
        self.manifests_list_node: ValueWrapper = None
        super().__init__(xml_node, **kwargs)

    def _parse_children(self, xml_node, **kwargs):
        super()._parse_children(xml_node, **kwargs)
        manifests_list_node_node = self._parse_node(xml_node, self.Tags.ManifestsList)
        self.manifests_list_node = ValueWrapper(manifests_list_node_node, self)

    def _scan_manifests_list(self, load_manifest_data=True):
        for manifest_component in self.manifests_list_node.value.children:
            if manifest_component.name != 'manifest':
                raise ComponentException(f'Unexpected node found: "{manifest_component.name}" '
                                         f'in "{self.manifests_list_node.value.name}"', self.name)
            yield self._parse_manifest_from_list(manifest_component, load_manifest_data)

    def _parse_manifest_from_list(self, manifest_component, load_manifest_data=True):
        try:
            import_node = manifest_component[self.ManifestListTags.Import]
            export_node = manifest_component[self.ManifestListTags.Export]
            manifest = self.Manifest(
                manifest=bytes(),
                index=manifest_component[self.ManifestListTags.Id].value,
                binary_path=import_node[self.ManifestListTags.ManifestBinary].value,
                manifest_hash=export_node[self.ManifestListTags.ManifestHash].value,
                public_key_hash=export_node[self.ManifestListTags.PublicKeyHash].value,
                manifest_offset=export_node[self.ManifestListTags.ManifestOffset].value,
                post_pv=export_node[self.ManifestListTags.PostPv].value
            )
            if load_manifest_data:
                if not os.path.exists(manifest.binary_path):
                    raise ComponentException(f"Binary with manifest doesn't exist: {manifest.binary_path}")
                with open(manifest.binary_path, 'rb') as f:
                    manifest.manifest = f.read()
            return manifest
        except ComponentException as e:
            raise ComponentException(f"Couldn't parse manifest entry in xml: {e}", self.name)
