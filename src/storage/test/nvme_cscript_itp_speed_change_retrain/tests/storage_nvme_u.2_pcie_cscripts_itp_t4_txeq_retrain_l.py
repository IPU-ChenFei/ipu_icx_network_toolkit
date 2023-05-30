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

from src.lib.test_content_logger import TestContentLogger
from src.storage.lib.storage_common import StorageCommon
from src.lib.dtaf_content_constants import PcieAttribute
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.pcie_provider import PcieProvider
from src.lib.install_collateral import InstallCollateral
from src.provider.pcie_ltssm_provider import PcieLtssmToolProvider
from src.lib import content_exceptions


class StorageNvmeItpT4TxEqRetrainLinux(ContentBaseTestCase):
    """
    Glasgow ID : G56861-NVMe_U.2_Direct Connect_CScripts_ITP_T4_TxEq retrain

    The purpose of this Test Case is to verify the functionality of all supported pcie nvme link state transition
    for a specific adapter in all slot of the system.
    """

    TEST_CASE_ID = ["G56861", "NVMe_U.2_Direct Connect_CScripts_ITP_T4_TxEq retrain"]
    LTSSM_TEST_NAME = "TxEqRedo"
    step_data_dict = {
        1: {'step_details': 'Install the Ltssm tool on SUT',
            'expected_results': 'Ltssm tool installed successfully'},
        2: {'step_details': 'To get socket number and sut bus id',
            'expected_results': 'Fetched socket number and bus id'},
        3: {'step_details': 'Check NVME device Link speed and Width',
            'expected_results': 'NVME Link speed and width speed as Expected'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a StorageNvmeItpT4TxEqRetrainLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        super(StorageNvmeItpT4TxEqRetrainLinux, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._storage_common = StorageCommon(test_log, cfg_opts)
        self._product_family = self._common_content_lib.get_platform_family()
        self._pcie_provider = PcieProvider.factory(self._log, self.os, cfg_opts, "os", uefi_obj=None)
        self._pcie_ltssm_provider = PcieLtssmToolProvider.factory(log=self._log, cfg_opts=cfg_opts,
                                                                  os_obj=self.os, pcie_provider_obj=self._pcie_provider)
        self._ltssm_iteration = self._common_content_configuration.get_number_of_cycle_to_test_ltssm()

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(StorageNvmeItpT4TxEqRetrainLinux, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. Install LTSSM Tools.
        2. To Get Socket and Bus id.
        3. Check Link and Width Speed.
        4. Test LTSSM Tool execution and Check Errors

        :return: True or False
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        sut_folder_path = self.install_collateral.install_ltssm_tool()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        slot_list = self._common_content_configuration.get_pcie_slot_mcio_check(self._product_family)
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self.SDP.itp.unlock()
        for each_slot in slot_list:
            bus_output, sut_socket, csp_path = self._storage_common.get_pcie_device_bus_id(
                self.SV, pcie_slot_device_list=each_slot)
            device_details = self._pcie_provider.get_device_details_with_bus(bus_output)
            if len(device_details) < 1:
                raise content_exceptions.TestFail("Device Details are not Captured, Please Verify Configuration, "
                                                  "VMD-Disable Mode and try again")
            for bdf_value in device_details.keys():
                speed, width = self._pcie_ltssm_provider.run_ltssm_tool(
                    test_name=self.LTSSM_TEST_NAME,
                    device_id=device_details[bdf_value][PcieAttribute.DEVICE_ID],
                    cmd_path=sut_folder_path, bdf=bdf_value, disable_kernel_driver=False)
                if sut_socket is None and csp_path is None:
                    self._log.debug("LTSSM tool is not implemented in PythonSV level for SLOT C")
                    continue
                cmd_output = self.SV.get_ltssm_object().runTxEqRedo(
                    int(self._ltssm_iteration), [int(sut_socket), ".".join(csp_path.split('.')[1:4]),
                                                 int(width[-1]), int(speed)])
                if cmd_output[0].has_errors:
                    raise content_exceptions.TestFail("Expected Output was not observed for "
                                                      "the test {}".format(self.LTSSM_TEST_NAME))
                self._log.debug("LTSSM tool got passed: test name: '{}' for PythonSv".format(self.LTSSM_TEST_NAME))
                break
            # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self.SDP.halt_and_check()
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        super(StorageNvmeItpT4TxEqRetrainLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageNvmeItpT4TxEqRetrainLinux.main() else Framework.TEST_RESULT_FAIL)
