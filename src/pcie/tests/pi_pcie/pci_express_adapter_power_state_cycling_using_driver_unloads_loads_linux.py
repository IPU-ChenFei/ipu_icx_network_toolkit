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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.dtaf_content_constants import DriverCycleToolConstant
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_configuration import ContentConfiguration
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from src.lib import content_exceptions


class PciExpressAdapterPowerStateCyclingUsingDriverUnloadsLoadsLinux(PcieCommon):
    """
    GLASGOW ID : G56023.0-PCI_Express_Adapter_power_state_cycling_using_driver_unloads_loads_Linux

    The objective of this test is to ensure that adapters going into low power states has no ill effect on system
    stability.
    """
    TEST_CASE_ID = ["G56023", "PCI_Express_Adapter_power_state_cycling_using_driver_unloads_loads_Linux"]

    step_data_dict = {
        1: {'step_details': 'Copy the file "DriverCycle.sh" from host to the SUT',
            'expected_results': 'Successfully Copied file "DriverCycle.sh" to the SUT'},
        2: {'step_details': 'Check the driver is loaded for a device & Run the script drivercycle.sh to'
                            'cycle the adapter drivers',
            'expected_results': 'The driver is loaded for the device & Successfully ran the script'},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PciExpressAdapterPowerStateCyclingUsingDriverUnloadsLoadsLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PciExpressAdapterPowerStateCyclingUsingDriverUnloadsLoadsLinux, self).__init__(test_log,
                                                                                             arguments, cfg_opts)

        #  Object of TestContentLogger class
        self._sut_path = None
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. This method is used to Clear OS logs and copy drivercycle.sh file to the SUT for Driver Cycle load & unload.
        """
        self._common_content_lib.clear_all_os_error_logs()  # To clear Os logs

        self._test_content_logger.end_step_logger(1, True)

        # Copying "drivercycle.sh" to the SUT
        self._sut_path = self._install_collateral.install_driver_cycle()

        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        1. get the driverlist from the SUT
        2. run the script drivercycle.sh to cycle the adapter

        :return: True, if the test case is successful.
        :raise: Content Exception
        """
        csp = ProviderFactory.create(self.sil_cfg, self._log)

        self._test_content_logger.start_step_logger(2)

        # used to get the driver lists
        driver_list = self.get_driver_list_to_load_and_unloads(csp=csp)
        args = ""
        for each_driver in driver_list:
            args = args + each_driver + ' '

        args = args.strip()
        if not args:
            raise content_exceptions.TestFail("No driver name is visible in lspci")
        self._common_content_configuration = ContentConfiguration(self._log)
        no_of_cycle = self._common_content_configuration.get_num_of_cycle_to_load_unload_driver()
        self.os.execute("sed -i -e 's/\r$//' drivercycle.sh", self._command_timeout, self._sut_path)
        sut_cmd = r"./{} {} {}".format(DriverCycleToolConstant.DRIVER_TOOL_NAME_LINUX, no_of_cycle, args)
        cmd_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd=sut_cmd,
                                                               cmd_str="driver load unload",
                                                               execute_timeout=self._command_timeout * 2,
                                                               cmd_path=self._sut_path)
        self._log.info(cmd_out_put)

        self._test_content_logger.end_step_logger(2, True)

        return True


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if PciExpressAdapterPowerStateCyclingUsingDriverUnloadsLoadsLinux.main() else
        Framework.TEST_RESULT_FAIL)
