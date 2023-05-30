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
import os
from lxml.etree import SubElement  #nosec

from ...Converter import Converter
from ...LibException import ComponentException
from ...components.function.IFunction import IFunction
from ...structures import ValueWrapper, SupportedSHAs
from ...utils import calculate_hash


class IManifestFunction(IFunction):

    class Tags:
        MagicNumber = 'magic_number'
        MagicNumberOffset = 'magic_number_offset'
        ManifestSize = 'manifest_size'
        LoadDataNode = 'load_data_node'
        DecompositionNode = 'decomposition_node'
        Output = 'output'
        PostPv = 'post_pv'
        ManifestHashInput = 'manifest_hash_input'
        PublicKeyHashInput = 'public_key_hash_input'
        ManifestsList = 'manifests_list'
        Sha = 'sha'

    class ManifestListTags:
        Id = 'id'
        Import = 'import'
        ManifestBinary = 'manifest_binary'
        Export = 'export'
        ManifestHash = 'manifest_hash'
        PostPv = 'post_pv'
        PublicKeyHash = 'public_key_hash'
        ManifestOffset = 'manifest_offset'

    class Manifest:
        def __init__(self, manifest, index, binary_path, manifest_hash, public_key_hash, manifest_offset, post_pv,
                     sha_size=None):
            self.manifest = manifest
            self.index = index
            self.binary_path = binary_path
            self.manifest_hash = manifest_hash
            self.public_key_hash = public_key_hash
            self.manifest_offset = manifest_offset
            self.post_pv = post_pv
            self.sha_size = sha_size

        def to_xml_node(self, parent):
            manifest_node = SubElement(parent, 'manifest')
            SubElement(manifest_node, 'number', {'name': IManifestFunction.ManifestListTags.Id, 'value': str(self.index)})
            import_node = SubElement(manifest_node, IManifestFunction.ManifestListTags.Import)
            SubElement(import_node, 'file',
                       {'name': IManifestFunction.ManifestListTags.ManifestBinary, 'value': self.binary_path})
            export_node = SubElement(manifest_node, IManifestFunction.ManifestListTags.Export)
            SubElement(export_node, 'byte_array', {'name': IManifestFunction.ManifestListTags.ManifestHash,
                                                   'value': Converter.bytes_to_string(self.manifest_hash),
                                                   'size': str(self.sha_size)})
            SubElement(export_node, 'number', {'name': IManifestFunction.ManifestListTags.PostPv, 'value': str(self.post_pv)})
            SubElement(export_node, 'byte_array', {'name': IManifestFunction.ManifestListTags.PublicKeyHash,
                                                   'value': Converter.bytes_to_string(self.public_key_hash),
                                                   'size': str(self.sha_size)})
            SubElement(export_node, 'number',
                       {'name': IManifestFunction.ManifestListTags.ManifestOffset, 'value': hex(self.manifest_offset)})

    def __init__(self, xml_node, **kwargs):
        self.decomposition_node: ValueWrapper = None
        self.magic_number: ValueWrapper = None
        self.magic_number_offset: ValueWrapper = None
        self.manifest_size: ValueWrapper = None
        self.post_pv: ValueWrapper = None
        self.manifest_hash_input_data = None
        self.public_key_hash_input_data = None
        self.manifests = []
        self.sha = None
        super().__init__(xml_node, **kwargs)

    @property
    def sha_type(self):
        return SupportedSHAs.ShaType(self.sha.value)

    def _parse_children(self, xml_node, **kwargs):
        super()._parse_children(xml_node, **kwargs)
        decomposition_node_node = self._parse_node(xml_node, self.Tags.DecompositionNode)
        self.decomposition_node = ValueWrapper(decomposition_node_node, self)
        magic_number_node = self._parse_node(xml_node, self.Tags.MagicNumber)
        self.magic_number = ValueWrapper(magic_number_node, self)
        magic_number_offset_node = self._parse_node(xml_node, self.Tags.MagicNumberOffset)
        self.magic_number_offset = ValueWrapper(magic_number_offset_node, self, Converter.string_to_int)
        manifest_size_node = self._parse_node(xml_node, self.Tags.ManifestSize)
        self.manifest_size = ValueWrapper(manifest_size_node, self, Converter.string_to_int)
        post_pv_node = self._parse_node(xml_node, self.Tags.PostPv)
        self.post_pv = ValueWrapper(post_pv_node, self, Converter.string_to_int)
        manifest_hash_input_node = self._parse_node(xml_node, self.Tags.ManifestHashInput)
        self.manifest_hash_input_data = self.parse_input_nodes(manifest_hash_input_node)
        public_key_hash_input_node = self._parse_node(xml_node, self.Tags.PublicKeyHashInput)
        self.public_key_hash_input_data = self.parse_input_nodes(public_key_hash_input_node)
        sha_node = self._parse_node(xml_node, self.Tags.Sha)
        self.sha = ValueWrapper(sha_node, self)

    def _parse_basic_attributes(self, xml_node):
        super()._parse_basic_attributes(xml_node)
        self._parse_legacy_attribute(xml_node)

    def _build(self, buffer):
        super()._build(buffer)
        # Manifest functions expect that buffer contains data in which we search manifests.
        # So it needs buffer to be positioned in the beginning
        buffer.seek(0)

    def _move_buffer_to_end(self, buffer):
        buffer.seek(self.offset)

    def _find_manifests(self, buffer, manifests_output_path=None):
        magic_number_bytes = self.magic_number.value.encode('ascii')
        magic_number_position = buffer.find(magic_number_bytes)
        index = 0
        while magic_number_position > 0:
            manifest_offset = magic_number_position - self.magic_number_offset.value
            if manifest_offset < 0:
                raise ComponentException(f"Found manifest magic magic number at offset {magic_number_position} "
                                         f"which indicates manifest at offset {manifest_offset} - "
                                         f"offset cannot be negative", self.name)
            buffer.seek(manifest_offset)
            manifest = self._load_manifest(buffer)
            manifest_output_path = os.path.join(manifests_output_path, str(index) + '.bin') \
                if manifests_output_path is not None else None
            yield self.Manifest(manifest=manifest, index=index,
                                binary_path=manifest_output_path,
                                manifest_hash=self._get_manifest_hash(), public_key_hash=self._get_public_key_hash(),
                                manifest_offset=manifest_offset, post_pv=self.post_pv.recalculate(),
                                sha_size=self._get_sha_size())

            magic_number_position = buffer.find(magic_number_bytes, buffer.tell())
            index += 1

    def _load_manifest(self, buffer):
        decomposition_component = self.decomposition_node.value
        decomposition_component.update_from_buffer(buffer[buffer.tell():buffer.max_size])
        manifest = buffer.read(self.manifest_size.recalculate())
        return manifest

    def _get_manifest_hash(self):
        data, _ = self.calculate_input_bytes(buffer=None, input_data=self.manifest_hash_input_data)
        return calculate_hash(data, self.sha_type, self.is_legacy)

    def _get_public_key_hash(self):
        data, _ = self.calculate_input_bytes(buffer=None, input_data=self.public_key_hash_input_data)
        return calculate_hash(data, self.sha_type, self.is_legacy)

    def _get_sha_size(self):
        return SupportedSHAs.get_sha_class(self.sha_type, self.is_legacy).digest_size
