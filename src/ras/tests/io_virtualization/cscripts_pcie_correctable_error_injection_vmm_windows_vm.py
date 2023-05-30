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
import os
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.dtaf_content_constants import ErrorTypeAttribute
from src.provider.vm_provider import VMs

from src.ras.tests.io_virtualization.cscripts_pcie_error_injection_base_test import VmmCscriptsPcieErrorInjectionBaseTest

from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.lib import content_exceptions



class VmmCscriptsPcieCorrectableErrorInjectionVmmWindowsVm(VmmCscriptsPcieErrorInjectionBaseTest):
    """
    GLASGOW ID: G67417_W

    This test case walks you through how to do PCIE error injection to the platform.
    This will injecting Correctable Error to VMM with VMs running.
    """
    BIOS_CONFIG_FILE = "cscripts_error_injection_bios_config_file.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CscriptsPcieCorrectableErrorInjectionVmmWindowsVm object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(VmmCscriptsPcieCorrectableErrorInjectionVmmWindowsVm, self).__init__(test_log, arguments, cfg_opts,
                                                                                   bios_config_file=bios_config_file
                                                                                   )

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(VmmCscriptsPcieCorrectableErrorInjectionVmmWindowsVm, self).prepare()
        self._vm_provider_obj.install_vm_tool()


    def execute(self, err_type=ErrorTypeAttribute.CORRECTABLE, severity=None):
        """
        1. Create Cscripts, sdp obj
        2. create VM
        3. check VM is functioning or not
        4. Get Socket and Port
        5. Inject Correctable Error
        6. Verify Error Signature in OS.

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        super(VmmCscriptsPcieCorrectableErrorInjectionVmmWindowsVm, self).execute(ErrorTypeAttribute.CORRECTABLE, None)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        super(VmmCscriptsPcieCorrectableErrorInjectionVmmWindowsVm, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VmmCscriptsPcieCorrectableErrorInjectionVmmWindowsVm.main()
             else Framework.TEST_RESULT_FAIL)

