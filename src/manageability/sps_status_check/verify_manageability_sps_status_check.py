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
import sys
import time
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.dtaf_content_constants import ProviderXmlConfigs
from src.lib.test_content_logger import TestContentLogger


class VerifyManageabilitySpsStatusCheck(ContentBaseTestCase):
    """
    HPQC ID: 91692-PI_Manageability_SPS_StatusCheck

    This test case aims to find out if SPS is in Operational mode or not.
    """
    TEST_CASE_ID = ["H91692", "PI_Manageability_SPS_StatusCheck"]
    step_data_dict = {
        1: {'step_details': 'Verify if SUT is in OS and pingable',
            'expected_results': 'SUT is in OS and pingable'},
        2: {'step_details': 'Run Read register commands and store SPS register values',
            'expected_results': 'Read register commands executed without any issues'},
        3: {'step_details': 'Check the value of FWSTS1. Convert the Hexadecimal value into Binary'
                            'and map the bits and verify if the SPS is in Operational Mode',
            'expected_results': 'SPS is In Operational Mode as Expected'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  VerifyManageabilitySpsStatusCheck object.

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyManageabilitySpsStatusCheck, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

    def prepare(self):  # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        self._test_content_logger.start_step_logger(1)
        super(VerifyManageabilitySpsStatusCheck, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    @staticmethod
    def check_fwsts_using_sv(pythonsv, log):
        """
        This Method is Used to Verify Status Of Cpu Fuse Bit(anchor_cove_en) by Using PythonSv

        :raise TestFail: if Cpu Fuse Bit(anchor_cove_en) is Not Set
        """
        si_cfg = ElementTree.fromstring(ProviderXmlConfigs.SDP_XML_CONFIG)
        sdp = ProviderFactory.create(si_cfg, log)  # type: SiliconDebugProvider
        search_keyword = "sps_check"
        log_file_name = "%s.log" % search_keyword
        sdp.itp.unlock()
        pythonsv.refresh()
        try:
            pythonsv.populate_scope_dict()
            sdp.start_log(log_file_name)
            fwsts1 = pythonsv.get_by_path(scope=pythonsv.SPCH, reg_path="cse.gasket.heci1.heci1_hfs.fs_ha")
            fwsts2 = pythonsv.get_by_path(scope=pythonsv.SPCH, reg_path="cse.gasket.heci1.heci1_gs_shdw1")
            sdp.stop_log()
            log.info("FWSTS1 = {}".format(fwsts1))
            log.info("FWSTS2 = {}".format(fwsts2))
        except Exception as e:
            raise e
        return [fwsts1, fwsts2]

    def execute(self):
        """
        Execute Main test case.

        Testcase Flow:
        step1 : Unlock the Silicon and PCH using itp.unlock()
        step2 : Run the below two commands to read the registers:
                FWSTS1 ---> sv.spch0.cse.gasket.heci1.heci1_hfs.fs_ha.show()
                FWSTS2 ---> sv.spch0.cse.gasket.heci1.heci1_gs_shdw1.show()
        step3 : Check the value of FWSTS1. Convert the Hexadecimal value into Binary
                and map the bits and verify if the SPS is in Operational Mode

        :return: True if test completed successfully, False otherwise.
        """
        #  Run the below two commands to read the registers:
        #  FWSTS1 ---> sv.spch0.cse.gasket.heci1.heci1_hfs.fs_ha.show()
        #  FWSTS2 ---> sv.spch0.cse.gasket.heci1.heci1_gs_shdw1.show()
        self._test_content_logger.start_step_logger(2)
        Read_register_values = self._common_content_lib.execute_pythonsv_function(self.check_fwsts_using_sv)
        self._log.debug("log output == {}".format(Read_register_values))
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Check the value of FWSTS1. Convert the Hexadecimal value into Binary
        # and map the bits and verify if the SPS is in Operational Mode
        self._test_content_logger.start_step_logger(3)
        self._log.debug("convert the FWSTS1 reg value obtained to binary")
        binary_fwsts1 = bin(int(str(Read_register_values[0]), 16)).zfill(8)

        if binary_fwsts1[-3:] != '101' and int(str(Read_register_values[1]),16)>0:
            raise content_exceptions.TestFail("Bits [6:8] are not 101(Binary) = 0x5(hexadecimal),"
                                              " Sps is not in operational mode")
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._log.info("Bits [6:8] is 101(Binary) = 0x5(hexadecimal),Thus SPS is in Operational Mode.")
        return True


# Execute this test with TestEngine when run as main.
if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if VerifyManageabilitySpsStatusCheck.main() else Framework.TEST_RESULT_FAIL)
