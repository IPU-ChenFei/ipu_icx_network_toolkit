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


class UceOnSecondaryChannel(MemMirroringBaseTest):
    """
    Glasgow ID : 60604
    Tests the feature to inject an error into the secondary region and make sure the system is still alive
    """
    BIOS_CONFIG_FILE = "memory_mirroring_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UceOnSecondaryChannel object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UceOnSecondaryChannel, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        self._cfg = cfg_opts

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
        super(UceOnSecondaryChannel, self).prepare()

    def execute(self):
        """
        This Method is used to run the Test Case Step.

        1. Check Mirror is enable or not.
        2. Validate the Memory info.
        3. Check Memory mirror ddr is enable or not.
        4. Set system Address.
        5. Check address is mapped to dimm space.
        6. Inject Mirror Un Correctable error.
        7. Check for Error through Klaxon

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

            ret_val = self._ras_common_obj.log_klaxon_memory_errors(klaxon_m2mem_file_signature_list=
                                                                    self._REGEX_FOR_KLAXON_NO_ERRORS,
                                                                    klaxon_mem_error_signature_list=
                                                                    self._REGEX_FOR_KLAXON_NO_ERRORS,
                                                                    error_validate_flag=True)
            if ret_val:
                self._log.info("There are No Memory Errors or Machine Errors")
            else:
                log_err = "Memory Error is Detected in the System"
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

            self._log.info("Inject the Uncorrectable Memory Error")
            self._ras_common_obj. \
                inject_memory_error(err_addr=self._CORE_ADDR, error_type="uce",
                                    Inject2ndChannel=True, error_validate_flag=True,
                                    error_signature_file_list=self._REGEX_FOR_UNCORR_ERR_ON_SECONDARY_CHANNEL)
            ret_val = self.check_mirroring_error_was_detected(
                self._ras_common_obj._UC_ERR_ON_SEC_CH_WITHOUT_FAILOVER[self._common_content_lib.get_platform_family()],
                True)
            if ret_val:
                self._log.info("Uncorrectable Memory Error is Injected")
            else:
                log_err = "Uncorrectable Memory Error is not detected"
                self._log.error(log_err)
                raise Exception(log_err)

            ret_val = self._ras_common_obj.log_klaxon_memory_errors(klaxon_m2mem_file_signature_list=
                                                                    self._REGEX_FOR_KLAXON_NO_ERRORS,
                                                                    klaxon_mem_error_signature_list=
                                                                    self._REGEX_FOR_KLAXON_NO_ERRORS,
                                                                    error_validate_flag=True)

            if ret_val:
                self._log.info("There are No Memory Errors or Machine Errors")
            else:
                log_err = "Memory Error is Detected in the System"
                self._log.error(log_err)
                raise Exception(log_err)

            if not self._os.is_alive():
                self._sdp.pulse_pwr_good()
                self._os.wait_for_os(self._reboot_timeout_in_sec)
            self._log.info("System is Alive after Injecting the UnCorrectable Error")

        except Exception as ex:
            log_err = "An Exception Occurred {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

        finally:
            self._log.info("Resume the Machine")
            self._sdp.go()

        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UceOnSecondaryChannel.main() else Framework.TEST_RESULT_FAIL)
