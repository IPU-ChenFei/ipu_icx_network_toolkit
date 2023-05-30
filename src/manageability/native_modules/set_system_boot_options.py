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


from montana.nativemodules import setsystembootoptions
from src.lib.common_content_lib import CommonContentLib


class SetSystemBootOptions(object):
    """
    This Class is Used to Boot the System to none/disk/bios
    """
    _MIV_LOG_FILE = "MEpythonlog.csv"
    _REGEX_FOR_BOOT_NONE = r"Set\sBoot\sDevice\sto\snone"
    _REGEX_FOR_BOOT_DISK = r"Set\sBoot\sDevice\sto\sdisk"
    _REGEX_FOR_BOOT_BIOS = r"Set\sBoot\sDevice\sto\sbios"
    SETBOOT_NONE = 'none'
    SETBOOT_DISK = 'disk'
    SETBOOT_BIOS = 'bios'

    def __init__(self, log, montana_log_path, os_obj):
        """
        Creates an Instance of SetSystemBootOptions

        :param log: log_object
        :param montana_log_path: montana_log_file path available in log_dir of TC.
        :param os_obj: Os object for all OS related Operations.
        """
        self._log = log
        self.dtaf_montana_log_path = montana_log_path
        self._os = os_obj
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.miv_log_file = os.path.join(self.cwd, self._MIV_LOG_FILE)
        self.set_boot_obj = setsystembootoptions.setsystembootoptions()
        self._common_content_lib = CommonContentLib(self._log, self._os, None)

    def set_boot_options(self, bootdev):
        """
        This Method is Used to Control the booting option of the system
        """
        if os.path.isfile(self.miv_log_file):
            os.remove(self.miv_log_file)
        self.set_boot_obj.bootdev = bootdev
        self._common_content_lib.execute_cmd_on_host("python {} --{}".format(setsystembootoptions.__file__, bootdev),
                                                     cwd=self.cwd)
        with open(self.miv_log_file, "r") as log_file:
            log_file_list = log_file.readlines()
            with open(self.dtaf_montana_log_path, "a") as montana_log:
                montana_log.write("".join(log_file_list))
            if bootdev == self.SETBOOT_NONE:
                if re.findall(self._REGEX_FOR_BOOT_NONE, "".join(log_file_list)):
                    self._log.info("System is set to none")
                else:
                    log_error = "System not set to none"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
            elif bootdev == self.SETBOOT_DISK:
                if re.findall(self._REGEX_FOR_BOOT_DISK, "".join(log_file_list)):
                    self._log.info("System is set to disk")
                else:
                    log_error = "System not set to disk"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
            elif bootdev == self.SETBOOT_BIOS:
                if re.findall(self._REGEX_FOR_BOOT_BIOS, "".join(log_file_list)):
                    self._log.info("System is set to bios")
                else:
                    log_error = "System not set to bios"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
