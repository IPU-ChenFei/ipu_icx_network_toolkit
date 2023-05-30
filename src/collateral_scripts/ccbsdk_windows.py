#!/usr/bin/env python
###############################################################################
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
# otherwise. Any license under such intellectual property rights must be
# express and approved by Intel in writing.
###############################################################################

import getopt
import sys


class WindowsCcbHwApi(object):

    def __init__(self):
        """
        Create an instance of WindowsCcbHwApi.
        """
        self.msr_read_dict = {}

    def read_msr(self, msr_address):
        """
        This Method is Used to Read MSR Value of a specific register.

        :param msr_address: Specific Register Address
        """
        import ccbhwapi as hw
        self.msr_read_dict = hw.read_msr(0, msr_address)
        print(self.msr_read_dict)


if __name__ == "__main__":
    try:
        hw_api_obj = WindowsCcbHwApi()
        try:
            # set up the arguments available to the user

            opts, args = getopt.getopt(sys.argv[1:], "r:hb:e:hb", ["read_msr", "execute"])

        except getopt.GetoptError as err:
            raise err

            # loop through the arguments passed by the user
        for o,a in opts:
            if o in ("-r", "--read_msr"):
                hw_api_obj.read_msr(int(args[0]))

    except Exception as ex:
        sys.exit(1)
