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
import time
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.provider_factory import ProviderFactory

import src.lib.content_exceptions as content_exception
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class CpuThrottlingPtuWorkloadUpiCrcLlr16b(IoPmCommon):
    """
    Glasgow_id : 70732.0 CPU thermal throttling + PTU workload + UPI CRC LLR error injection + OS log checks
    Requirement: cscripts_ei_pcie_device socket and pxp_port must be set in content_configuration.xml
    """

    _BIOS_CONFIG_FILE = "cpu_throttling_upi_llr_ei_bios_knobs.cfg"
    ERROR_INJECTION_DELAY_SEC = 30
    NUM_INJ = 30
    EI_SOCKET = 0

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new CpuThrottlingPtuWorkloadPcieCe object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        super(CpuThrottlingPtuWorkloadUpiCrcLlr16b, self).__init__(test_log,
                                                                   arguments,
                                                                   cfg_opts,
                                                                   self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(CpuThrottlingPtuWorkloadUpiCrcLlr16b, self).prepare()

    def execute(self):
        """
        PCIe UC error injection while thermal throttling with PTU workload and TCC Activation Offset.

        :return: True or False based on Test Case fail or pass.
        """
        self.install_ptu_on_sut_linux()
        self.ptu_execute_linux(self.PTU_CPU_TEST, self.PTU_WORKLOAD_TEST_DICT[self.product], duration_sec=0)
        initial_inj_count = 0
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            try:
                for i in range(self.NUM_INJ):
                    self._log.info("Starting injection number: " + str(i))
                    # check thermal throttling registers
                    therm_log_sts, therm_sts = self.get_thermal_monitor_log_reg(cscripts_obj, socket=self.EI_SOCKET)
                    if therm_log_sts == 0:
                        log_err = "Thermal log Status == {}!".format(therm_log_sts)
                        self._log.error(log_err)
                        raise content_exception.TestFail(log_err)
                    # inject error
                    initial_inj_count = self.inject_and_check_upi_error_single_injection(
                        cscripts_obj, init_err_count=initial_inj_count, socket=0, port=0)
                    if not self._os_log_obj.verify_os_log_error_messages(
                            __file__,
                            self._os_log_obj.DUT_JOURNALCTL_DMESG_SINCE_30_SECONDS,
                            self.UPI_MACHINE_CHECK_BOOTED_JOURNALCTL):
                        log_err = "Error not found in OS logs!"
                        self._log.error(log_err)
                        raise content_exception.TestFail(log_err)
                    time.sleep(self.ERROR_INJECTION_DELAY_SEC)

            except Exception as ex:
                self._log.error("Failed on injection: " + str(i))
                log_err = "An Exception Occurred : {}".format(ex)
                self._log.error(log_err)
                raise content_exception.TestFail(log_err)
            finally:
                self.ptu_kill_linux()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CpuThrottlingPtuWorkloadUpiCrcLlr16b.main() else Framework.TEST_RESULT_FAIL)
