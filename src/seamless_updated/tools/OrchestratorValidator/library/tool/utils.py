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
import operator
import os
import os.path
import mmap
import re
import json
from sys import maxsize
from enum import Enum
from functools import partial

import sys
from math import ceil, pow
from lxml.etree import tostring  #nosec - parsed xml is checked if there are no DOCTYPE elements. We don't use features that introduce other vulnerabilities
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.primitives import hashes
from xml.dom import minidom #nosec - we only parse content created by us

from .LibConfig import LibConfig
from .exceptions import InvalidAttributeException, MissingAttributeException, GeneralException
from .LibException import LibException, ComponentException
from . import structures as ss
from .Converter import Converter
from .exceptions import JSONException
from .ColorPrint import ColorPrint


copyrightComment = """<!--
INTEL CONFIDENTIAL
Copyright 2019-2020 Intel Corporation.
This software and the related documents are Intel copyrighted materials, and
your use of them is governed by the express license under which they were
provided to you (License).Unless the License provides otherwise, you may not
use, modify, copy, publish, distribute, disclose or transmit this software or
the related documents without Intel's prior written permission.

This software and the related documents are provided as is, with no express or
implied warranties, other than those that are expressly stated in the License.
-->

"""

bin_operators_map = {  # python operators precedence
    'or': (lambda a, b: a or b, False),
    'and': (lambda a, b: a and b, False),
    'not': (operator.not_, False),
    '!=': (operator.ne, False),
    '==': (operator.eq, False),
    '>': (operator.gt, False),
    '>=': (operator.ge, False),
    '<=': (operator.le, False),
    '<': (operator.lt, False),
    '^': (operator.xor, True),
    '|': (operator.or_, True),
    '&': (operator.and_, True),
    '<<': (operator.lshift, True),
    '>>': (operator.rshift, True),
    '+': (operator.add, True),
    '-': (operator.sub, True),
    '*': (operator.mul, True),
    '/': (operator.floordiv, True),
    '%': (operator.mod, True),
}


def calc_operator(oper: str, left, right):
    return bin_operators_map[oper][0](left, right)


def calculate_hash(buffer, hash_type: ss.SupportedSHAs.ShaType, is_legacy: bool):
    if hash_type:
        digest = hashes.Hash(ss.SupportedSHAs.get_sha_class(hash_type, is_legacy), backend = default_backend())
        digest.update(bytes(buffer))
        return digest.finalize()
    raise LibException("Hash type not supported")


def set_nth_bit(length, bit):
    arr = bytearray(length)
    bbyte = bit // 8
    bit_in_byte = bit - 8 * bbyte
    arr[length - 1 - bbyte] |= 1 << bit_in_byte

    return bytes(arr)


def process_key_file(file_name, hash_type: ss.SupportedSHAs.ShaType, is_legacy: bool):
    if not os.path.isfile(file_name) and not os.access(file_name, os.R_OK):
        msg = 'Could not open key file - "{}"'.format(file_name)
        raise LibException(msg)

    use_dbg_key = False

    with open(file_name, 'rb') as kfile:
        line = b'(8:sequence'
        buffer = kfile.read(len(line))
        if line == buffer:
            use_dbg_key = True

    if use_dbg_key:
        # convert the raw data into the right structure
        key = convert_rsa_key_format(file_name, hash_type, is_legacy)
    else:
        key = process_openssl_key(file_name, hash_type, is_legacy)

    if isinstance(key, ss.RsaSigningKey):
        expected_exponent = 0x010001
        exponent = int.from_bytes(key.public_exponent, 'little')
        if exponent != expected_exponent:
            ColorPrint.warning(f"WARNING:\nDangerous RSA key! Public exponent should be {expected_exponent} "
                               f"but is {exponent}")

    return key


def hash_signing_key(signing_key, hash_type: ss.SupportedSHAs.ShaType, is_legacy: bool):
    if isinstance(signing_key, ss.EcSigningKey):
        to_hash = signing_key.qx + signing_key.qy
    else:
        to_hash = signing_key.modulus + signing_key.public_exponent
    signing_key.hashed_key = calculate_hash(to_hash, hash_type, is_legacy)


def convert_rsa_key_format(key_file, hash_type: ss.SupportedSHAs.ShaType, is_legacy: bool):
    stat = os.stat(key_file)
    with open(key_file, 'rb') as kfile:
        mm = mmap.mmap(-1, stat.st_size)
        mm.write(kfile.read())
        mm.seek(0)

        search = b'(11:private-key'
        pos = mm.find(search)

        mm.seek(pos)
        search = b'(1:e'  # search for exponent. I.e. this can be b'(1:e1:' or b'(1:e4:'
        pos = mm.find(search)
        offset = pos + len(search)
        exponent_size = int(mm[offset: offset + 1])
        offset = pos + len(b'(1:e1:')  # skip exponent marker
        public_exponent = mm[offset: offset + exponent_size].ljust(4, b'\x00')

        mm.seek(pos)
        search = b'(1:n256:'
        pos = mm.find(search)
        offset = pos + len(search)
        modulus = mm[offset: offset + 256]
        modulus = modulus[::-1]

        mm.seek(pos)
        search = b'(1:d256:'
        pos = mm.find(search)
        offset = pos + len(search)
        private_exponent = mm[offset: offset + 256]
        private_exponent = private_exponent[::-1]

        mm.seek(pos)
        search = b'(1:p128:'
        pos = mm.find(search)
        offset = pos + len(search)
        primep = mm[offset: offset + 128]
        primep = primep[::-1]

        mm.seek(pos)
        search = b'(1:q128:'
        pos = mm.find(search)
        offset = pos + len(search)
        primeq = mm[offset: offset + 128]
        primeq = primeq[::-1]

        signing_key = ss.RsaSigningKey()
        signing_key.modulus = modulus
        signing_key.public_exponent = public_exponent
        signing_key.private_exponent = private_exponent
        signing_key.prime_p = primep
        signing_key.prime_q = primeq

        n = int.from_bytes(modulus, 'little')
        e = int.from_bytes(public_exponent, 'little')
        d = int.from_bytes(private_exponent, 'little')
        p = int.from_bytes(primep, 'little')
        q = int.from_bytes(primeq, 'little')

        ppn = rsa.RSAPrivateNumbers(p, q, d, rsa.rsa_crt_dmp1(d, p), rsa.rsa_crt_dmq1(d, q), rsa.rsa_crt_iqmp(p, q),
                                    rsa.RSAPublicNumbers(e, n))
        pkey = ppn.private_key(backend = default_backend())
        signing_key.rsa_key = pkey
        hash_signing_key(signing_key, hash_type, is_legacy)
        return signing_key


def check_is_private_key(file_name):
    with open(file_name, 'rb') as kfile:
        private_key_header = b"PRIVATE"
        header = kfile.readline()
        if private_key_header in header:
            return True
        return False


def process_private_key(data, hash_type: ss.SupportedSHAs.ShaType, is_legacy: bool):
    pkey = serialization.load_pem_private_key(data, password = None, backend = default_backend())
    if isinstance(pkey, rsa.RSAPrivateKey):
        return process_private_rsa_key(pkey, hash_type, is_legacy)
    if isinstance(pkey, ec.EllipticCurvePrivateKey):
        return process_private_ec_key(pkey, hash_type, is_legacy)


def process_private_rsa_key(pkey, hash_type: ss.SupportedSHAs.ShaType, is_legacy: bool):
    signing_key = ss.RsaSigningKey()
    # Key size must be in full DWORDS, if a key is shorter then we have to round it up.
    key_size = ceil(pkey.key_size / 32) * 4  # key_size in bytes
    signing_key.rsa_key = pkey

    public_key = pkey.public_key()
    signing_key.modulus = public_key.public_numbers().n.to_bytes(key_size, 'little')
    signing_key.public_exponent = public_key.public_numbers().e.to_bytes(ss.RsaSigningKey.ExponentSize, 'little')

    hash_signing_key(signing_key, hash_type, is_legacy)

    signing_key.private_exponent = pkey.private_numbers().d.to_bytes(key_size, 'little')
    signing_key.prime_p = pkey.private_numbers().p.to_bytes(int(key_size / 2), 'little')
    signing_key.prime_q = pkey.private_numbers().q.to_bytes(int(key_size / 2), 'little')
    return signing_key


def process_private_ec_key(prv_key, hash_type: ss.SupportedSHAs.ShaType, is_legacy: bool):
    signing_key = process_public_ec_key(prv_key.public_key(), hash_type, is_legacy)
    signing_key.ec_key = prv_key
    hash_signing_key(signing_key, hash_type, is_legacy)
    return signing_key


def process_public_ec_key(pkey, _, __):
    public_key = ss.EcSigningKey()
    bytes_length = (pkey.curve.key_size + 7) // 8
    public_numbers = pkey.public_numbers()
    public_key.coordinate_size = bytes_length
    public_key.qx = public_numbers.x.to_bytes(bytes_length, 'little')
    public_key.qy = public_numbers.y.to_bytes(bytes_length, 'little')
    public_key.ec_key = pkey
    public_key.curve = pkey.curve.name
    return public_key


def process_public_key(data, hash_type, is_legacy):
    public_key = serialization.load_pem_public_key(data, default_backend())
    if isinstance(public_key, rsa.RSAPublicKey):
        return process_public_rsa_key(public_key, hash_type, is_legacy)
    if isinstance(public_key, ec.EllipticCurvePublicKey):
        return process_public_ec_key(public_key, hash_type, is_legacy)


def process_public_rsa_key(pkey, hash_type, is_legacy):
    pub_num = pkey.public_numbers()
    public_key = ss.RsaSigningKey()
    key_size = pkey.key_size // 8  # key_size in bytes
    public_key.rsa_key = pkey
    public_key.modulus = pub_num.n.to_bytes(key_size, 'little')
    public_key.public_exponent = pub_num.e.to_bytes(ss.RsaSigningKey.ExponentSize, 'little')
    hash_signing_key(public_key, hash_type, is_legacy)
    return public_key


def process_openssl_key(file_name, hash_type: ss.SupportedSHAs.ShaType, is_legacy: bool):
    is_private = check_is_private_key(file_name)
    with open(file_name, 'rb') as kfile:
        data = kfile.read()
        try:
            if is_private:
                signing_key = process_private_key(data, hash_type, is_legacy)
            else:
                signing_key = process_public_key(data, hash_type, is_legacy)
        except (ValueError, IndexError, TypeError) as ex:
            raise LibException(str(ex))

        return signing_key


def construct_public_key(exponent: bytearray, modulus: bytearray):
    key = ss.RsaSigningKey()
    key.public_exponent = exponent
    key.modulus = modulus
    numbers = RSAPublicNumbers(int.from_bytes(exponent, 'little'), int.from_bytes(modulus, 'little'))
    key.rsa_key = numbers.public_key(default_backend())
    return key


#
# Function prints (and writes to file) hash of signing key
#
def hashed_key_printer(signing_key, file_name):
    if not signing_key:
        return

    if isinstance(signing_key, bytes):
        txt_hashed_key = Converter.bytes_to_string(calculate_hash(signing_key, ss.SupportedSHAs.ShaType.Sha256, True))
        key_kind = 'AesKey'
        print('{} key hash: {}'.format(key_kind, txt_hashed_key))
    else:
        txt_hashed_key = Converter.bytes_to_string(signing_key.hashed_key)
        key_kind = signing_key.key_type.value
        print('Key public part hash: {}'.format(txt_hashed_key))

    if file_name:
        with open(file_name, mode='w') as f:
            f.write(txt_hashed_key)
        print('{} key hash saved in file: {}'.format(key_kind, file_name))


#
#   Function validating whether file with given path is ok
#
def validate_file(file):
    if not os.path.isfile(file) and not os.access(file, os.R_OK):
        raise LibException("File '{}' could not be opened!".format(file))


#
#   Function which unifies path separators in the specified path
#
def unify_path(path: str):
    return os.path.join(*re.compile(r"[\\/]").split(path))


#
#   Function returns file name without extension
#
def get_file_name_no_ext(file_name):
    input_name = os.path.basename(file_name)
    return os.path.splitext(input_name)[0]


#
#   Function returns file extension including dot
#
def get_file_ext(file_name):
    input_name = os.path.basename(file_name)
    return os.path.splitext(input_name)[1]


def save_node_to_file(node, xml_path, include_copyright=False):
    if not os.access(xml_path, os.W_OK) and os.path.isfile(xml_path):
        raise GeneralException("Could not save to read-only file")
    raw_xml_string = tostring(node).decode("utf-8")
    if include_copyright:
        raw_xml_string = copyrightComment + '\n' + raw_xml_string
    reparsed = minidom.parseString(raw_xml_string)
    final_xml = reparsed.toprettyxml(indent=' ' * 4)
    with open(xml_path, 'w') as f:
        f.write(final_xml)


#
#    Function returns last index of searched item in a list
#
def last_index(list_, item_):
    return len(list_) - 1 - list_[::-1].index(item_)


def align_value(value, alignment):
    if (value % alignment) != 0:
        difference = alignment - (value % alignment)
        return value + difference
    return value


def get_value_from_child_component(parent_component, tag_name):
    try:
        node = parent_component.get_child(tag_name)
    except ComponentException:
        raise LibException("Couldn't get node '{}' from '{}'".format(tag_name, parent_component.name))
    value = node.value
    if value is None:
        raise LibException('Value is not set in {}/{}'.format(parent_component.name, tag_name))
    return value


def to_hex(value, size):
    if value is None:
        return None

    return hex(value & 2 ** (size * 8) - 1) if value < 0 else hex(value)


def bit_count(value):
    return len(bin(int(value, 0))[2:])


def get_min_max_values(size: int, signed: bool) -> (str, str):
    str_min = "0x0"
    str_max = hex(maxsize)

    if size is not None:
        if size > 0:
            maximum = int(pow(2, size * 8))
            if signed:
                half = maximum // 2
                str_min = str(half * -1)
                str_max = str(half - 1)
            else:
                str_max = str(hex(maximum - 1))
        else:
            raise LibException("Can not generate minimum and maximum value if size is less than 1.")

    return str_min, str_max


def check_value_in_enum(value, enum_class):
    values = [item.value for item in enum_class]
    if value not in values:
        raise LibException(', '.join(values))


def parse_json_str(text):
    text = text.replace("\'", "\"")
    text = text.replace("&apos;", "\'")

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise JSONException(f'Incorrect json params definition: [{text}]')


def prepare_string_to_xml(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")\
        .replace("\0", "")


def str_empty(string: str):
    return bool(re.match(r'^\s*$', string))


def get_item_from_structure(structure, key):
    if isinstance(structure, dict) and key in structure:
        return structure[key]
    if isinstance(structure, list):
        for element in structure:
            item = get_item_from_structure(element, key)
            if item is not None:
                return item
    if isinstance(structure, dict):
        for element in structure.values():
            item = get_item_from_structure(element, key)
            if item is not None:
                return item
    return None


def write_value_to_byte_array(component, buffer: bytearray):
    if len(buffer) <= component.offset:
        raise ComponentException(
                "Component has offset ({}) higher than binary size ({})!".format(component.offset, len(buffer)),
                component.name)
    if len(buffer) < component.offset + len(component.get_bytes()):
        raise ComponentException("Component exceeded the binary size\n"
                                 "Offset: {} Size: {}\n"
                                 "Maximum binary size: {}".format(component.offset, len(component.get_bytes()),
                                                                  len(buffer)), component.name)
    buffer[component.offset: component.offset + component.size] = component.get_bytes()


def max_value(size):
    return 2 ** (size * 8) - 1


def validate_path_to_file(component_name: str, path: str, check_write_access = False):
    directory_path = os.path.dirname(path)
    file_name = os.path.basename(path)
    # check if directory exists and the file name does not exceed Windows limitation for file name
    if (directory_path and not os.path.isdir(directory_path)) or len(file_name) > 255:
        raise ComponentException(f"Invalid path to file: {path}", component_name)

    if check_write_access:
        if os.access(path, os.F_OK):
            if not os.access(path, os.W_OK):
                raise ComponentException(f"Could not save to {path}. No write access", component_name)
            try:
                with open(path, "w"):
                    pass
            except (PermissionError, OSError) as e:
                raise ComponentException(f"Could not save to {path}. No write access", component_name)
    elif not os.path.isfile(path):
        raise ComponentException(f"Invalid path to file: {path}", component_name)
    elif not os.access(path, os.R_OK):
        raise ComponentException(f"Could not open file: {path}. No read access", component_name)


def check_file_path(path, can_be_empty = True, throwing = True, restrict_types = None):
    # we allow empty path or not according the flag can_be_empty
    is_exist = os.path.isfile(path) if path else False
    is_proper_type = (can_be_empty and not path) or (
                not restrict_types or os.path.splitext(path)[1][1:] in restrict_types)
    should_throw = (not can_be_empty and not path) or path
    if should_throw and not is_exist and throwing:
        raise InvalidAttributeException("Given path does not exist: '{}'".format(path))
    elif throwing and not is_proper_type:
        raise InvalidAttributeException(f'Incorrect file type: "{path}". Must be one of: {", ".join(restrict_types)}.')
    elif not is_exist or not is_proper_type:
        return False
    return True


def check_directory_exists_create_if_not(path):
    if not os.path.exists(path):
        os.makedirs(path)


def print_header(name, version, copyright_date_range = None):
    copyright_date = copyright_date_range if copyright_date_range else datetime.now().year
    current_date = datetime.now().strftime("%d/%m/%Y - %H:%M")
    ColorPrint.info('\n\n=============================================================================\n'
                    f'{name} '
                    f'Version: {version}\n'
                    f'Copyright (c) {copyright_date}, Intel Corporation. All rights reserved.\n'
                    f'{current_date}\n'
                    '=============================================================================\n')


def is_python_ver_satisfying(required_python: (int, int)):
    if sys.version_info[:2] < required_python:
        print(f'Python version {",".join([str(num) for num in required_python])} or greater is necessary to run.')
        return False
    return True


def bit_mask(n: int):
    """Returns bit mask with n 1 bits at the end"""
    result = 0
    for i in range(n):
        result <<= 1
        result |= 1
    return result


def merge_masks(a, b):
    """Returns bit "and" for given masks. If one of masks is None its treated like positive bits only"""
    if a is None:
        return b
    if b is None:
        return a
    return a & b


class XmlAttrType(Enum):
    STRING = lambda s: s
    PATH = lambda s: s if check_file_path(s, True, True) else s
    VERSION = Converter.string_to_version
    BOOL = Converter.string_to_bool
    INT = Converter.string_to_int


class XmlAttr:
    id = 'name'

    def __init__(self, **kwargs):
        self.name = kwargs.get(self.id, '')
        self.is_required = kwargs.get('is_required', True)
        self.node = kwargs.get('xml_node', None)
        self.attr_type = kwargs.get('attr_type', XmlAttrType.STRING)
        self.default = kwargs.get('default', None)

    @property
    def value(self):
        if self.name in self.node.attrib:
            return partial(self.attr_type, self.node.attrib[self.name])()
        if self.is_required:
            raise MissingAttributeException(
                "Cannot find required attribute '{}' at node: {}".format(self.name, self.node.tag))
        return self.default


class Section(Enum):
    CONFIGURATION = LibConfig.configurationTag
    DECOMPOSITION = LibConfig.decompositionTag
    LAYOUT = LibConfig.layoutTag

    @classmethod
    def values(cls):
        return (section.value for section in cls)

    @staticmethod
    def for_component(component):
        cmp = component
        while cmp.name not in Section.values():
            cmp = cmp.parent
        return Section(cmp.name)


def save_binary_file(path: str, data):
    check_directory_exists_create_if_not(os.path.dirname(path))
    try:
        with open(path, 'wb') as file:
            file.write(data)
    except (OSError, IOError):
        raise GeneralException(f'Cannot write file into "{path}". Make sure you have proper access and file is not used.')
