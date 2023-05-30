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
from enum import Enum

from .IComponent import IComponent
from ..LibException import LibException, ComponentException
from .. import utils as utils
from ..structures import RsaSigningKey, AsymmetricKeyType, SupportedSHAs, EcSigningKey
from ..utils import validate_file
from ..LibConfig import LibConfig


class AsymmetricKeyComponent(IComponent):
    hashTypeTag = "hash_type"
    shaPrefix = "sha"

    class ComponentProperty(Enum):
        Modulus = "modulus"
        Exponent = "exponent"
        HashedKey = "hashed_key"
        SignatureSize = "signature_size"
        TypeRsa = "type_rsa"
        Qx = "qx"
        Qy = "qy"
        CoordinateSize = "coordinate_size"
        Empty = "empty"
        Private = "is_private"

    class KeyType(Enum):
        Ec = 0
        Rsa = 1

    hash_type = None

    def __init__(self, xml_node, **kwargs):
        super().__init__(xml_node, **kwargs)
        self._key = None

    @property
    def key(self):
        if self._key is None:
            self._reload_key()
        return self._key

    @property
    def is_private(self):
        return self.key.key_type == AsymmetricKeyType.Private

    @property
    def key_type(self):
        return self.KeyType.Ec if isinstance(self.key, EcSigningKey) else self.KeyType.Rsa

    def _parse_string_value(self, value):
        self._set_value(value)
        self._key = None  # lazy reloading
        return self.value

    def _reload_key(self):
        validate_file(self.value)
        try:
            self._key = utils.process_key_file(self.value, self.hash_type, True)
        except LibException as e:
            raise ComponentException(f"Could not parse key: {self.value}\n" + str(e), self.name)

        if LibConfig.isVerbose:
            print(self.name)
            utils.hashed_key_printer(self._key, None)
            print("")

    def _parse_additional_attributes(self, xml_node):
        super()._parse_additional_attributes(xml_node)
        self._parse_hash_type(xml_node)

    def _parse_hash_type(self, xml_node):
        if self.hashTypeTag in xml_node.attrib:
            hash_name: str = xml_node.attrib[self.hashTypeTag]
            if not hash_name.startswith(self.shaPrefix):
                hash_name = self.shaPrefix + hash_name
            self.hash_type = SupportedSHAs.get_sha_type(hash_name)
        else:
            self.hash_type = SupportedSHAs.ShaType.Sha256

    def _get_property(self, component_property, _ = False):
        if component_property == self.ComponentProperty.Empty:
            if not self.value:
                return True
            return False
        self._check_error()
        if component_property == self.ComponentProperty.Modulus:
            return self.key.modulus
        if component_property == self.ComponentProperty.Exponent:
            return self.key.public_exponent
        if component_property == self.ComponentProperty.HashedKey:
            return self.key.hashed_key
        if component_property == self.ComponentProperty.SignatureSize:
            if isinstance(self.key, RsaSigningKey):
                return len(self.key.modulus)
            if isinstance(self.key, EcSigningKey):
                return len(self.key.qx) + len(self.key.qy)
            raise ComponentException("Unsupported key type", self.name)
        if component_property == self.ComponentProperty.TypeRsa:
            return isinstance(self.key, RsaSigningKey)
        if component_property == self.ComponentProperty.Qx:
            return self.key.qx
        if component_property == self.ComponentProperty.Qy:
            return self.key.qy
        if component_property == self.ComponentProperty.CoordinateSize:
            return self.key.coordinate_size
        if component_property == self.ComponentProperty.Private:
            return self.key.key_type == AsymmetricKeyType.Private

    def sign(self, computed_hash, padding_algorithm, hash_algorithm, reverse):
        return self.key.sign(computed_hash, padding_algorithm, hash_algorithm, reverse)

    def verify(self, signature, computed_hash, padding_algorithm, hash_algorithm):
        return self.key.verify(bytes(signature), computed_hash, padding_algorithm, hash_algorithm)

    def encrypt(self, _, __):
        raise LibException("Encryption with RSA key is not supported")

    def _copy_to(self, dst):
        super()._copy_to(dst)
        dst._key = self._key
        dst.hash_type = self.hash_type
