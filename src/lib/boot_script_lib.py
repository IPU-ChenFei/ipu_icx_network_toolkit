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
import time
import threading
from xml.etree import ElementTree
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.dtaf_content_constants import BootScriptConstants
from src.lib.dtaf_content_constants import ProviderXmlConfigs


class BootScript(object):
    """
    Runs the boot script command from PythonSv
    """

    def __init__(self, log, sdp, ac, common_content_lib, cfg_opts):
        self._log = log
        self._sdp = sdp
        self._ac = ac
        self._common_content_lib = common_content_lib
        self._cfg = cfg_opts
        self._cpu = self._common_content_lib.get_platform_family()
        self._pch = self._common_content_lib.get_pch_family()

        sv_cfg = ElementTree.fromstring(ProviderXmlConfigs.PYTHON_SV_XML_CONFIG.format(self._cpu, self._pch))
        self._sv = ProviderFactory.create(sv_cfg, self._log)  # type: SiliconRegProvider

        self._log_path = self._common_content_lib.get_log_file_dir()
        self._bootscript_file_path = os.path.join(self._log_path, BootScriptConstants.BOOTSCRIPT_LOG_FILE_NAME)
        Path(self._bootscript_file_path).touch()
        # start the boot script logs
        self._sdp.start_log(self._bootscript_file_path)

    def parse_boot_script_log(self, bs_log_file_path):
        """
        This function parses the boot scrip log, power-off and power-on SUT.

        :return: None.
        """
        obj_log_file = open(bs_log_file_path, 'r')

        time_end = time.time() + BootScriptConstants.POWER_OFF_ON_TRIGGER_WAIT_TIME
        bs_log = ""
        power_off_trigger = False
        while time.time() < time_end:
            # search for power_off pattern
            bs_log = bs_log + str(obj_log_file.readlines())
            if BootScriptConstants.POWER_OFF_PATTERN in str(bs_log):
                power_off_trigger = True
                break
            time.sleep(0.2)

        if power_off_trigger:
            self._log.info("Got the trigger for SUT power off and powering off the SUT...")
            ret_val = self._ac.ac_power_off(5)
            self._log.info("AC power off ret val='{}'".format(ret_val))
        else:
            self._log.error("Did not get the trigget for SUT power off...")

        power_on_trigger = False
        time_end = time.time() + BootScriptConstants.POWER_OFF_ON_TRIGGER_WAIT_TIME
        while time.time() < time_end:
            # search for power_off pattern
            bs_log = bs_log + str(obj_log_file.readlines())
            if BootScriptConstants.POWER_ON_PATTERN in str(bs_log):
                power_on_trigger = True
                break
            time.sleep(0.2)

        if power_on_trigger:
            self._log.info("Got the trigger for SUT power on and powering on the SUT...")
            ret_val = self._ac.ac_power_on(5)
            self._log.info("AC power on ret val='{}'".format(ret_val))
        else:
            self._log.error("Did not get the trigget for SUT power off...")

    def is_booscript_required(self):
        """
        This function checks if bootscript is required to boot the system

        :return: str - True if bootscript required else False
        """
        try:
            list_stepping = BootScriptConstants.SILICON_REQUIRES_BOOTSCRIPT[self._cpu]
            # get the target stepping info
            self._sv.refresh()
            sockets = self._sv.get_sockets()
            stepping = sockets[0].uncore.target_info.stepping
            self._log.info("Platform='{}' and stepping='{}'".format(self._cpu, stepping))
            if stepping and str(stepping).upper() in str(list_stepping).upper():
                self._log.info("The bootscript is required for this target..")
                return True
            self._log.info("The bootscript is not required for this target..")
            return False
        except Exception as ex:
            stepping = None
            self._log.error("Failed to get stepping info due to exception '{}'".format(ex))
        return False

    def run_boot_script(self):
        """
        This function will run the boot script go from PythonSV.

        :return: boolean - True if boot script is passed else False.
        """
        # first check if we need to run boot script
        if not self.is_booscript_required():
            print("Bootscript not required for this target.")
            return True

        # get the boot script object
        bs = self._sv.get_bootscript_obj()

        sut_power_cycle_thread = threading.Thread(target=self.parse_boot_script_log,
                                                  args=(self._bootscript_file_path,))
        # start the thread to ac power off and on by parsing boot script log file
        sut_power_cycle_thread.start()

        self._log.info("Starting boot script...")
        bs.go(warm_reset_timeout=200)  # with log level > normal, need additional timeout for warm_reset
        self._sdp.stop_log()
        self._log.info("Boot script execution complete and refer to log file '{}' for more "
                  "details.".format(self._bootscript_file_path))

        # read boot script log
        obj_log_file = open(self._bootscript_file_path, 'r')
        bs_log = str(obj_log_file.readlines())
        if BootScriptConstants.BOOT_SCRIPT_PASSED not in bs_log:
            self._log.error("Boot script failed...")
            return False

        self._log.info("Boot script passed without any errors..")
        return True

