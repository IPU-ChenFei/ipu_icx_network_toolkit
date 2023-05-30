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
import subprocess
import shutil

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.manageability.native_modules.get_device_id import GetDeviceId
from src.manageability.native_modules.chassis_control import ChassisControl
from src.manageability.native_modules.get_nm_capabilities import GetNMCapabilities
from src.manageability.native_modules.set_system_boot_options import SetSystemBootOptions


class ManageabilityCommon(ContentBaseTestCase):
    """
    Base class extension for ManageabilityCommon which holds common functionality
    """
    MONTANA_LOG_FILE = "montana_log.log"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of sut ManageabilityCommon.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ManageabilityCommon, self).__init__(test_log, arguments, cfg_opts)
        self.bmc_ip = cfg_opts.find("suts/sut/silicon/bmc/ip")
        self._log.info("Found BMC IP: " + self.bmc_ip.text)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self.dtaf_montana_log_path = os.path.join(self.log_dir, self.MONTANA_LOG_FILE)
        self.copy_montana_log_to_log_dir()
        self.get_dev_id_obj = GetDeviceId(self._log, self.dtaf_montana_log_path, self.os)
        self.chassis_cntrl_obj = ChassisControl(self._log, self.dtaf_montana_log_path, self.os)
        self.boot_options_obj = SetSystemBootOptions(self._log, self.dtaf_montana_log_path, self.os)
        self.get_nm_capabilities_obj = GetNMCapabilities(self._log, self.dtaf_montana_log_path, self.os)

    def verify_ip_connectivity(self):
        """
        This Method is Used to Verify the Connectivity of System and  Bmc by os.is_alive() method and Pinging Bmc IP
        Respectively.

        :raise: RunTimeError If the BMC Ip is not Reachable.
        """
        if self.os.is_alive():
            self._log.info("System is Up and Reachable")
            ping_command = r"ping " + self.bmc_ip.text
            result = subprocess.call(ping_command)
            self._log.info("ping result for ip '{}' = {}".format(self.bmc_ip.text, str(result)))
            if result != 0:
                self._log.error("Error - ping " + self.bmc_ip.text + " failed")
                raise RuntimeError("Error - ping " + self.bmc_ip.text + " failed")

            self._log.info("BmcIp is Pinging and Reachable")
        else:
            self._log.error("System is Not Up")
            raise RuntimeError("System is Not Up")

    def copy_montana_log_to_log_dir(self):
        """
        This Method is Used to Copy Montana Log to Log Directory.
        """
        self._log.info("Copying Montana Log file to Log Folder")
        with open(self.MONTANA_LOG_FILE, "w"):
            shutil.copy(self.MONTANA_LOG_FILE, self.log_dir)
