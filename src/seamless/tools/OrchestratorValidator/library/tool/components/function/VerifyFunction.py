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

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend

from enum import Enum
from .SignFunction import SignFunction
from ...LibException import ComponentException, LibException
from ...structures import SupportedSHAs, SupportedPaddings
from ...Converter import Converter
from ..AsymmetricKeyComponent import AsymmetricKeyComponent

class VerifyFunction(SignFunction):
    hashTag = "hash"
    customKeyTag = "custom_key"
    signatureTag = "signature"
    isLegacy = True

    class KeyData(Enum):
        sizeTag = "size"
        exponentTag = "exponent"
        modulusTag = "modulus"

    hash_path = None
    hash = None
    key = None
    signature_to_verify = None

    def __init__(self, xml_node, **kwargs):
        self.data = { }
        super().__init__(xml_node, **kwargs)

    def _parse_children(self, xml_node, **kwargs):
        self.data[self.hashTag] = self._parse_component(xml_node, self.hashTag)
        self.data[self.signatureTag] = self._parse_component(xml_node, self.signatureTag)
        self._parse_key(xml_node)
        self.padding_scheme = None
        self._parse_padding_scheme_tag(xml_node)

    # unlike SignFunction, VerifyFunction supports two sources of the key: not only path to key but additionally
    # key embedded in binary. So depending on which tag is placed in xml, proper _parse_key_tag() logic is triggered
    def _parse_key(self, xml_node):
        custom_key_node = xml_node.find(self.customKeyTag)
        key_node = xml_node.find(self.keyTag)
        if custom_key_node is not None and key_node is not None:
            raise ComponentException(
                    f"Cannot provide both '{self.customKeyTag}' and '{self.keyTag}' for verify function")
        elif key_node is not None:
            self._parse_key_tag(xml_node)
        elif custom_key_node is not None:
            self._parse_custom_key_tag(custom_key_node)
        else:
            raise ComponentException(f"Either '{self.customKeyTag}' or '{self.keyTag}' node is required")

    def _parse_key_tag(self, xml_node):
        super()._parse_key_tag(xml_node)
        self.key = self.calculate_value(self.key_path, allow_calculate = True)
        self.size = self.key.get_property("signature_size")

    def _parse_custom_key_tag(self, custom_key_node):
        for e in self.KeyData:
            comp_data = self._parse_component(custom_key_node, e.value)
            self.data[e] = comp_data
        key_size = self.calculate_value_from_path(self.data[self.KeyData.sizeTag][self.valueTag])
        exponent = self.calculate_value_from_path(self.data[self.KeyData.exponentTag][self.valueTag])
        modulus = self.calculate_value_from_path(self.data[self.KeyData.modulusTag][self.valueTag])
        self._construct_rsa_key(key_size, exponent, modulus)
        self.size = self.key.key_size // 8
        self.salt_len = SupportedPaddings.maxSaltLen

    def _parse_component(self, key_node, tag):
        key_comp_node = key_node.find(tag)
        key_comp_data = {}
        if key_comp_node is None:
            self._raise_missing_child(tag)
        key_comp_data[self.valueTag] = key_comp_node.attrib[self.valueTag]
        if self.orderTag in key_comp_node.attrib:
            order_cont = key_comp_node.attrib[self.orderTag]
        else:
            order_cont = self.bigOrder
        key_comp_data[self.orderTag] = order_cont
        return key_comp_data

    def _build_layout(self):
        self._set_value(b'\0' * self.size)

    def _build(self, buffer):
        self.hash = self.calculate_value_from_path(self.data[self.hashTag][self.valueTag])
        self._parse_signature()

        for padding in [self.padding_scheme] if self.padding_scheme else SupportedPaddings.PaddingSchemeType:
            padding_args = SupportedPaddings.get_padding_args(self.salt_len, padding, self.hash.sha_type, self.isLegacy)
            padding_class = SupportedPaddings.get_padding_class(padding, self.isLegacy)
            padding = padding_class(*padding_args)
            if self._verify(padding, buffer):
                return
        raise ComponentException("Verification failure!", self.name)

    def _verify(self, padding_class, buffer=None):
        try:
            self.key.verify(bytes(self.signature),
                            self.hash.get_sha(buffer),
                            padding_class,
                            utils.Prehashed(SupportedSHAs.get_sha_class(self.hash.sha_type, self.isLegacy)))  # We allow to verify any sha
        except (LibException, InvalidSignature):
            return False
        print("Verification succeeded!")
        return True

    def _parse_signature(self):
        self.signature = self.calculate_value_from_path(self.data[self.signatureTag][self.valueTag])
        self.signature = bytearray(self.signature[:self.size])
        if self.data[self.signatureTag][self.orderTag] == self.littleOrder:
            self.signature.reverse()
        if isinstance(self.key, AsymmetricKeyComponent) and self.key.key_type == self.key.KeyType.Ec:
            ingredient_size = len(self.signature) // 2
            r = int.from_bytes(self.signature[:ingredient_size], self.byte_order)
            s = int.from_bytes(self.signature[ingredient_size:], self.byte_order)
            self.signature = utils.encode_dss_signature(r, s)

    def _construct_rsa_key(self, size, e, n):
        size = int.from_bytes(size, self.data[self.KeyData.sizeTag][self.orderTag]) // 8
        e = int.from_bytes(e, self.data[self.KeyData.exponentTag][self.orderTag])
        n = n[:size]
        n = int.from_bytes(n, self.data[self.KeyData.modulusTag][self.orderTag])
        try:
            key = rsa.RSAPublicNumbers(e, n)
            self.key = key.public_key(backend = default_backend())
        except ValueError as e:
            raise ComponentException("Cannot create RSA key from given data!", self.name)
