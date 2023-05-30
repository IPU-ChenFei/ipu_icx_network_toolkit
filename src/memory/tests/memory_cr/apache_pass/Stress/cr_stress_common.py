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

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.bios_util import BiosUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.os_lib import WindowsCommonLib
from src.lib.windows_event_log import WindowsEventLog
from src.lib.content_configuration import ContentConfiguration
from src.lib.fio_utils import FIOCommonLib


class CrStressTestCommon(BaseTestCase):
    """
    Base class for all CR stress related test cases with Interleaved or Non-Interleaved memory mode.
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        super(CrStressTestCommon, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self.windows_home_drive_path = None
        self.store_generated_dcpmm_drive_letters = []

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._fio_runtime = self._common_content_configuration.memory_fio_run_time()
        self._dc_on_time = self._common_content_configuration.memory_dc_on_time()

        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

        self.ipmctl_cmd_name = self._common_content_lib.get_ipmctl_name()

        self._os_lib = WindowsCommonLib(self._log, self._os)
        self._windows_event_log = WindowsEventLog(self._log, self._os)

        self._fio_common_lib = FIOCommonLib(self._log, self._os, cfg_opts)

    def create_fiotest_drive_letters(self, list_drive_letters):
        """
        Function to create a list of drive letters concatenated with fiotest string.

        :param list_drive_letters: pmem drives
        """
        letter_list = []
        self.store_generated_dcpmm_drive_letters = list_drive_letters
        for drive_ltr in self.store_generated_dcpmm_drive_letters:
            letter_list.append(r"{}\:fiotest".format(drive_ltr))

        test_drives = ":".join(letter_list)

        return test_drives

    def verify_pmem_disk_size(self, pmem_disk_output):
        """
        Function to verify the pmem disk sze is larger than the mentioned size in the test case.

        :param pmem_disk_output: persistent memory output
        :return ret_val: a list of values based on the comparision on sizes of disks.
        """
        size_pattern = r"\d*\sGB|\d*\sTB|\d*\sPB|\d*\sEB"
        pmem_sizes_in_gb = re.findall(size_pattern, pmem_disk_output)

        # To get only numeric from a list element has both numeric and strings.
        pmem_sizes_list_in_gb = list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])),
                                         pmem_sizes_in_gb))

        res_size = []

        for size in pmem_sizes_list_in_gb:
            if size > 10:
                res_size.append(True)
            else:
                res_size.append(False)

        if all(res_size):
            self._log.info("The pmem volume(s) are larger than 10GB.")
        else:
            self._log.error("Not all the pmem volume(s) are larger than 10GB.")

        return all(res_size)

    def get_ipmctl_error_logs(self, ipmctl_path, *err_type):
        """
        Function to get the error logs for media and thermal using ipmctl commands.

        :param ipmctl_path: where the logs will generate.
        :param err_type: will hold the error types.
        :return None
        """
        for err_tp in err_type:
            cmd_run = self.ipmctl_cmd_name + " show -error {} -dimm > {}.log".format(err_tp, err_tp)

            self._common_content_lib.execute_sut_cmd(cmd_run, "Get {} error".format(err_tp),
                                                     self._command_timeout, ipmctl_path)

    def verify_ipmctl_error(self, err_type, log_path):
        """
        Function to check whether we find any Media or Thermal error on the dimms

        :param err_type: will hold the error type.
        :param log_path: log file path
        :return ret_val: false if error else true
        """
        ret_val = True

        with open(log_path, "r") as ipmctl_file:
            if "{} Error occurred".format(err_type) in ipmctl_file.read():
                self._log.error("Error has encountered on dimms, please check the '{}' "
                                "for more information.".format(log_path))
                ret_val = False
            else:
                self._log.info("There are no '{}' errors in log stored under '{}'".format(err_type, log_path))

        return ret_val
