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
"""
    :UMA Memory Exclusivity:

    Verify TDX and UMA-Based Clustering cannot co-exist.
"""
import os
import sys
import logging
import argparse
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.private.cl_utils.adapter import data_types
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


class TDXUMAMemoryExclusivity(LinuxTdxBaseTest):
    """
            This recipe tests TDX compatibility with UMA-based clustering feature and is compatible with most OSes.
            The SUT must be equipped with CPUs which support TDX functionality.  The dimm population must support
            UMA; refer to memory POR documentation for the product for what is necessary to meet this need.

            :Scenario: Ensure UMA-based clustering feature cannot be enabled with TDX enabled and ensure UMA-based
            clustering can be enabled with TDX disabled.

            :Phoenix ID: 18014074002

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Enable TDX knobs.

                :3: Attempt to disable Numa.

                :4: Disable TDX and Numa.

            :Expected results: Numa cannot be disabled and UMA-based clustering cannot be enabled with TDX enabled.
            After TDX is disabled, Numa can be disabled and UMA-based clustering can be enabled.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of sut os provider, XmlcliBios provider, BIOS util and Config util
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(TDXUMAMemoryExclusivity, self).__init__(test_log, arguments, cfg_opts)
        self._NUMA_KNOB = "../collateral/numa_en_reference_knob.cfg"
        self._NUMA_DIS_KNOB = "../collateral/numa_dis_reference_knob.cfg"
        self._SNC_DIS_KNOB = "../collateral/snc_dis_reference_knob.cfg"

    def prepare(self):
        self.bios_util.load_bios_defaults()
        super(TDXUMAMemoryExclusivity, self).prepare()

    def execute(self):
        # verify Numa knob is enabled
        bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._NUMA_KNOB)
        try:
            self.check_knobs(bios_knob_file)
        except RuntimeError:
            raise RuntimeError("TDX is enabled, but Numa knob is not set to enable.")

        # check UMA is not enabled
        if self.uma_check():
            raise content_exceptions.TestError("UMA is enabled with TDX; this shouldn't be allowed.")

        # disable TDX, SGX, Numa, and SNC and reboot
        self._log.info("Disabling TDX, SGX, Numa, and SNC.")
        knob_settings = [self.tdx_bios_disable, self._NUMA_DIS_KNOB, self._SNC_DIS_KNOB]
        combined_bios_file = self.bios_file_builder(knob_settings)
        self.set_knobs(knob_file=combined_bios_file)

        # check UMA is enabled
        if not self.uma_check():
            raise content_exceptions.TestError("UMA is not enabled with TDX/SGX disabled.  Please verify dimm config "
                                               "can support UMA.")

        # verify TDX is not enabled
        if self.validate_tdx_setup():
            raise content_exceptions.TestFail("TDX was enabled with UMA enabled.")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDXUMAMemoryExclusivity.main() else Framework.TEST_RESULT_FAIL)
