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

import subprocess #nosec
import os

from enum import Enum
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import utils

from ...LibException import ComponentException
from .HashFunction import HashFunction
from ...structures import SupportedSHAs, SupportedPaddings, AsymmetricKeyType, RsaSigningKey, EcSigningKey
from ...Converter import Converter
from ...ColorPrint import ColorPrint


class SignFunction(HashFunction):
    keyTag = "key"
    paddingSchemeTag = "padding_scheme"
    paddingSaltLenAttrTag = "salt_len"
    signingUtilTag = "signing_utility"
    signingUtilTimeoutTag = "signing_utility_timeout"
    loadExternalDataTag = "load_external_data"
    externalDataTag = "external_data"
    offlineSigningTag = "offline_signing"
    eccPaddingTag = "ecc_padding"

    key_path = None
    key = None
    padding_scheme = SupportedPaddings.PaddingSchemeType.pkcs1_v1_5
    signing_script_path = None
    signing_script = None
    signing_script_timeout_formula = None
    signing_script_timeout = 60
    salt_len = SupportedPaddings.maxSaltLen
    load_external_data_formula = None
    load_external_data = False
    external_data_formula = None
    external_data = None
    offline_signing_formula = None
    offline_signing = False
    ecc_padding = None

    class ComponentProperty(Enum):
        HeaderVersion = "header_version"
        Value = "value"

    @HashFunction.size.getter
    def size(self):
        return self._size

    def _parse_children(self, xml_node, **kwargs):
        super()._parse_children(xml_node, **kwargs)
        self._parse_key_tag(xml_node)
        self._parse_padding_scheme_tag(xml_node)
        self._parse_signing_utility_tag(xml_node)
        self.load_external_data_formula = self.parse_extra_node(xml_node, self.loadExternalDataTag)
        self.external_data_formula = self.parse_extra_node(xml_node, self.externalDataTag)
        self.offline_signing_formula = self.parse_extra_node(xml_node, self.offlineSigningTag)
        ecc_padding_str = self.parse_extra_node(xml_node, self.eccPaddingTag, self.valueTag)
        if ecc_padding_str:
            self.ecc_padding = Converter.string_to_int(ecc_padding_str)

    def _parse_key_tag(self, xml_node):
        key_node = self._parse_node(xml_node, self.keyTag)

        if self.valueTag not in key_node.attrib:
            raise ComponentException("Missing value for tag: '{}'".format(self.keyTag), self.name)

        self.key_path = key_node.attrib[self.valueTag]

    def _parse_padding_scheme_tag(self, xml_node):
        padding_scheme_node = xml_node.find(self.paddingSchemeTag)
        if padding_scheme_node is not None:
            if self.valueTag not in padding_scheme_node.attrib:
                raise ComponentException("Missing value for tag: '{}'".format(self.paddingSchemeTag), self.name)
            padding_scheme_string = padding_scheme_node.attrib[self.valueTag]
            allowed_padding_schemes = [e.value for e in SupportedPaddings.PaddingSchemeType]
            if padding_scheme_string in allowed_padding_schemes:
                padding_scheme_value = padding_scheme_string
            else:
                calculate_exception = None
                try:
                    padding_scheme_value = self.calculate_value(padding_scheme_string, allow_calculate = True)
                except ComponentException as ex:
                    calculate_exception = ex
                if calculate_exception or padding_scheme_value not in allowed_padding_schemes:
                    raise ComponentException("Invalid value for '{}', use one of: '{}'{}".format(self.paddingSchemeTag,
                                                                                                 ", ".join(
                                                                                                     allowed_padding_schemes),
                                                                                                 ", " + str(
                                                                                                     calculate_exception) if calculate_exception else ""),
                                             self.name)
            self.padding_scheme = SupportedPaddings.PaddingSchemeType(padding_scheme_value)
            if self.paddingSaltLenAttrTag not in padding_scheme_node.attrib:
                raise ComponentException("Missing salt_len tag: '{}'".format(self.paddingSaltLenAttrTag), self.name)
            if padding_scheme_node.attrib[self.paddingSaltLenAttrTag]:
                try:
                    self.salt_len = self.calculate_value(padding_scheme_node.attrib[self.paddingSaltLenAttrTag],
                                                         allow_calculate = True)
                except (ValueError, TypeError, ComponentException):
                    raise ComponentException(
                            "Incorrect salt_len: {}".format(padding_scheme_node.attrib[self.paddingSaltLenAttrTag]),
                            self.name)

    def _parse_signing_utility_tag(self, xml_node):
        signing_util_node = xml_node.find(self.signingUtilTag)
        if signing_util_node is not None:
            if self.valueTag in signing_util_node.attrib:
                self.signing_script = signing_util_node.attrib[self.valueTag]
            else:
                self.signing_script_path = signing_util_node.attrib[self.calculateTag]

        signing_util_timeout_node = xml_node.find(self.signingUtilTimeoutTag)
        if signing_util_timeout_node is not None:
            if self.calculateTag not in signing_util_timeout_node.attrib:
                raise ComponentException(f"Missing mandatory attribute '{self.signingUtilTimeoutTag}' "
                                         f"in '{self.signingUtilTag}'", self.name)
            timeout_formula = signing_util_timeout_node.attrib[self.calculateTag]
            if timeout_formula:
                self.signing_script_timeout_formula = timeout_formula

    def _get_property(self, component_property, _=False):
        if component_property == SignFunction.ComponentProperty.HeaderVersion:
            return self.create_header_version()
        return super()._get_property(component_property, _)

    def create_header_version(self):
        if isinstance(self.key.key, RsaSigningKey):
            version = SupportedPaddings.get_mask_version(self.padding_scheme)
        else:
            curve_type = EcSigningKey.get_curve_type(self.key.key.curve)
            version = EcSigningKey.get_mask_version(curve_type)
        version += SupportedSHAs.get_mask_version(self.sha_type)
        return version

    def sign_external(self, buffer=None):
        data_file_name = 'data_to_sign.bin'
        signature_file_name = 'signature.bin'
        sha_arg = "sha" + self.sha_type.value

        with open(data_file_name, 'wb') as file:
            file.write(self.get_input_bytes(buffer))

        absIn = os.path.abspath(data_file_name)
        absPath = os.path.dirname(absIn)
        absOut = os.path.join(absPath, signature_file_name)

        if not os.path.isabs(self.signing_script):
            raise ComponentException(f"Full path must be used for {self.signingUtilTag}", self.name)

        cmd = ['python', self.signing_script, sha_arg, self.key.value, absOut, absIn, self.padding_scheme.value]

        try:
            print('Calling external signing script: "{}"'.format(' '.join(cmd)))
            ColorPrint.warning('WARNING:\nMake sure that the called script can be safely called and does not pose any threat!')
            subprocess.check_call(cmd, shell=False, timeout=self.signing_script_timeout) #nosec
        except subprocess.CalledProcessError as e:
            raise ComponentException(
                "Problem calling signing script '{}': {}".format(self.signing_script, e.returncode), self.name)
        except subprocess.TimeoutExpired:
            raise ComponentException(
                "Timeout ({}) occurred while calling signing script '{}'".format(self.signing_script_timeout,
                                                                                 self.signing_script), self.name)

        try:
            with open(signature_file_name, 'rb') as file:
                signature = file.read()
        except FileNotFoundError as ex:
            raise ComponentException("Cannot open calculated signature. {}: {}".format(ex.strerror, ex.filename),
                                     self.name)

        return signature[::-1]

    def _build_layout(self):
        self.key = self.calculate_value(self.key_path, allow_calculate = True)
        self._size = self._calc_size()
        self._set_value(b'\0' * self.size)
        if self.signing_script_path:
            self.signing_script = self.calculate_value_from_path(self.signing_script_path).value
        if self.signing_script_timeout_formula:
            timeout_str = self.calculate_value(self.signing_script_timeout_formula)
            if timeout_str:
                self.signing_script_timeout = Converter.string_to_int(timeout_str)
            else:
                self.signing_script_timeout = None

    def _calc_size(self):
        sign_size = self.key.get_property("signature_size")  # * 2 because we have Qx and Qy
        if isinstance(self.key.key, EcSigningKey) and self.ecc_padding and self.ecc_padding * 2 > sign_size:
            return self.ecc_padding * 2
        return sign_size

    def _build(self, buffer):
        super()._build(buffer)

        if self.offline_signing_formula:
            self.offline_signing = self.calculate_value(formula = self.offline_signing_formula)

        if self.offline_signing:
            print("{}:\nOffline signing - signature will NOT be computed!\n".format(self.get_string_path()))

            if self.load_external_data_formula:
                self.load_external_data = self.calculate_value(formula = self.load_external_data_formula)

            if self.load_external_data:
                if self.external_data_formula is None:
                    raise ComponentException(
                            "Cannot load external data - '{}' tag with '{}' attribute was not specified".format(
                                self.externalDataTag, self.calculateTag), self.name)
                self.external_data = self.calculate_value(formula = self.external_data_formula)
                if not isinstance(self.external_data, bytes) and not isinstance(self.external_data, bytearray):
                    raise ComponentException(
                        "{} must result in a 'bytearray' or 'bytes', but is: {}".format(self.externalDataTag, type(
                            self.external_data).__name__), self.name)
                # ensure that external data fills all space of this component
                if len(self.external_data) != self.size:
                    raise ComponentException(
                        "Invalid size of '{}', should be {} but is {}".format(self.externalDataTag, self.size,
                                                                              len(self.external_data)), self.name)

                # verify if loaded signature matches computed hash and given public key
                padding_args = SupportedPaddings.get_padding_args(self.salt_len, self.padding_scheme, self.sha_type,
                                                                  self.is_legacy)
                padding_class = SupportedPaddings.get_padding_class(self.padding_scheme, self.is_legacy)

                try:
                    self.key.verify(self.external_data, self.get_sha(buffer), padding_class(*padding_args),
                                    utils.Prehashed(SupportedSHAs.get_sha_class(self.sha_type, self.is_legacy)))
                except InvalidSignature as e:
                    raise ComponentException(
                        "Loaded signature does not match given key and computed hash".format(str(e)), self.name)
                print("Loaded signature is valid.\n")
            else:
                self.external_data = bytes([0xFF] * self.size)

            self._set_value(self.external_data[::-1] if self.reverse else self.external_data)
            return

        if self.signing_script:
            self._set_value(self.sign_external(buffer))
        else:
            padding_args = SupportedPaddings.get_padding_args(self.salt_len, self.padding_scheme, self.sha_type,
                                                              self.is_legacy)
            padding_class = SupportedPaddings.get_padding_class(self.padding_scheme, self.is_legacy)

            if not self.key.is_private:
                raise ComponentException("Public key detected for signature", self.name)

            if isinstance(self.key.key, RsaSigningKey):
                padding = padding_class(*padding_args)
            else:
                padding = self.ecc_padding

            try:
                signature = self.key.sign(self.get_sha(buffer), padding,
                    utils.Prehashed(SupportedSHAs.get_sha_class(self.sha_type, self.is_legacy)), self.reverse)
            except (ValueError, TypeError) as e:
                raise ComponentException("Signing error: {}".format(e.args[0]), self.name)
            self._set_value(signature)
