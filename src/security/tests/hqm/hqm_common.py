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

import re

from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral


class HqmBaseTest(ContentBaseTestCase):
    """
    Base class extension for HqmBaseTest which holds common functions.
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of sut HqmBaseTest.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(HqmBaseTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._platform = self._common_content_lib.get_platform_family()
        if self._platform != ProductFamilies.SPR:
            raise content_exceptions.TestFail("HQM Tool required SPR Platform")

    def prepare(self):
        # type: () -> None
        """
        Prepeare the test setup.
        """
        super(HqmBaseTest, self).prepare()
        # Setting date and time
        self._common_content_lib.set_datetime_on_linux_sut()

    def install_hqm_driver_libaray(self):
        """
        This function installing the hqm driver library in sut
        """
        # install hqm driver library
        self._install_collateral.install_hqm_driver()

    def verify_hqm_dlb_kernel(self):
        """
        This function verify the HQM kernel driver in the sut.
        Remove the hqmv2 driver
        """
        regex_kernel_driver = r"Kernel driver in use:\s(.*)"
        lspci_dlb_kernel_cmd = "lspci -v -d :2710"
        hqm_kernel = "hqmv2"
        rmmod_cmd = "rmmod"
        self._log.info("Verify the hqm kernel driver used in the sut")
        cmd_output = self._common_content_lib.execute_sut_cmd(lspci_dlb_kernel_cmd, "find the Kernel driver in use"
                                                                                    " the sut", self._command_timeout)
        self._log.debug("lspci command output results {}".format(cmd_output))
        available_kernel_driver = re.findall(regex_kernel_driver, "".join(cmd_output))
        self._log.debug("Present kernel driver in the sut {}".format(available_kernel_driver))
        if not available_kernel_driver:
            self._log.debug("{} kernel driver not available".format(hqm_kernel))
            return
        for kernel_item in available_kernel_driver:
            if kernel_item == hqm_kernel:
                self.os.execute(rmmod_cmd + " " + hqm_kernel, self._command_timeout)
                self._log.info("Removed the hqmv2 kernel driver from the sut")
                return

    def execute_ldb_traffic(self):
        """
        This function execute ldb_traffic command and verify the tx/rx data events

        :raise: content_exceptions.TestFail If not getting expected tx/rx data events
        """
        find_libldb_dir = "find $(pwd) -type d -name 'libdlb'"
        export_cmd = r"export LD_LIBRARY_PATH="
        examples_folder = "/examples/"
        self._log.info("Execute ldb_traffic command")
        libdlb_dir_path = self._common_content_lib.execute_sut_cmd(find_libldb_dir, "find the libdlb dir in the sut",
                                                                   self._command_timeout)
        self._log.debug("libdlb dir path {}".format(libdlb_dir_path.strip()))
        ldb_traffic_result = self._common_content_lib.execute_sut_cmd((export_cmd + libdlb_dir_path.strip()) + " " +
                                                                      "&&" + " " + (libdlb_dir_path.strip() +
                                                                                    examples_folder +
                                                                                    self.LDB_TRAFFIC_FILE_CMD),
                                                                      "execute ldb traffic command",
                                                                      self._command_timeout)
        self._log.debug("ldb traffic command results {}".format(ldb_traffic_result))
        ldb_tx_traffic = re.search(self.REGEX_TX, ldb_traffic_result)
        ldb_rx_traffic = re.search(self.REGEX_RX, ldb_traffic_result)
        if not (ldb_tx_traffic and ldb_rx_traffic):
            raise content_exceptions.TestFail("Failed to get the TX/RX data events")
        if (ldb_tx_traffic.group(1) != self._ldb_traffic_data) and (ldb_rx_traffic.group(1) != self._ldb_traffic_data):
            raise content_exceptions.TestFail("Failed to get the ldb_traffi TX/RX data events")
        self._log.info("The ldb traffic run successfully without any errors")

