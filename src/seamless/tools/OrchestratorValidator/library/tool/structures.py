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

import sys
from os import urandom
from mmap import mmap
from enum import Enum
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import algorithms, modes
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey, ECDSA
from cryptography.exceptions import InvalidSignature

from .LibException import LibException


class SupportedSHAs:
    class ShaType(Enum):
        Sha256 = "256"
        Sha384 = "384"
        Sha512 = "512"

    _supportedSHAClasses = { ShaType.Sha384: hashes.SHA384(), ShaType.Sha512: hashes.SHA512() }
    _legacySHAClasses = { ShaType.Sha256: hashes.SHA256() }

    _maskVersions = { ShaType.Sha256: 0, ShaType.Sha384: 0x1000, ShaType.Sha512: 0x2000, }

    @classmethod
    def get_sha_type(cls, sha: str):
        for sha_type in SupportedSHAs.ShaType:
            if sha_type.name.lower() == sha.lower():
                return sha_type
        cls.raise_not_supported(sha)

    @classmethod
    def get_sha_class(cls, sha_type: ShaType, is_legacy = False):
        if sha_type in SupportedSHAs._supportedSHAClasses:
            return cls._supportedSHAClasses[sha_type]
        if is_legacy and sha_type in cls._legacySHAClasses:
            return cls._legacySHAClasses[sha_type]
        raise LibException(f"Given sha size is deprecated: {sha_type.value}.\n"
                           f"Accepted are: " + ", ".join([sha.value for sha in cls._supportedSHAClasses.keys()]))

    @classmethod
    def get_mask_version(cls, sha_type: ShaType):
        if sha_type in cls._maskVersions:
            return cls._maskVersions[sha_type]
        cls.raise_not_supported(sha_type)

    @classmethod
    def raise_not_supported(cls, sha):
        raise LibException(f"Given sha type: {str(sha)} is not supported. "
                           f"Possible are: {', '.join([sha.name for sha in cls.ShaType])}")


class SupportedPaddings:
    class PaddingSchemeType(Enum):
        pkcs1_v1_5 = "v1_5"
        pkcs1_pss = "PSS"

    _supportedPaddingClasses = { PaddingSchemeType.pkcs1_pss: padding.PSS }
    _legacyPaddingClasses = { PaddingSchemeType.pkcs1_v1_5: padding.PKCS1v15 }
    _maskVersions = { PaddingSchemeType.pkcs1_v1_5: 0x10000, PaddingSchemeType.pkcs1_pss: 0x20000 }
    maxSaltLen = padding.PSS.MAX_LENGTH

    @classmethod
    def get_padding_class(cls, padding_type: PaddingSchemeType, is_legacy = False):
        if padding_type in cls._supportedPaddingClasses:
            return cls._supportedPaddingClasses[padding_type]
        if is_legacy and padding_type in cls._legacyPaddingClasses:
            return cls._legacyPaddingClasses[padding_type]
        raise LibException(f"Given padding type is deprecated: {padding_type.value}.\n"
                           f"Accepted are: " + ", ".join([sha.value for sha in cls._supportedPaddingClasses.keys()]))

    @classmethod
    def get_padding_args(cls, salt_len, padding_type, sha_type, is_legacy):
        padding_args = { cls.PaddingSchemeType.pkcs1_v1_5: [], cls.PaddingSchemeType.pkcs1_pss: [
            padding.MGF1(SupportedSHAs.get_sha_class(sha_type, is_legacy)), salt_len] }
        return padding_args[padding_type]

    @classmethod
    def get_mask_version(cls, padding_type: PaddingSchemeType):
        if padding_type in cls._maskVersions:
            return cls._maskVersions[padding_type]
        cls.raise_not_supported(padding_type)

    @classmethod
    def raise_not_supported(cls, padding):
        raise LibException(f"Given padding type: {str(padding)} is not supported. "
                           f"Possible are: {', '.join([padd.name for padd in cls.PaddingSchemeType])}")


class AsymmetricKeyType(Enum):
    Public = "Public"
    Private = "Private"


class RsaSigningKey:
    class RsaKeyLength(Enum):
        Len2K = 256
        Len3K = 384

    _supportedRsaMapping = [RsaKeyLength.Len3K]
    _legacyRsaMapping = [RsaKeyLength.Len2K]

    ExponentSize = 4

    def __init__(self):
        (self.modulus, self.public_exponent, self.private_exponent, self.prime_p, self.prime_q, self._rsa_key,
         self.hashed_key) = [0] * 7
        self.key_type = AsymmetricKeyType.Public

    @property
    def rsa_key(self):
        return self._rsa_key

    @rsa_key.setter
    def rsa_key(self, value):
        self._rsa_key = value
        if isinstance(value, RSAPrivateKey):
            self.key_type = AsymmetricKeyType.Private
        else:
            self.key_type = AsymmetricKeyType.Public

    def sign(self, computed_hash, padding_algorithm, hash_algorithm, reverse):
        signature = self.rsa_key.sign(computed_hash, padding_algorithm, hash_algorithm)
        if reverse:
            return signature[::-1]
        return signature

    def verify(self, signature, computed_hash, padding_algorithm, hash_algorithm):
        if self.key_type == AsymmetricKeyType.Private:
            key = self.rsa_key.public_key()
        else:
            key = self.rsa_key
        return key.verify(bytes(signature), computed_hash, padding_algorithm, hash_algorithm)

    @classmethod
    def get_key_len_type(cls, key: "RsaSigningKey", is_legacy):
        def _get_key_len_for_map(key, key_map):
            for key_type in key_map:
                if key_type.value == len(key.modulus):
                    return key_type
            return None

        key_type = _get_key_len_for_map(key, cls._supportedRsaMapping)
        if key_type is None and is_legacy:
            key_type = _get_key_len_for_map(key, cls._legacyRsaMapping)
        if key_type is None:
            cls.raise_not_supported(key.rsa_key.key_size)
        return key_type

    @classmethod
    def get_key_len(cls, key_len: RsaKeyLength, is_legacy):
        if (key_len in cls._supportedRsaMapping) or (is_legacy and key_len in cls._legacyRsaMapping):
            return key_len.value
        cls.raise_not_supported(key_len.value * 8)

    @classmethod
    def raise_not_supported(cls, rsa_len):
        raise LibException(f"Given signing key size: {str(rsa_len)} is not supported. "
                           f"Possible are: "
                           f"{', '.join([str(rsa.value * 8) for rsa in cls._supportedRsaMapping])}")


class EcSigningKey:
    class EcCurve(Enum):
        Secp256 = 'secp256r1'
        Secp384 = 'secp384r1'
        Brainpool384 = 'brainpoolP384r1'

    _supportedCurves = [EcCurve.Brainpool384, EcCurve.Secp384]
    _legacyCurves = [EcCurve.Secp256]
    _maskVersion = 0x30000
    _maskCurveVersions = { EcCurve.Secp256: 0, EcCurve.Secp384: 0x100, EcCurve.Brainpool384: 0x200 }

    def __init__(self):
        (self._curve, self.qx, self.qy, self._ec_key, self.coordinate_size, self.hashed_key) = [0] * 6
        self.key_type = AsymmetricKeyType.Public

    @property
    def curve(self):
        return self._curve

    @curve.setter
    def curve(self, value):
        curve_type = self.get_curve_type(value)
        self._curve = curve_type.value

    @property
    def ec_key(self) -> EllipticCurvePrivateKey:
        return self._ec_key

    @ec_key.setter
    def ec_key(self, value):
        self._ec_key: EllipticCurvePrivateKey = value
        if isinstance(value, EllipticCurvePrivateKey):
            self.key_type = AsymmetricKeyType.Private
        else:
            self.key_type = AsymmetricKeyType.Public

    def sign(self, computed_hash, length, hash_algorithm, reverse_order: int):
        signature = self.ec_key.sign(computed_hash, ECDSA(hash_algorithm))
        r, s = utils.decode_dss_signature(signature)
        bytes_length = length if length and length > self.coordinate_size else self.coordinate_size
        order_str = "little" if reverse_order else "big"
        r = r.to_bytes(self.coordinate_size, order_str)
        s = s.to_bytes(self.coordinate_size, order_str)
        r_padded = r + b'\0' * (bytes_length - self.coordinate_size)
        s_padded = s + b'\0' * (bytes_length - self.coordinate_size)
        return r_padded + s_padded

    def verify(self, signature, computed_hash, _, hash_algorithm):
        if self.key_type == AsymmetricKeyType.Private:
            key = self.ec_key.public_key()
        else:
            key = self.ec_key
        try:
            key.verify(bytes(signature), computed_hash, ECDSA(hash_algorithm))
        except InvalidSignature:
            raise LibException('Failed to verify signature, invalid value detected.')

    @classmethod
    def get_curve_type(cls, curve: str):
        for en_curve in cls.EcCurve:
            if en_curve.value.lower() == curve.lower():
                return en_curve
        cls.raise_not_supported(curve)

    @classmethod
    def raise_not_supported(cls, curve):
        raise LibException(f"Given ec curve type: {str(curve)} is not supported. "
                           f"Possible are: {', '.join([curve.value for curve in cls.EcCurve])}")

    @classmethod
    def get_mask_version(cls, curve_type: EcCurve):
        if curve_type in cls._maskCurveVersions:
            return cls._maskVersion + cls._maskCurveVersions[curve_type]
        cls.raise_not_supported(curve_type)


class DataNode:
    nameTag = "name"
    valueTag = "value"
    pathTag = "path"
    startTag = "start"
    endTag = "end"
    startIndexTag = "start_index"
    endIndexTag = "end_index"
    excludeRangesTag = "exclude_ranges"

    name = None
    value = None
    path = None
    start = None
    end = None
    start_index = None
    end_index = None

    def __init__(self, xml_node):
        if self.nameTag in xml_node.attrib:
            self.name = xml_node.attrib[self.nameTag]
        if self.valueTag in xml_node.attrib:
            self.value = xml_node.attrib[self.valueTag]
        if self.pathTag in xml_node.attrib:
            self.path = xml_node.attrib[self.pathTag]
        if self.startTag in xml_node.attrib:
            self.start = xml_node.attrib[self.startTag]
        if self.endTag in xml_node.attrib:
            self.end = xml_node.attrib[self.endTag]
        if self.startIndexTag in xml_node.attrib:
            self.start_index = xml_node.attrib[self.startIndexTag]
        if self.endIndexTag in xml_node.attrib:
            self.end_index = xml_node.attrib[self.endIndexTag]
        if self.excludeRangesTag in xml_node.attrib:
            self.exclude_ranges = xml_node.attrib[self.excludeRangesTag]
        else:
            self.exclude_ranges = None

        if not self.value and not self.path and (not self.start or not self.end):
            raise LibException(
                    "Missing mandatory attributes '{}' or '{}' or '{}' and '{}'".format(self.valueTag, self.pathTag,
                                                                                        self.startTag, self.endTag))

    def check_start_end(self):
        if not self.start or not self.end:
            raise LibException("Missing mandatory attributes '{}' and '{}'".format(self.startTag, self.endTag))

    def check_name(self):
        if not self.name:
            raise LibException("Missing mandatory attributes '{}'".format(self.nameTag))


class AesEncryption:
    class KeyLength(Enum):
        Aes128 = 128
        Aes256 = 256

    class Mode(Enum):
        CBC = 'CBC'
        CTR = 'CTR'

    modeTypes = { Mode.CBC: 1, Mode.CTR: 2 }
    aesBlockSizeBytes = algorithms.AES.block_size // 8

    _paddingTypes = None
    _supportedAesSizes = [KeyLength.Aes256]
    _legacyAesSizes = [KeyLength.Aes128]

    @classmethod
    def GetPaddingTypes(cls):
        if cls._paddingTypes is None:
            cls._paddingTypes = { cls.Mode.CBC: cls.ErrorPadding, cls.Mode.CTR: cls.NoPadding }
        return cls._paddingTypes

    @classmethod
    def parse_mode(cls, modeStr):
        try:
            return cls.Mode(modeStr.upper())
        except Exception:
            values = [item.value for item in cls.Mode]
            raise LibException("Invalid name of encryption mode, choose one of: {}".format(", ".join(values)))

    """
    mode instance must never be reused - when starting new encryption a new initialization vector
    of random data must be generated
    """

    @classmethod
    def get_mode_instance(cls, name, iv = None):
        if name == cls.Mode.CBC:
            return modes.CBC(iv if iv is not None else urandom(cls.aesBlockSizeBytes))
        if name == cls.Mode.CTR:
            return modes.CTR(iv if iv is not None else urandom(cls.aesBlockSizeBytes))
        raise LibException("There is no such encryption mode: {}".format(name))

    @classmethod
    def create_initialisation_vector(cls, mode_name):
        return urandom(cls.aesBlockSizeBytes)

    @classmethod
    def get_empty_initialisation_vector(cls, mode_name):
        return bytes([0] * cls.aesBlockSizeBytes)

    @classmethod
    def get_key_length_type(cls, key_length: int, is_legacy):
        results = list(filter(lambda key: key.value == key_length, cls._supportedAesSizes))
        if not results and is_legacy:
            results = list(filter(lambda key: key.value == key_length, cls._legacyAesSizes))
        if results:
            return next(iter(results))
        cls._raise_not_supported(key_length, is_legacy)

    @classmethod
    def _raise_not_supported(cls, key_len, is_legacy):
        size_collection = cls._supportedAesSizes if is_legacy else cls._legacyAesSizes + cls._supportedAesSizes
        raise LibException(f"Given key size: {str(key_len)} is not supported.\n"
                           f"Possible are: {', '.join([str(en_k.value) for en_k in size_collection])}.")

    @classmethod
    def get_padding_instance(cls, encryption_mode):
        if encryption_mode not in cls.GetPaddingTypes():
            raise LibException(
                    "There is no padding type defined for following encryption mode: {}".format(encryption_mode))
        return cls.GetPaddingTypes()[encryption_mode]()

    class Padding:
        def get_encrypted_data_size(self, data_size):
            raise LibException("Invalid padding - base class used")

        def calculate_padding_length(self, data_size):
            self.n_extra_bytes = data_size % AesEncryption.aesBlockSizeBytes
            self.padding_length = -data_size % AesEncryption.aesBlockSizeBytes
            self.n_full_blocks = data_size // AesEncryption.aesBlockSizeBytes

        def preencrypt(self, data):
            raise LibException("Invalid padding - base class used")

        def postencrypt(self, data):
            raise LibException("Invalid padding - base class used")

    class Cs1Padding(Padding):
        # For padding algorithm description see:
        # http://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38a-add.pdf
        def get_encrypted_data_size(self, data_size):
            return data_size

        def preencrypt(self, data):
            self.calculate_padding_length(len(data))
            if self.n_full_blocks < 1:
                raise LibException(
                        "Invalid Length: must be at least {} (1 block size)".format(AesEncryption.aesBlockSizeBytes))

            return data + bytes([0] * self.padding_length)

        def postencrypt(self, data):
            part1 = data[:(self.n_full_blocks - 1) * AesEncryption.aesBlockSizeBytes + self.n_extra_bytes]
            part2 = data[-AesEncryption.aesBlockSizeBytes:]
            return part1 + part2

    class NoPadding(Padding):
        # For CTR mode we don't need any paddng
        def get_encrypted_data_size(self, data_size):
            return data_size

        def preencrypt(self, data):
            return data

        def postencrypt(self, data):
            return data

    class ErrorPadding(Padding):
        # This class doesn't allow any padding - data must be of proper size, otherwise an error is raised
        def get_encrypted_data_size(self, data_size):
            self.calculate_padding_length(data_size)
            if self.padding_length:
                raise LibException(
                        "Padding is disabled for this encryption mode, data must be aligned to {}. Use 'padding' attribute to align data size".format(
                                AesEncryption.aesBlockSizeBytes))
            return data_size

        def preencrypt(self, data):
            return data

        def postencrypt(self, data):
            return data


class Buffer(mmap):
    _error_message_pattern = "out of range"

    def __init__(self, file_no, length, **_):
        self._file_no = file_no
        self._max_size = length if length != 0 else self.size()

    def size(self):
        if self._file_no == -1:
            raise LibException(r"Cannot call 'size' method without an underlying file. Use 'max_size' property instead")
        return super().size()

    @property
    def max_size(self):
        return self._max_size

    def seek(self, *args, **kwargs):
        try:
            return super().seek(*args, **kwargs)

        except OverflowError as e:
            offset = args[0]
            raise LibException(f"Value of {hex(offset)} is too big. Limit is {hex(sys.maxsize)}")

        except ValueError as e:
            if self._error_message_pattern in str(e):
                raise LibException("Internal buffer of size {} is too small: {}".format(self.max_size, str(e)))
            else:
                raise

    def write(self, *args, **kwargs):
        try:
            return super().write(*args, **kwargs)
        except ValueError as e:
            if self._error_message_pattern in str(e):
                raise LibException("Internal buffer of size {} is too small: {}".format(self.max_size, str(e)))
            else:
                raise

    def reduce_buffer_to_match_content(self):
        current_offset = self.tell()
        if current_offset == 0:
            # We cannot create mmap with size 0 so we set size to 1
            # but the current position (tell()) will stay at 0 so it will be fine
            new_buffer = Buffer(self._file_no, 1)
            new_buffer._max_size = 0
        else:
            self.seek(0)
            content = self.read(current_offset)
            new_buffer = Buffer(self._file_no, current_offset)
            new_buffer.write(content)
        self.flush()
        self.close()
        return new_buffer


class ValueWrapper:
    class Tags:
        ValueTag = 'value'
        CalculateTag = 'calculate'

    def __init__(self, xml_node, component, convert_function=None):
        self._value = None
        self._formula = None
        self.component = component
        if self.Tags.ValueTag in xml_node.attrib:
            self._value = xml_node.attrib[self.Tags.ValueTag]
            # if convert_function has been given then we use it to convert convent of 'value' attribute
            if convert_function:
                self._value = convert_function(self._value)
        if self.Tags.CalculateTag in xml_node.attrib:
            self._formula = xml_node.attrib[self.Tags.CalculateTag]

    def needs_calculation(self):
        return self._value is None and self._formula is not None

    @property
    def value(self):
        if self.needs_calculation():
            self._value = self.component.calculate_value(self._formula)
        return self._value

    def recalculate(self):
        if self._formula is not None:
            self._value = self.component.calculate_value(self._formula)
        return self._value

