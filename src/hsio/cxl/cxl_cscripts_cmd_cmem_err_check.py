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


class CxlCscriptsCmdCmemErrCheck(CxlCommon):
    """
    hsdes_id :  14016472256 CXL Cscripts cxl. command "cmem_err_check"
    This test exercises the new "cxl." command set in Cscripts, specifically the command "cmem_err_check" which
    displays various aspects of memory error logging and correction.

    """
    CXL_BIOS_KNOBS = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), "cxl_common_bios_file.cfg")

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=CXL_BIOS_KNOBS):
        """
        Create an instance of CxlCscriptsCmdCmemErrCheck.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCscriptsCmdCmemErrCheck, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCscriptsCmdCmemErrCheck, self).prepare()

    def execute(self):
        """
        Method covers
        Running cxl method "cmem_err_check" from cscripts. Also check for any error
        
        """
        cxl_inventory_dict = self.get_cxl_device_inventory()
        return self.cxl_cmem_err_check(cxl_inventory_dict)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCscriptsCmdCmemErrCheck.main() else
             Framework.TEST_RESULT_FAIL)
