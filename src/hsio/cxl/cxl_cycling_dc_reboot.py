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
import time

from dtaf_core.providers.provider_factory import ProviderFactory

from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.cxl.cxl_cycling_warm_reboot import CxlCyclingWarmReboot
from src.lib import content_exceptions


class CxlCyclingDcReboot(CxlCyclingWarmReboot):
    """
    hsdes_id :  22014846322

    This test case will check the various registers and features on CXL for every cycling of the system.
    The checks are to ensure that the CLX device is consist in the mode, device type, CXL version, training speed,
    training width and CXL features that the device supports.

    The cScripts command used are below.

    cxl.in_cxl_mode(socketX, 'PCIePortX')
    cxl.get_device_type(socketX, 'PCIePortX')
    cxl.get_cxl_version(socketX, 'PCIePortX')
    pcie.get_current_link_speed(socketX, 'PCIePortX')
    pcie.get_negotiated_link_width(socketX, 'PCIePortX')
    pcie.getBitrate(socketX, 'PCIePortX')
    pcie.getCrcErrCnt(socketX, 'PCIePortX')
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCyclingDcReboot.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCyclingDcReboot, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCyclingDcReboot, self).prepare()

    def execute(self, reboot_type="ac_cycle"):
        """
        This method is to perform Warm cycling and  validating linkspeed, width speed, bitrate, cxl version etc.
        """
        super(CxlCyclingDcReboot, self).execute(reboot_type="dc_cycle")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCyclingDcReboot.main() else
             Framework.TEST_RESULT_FAIL)
