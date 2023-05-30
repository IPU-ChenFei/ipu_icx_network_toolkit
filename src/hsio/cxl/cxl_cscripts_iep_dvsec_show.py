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
import os


from src.lib import content_exceptions
from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.cxl.cxl_common import CxlCommon


class CxlCscriptsIepDvsecShow(CxlCommon):
    """
    hsdes_id :  22014971523 CXL Cscripts cxl. command "cxl.cxl_iep_dvsec_show()
    This test exercises the new Cscript "cxl." command to read the the CXL device's Integrated Endpoint DVSEC
    register and cross verifies the settings with busybox devmem.

    Note: install Busybox on SUT
    """
    CXL_BIOS_KNOBS = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), "cxl_common_bios_file.cfg")

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=CXL_BIOS_KNOBS):
        """
        Create an instance of CxlCscriptsIepDvsecShow.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCscriptsIepDvsecShow, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCscriptsIepDvsecShow, self).prepare()

    def execute(self):
        """
        Method covers
        Running cxl method "cxl_iep_dvsec_show" from cscripts. Also verify values of registers form busybox.
        
        """
        self._log.info("Checking whether busybox installed or not...")
        if not self._common_content_lib.execute_sut_cmd("rpm -qa busybox", "Command to check busybox installation status",
                                                        self._command_timeout):
            raise content_exceptions.TestFail("Busybox tool not installed, please install and run again")
        cxl_inventory_dict = self.get_cxl_device_inventory()
        for key, value in cxl_inventory_dict.items():
            for port in value:
                if port:
                    cxl_addr_value_dict = self.get_dvsec_address_value_pair("cxl_iep_dvsec_show", key, port)
                    if not self.verify_addr_value_from_busybox(cxl_addr_value_dict):
                        return False
                    self._log.info("Test passed for cxl device at socket-{} port-{}".format(key, port))
                self.sdp.go()
        self._log.info("Test passed for cxl devices")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCscriptsIepDvsecShow.main() else
             Framework.TEST_RESULT_FAIL)
