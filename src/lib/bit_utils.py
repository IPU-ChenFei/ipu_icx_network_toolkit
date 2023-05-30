#!/usr/bin/env python
#################################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################


class GetBits:

    """
    Provide a utility to get a single bit or a range from a hex value.
    """

    def __init__(self):
        pass

    @classmethod
    def get_bits(cls, value, beginning_bit_index, ending_bit_index=None):
        """
        Get a bit or set of bits from a hex value

        :param value: Integer value to be operated on.
        :type: int
        :param beginning_bit_index: if range of bits, position of first bit to be evaluated.  If a single bit, this is
        the position of the bit that is to be evaluated.
        :type: int
        :param ending_bit_index:  if range of bits, the position of hte last bit to be evaluated.  If a single bit, this
        value is not required.
        :type: int
        :return: return value of the bit or bits.
        :rtype: int
        """

        if ending_bit_index is None:
            ending_bit_index = beginning_bit_index

        mask = (1 << (ending_bit_index - beginning_bit_index + 1)) - 1
        value >>= beginning_bit_index
        return int(value & mask)

    @classmethod
    def is_bit_set(cls, value, bit):
        """
        Bitwise operation to check if the bit in the given is set or cleared.

        :param value: Integer value to be operated on.
        :type: int
        :param bit: Bit to verify, starting at the right most bit of the integer being '0'.
        :type: int
        :return: True if bit is set (is equal to 1), False if bit is cleared (is equal to 0).
        :rtype: bool
        """
        return bool((value >> bit) & 1)
