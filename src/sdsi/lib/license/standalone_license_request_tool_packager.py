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
"""Creates a standalone exe file for the license request GUI tool.

    Typical usage example:
        This module is currently meant to be run as a script.
        When executed, a standalone exe file for the license request GUI tool is created at the current directory.
"""
import os
import shutil


if __name__ == "__main__":
    os.system('pyinstaller -F sdsi_license_request_gui.py')
    shutil.rmtree('build', ignore_errors=True)
    os.remove('sdsi_license_request_gui.spec')
    shutil.move('dist/sdsi_license_request_gui.exe', 'sdsi_license_request_gui.exe')
    shutil.rmtree('dist', ignore_errors=True)
