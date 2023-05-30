#!/usr/bin/env python
###############################################################################
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
###############################################################################

import os
import re

from montana.nativemodules import chassiscontrol

from src.lib.common_content_lib import CommonContentLib


class ChassisControl(object):
    """
    This Class is Used to Control the System using Chassis
    """
    _MIV_LOG_FILE = "MEpythonlog.csv"
    _REGEX_FOR_POWER_UP = r"Powering\sUp"
    _REGEX_FOR_POWER_DOWN = r"Powering\sDown"
    _REGEX_FOR_POWER_CYCLE = r"Power\sCycle"
    _REGEX_FOR_HARD_RESET = r"Hard\sReset"
    _REGEX_FOR_SOFT_SHUTDOWN = r"Soft\sShutdown"
    POWER_OFF = r'off'
    POWER_ON = r'on'
    POWER_CYCLE = r'cycle'
    HARD_RESET = r'reset'
    SOFT_SHUTDOWN = r'softoff'

    def __init__(self, log, montana_log_path, os_obj):
        """
        Creates an Instance of ChassisControl

        :param log: log_object
        :param montana_log_path: montana_log_file path available in log_dir of TC.
        :param os_obj: Os object for all OS related Operations.

        """
        self._log = log
        self.dtaf_montana_log_path = montana_log_path
        self._os = os_obj
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.miv_log_file = os.path.join(self.cwd, self._MIV_LOG_FILE)
        self.chassis_cntrl_obj = chassiscontrol.chassiscontrol()
        self._common_content_lib = CommonContentLib(self._log, self._os, None)

    def chassis_control(self, control):
        """
        This Method is Used to Control the Chassis

        :param control: To Control the System Power
        :raise RuntimeError: If System Power is not as desired
        """
        if os.path.isfile(self.miv_log_file):
            os.remove(self.miv_log_file)
        self.chassis_cntrl_obj.control = control
        self._common_content_lib.execute_cmd_on_host("python {} --{}".format(chassiscontrol.__file__, control),
                                                     cwd=self.cwd)
        with open(self.miv_log_file, "r") as log_file:
            log_file_list = log_file.readlines()
            with open(self.dtaf_montana_log_path, "a") as montana_log:
                montana_log.write("".join(log_file_list))
            if control == self.POWER_ON:
                if re.findall(self._REGEX_FOR_POWER_UP, "".join(log_file_list)):
                    self._log.info("System is Powering Up")
                else:
                    log_error = "Power On is Not Applied to System"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
            elif control == self.POWER_OFF:
                if re.findall(self._REGEX_FOR_POWER_DOWN, "".join(log_file_list)):
                    self._log.info("System is Powering Down")
                else:
                    log_error = "Power Off is Not Applied to System"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
            elif control == self.POWER_CYCLE:
                if re.findall(self._REGEX_FOR_POWER_CYCLE, "".join(log_file_list)):
                    self._log.info("Power Cycle is Applied to System")
                else:
                    log_error = "Power Cycle is Not Applied to System"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
            elif control == self.HARD_RESET:
                if re.findall(self._REGEX_FOR_HARD_RESET, "".join(log_file_list)):
                    self._log.info("Hard Reset is Applied to System")
                else:
                    log_error = "Hard Reset is Not Applied to System"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
            elif control == self.SOFT_SHUTDOWN:
                if re.findall(self._REGEX_FOR_SOFT_SHUTDOWN, "".join(log_file_list)):
                    self._log.info("Soft Shutdown is Applied to System")
                else:
                    log_error = "Soft Shutdown is Not Applied to System"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
