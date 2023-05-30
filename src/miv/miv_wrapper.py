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

import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.miv.miv_common import MivCommon
import src.lib.content_exceptions as content_exceptions


class MivWrapper(MivCommon):
    """
    Montana wrapper
    """
    BIOS_CONFIG_FOLDER = "bios_config"

    DICT_BIOS_CONFIG_FILES = {"bios_ht_disable.cfg": r"src\miv\bios_config\bios_ht_disable.cfg",
                              "bios_ht_enable.cfg": r"src\miv\bios_config\bios_ht_enable.cfg",
                              "bios_error_inj_enable.cfg": r"src\miv\bios_config\bios_error_inj_enable.cfg",
                              "einj_mem_biosknobs.cfg": r"src\ras\tests\einj_tests\einj_mem_biosknobs.cfg",}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MivCommon object

        :param test_log: Used for debug and info messages
        """
        self.use_ping = True
        self.use_getdeviceid = True

        super(MivWrapper, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        super(MivWrapper, self).prepare()
        # set bios knobs if bios config file is passed as argument
        bios_config_file_path = self.get_bios_config_file()
        if bios_config_file_path is not None:
            self._bios_util.load_bios_defaults()
            self._log.info("Bios config file= '{}'".format(bios_config_file_path))
            self._bios_util.set_bios_knob(bios_config_file_path)
            self.set_default_bios = True # in cleanup function, bios knobs will be set to defaults
            # reboot the system for bios knobs to be effective
            self._common_content_lib.perform_graceful_ac_off_on(self._ac)
            self._log.info("Waiting for SUT to boot to OS..")
            self._os.wait_for_os(self._reboot_timeout)

    def get_bios_config_file(self):
        if not self.bios_config_file:
            self._log.debug("The bios config file is specified..")
            return None
        if str(self.bios_config_file).lower() not in self.DICT_BIOS_CONFIG_FILES.keys():
            log_error = "The specified bios config file '{}' is not valid.".format(self.bios_config_file)
            self._log.error(log_error)
            raise content_exceptions.TestUnSupportedError(log_error)
        file_rel_path = self.DICT_BIOS_CONFIG_FILES[self.bios_config_file]
        bios_file_path = os.path.join(self._common_content_lib.get_project_src_path(), file_rel_path)
        if not os.path.exists(bios_file_path):
            log_error = "The specified bios config file '{}' does not exists.".format(self.bios_config_file)
            self._log.error(log_error)
            raise content_exceptions.TestUnSupportedError(log_error)
        return bios_file_path

    def execute(self):
        result = self.run_montana_tdf(tdf_filename=self.tdf_filename, time=self.time)
        return result


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MivWrapper.main() else Framework.TEST_RESULT_FAIL)
