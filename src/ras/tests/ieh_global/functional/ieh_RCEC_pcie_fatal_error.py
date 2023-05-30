#!/usr/bin/env python
##########################################################################
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
##########################################################################


import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.ieh_global.functional.ieh_register_status_common import \
    IehCommon


class IehRcecPcieFatalError(IehCommon):
    """
    HSD ID: 22012815417 ieh_RCEC_pcie_fatal_error

    This test creates a unsupported request(UR) in the iax1 IP . The UR results in a Fatal error
    handled by IEH RCEC error flow.
    This test assumes that iax_bdf was provided in the content_configuration.xml.
    i.e. content_configuration.xml must have a new value: /ras/Iax_BDF
    """
    _BIOS_CONFIG_FILE = "ieh_RCEC_pcie_fatal_error_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new IehRcecPcieFatalError object,

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param arguments: None
        """
        super(IehRcecPcieFatalError, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """
        super(IehRcecPcieFatalError, self).prepare()

    def execute(self):
        """
        Calling multiple functions to check the occurrence of Fatal errors after creating UR.

        :return: True if valid else False
        """

        self.determine_iax_bdf_and_device_id()
        self.update_linux_tolerants()

        # Error Print
        self._log.info("Checking for errors before test.")
        self.print_ieh_rcec_error_regs()

        self.adjust_iax_and_ieh_register_values()
        cmd = self.create_unsupported_req()

        # Printing Errors to see registers indicate UR and errors have occurred
        self._log.info("Checking for errors to Verify registers indicate UR and errors have occurred.")
        self.print_ieh_rcec_error_regs()

        self.resume_cores_after_ur_verification(cmd)

        return self.check_ieh_RCEC_pcie_fatal_error()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if IehRcecPcieFatalError.main()
             else Framework.TEST_RESULT_FAIL)
