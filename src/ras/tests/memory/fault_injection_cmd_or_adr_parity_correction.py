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
import sys

from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies

from src.lib.content_base_test_case import ContentBaseTestCase
from src.ras.lib.ras_common_utils import RasCommonUtil


class FaultInjectionCmdOrAdrParityCorrection(ContentBaseTestCase):
    """
    Glasgow_id : G56399-MEM Std RAS - Fault Injection - CMD/ADR Parity Correction - RDIMMs
    This test case injects CMD/ADR Parity Correction and verifies the alert signal.

    """
    TEST_CASE_ID = ["G56399", "MEM Std RAS - Fault Injection - CMD/ADR Parity Correction - RDIMMs"]
    BIOS_CONFIG_FILE = "fault_injection_cmd_or_adr_parity_correction.cfg"
    DIMM_INFO_LOG_FILE = "dimminfolog.txt"
    DIMM_INFO_SIGN_LIST = [r"Directory\sMode\s*\|\s*Off\s*\|\s*Off\s*\|\s*Off\s*\|",
                           r"ECC\sChecking\s\/\sPFD\s*\|\s*On\s\/\sOff\s*\|\s*On\s\/\sOff\s*\|\s*On\s\/\sOff\s*\|"]
    ALERT_SEEN_LOG = "Alert_Seen_Log_file.txt"
    ALERT_SEEN_VALUE = "0x00000001"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new FaultInjectionCmdOrAdrParityCorrection object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for
        execution environment.
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(FaultInjectionCmdOrAdrParityCorrection, self).__init__(test_log, arguments,
                                                                     cfg_opts, bios_config_file)
        self._ras_common_obj = RasCommonUtil(self._log, self.os, cfg_opts, self._common_content_configuration,
                                             self.bios_util)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def prepare(self):
        """
        Creates a new FaultInjectionCmdOrAdrParityCorrection object and we are calling a Prepare
        function that sets the bios knobs

        :return: None
        """
        super(FaultInjectionCmdOrAdrParityCorrection, self).prepare()

    def execute(self):
        """
        This Method is Used to execute below:
        1.Executes the DimmInfo cmd and validates the output
        2.Resets the injectorLockCheck for injecting the cap
        3.Initializes the error injection object and injects the cap
        4.Verifies the alert signal message in the corresponding channel

        :return: True or False
        """
        cap_error_flag = False
        try:
            # Halting the system
            self.SDP.itp.halt()
            self.SDP.start_log(log_file_name=self.DIMM_INFO_LOG_FILE, mode="w")
            # Executes the DimmInfo cmd and validates the output
            dimm_info = self.SV.get_dimminfo_object()
            self._log.info("Executing the DimmInfo command: ")
            dimm_info.spr_dimm_info()
            self.SDP.stop_log()
            self.SDP.itp.go()
            with open(self.DIMM_INFO_LOG_FILE, "r") as info_log:
                self._log.info("Checking the log file")
                dimm_info_log_msg = info_log.read()  # Getting the machine error log
                self._log.info(dimm_info_log_msg)
                # Verifying the dimminfo signature in the captured log
                if self._ras_common_obj.check_signature_in_log_file(dimm_info_log_msg,
                                                                    self.DIMM_INFO_SIGN_LIST):
                    self._log.info("string matched successfully with dimm info log")
                    cap_error_flag = True
                else:
                    cap_error_flag = False
                    self._log.error("string did not match with dimm info log")
            # Resets the injectorLockCheck for injecting the cap
            self.injectorlockcheck()
            # Initializes the error injection object for injecting cap
            sprinj = self.SV.get_err_injection_obj()
            # injects the cap
            self._log.info("Injecting the CAP:")
            # Selects the memory type based on the platform
            if self._common_content_lib.get_platform_family() == ProductFamilies.SPR:
                memType = 'ddr5'
            elif self._common_content_lib.get_platform_family() == ProductFamilies.SKX or\
                    self._common_content_lib.get_platform_family() == ProductFamilies.CLX or \
                    self._common_content_lib.get_platform_family() == ProductFamilies.CPX or \
                    self._common_content_lib.get_platform_family() == ProductFamilies.ICX:
                memType = 'ddr4'
            else:
                raise Exception("MemType for injecting cmd or adr parity is not supported for this platform")
            sprinj.inject_cap(mem_type=memType)
            self.SDP.start_log(log_file_name=self.ALERT_SEEN_LOG, mode="w")
            alert_seen_cmd_dict = {
                ProductFamilies.SPR: "uncore.memss.mcs.chs.alertsignal",
                ProductFamilies.ICX: "uncore.memss.mcs.chs.alertsignal",
                ProductFamilies.SKX: "uncore.memss.mcs.chs.alertsignal",
                ProductFamilies.CLX: "uncore.memss.mcs.chs.alertsignal",
                ProductFamilies.CPX: "uncore.imc0_c0_alertsignal"
            }
            # Verifies the alert signal message in the corresponding channel
            self.SV.get_by_path(self.SV.SOCKETS, alert_seen_cmd_dict[
                self._common_content_lib.get_platform_family()]).show()
            self.SDP.stop_log()
            with open(self.ALERT_SEEN_LOG, "r", encoding="UTF-8") as file_pointer:
                for xml_line in file_pointer.readlines():
                    if self.ALERT_SEEN_VALUE in xml_line:
                        cap_error_flag = True
                        self._log.info("Alert seen successfully")
                        break
                    else:
                        cap_error_flag = False
        except Exception as ex:
            cap_error_flag = False
            self._log.error("Exception Occured:", str(ex))
        finally:
            self.SDP.itp.go()
            self.SDP.stop_log()
        return cap_error_flag

    def _entersmm(self):
        """
        Issues a port out to 0xB2 and set a break.
        """
        thread = self.SDP.itp.threads[0]
        self.SDP.itp.halt()
        thread.port(0xb2, 1)
        self.SDP.itp.cv.smmentrybreak = 1
        self.SDP.itp.go()
        self.SDP.itp.cv.smmentrybreak = 0

    def injectorlockcheck(self):
        """
        Needed to unlock the red cover injections via SMM.
        """
        self._log.info('MSR 0x790 - unlocking')
        self.SDP.itp.events.ignore_run_control(turnoff=True, warn=False)
        self._entersmm()
        # For simplicty do the MSR on all threads
        for t in self.SDP.itp.threads:
            t.msr(0x790, 0)
        self.SDP.itp.go()
        self.SDP.itp.events.ignore_run_control(turnoff=False, warn=False)
        self._log.info('MSR 0x790 - unlocked')


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if FaultInjectionCmdOrAdrParityCorrection.main()
        else Framework.TEST_RESULT_FAIL)
