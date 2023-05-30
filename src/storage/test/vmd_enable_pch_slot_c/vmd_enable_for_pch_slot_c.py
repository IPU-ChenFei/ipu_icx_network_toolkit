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
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.bios_constants import BiosSerialPathConstants
from src.lib.bios_util import SerialBiosUtil
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions


class VMDEnableForPchSlotC(ContentBaseTestCase):
    """
    Phoenix ID : P16013565012-Verify system booting with VMD enable for PCH(Slot C) for Rhel OS and
                 P16013544699-Verify system booting with VMD enable for PCH(Slot C) for Centos OS
    This testcase is to verify system with RHEL/Centos OS installed boots successfully with PCH slot for
    HHHL is enabled in bios
    """
    BIOS_CONFIG_FILE = "vmd_enable_for_pch_slot_c.cfg"
    DEVICE_NAME = 'Pcie_Device_Name'
    PCH_STR = "(PCH)"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VMDEnableForPchSlotC object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VMDEnableForPchSlotC, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self.product_family = self._common_content_lib.get_platform_family()

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(VMDEnableForPchSlotC, self).prepare()

    def execute(self):
        """
        verify system with RHEL OS or Centos installed boots successfully with PCH slot for HHHL is enabled in bios

        :return: True
        :raise: If driver verification failed raise content_exceptions.TestFail
        """
        slot_c_info = self._common_content_configuration.get_pch_slot_c_info(self.product_family)
        self._log.info("PCIE NVME Drive connected to Slot C is {}".format(slot_c_info[self.DEVICE_NAME]))
        self._log.info("Navigating to the BIOS Page")
        status, ret_val = self._serial_bios_util.navigate_bios_menu()
        if not status:
            content_exceptions.TestFail("Bios Knobs did not navigate to the Bios Page")

        serial_path = BiosSerialPathConstants.INTEL_VROC_NVME_CONTROLLER[self.product_family.upper()]
        self._serial_bios_util.select_enter_knob(serial_path)
        screen_info = self._serial_bios_util.get_current_screen_info()
        self._log.debug("Intel VROC VMD Controller output is {}".format(screen_info))
        flag = 0
        for each_line in screen_info[0]:
            if re.search(slot_c_info[self.DEVICE_NAME], each_line):
                index_value = screen_info[0].index(each_line)
                if re.search(self.PCH_STR, screen_info[0][index_value + 1]):
                    self._log.info("SLOT C connected drive {} and drive detect under VROC VMD controller {} are same".
                                   format(slot_c_info[self.DEVICE_NAME], each_line))
                    flag += 1
                    break
        if flag == 0:
            raise content_exceptions.TestFail("SLOT C connected drive {} not detected under VROC VMD controller".
                                              format(slot_c_info[self.DEVICE_NAME]))
        self._serial_bios_util.go_back_a_screen()
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("Waiting for SUT to boot to OS..")
        self.os.wait_for_os(self.reboot_timeout)
        self._log.info("System boot to RHEL/Centos OS successfully with PCH slot enabled")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VMDEnableForPchSlotC.main() else Framework.TEST_RESULT_FAIL)
