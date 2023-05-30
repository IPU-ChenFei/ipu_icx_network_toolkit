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
"""Provides a class which can be used to create test case deployment XML file.

    Typical usage example:
        test_case_xml_tool = TestCaseXmlTool()
        test_case_xml_tool.create_test_case_xml(xml_path)
"""
import glob
import os
from xml.dom import minidom

class TestCaseXmlTool:
    """A class which can be used to create test case deployment XML file."""
    CONTENT_DIR = "/tests/agent/**"

    def create_test_case_xml(self, xml_dir: str) -> None:
        """Create a test case xml file for deployment.

        Args:
            xml_dir: The directory to create the test case xml file.
        """
        root = minidom.Document()
        test_cases = root.createElement('TestCases')
        root.appendChild(test_cases)

        # Iterate through test directories to create test package categories.
        for script_folder in glob.glob(os.path.dirname(os.getcwd()) + self.CONTENT_DIR):
            if '__' in script_folder or '.' in script_folder: continue
            # Iterate through test cases to add them to the xml file.
            for script in glob.glob(script_folder + "/**/*.py", recursive=True):
                if '__' in script: continue
                test_case = root.createElement('TestCase')

                package_name = root.createElement('PackageName')
                package_name.appendChild(root.createTextNode(os.path.basename(script_folder)))
                test_case.appendChild(package_name)

                test_case_name = root.createElement('TestCaseName')
                test_case_name.appendChild(root.createTextNode(os.path.basename(script).replace('.py', '')))
                test_case.appendChild(test_case_name)

                command = root.createElement('Command')
                command.appendChild(root.createTextNode('python'))
                test_case.appendChild(command)

                arguments = root.createElement('Arguments')
                arguments.appendChild(root.createTextNode(script[script.index('src'):].replace('\\', '/')))
                test_case.appendChild(arguments)

                is_event = root.createElement('IsEvent')
                is_event.appendChild(root.createTextNode('false'))
                test_case.appendChild(is_event)

                out_path_as_param = root.createElement('PassOutputPathAsParameter')
                out_path_as_param.appendChild(root.createTextNode('true'))
                test_case.appendChild(out_path_as_param)

                out_path_param = root.createElement('OutputPathParameter')
                out_path_param.appendChild(root.createTextNode('-o'))
                test_case.appendChild(out_path_param)

                test_cases.appendChild(test_case)

        # Save the xml file at the provided directory.
        with open(xml_dir, "w") as f:
            f.write(root.toprettyxml(indent="\t"))
