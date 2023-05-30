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
import time

from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies

from src.lib import content_exceptions
from src.hsio.pcie_upi_interop.pcie_upi_interop_common import PcieUpiInteropCommon
from src.hsio.pcie.pcie_surprise_linkdown_trigger_basetest import PcieSurpriseLinkDownBaseTest
from src.hsio.upi.hsio_upi_common import HsioUpiCommon, check_mlc_running


class UpiMlcWithPcieSurpriseLinkDown(PcieUpiInteropCommon):
    """
    HSD: 22014658512

    This test verifies link width is stable and all lanes are active after mlc stress and PCIe endpoint SLD event

    Note: Please ensure fio tool is installed on sut.
    """
    TEST_CASE_ID = ["22014658512", "upi_non_ras_linkwidth with mlc load and PCI Express traffic with Surprise Link Down"]
    _BIOS_CONFIG_FILE = "../pcie/slde_testing.cfg"
    SLDE_DICT = {
        ProductFamilies.SPR: "uncore.pi5.{}.cfg.erruncsts.slde",
        ProductFamilies.EMR: "uncore.pi5.{}.cfg.erruncsts.slde",
        ProductFamilies.GNR: "uncore.pi5.{}.rp0.cfg.erruncsts.slde"
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a UpiMlcWithPcieSurpriseLinkDown object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiMlcWithPcieSurpriseLinkDown, self).__init__(test_log, arguments, cfg_opts,
                                                           os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                        self._BIOS_CONFIG_FILE))
        self._pcie_surprise_link_down = PcieSurpriseLinkDownBaseTest(test_log, arguments, cfg_opts)
        self.PCIE_SOCKET = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        self.OS_ERR_SIGNATURE = ["containment event", "severity=Uncorrected"]
        self.FIO_TOOL_RUN_CMD = "numactl --membind={} fio --filename=/dev/nvme0n1 --direct=1 --rw=randrw --bs=4k " \
                                "--ioengine=libaio --iodepth=256 --runtime=7200 --numjobs=4 --time_based " \
                                "--group_reporting --name=iops-test-job --eta-newline=1"
        self.MLC_PROCESS_CMD = "ps -ef | grep mlc"
        self.MLC_FILE_PERMISSION_CHANGE_CMD = "chmod 777 ./mlc"
        self.ROOT_PATH = "/root"
        self.FIO_PROCESS_CMD = "ps -ef | grep fio"
        self.MLC_ITERATIONS = 600
        self.TOOL_RUN_TIME_SEC = 600
        self.TOTAL_RUN_TIME_PER_CYCLE_SEC = 1100

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        super(UpiMlcWithPcieSurpriseLinkDown, self).prepare()

    def execute(self):
        """
        This method is to execute:

        1. MLC load for a minimum of 10 min
        2. fio stress affinitized to opposite CPU running on NVMe storage drive
        3. Trigger surprise Link Down (SLD) on NVMe drive
        4. After MLC  has completed verify the bandwidth >=  85% of expected (based on current link speed)
        5. Power cycle and repeat test for 2 hours

        :return: True or False
        """
        self._log.info("Checking UPI lanes operational and Print upi errors....")
        self.check_upi_lanes_and_errors()

        # check for slde bit, shouldn't be set
        unc_slde_reg = self.SLDE_DICT[self._pcie_surprise_link_down._product_family].\
            format(self._pcie_surprise_link_down.PCIE_PXP_PORT)
        sld_output = self._pcie_surprise_link_down.si_reg_obj.get_by_path(
            scope=self._pcie_surprise_link_down.si_reg_obj.SOCKET, reg_path=unc_slde_reg,
            socket_index=int(self.PCIE_SOCKET)).read()
        if sld_output:
            raise content_exceptions.TestFail("PCIe Link Uncorrectable Surprise Link Down Status is already set")

        # install MLC tool
        self._log.info("Installing MLC tool to sut")
        self.mlc_path = self._install_collateral.install_mlc()

        # 'membind' value to match the CPU socket opposite of PCIe endpoint
        # if endpoint is at socket 0, then opposite is taken as 1, otherwise opposite is always taken as 0.
        # Applies to any socket count.
        opp_socket = 1 if int(self.PCIE_SOCKET) == 0 else 0
        self._log.info("'membind' value to match the CPU socket opposite of PCIe endpoint at socket{} - {}".
                       format(self.PCIE_SOCKET, opp_socket))

        # 2 hours timer
        while self.TWO_HOURS_TIMER > 0:
            # Starting MLC App run
            self._log.info("Starting MLC app for 10 min.........")
            self.os.execute(self.MLC_FILE_PERMISSION_CHANGE_CMD, self._common_content_configuration.get_command_timeout(),
                            self.mlc_path)
            self.os.execute_async("./mlc -t{}".format(self.MLC_ITERATIONS), cwd=self.mlc_path)
            time.sleep(self.CMD_RE_CHECK_WAIT_TIME_SEC)

            if not check_mlc_running(self):
                raise content_exceptions.TestFail("MLC APP is not running")
            self._log.info("MLC app has successfully started.")

            # Starting fio run
            self._log.info("Starting fio tool for 10 min.........")
            self.os.execute_async(self.FIO_TOOL_RUN_CMD.format(opp_socket), cwd=self.ROOT_PATH)
            time.sleep(self.CMD_RE_CHECK_WAIT_TIME_SEC)

            fio_run_status = self.os.execute(self.FIO_PROCESS_CMD, self._common_content_configuration.
                                                get_command_timeout()).stdout.split().count("fio")
            if not fio_run_status > 1:
                raise content_exceptions.TestFail("fio tool is not running")
            self._log.info("fio tool has successfully started.")

            self._log.info("10 min started of both tools run time")
            time.sleep(self.TOOL_RUN_TIME_SEC)

            self._log.info("SLDE Triggering............")
            self._pcie_surprise_link_down.execute(self.OS_ERR_SIGNATURE)

            self._log.info("MLC Tool status after slde trigger")
            if not check_mlc_running(self):
                raise content_exceptions.TestFail("MLC APP not running after SLD triggered")
            self._log.info("MLC stress tool is running after SLD triggered.")

            # killing MLC tool
            self._log.info("Killing MLC")
            self._stress_provider_obj.kill_stress_tool(stress_tool_name="mlc",
                                                                        stress_test_command="mlc")

            self._log.info("Checking UPI lanes operational and Print upi errors....")
            self.check_upi_lanes_and_errors()

            # Bandwidth results
            self._log.info("Checking Bandwidth status..................")
            expected_bandwidth_dict = self.sum_sockets_expected_bandwidth()
            expected_bandwidth_status = self.check_bandwidth_with_mlc(expected_bandwidth_dict)
            if not expected_bandwidth_status:
                raise content_exceptions.TestFail("BW is not as expected")
            self._log.info("BW is as expected")

            self.TWO_HOURS_TIMER -= self.TOTAL_RUN_TIME_PER_CYCLE_SEC

            if self.TWO_HOURS_TIMER > 0:
                self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
                self.os.wait_for_os(self.reboot_timeout)

        self._log.info("Timer finished, 2 hours completed")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiMlcWithPcieSurpriseLinkDown.main() else Framework.TEST_RESULT_FAIL)
