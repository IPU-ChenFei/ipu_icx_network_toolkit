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


class CxlCyclingAcReboot(CxlCyclingWarmReboot):
    """
    hsdes_id :  16016281810

    The purpose of this test is to verify the below register values through  cscripts during AC cycling.
    This is additional check in cycling content .

    pcie.get_data_link_layer_link_active(socket,port) : Returns True if the given port/link has an active Link Layer.

    pcie.get_current_link_speed(socket, port): Get the current speed of the given port/link (i.e., 5.0 as in Gen5)

    pcie.getBitrate(socket,port): Gets the speed rate of the link in GT/s

    cxl.in_cxl_mode(socket,port): Validates if  device is in CXL mode.

    cxl.get_device_type(socket, port): Gets device type in which the CXL device is operating with.

    cxl.get_cxl_version(socket, port): Gets CXL version in which the device was developed with.
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCyclingAcReboot.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCyclingAcReboot, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCyclingAcReboot, self).prepare()

    def execute(self, reboot_type="ac_cycle"):
        """
        This method is to perform AC cycling and  validating linkspeed, width speed, bitrate, cxl version etc.
        """
        super(CxlCyclingAcReboot, self).execute(reboot_type="ac_cycle")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCyclingAcReboot.main() else
             Framework.TEST_RESULT_FAIL)
