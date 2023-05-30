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


from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
import src.lib.content_exceptions as content_exception
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.test_content_logger import TestContentLogger
from sys import exit
from os import path
from time import sleep


class PcieCorrectedErrorThresholdRootPort(IoPmCommon):
    """
    Phoenix_ID: ["22012520524", "PCIe Correctable Error Thresholding - Linux OS : cscripts"]

    This TestCase Injects PCIe correctable errors above set threshold in BIOS and checks error is reported to the OS.
    """
    TEST_CASE_ID = ["22012520524", "PCIe_Correctable_Error_Thresholding_-_Linux_OS_:_cscripts"]

    STEP_DATA_DICT = {
                        1: {'step_details': 'Verify receiver error mask is set by BIOS',
                            'expected_results': "Receiver error mask is set by BIOS"},
                        2: {'step_details': 'Inject PCIe correctable errors above set threshold',
                            'expected_results': 'PCIe correctable error are injected'},
                        3: {'step_details': 'Verify error threshold counter is updated correctly',
                            'expected_results': 'Error threshold counter value reflects set threshold value in BIOS'},
                        4: {'step_details': 'Verify AER error is reported in OS log',
                            'expected_results': 'AER error is reported in the OS log'},
                        5: {'step_details': 'Inject only one PCie correctable error below set threshold',
                            'expected_results': 'PCIe correctable error is injected'},
                        6: {'step_details': 'Verify AER error is not reported in OS log when threshold not reached',
                            'expected_results': 'AER error not reported in OS log when threshold not reached'}
                    }

    PCIE_CORERR_SIGNATURE = ["aer_status",
                             "Hardware Error",
                             "It has been corrected by h/w and requires no further action"]

    _BIOS_CONFIG_FILE = "pcie_corrected_error_threshold_bios_knobs_rootport.cfg"
    _PCIE_ERR_THRESH_VALUE = 5  # value must match bios knob setting
    TEST_ITERATIONS = 2
    REG_READ_DELAY_SEC = 10  # how many seconds to wait between register reads

    def __init__(self, test_log, arguments, cfg_opts):
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)
        super(PcieCorrectedErrorThresholdRootPort, self).__init__(test_log, arguments, cfg_opts,
                                                                  path.join(path.dirname(
                                                                      path.abspath(__file__)),
                                                                      self._BIOS_CONFIG_FILE))

        self.PCIE_SOCKET = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        self.PCIE_PXP_PORT = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()

    def prepare(self):
        # type: () -> None
        """
        :return: None
        """
        super(PcieCorrectedErrorThresholdRootPort, self).prepare()

    def execute(self):
        """
        This test case provides the validation plan and recipe for error reporting enhancement where corrected
        error reporting within the PCI Express module can be configured to only signal once a predetermined
        threshold is reached.

        :return: True if passed else False
        :raise: None
        """

        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)  # instantiate CScript object
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)    # instantiate XDP object

        for _iter in range(self.TEST_ITERATIONS):
            self._log.info("Halting system")
            sdp_obj.halt_and_check()

            self._test_content_logger.start_step_logger(1)
            self._log.info('Checking if BIOS sets receiver error mask')
            receiver_mask = self.get_receiver_mask_reg_value(cscripts_obj, socket=self.PCIE_SOCKET,
                                                             port=self.PCIE_PXP_PORT)
            if receiver_mask == 1:
                self._test_content_logger.end_step_logger(1, return_val=True)
                self._test_content_logger.start_step_logger(2)
                self._log.info('Injecting %d correctable errors to root port %s' % (self._PCIE_ERR_THRESH_VALUE,
                                                                                    self.PCIE_PXP_PORT))
                for inj_err in range(self._PCIE_ERR_THRESH_VALUE):
                    self.inject_pcie_error_cscripts(cscripts_obj, "ce", socket=self.PCIE_SOCKET,
                                                    port=self.PCIE_PXP_PORT)
                self._test_content_logger.end_step_logger(2, return_val=True)

                self._test_content_logger.start_step_logger(3)
                self._log.info("Checking error threshold counter was updated accordingly")
                error_count = self.get_correrr_counter_reg_value(cscripts_obj, socket=self.PCIE_SOCKET,
                                                                 port=self.PCIE_PXP_PORT)
                if error_count >= self._PCIE_ERR_THRESH_VALUE:
                    self._log.info("correctable error counter updated correctly")
                else:
                    raise content_exception.TestFail("correctable error counter is %d instead of %d after error "
                                                     "injection" % (error_count, self._PCIE_ERR_THRESH_VALUE))
                self._test_content_logger.end_step_logger(3, return_val=True)

                self._log.info("Resuming")
                sdp_obj.go()
                sleep(self.REG_READ_DELAY_SEC)

                error_count = self.get_correrr_counter_reg_value(cscripts_obj, socket=self.PCIE_SOCKET,
                                                                 port=self.PCIE_PXP_PORT)
                if error_count == 0:
                    self._log.info("correctable error counter was cleared after resuming")
                else:
                    raise content_exception.TestFail("correctable error counter was not cleared after resuming")

                self._test_content_logger.start_step_logger(4)

                self._log.info("Verify OS Log")
                errors_reported = self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                                        self.PCIE_CORERR_SIGNATURE)
                if errors_reported:
                    self._log.info("Correctable error reported to OS after threshold reached")
                else:
                    log_err = "Correctable error not reported to the OS after threshold reached"
                    self._log.error(log_err)
                    raise content_exception.TestFail(log_err)
                self._test_content_logger.end_step_logger(4, return_val=True)

                # clear logs before next error injection
                self._common_content_lib.clear_os_log()
                self._common_content_lib.clear_dmesg_log()

                # inject one CE only
                self._test_content_logger.start_step_logger(5)
                self._log.info("Injecting one CE only")
                self.inject_pcie_error_cscripts(cscripts_obj, "ce", socket=self.PCIE_SOCKET, port=self.PCIE_PXP_PORT)
                self._test_content_logger.end_step_logger(5, return_val=True)

                # verify no AER is logged in OS log
                self._test_content_logger.start_step_logger(6)
                self._log.info("Verify OS Log doesn't report any AER when CE threshold is not reached")
                errors_reported = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                                self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                                                self.PCIE_CORERR_SIGNATURE)
                if errors_reported:
                    log_err = "Correctable error reported to the OS after threshold not reached"
                    self._log.error(log_err)
                    raise content_exception.TestFail(log_err)

                else:
                    self._log.info("Correctable error not reported to OS after threshold not reached")
                self._test_content_logger.end_step_logger(6, return_val=True)

            else:
                raise content_exception.TestFail("BIOS did not set receiver error mask, cannot continue")

        return True


if __name__ == "__main__":
    exit(Framework.TEST_RESULT_PASS if PcieCorrectedErrorThresholdRootPort.main()
         else Framework.TEST_RESULT_FAIL)
