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

import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.virtualization.virtualization_common import VirtualizationCommon


class PiVirtualizationVirtualInterruptDeliveryL(VirtualizationCommon):
    """
    HPALM ID: H81075-PI_Virtualization_virtual_interrupt_delivery_L

    1. Run KVM Unit Test command
    2. Verify the expected output is present in the command result
    """
    TC_ID = ["H81075-PI_Virtualization_virtual_interrupt_delivery_L"]
    __BIOS_CONFIG_FILE = r"..\..\kvm_unittests_bios_knobs.cfg"
    __KVM_UNIT_TEST_EXPECTED_RESULT = "PASS: Virtualize interrupt-delivery"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationVirtualInterruptDeliveryL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiVirtualizationVirtualInterruptDeliveryL, self).__init__(test_log, arguments, cfg_opts,
                                                                        create_bridge=False)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))

    def prepare(self):  # type: () -> None
        self.bios_util.set_bios_knob(self.__BIOS_CONFIG_FILE)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self.bios_util.verify_bios_knob(self.__BIOS_CONFIG_FILE)

    def execute(self):
        """
        1. run KVM Unit Test command
        2. Verify the expected output is present in the command result
        """
        self.verify_kvm_unit_test_results(self.KVM_UNIT_TEST_VMX_COMMAND, self.__KVM_UNIT_TEST_EXPECTED_RESULT)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(PiVirtualizationVirtualInterruptDeliveryL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationVirtualInterruptDeliveryL.main()
             else Framework.TEST_RESULT_FAIL)
