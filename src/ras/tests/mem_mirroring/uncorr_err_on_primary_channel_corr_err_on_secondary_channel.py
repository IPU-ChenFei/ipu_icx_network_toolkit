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

from src.ras.tests.mem_mirroring.mem_mirroring_common import MemMirroringBaseTest


class UnCorrErrOnPrimaryChannelCorrErrOnSecondaryChannel(MemMirroringBaseTest):
    """
    Glasgow_id : 59904

    This Tests injects Uncorrectable Error on Primary Channel, Correctable Error on Secondary Channel
    """
    _BIOS_CONFIG_FILE = "memory_mirroring_bios_knobs.cfg"
    _ADDR_SIGN = "ADDR "

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UnCorrErrOnPrimaryChannelCorrErrOnSecondaryChannel object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UnCorrErrOnPrimaryChannelCorrErrOnSecondaryChannel, self).__init__(test_log,
                                                                                 arguments, cfg_opts,
                                                                                 self._BIOS_CONFIG_FILE)
        self._cfg = cfg_opts

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.

        :return: None
        """
        super(UnCorrErrOnPrimaryChannelCorrErrOnSecondaryChannel, self).prepare()

    def execute(self):
        """
        This Method is used to run the Test Case Step.

        1. Check Mirror is enable or not.
        2. Validate the Memory info.
        3. Check Memory mirror ddr4 is enable or not.
        4. Set Mirror Address.
        5. Check address is mapped to dimm space.
        6. Inject UnCorrectable error on Primary and Correctable on Secondary.
        7. Check error detection.
        8. Check mci status register.
        9. Check system Error.

        :return: True if Test Case Pass
        :raise: RuntimeError
        """
        try:
            if self.memory_mirroring_utils_obj.is_ddr_mirroring_enabled():
                self._log.info("Memory Mirroring is enabled")
            else:
                log_err = "Memory Mirroring is not enabled"
                self._log.error(log_err)
                raise Exception(log_err)

            if self.get_mc_dimm_info(self._MC_DIMM_INFO_REGEX):
                self._log.info("All dimm information Validated.")
            else:
                log_err = "Please Check the Dimm Configuration"
                self._log.error(log_err)
                raise Exception(log_err)

            if self.memory_mirroring_utils_obj.is_ddr_mirroring_enabled():
                self._log.info("DDR Memory Mirroring is enabled")
            else:
                log_err = "DDR Memory Mirroring is enabled"
                self._log.error(log_err)
                raise Exception(log_err)

            self.check_mirror_address()
            if self.is_address_mapped_to_dimm_space(self._START_ADDR, self._END_ADDR):
                self._log.info("Address is Mapped to Dimm Space as Expected")
            else:
                log_err = "Error: Address is not Mapped to Dimm Space"
                self._log.error(log_err)
                raise Exception(log_err)
            self._log.info("Inject the Uncorrectable Error on Primary Channel and Correctable Error "
                           "on Secondary Channel")
            self._ras_common_obj.inject_memory_error(err_addr=self._CORE_ADDR, error_type="ce", imm_Inject=False,
                                            Imm_Consume=False, Inject2ndChannel=True)
            self._ras_common_obj.inject_memory_error(err_addr=self._CORE_ADDR, error_type="uce", imm_Inject=True,
                                            Imm_Consume=True, Inject2ndChannel=False)
            ret_val = self.check_mirroring_error_was_detected(self._ras_common_obj._UC_ON_PRI_CE_ON_SEC[
                                                                  self._common_content_lib.get_platform_family()],
                                                              True)
            if ret_val:
                self._log.info("Uncorrected error is detected on Primary Channel and Correctable error "
                               "on Secondary Channel is detected")
            else:
                log_err = "Error is not detected"
                self._log.error(log_err)
                raise Exception(log_err)
            if self.check_mci_status_register():
                self._log.info("MCI Status Register for Correctable error is Found as Expected")
            else:
                log_err = "Error: MCI Status Register for Correctable error is not valid"
                self._log.error(log_err)
                raise Exception(log_err)
            ret_val = self._ras_common_obj.log_klaxon_memory_errors(self._ras_common_obj._UC_KLAXON_M2MEM_SIG,
                                                                    self._ras_common_obj._UC_KLAXON_MEM_SIG,
                                                                    True)
            if ret_val:
                self._log.info("Error Signature Captured in Klaxon Log")
            else:
                log_err = "Error: Error Signature was not Captured"
                self._log.error(log_err)
                raise Exception(log_err)

            self._ras_common_obj._UC_ERROR_ON_PRI_CH_LOG_SIG.append(
                self._ADDR_SIGN + str(hex(self._CORE_ADDR)).replace('0x', ''))
            if not self._os.is_alive():
                self._sdp.pulse_pwr_good()
                self._os.wait_for_os(self._reboot_timeout_in_sec)

            self._log.info("Verify Os Log Error....")
            ret_val = self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                                                          self._ras_common_obj._UC_ERROR_ON_PRI_CH_LOG_SIG)
            if ret_val:
                self._log.info("OS Log Signature Captured in Os Log")
            else:
                log_err = "Os Log Signature was not detected"
                self._log.error(log_err)
                raise RuntimeError(log_err)

        except Exception as ex:
            log_err = "An Exception Occurred {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

        finally:
            self._log.info("Resume the Machine")
            self._sdp.go()

        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UnCorrErrOnPrimaryChannelCorrErrOnSecondaryChannel.main() else
             Framework.TEST_RESULT_FAIL)
