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

import sys


class WindowsCcbPackage(object):

    def __init__(self):
        pass

    def dsl_get_device_list(self):
        """
        This method is to get the device List.

        :return dict
        """
        try:
            import DeviceStackList as obj
            return obj.get_device_list()
        except ImportError:
            raise ImportError("Please check DeviceStackList package is installed on SUT.")

    def dsl_checkforYellowBang(self, devProperty, devPropertyType):
        """
        This method is to check the driver is enable or not in device manager.

        :return True or False
        """
        try:
            import DeviceStackList as obj
            return obj.checkforYellowBang(devProperty, int(devPropertyType))
        except ImportError:
            raise ImportError("Please check DeviceList package is installed on SUT.")


if __name__ == "__main__":
    try:
        windows_ccb_obj = WindowsCcbPackage()
        arg_list = sys.argv[1:]
        if len(arg_list) == 1:
            out_put = eval("windows_ccb_obj.{}()".format(arg_list[0]))
        elif len(arg_list) == 2:
            k = eval("windows_ccb_obj.{}".format(arg_list[0]))
            out_put = k(arg_list[1])
        elif len(arg_list) == 3:
            k = eval("windows_ccb_obj.{}".format(arg_list[0]))
            out_put = k(arg_list[1], arg_list[2])
        else:
            if not len(arg_list):
                print(r"No argument is passed....Please check")
                sys.exit(1)
            print("Please Add....not implemented for more than two arguments")
            sys.exit(1)
        print(out_put)
        sys.exit(0)
    except Exception as ex:
        print(ex)
        sys.exit(1)
