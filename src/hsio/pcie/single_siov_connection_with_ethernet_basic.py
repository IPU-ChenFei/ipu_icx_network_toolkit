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

from src.hsio.pcie.siov_connection_common import SiovConnectionCommon


class SingleSiovConnectionWithEthernetBasic(SiovConnectionCommon):
    """
    Phoenix ID: 22014383316

    The purpose is to test for SIOV compatibility with an ethernet endpoint using an MDEV system device.

    Note: please make the required driver in the SUT
    Also add the nic driver module for siov interface (eg - ice,i40e) at "ras/sut_nic_driver_module_name"
    """
    TEST_CASE_ID = ["22014383316", "Single SIOV connection with ethernet endpoint: basic case"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a SingleSiovConnectionWithEthernetBasic object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SingleSiovConnectionWithEthernetBasic, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        prepare
        1. enable iommu.
        2. create mdev.
        """
        super(SingleSiovConnectionWithEthernetBasic, self).prepare()

    def execute(self):
        """
        This method is to execute:

        1. attach SIOV to VM.
        2. check iavf interface in VM

        :return: True or False
        """
        status = super(SingleSiovConnectionWithEthernetBasic, self).execute()
        self._log.info("Shutdown VM immediately")
        self.vm_os_obj.execute(self.SHUTDOWN_VM, self._command_timeout)
        return status

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        2. Destroy mdev
        """
        super(SingleSiovConnectionWithEthernetBasic, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SingleSiovConnectionWithEthernetBasic.main() else Framework.TEST_RESULT_FAIL)
