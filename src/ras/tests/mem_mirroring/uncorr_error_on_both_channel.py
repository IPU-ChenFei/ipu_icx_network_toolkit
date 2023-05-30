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
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.ras.tests.mem_mirroring.mem_mirroring_common import MemMirroringBaseTest


class UnCorrErrOnBothChannel(MemMirroringBaseTest):
    """
    Glasgow_id : 59903

    Tests the feature to inject uncorrectable error on both channels.
    """
    _BIOS_CONFIG_FILE = "memory_mirroring_bios_knobs.cfg"
    _ADDR_SIGN = "ADDR "

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UnCorrErrOnPrimaryChannel object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UnCorrErrOnBothChannel, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self._product = self._common_content_lib.get_platform_family()

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
        super(UnCorrErrOnBothChannel, self).prepare()

    def execute(self):
        """
        This Method is used to run the Test Case Step.

        1. Check Mirror is enable or not.
        2. Validate the Memory info.
        3. Check Memory mirror ddr is enable or not.
        4. Set system Address.
        5. Check address is mapped to dimm space.
        6. Inject Mirror Un Correctable error on both channel.
        7. Check system Error.

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
                log_err = "DDR Memory Mirroring is not enabled"
                self._log.error(log_err)
                raise Exception(log_err)

            self.check_mirror_address()
            if self.is_address_mapped_to_dimm_space(self._START_ADDR, self._END_ADDR):
                self._log.info("Address is Mapped to Dimm Space as Expected")
            else:
                log_err = "Error: Address is not Mapped to Dimm Space"
                self._log.error(log_err)
                raise Exception(log_err)

            self._log.info("Inject the mirror uncorrectable Error")
            self._ras_common_obj.inject_memory_error(err_addr=self._CORE_ADDR, error_type="mirror_uce")
            ret_val = self.check_mirroring_error_was_detected(
                self._ras_common_obj._UC_ERROR_ON_BOTH_CHANNEL[self._product], True)
            if ret_val:
                self._log.info("UnCorrected mirror channel error...")
            else:
                log_err = "UnCorrected mirror channel error is not detected"
                self._log.error(log_err)
                raise Exception(log_err)

            ret_val = self._ras_common_obj.log_klaxon_memory_errors(klaxon_m2mem_file_signature_list=
                                            self._ras_common_obj._UC_ON_BOTH_CH_KLAXON_M2MEM_SIG,
                                            klaxon_mem_error_signature_list=
                                        self._ras_common_obj._UC_ON_BOTH_CH_KLAXON_MEM_SIG, error_validate_flag=True)
            self._ras_common_obj._UC_ERROR_LOG_SIG.append(self._ADDR_SIGN + str(hex(self._CORE_ADDR)).replace('0x', ''))
            if not self._os.is_alive():
                self._sdp.pulse_pwr_good()
                self._os.wait_for_os(self._reboot_timeout_in_sec)

            self._log.info("Verify Os Log Error....")
            self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                                                          self._ras_common_obj._UC_ERROR_LOG_SIG)

        except Exception as ex:
            log_err = "An Exception Occurred {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

        finally:
            self._log.info("Resume the Machine")
            self._sdp.go()

        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UnCorrErrOnBothChannel.main() else Framework.TEST_RESULT_FAIL)
