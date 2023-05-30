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
"""A script which can be used to create a deployable content framework zip folder.

    Typical usage example:
        This script is called directly to perform packaging.
"""

import shutil
import os
import zipfile
from datetime import date
from src.sdsi.deployment.make_test_cases import TestCaseXmlTool

if __name__ == "__main__":
    # Create test cases xml
    test_case_xml_tool = TestCaseXmlTool()
    xml_path = 'testCases.xml'
    test_case_xml_tool.create_test_case_xml(xml_path)

    # Zip content framework
    framework_name = 'dtaf-sdsi-' + date.today().strftime("%b-%d-%Y")
    folder_format = 'zip'
    root_dir = '../../../'
    base_dir = 'src/sdsi'
    shutil.make_archive(framework_name, folder_format, root_dir, base_dir)
    framework_name += '.' + folder_format
    print(f"Created {framework_name} content {folder_format} at {os.getcwd()}")

    # Add test case xml to zipped framework
    zipped_framework = zipfile.ZipFile(framework_name, 'a')
    zipped_framework.write(xml_path)
    zipped_framework.close()

    # Remove test case xml from deployment folder
    os.remove(xml_path)
