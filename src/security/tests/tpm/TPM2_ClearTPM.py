#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.private.cl_utils.adapter import data_types
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.bios_util import BootOptions, SerialBiosUtil
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from collections import OrderedDict
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.provider.host_usb_drive_provider import HostUsbDriveProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider
from src.lib.dtaf_content_constants import UefiTool
from src.lib.bios_util import ItpXmlCli
from src.lib.dtaf_content_constants import TimeConstants


class ClearTpm(TxtBaseTest):
    """
    Phoenix ID : 18014072192-TPM 2.0 - Clear TPM

    Verifies the PCR4 value will be changed due to UEFI boot service change.
    """
    BIOS_BOOTMENU_CONFIGPATH = "suts/sut/providers/bios_setupmenu"
    TEST_CASE_ID = ["18014072192", "TPM 2.0 - Clear TPM"]
    STEP_DATA_DICT = {1: {'step_details': 'Locate "TPM2 Physical Presence Operation" option to clear the ownership contents.Change the value from No Actionto TPM2 Clear',
                          'expected_results': 'Eaglestream Platforms and later:Platform does not request user action to clear the TPM.'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of ClearTPM
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ClearTpm, self).__init__(test_log, arguments, cfg_opts)

        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._bios_boot_util = SerialBiosUtil(self._ac_obj, test_log, self._common_content_lib, cfg_opts)
        self.bios_set_menu_cfg = cfg_opts.find(self.BIOS_BOOTMENU_CONFIGPATH)
        self._bios_setup_menu_obj = ProviderFactory.create(self.bios_set_menu_cfg, self._log)  # type: # BiosSetupMenuProvid
        self.enter_bios_path_order0 = OrderedDict([(r"EDKII Menu", data_types.BIOS_UI_DIR_TYPE),
                                                   (r"TCG2 Configuration", data_types.BIOS_UI_DIR_TYPE)])
        self.SECURE_BOOT_CONFIGURATION = 'TPM2 Operation'

    def prepare(self):
        # type: () -> None
        """
        Using fTPM 2.0:
        1.Please complete TC "Enabling fTPM on a system" before running this test.
        """
        self._test_content_logger.start_step_logger(1)
        super(ClearTpm, self).prepare()
        # Verify TPM present or not
        self.verify_tpm()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        After "Preparation" procedure is completed, boot to System Setup (BIOS) and navigate to the Security screen.

        Locate "TPM2 Physical Presence Operation" option to clear the ownership contents.
        --Change the value from "No Action" to "TPM2 Clear"

        Save the changes with F10 and reboot the system.

        :raise: Test fail exception if SUT failed to boot in UEFI shell
        :raise: content Exception if PCR 4 values are same
        :return: True if both the version has different pcr 04 value
        """
        if not self._bios_boot_util.navigate_bios_menu():
            raise RuntimeError("log_error")
        self._log.info("=====================Entering BIOS Menu=======================")
        self._bios_boot_util.select_enter_knob(self.enter_bios_path_order0)
        self._bios_boot_util.set_bios_knob(self.SECURE_BOOT_CONFIGURATION, data_types.BIOS_UI_OPT_TYPE, "TPM2 ClearControl(NO) + Clear")
        self._bios_boot_util.save_bios_settings()
        self.perform_graceful_g3()
        if not self._os.os_type == OperatingSystems.LINUX:
            log_error = "This test case only applicable for Linux system"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        #self._test_content_logger.end_step_logger(2, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(ClearTpm, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ClearTpm.main() else Framework.TEST_RESULT_FAIL)
