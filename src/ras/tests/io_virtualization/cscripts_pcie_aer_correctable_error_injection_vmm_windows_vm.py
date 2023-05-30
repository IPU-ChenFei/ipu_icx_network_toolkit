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
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.dtaf_content_constants import ErrorTypeAttribute
from src.provider.vm_provider import VMs

from src.ras.tests.io_virtualization.cscripts_pcie_error_injection_base_test import VmmCscriptsPcieErrorInjectionBaseTest

from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.lib import content_exceptions



class VmmCscriptsPcieAerCorrectableErrorInjectionVmmWindowsVm(VmmCscriptsPcieErrorInjectionBaseTest):
    """
    GLASGOW ID: G68649_W

    The premise of this test case is to test out PCIE error injection with AER disabled and enabled.
    OS should output accordingly if the errors come from AER or not based on BIOS knob.
    This will require an OS with virtualization function enabled
    """
    BIOS_CONFIG_FILE = "cscripts_error_injection_bios_config_file.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VmmCscriptsPcieAerCorrectableErrorInjectionVmmWindowsVm object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(VmmCscriptsPcieAerCorrectableErrorInjectionVmmWindowsVm, self).__init__(test_log, arguments, cfg_opts,
                                                                                   bios_config_file=bios_config_file
                                                                                   )

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(VmmCscriptsPcieAerCorrectableErrorInjectionVmmWindowsVm, self).prepare()
        self._vm_provider_obj.install_vm_tool()


    def execute(self, err_type=ErrorTypeAttribute.CORRECTABLE, severity=None):
        """
        1. execute correctable test
        2. Enable bios knob - OsNativeAerSupport
        3. Perform G3
        4. execute correctable aer test

        :param err_type : type of error to inject (ce / nce)
        :severity: error severity (fatal / non fatal)
        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        super(VmmCscriptsPcieAerCorrectableErrorInjectionVmmWindowsVm, self).execute(ErrorTypeAttribute.CORRECTABLE, None, 0)
        self._log.info("Enable bios knob, OS Native AER Support")
        self.bios_util.set_single_bios_knob("OsNativeAerSupport", "0x01")

        self._log.info("Powercycle the SUT for the BIOS changes to take effect.")
        self.perform_graceful_g3()

        super(VmmCscriptsPcieAerCorrectableErrorInjectionVmmWindowsVm, self).execute(
            ErrorTypeAttribute.CORRECTABLE_AER, None, self.num_vms)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        self.num_vms += self.num_vms
        super(VmmCscriptsPcieAerCorrectableErrorInjectionVmmWindowsVm, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VmmCscriptsPcieAerCorrectableErrorInjectionVmmWindowsVm.main()
             else Framework.TEST_RESULT_FAIL)

