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
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.lib.dtaf_constants import Framework

from src.ras.lib.ras_common_utils import RasCommonUtil
from src.ras.tests.esmm.esmm_common import EsmmSaveCommon


class EmcaGen1Enable(EsmmSaveCommon):
    """
    Glasgow_id : G58271-_20_01_01_emcag1
    This test verifies if BIOS is enabling eMCA gen1.

    """
    TEST_CASE_ID = ["G58271", "_20_01_01_emcag1"]
    BIOS_CONFIG_FILE = "emca_gen1_bios_knob.cfg"
    EMCA_GEN1_SIGN_LIST = [r"0x00000001\s\:\smapcmcitocsmi\s\(32\:32\)",
                           r"0x00000001\s\:\smapmcetomsmi\s\(34\:34\)",
                           r"0x00000001\s\:\senable_io_mca\s\(22\:22\)"]
    EMCA_GEN1_LOG_FILE = "EMCA_GEN1_LOG.txt"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EmcaGen1Enable object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EmcaGen1Enable, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._ras_common_obj = RasCommonUtil(self._log, self.os, cfg_opts, self._common_content_configuration)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def prepare(self):
        # type: () -> None
        """
        Creates a new EmcaGen1Enable object and we are calling a Prepare function
        Prepare Function does the Following tasks:
            1. Set the bios knobs to its default mode.
            2. Set the bios knobs as per the test case.
            3. Reboot the SUT to apply the new bios settings.
            4. Verify the bios knobs that are set.
        :return: None
        """
        super(EmcaGen1Enable, self).prepare()

    def execute(self):
        """
        This Method is Used to execute below:
        1.Verifies if BIOS is enabling eMCA gen1

        :return: True or False
        """
        emca_gen1_status = False
        try:
            self.SV.refresh()
            self.SDP.itp.unlock()
            MAPCMCITOCSMI_DICT = {
                ProductFamilies.ICX: "self.SV._sv.sockets.uncore.memss.m2mems.mci_ctl2.mapcmcitocsmi.show()",
                ProductFamilies.SPR: "self.SV._sv.sockets.uncore.memss.m2mems.mci_ctl2.mapcmcitocsmi.show()",
                ProductFamilies.CPX: "self.SV._sv.sockets.uncore.imc0_c0_m2mems.mci_ctl2.mapcmcitocsmi.show()",
                ProductFamilies.SKX: "self.SV._sv.sockets.uncore.memss.m2mems.mci_ctl2.mapcmcitocsmi.show()",
                ProductFamilies.CLX: "self.SV._sv.sockets.uncore.memss.m2mems.mci_ctl2.mapcmcitocsmi.show()"
            }
            MAPMCETOMSMI_DICT = {
                ProductFamilies.ICX: "self.SV._sv.sockets.uncore.memss.m2mems.mci_ctl2.mapmcetomsmi.show()",
                ProductFamilies.SPR: "self.SV._sv.sockets.uncore.memss.m2mems.mci_ctl2.mapmcetomsmi.show()",
                ProductFamilies.CPX: "self.SV._sv.sockets.uncore.imc0_c0_m2mems_mci_ctl2.mapmcetomsmi.show()",
                ProductFamilies.SKX: "self.SV._sv.sockets.uncore.memss.m2mems.mci_ctl2.mapmcetomsmi.show()",
                ProductFamilies.CLX: "self.SV._sv.sockets.uncore.memss.m2mems.mci_ctl2.mapmcetomsmi.show()"
            }
            ENABLE_IO_MCA_DICT = {
                ProductFamilies.ICX: "self.SV._sv.sockets.uncore.ubox.ncevents.ncevents_cr_uboxerrctl2_cfg.enable_io_mca.show()",
                ProductFamilies.SPR: "self.SV._sv.sockets.uncore.ubox.ncevents.ncevents_cr_uboxerrctl2_cfg.enable_io_mca.show()",
                ProductFamilies.CPX: "self.SV._sv.sockets.uncore.ubox.ncevents.ncevents_cr_uboxerrctl2_cfg.enable_io_mca.show()",
                ProductFamilies.SKX: "self.SV._sv.sockets.uncore.ubox.ncevents.ncevents_cr_uboxerrctl2_cfg.enable_io_mca.show()",
                ProductFamilies.CLX: "self.SV._sv.sockets.uncore.ubox.ncevents.ncevents_cr_uboxerrctl2_cfg.enable_io_mca.show()"
            }
            self.SDP.start_log(self.EMCA_GEN1_LOG_FILE)
            eval(MAPCMCITOCSMI_DICT[self._common_content_lib.get_platform_family()])
            eval(MAPMCETOMSMI_DICT[self._common_content_lib.get_platform_family()])
            eval(ENABLE_IO_MCA_DICT[self._common_content_lib.get_platform_family()])
            self.SDP.stop_log()
            with open(self.EMCA_GEN1_LOG_FILE, "r") as info_log:
                self._log.info("Checking the log file for EMCA GEN1 Status")
                log_msg = info_log.read()  # Getting the machine error log
                self._log.info(log_msg)
                # Verifying the emca gen1 signature in the captured log
                if self._ras_common_obj.check_signature_in_log_file(log_msg,
                                                                    self.EMCA_GEN1_SIGN_LIST):
                    self._log.info("Successfully verified emca Gen1 status")
                    emca_gen1_status = True
                else:
                    emca_gen1_status = False
                    self._log.error("Failed to verify emca Gen1 status")
        except Exception as e:
            self._log.error("Failed to verify emca Gen1 status due to the Exception '{}'".format(e))
        return emca_gen1_status


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EmcaGen1Enable.main() else Framework.TEST_RESULT_FAIL)
