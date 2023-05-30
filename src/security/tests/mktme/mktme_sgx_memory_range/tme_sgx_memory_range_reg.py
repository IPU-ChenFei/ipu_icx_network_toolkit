#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,
# copied, reproduced, modified, published, uploaded, posted, transmitted,
# distributed, or disclosed in any way without Intel's prior express written
# permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import sys
import os
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.bios_util import ItpXmlCli
from src.security.tests.mktme.mktme_common import MktmeBaseTest


class MkTmeSgxMemoryRangeRegister(MktmeBaseTest):
    """
    Phoenix ID : 18014070285 - Verify KeyId bits are masked for SGX memory range registers
    """
    TEST_CASE_ID = "18014070285"
    _BIOS_CONFIG_FILE_ENABLE = r"..\collateral\sgx_mktme_vm_bios_knobs.cfg"

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """Create an instance of MkTmeKeyCheckForEachSocket

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.BYTE_8 = 8
        self.tme_sgx_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._BIOS_CONFIG_FILE_ENABLE)
        super(MkTmeSgxMemoryRangeRegister, self).__init__(test_log, arguments, cfg_opts)
        self.initialize_sdp_objects()
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.EXPECTED_PRMRR_MASK_VALUE = 0xFFFFFFFFFFFFFFFF

    def prepare(self) -> None:
        super(MkTmeSgxMemoryRangeRegister, self).prepare()
        self._log.info("Unlocking the itp")
        self.unlock_itp()

    def get_prmrr_value(self) -> int:
        """Read the PRMRR base value and mask value then combine together by bitwise "and" to get PRMRR mem address
        :return: the PRMRR memory address value"""

        ret_val = 0
        try:
            # Halt the SUT
            self.SDP.halt()

            # Read the PRMRR base value
            msr_prmrr_base_values = self.SDP.msr_read(self.mktme_consts.RegisterRef.RegisterConstants.PRMRR_BASE)
            hex_msr_base_values = [hex(msr_value) for msr_value in msr_prmrr_base_values]
            self._log.info(f"PRMRR base values for all the threads - {hex_msr_base_values}")

            # Read the PRMRR mask value
            msr_prmrr_mask_values = self.SDP.msr_read(self.mktme_consts.RegisterRef.RegisterConstants.PRMRR_MASK)
            hex_msr_mask_values = [hex(msr_value) for msr_value in msr_prmrr_mask_values]
            self._log.info(f"PRMRR_MASK values for all the threads - {hex_msr_mask_values}")

            # Get PRMRR mem address value by "bitwise &" of msr_prmrr_values_list[0] & msr_prmrr_mask_values_list[0]
            ret_val = msr_prmrr_base_values[0] & msr_prmrr_mask_values[0]
            self._log.info(f"PRMRR  value is {hex_msr_base_values[0]} & {hex_msr_mask_values[0]}  = {hex(ret_val)}")

        except RuntimeError as e:
            raise e
        finally:
            self.SDP.go()

        return ret_val

    def get_prmrr_memory_values(self, prmrr_mem_add: str) -> int:
        """Read PRMRR memory value
        :param prmrr_mem_add: memory address
        :return: memory address value.
        :return RuntimeError if memory read fails"""

        ret_val = 0
        try:
            self.SDP.halt()
            prmrr_memory_value = self.SDP.mem_read(prmrr_mem_add, size=self.BYTE_8, thread_index=0)
            ret_val = prmrr_memory_value
        except RuntimeError as e:
            raise e
        finally:
            self.SDP.go()
        return ret_val

    def execute(self):
        """ 1. Clear CMOS
            2. Set TME, TME-MT and SGX Bios knobs
            3. Get PRMRR value by  "itp.threads[0].msr(0x2a0) & itp.threads[0].msr(0x1F5)"
            4. Read PRMRR memory value and check the value is 0xFFFFFFFFFFFFFFFF
            5. Apply MKTMETool.efi -k 1 random to create a new key value
            6. Get PRMRR value by  "itp.threads[0].msr(0x2a0) & itp.threads[0].msr(0x1F5)"
            7. Apply key ID 1 ((0x1 << 46 ) | PRMRR value) to PRMRR value
            8. Read PRMRR memory value and check the value is 0xFFFFFFFFFFFFFFFF
        """
        # Copy the mktme value to at least one USB drive attached to SUT.
        self.copy_mktme_tool_to_sut_usb_drives()

        # If TME, SGX and TME-MT is not enabled by default, then set the values, reboot and verify again
        self._log.info("Clearing the CMOS")
        self.itp_xml_cli_util.perform_clear_cmos(self.SDP, self.os, self.reboot_timeout)
        self.unlock_itp()
        try:
            self.itp_xml_cli_util.set_bios_knobs(knob_file=self.tme_sgx_bios_enable, restore_modify=True)
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.SDP.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            self.itp_xml_cli_util.set_bios_knobs(knob_file=self.tme_sgx_bios_enable, restore_modify=True)

        self.perform_graceful_g3()

        # If SUT is booted by previous steps, then need to unlock the ipc/itp
        self.unlock_itp()

        # Get PRMRR value
        prmrr_mem_add = self.get_prmrr_value()
        prmrr_mem_add_str_fmt = str(hex(prmrr_mem_add)) + "P"
        self._log.info(f"PRMRR Memory Address : {prmrr_mem_add_str_fmt}")

        # Get the memory value of PRMRR address.
        prmrr_mem_add_value = self.get_prmrr_memory_values(prmrr_mem_add_str_fmt)
        self._log.info(f"PRMRR Memory Address {prmrr_mem_add_str_fmt} value is {hex(prmrr_mem_add_value)}")

        # Verify the actual value vs expected values.
        if prmrr_mem_add_value != self.EXPECTED_PRMRR_MASK_VALUE:
            raise content_exceptions.TestFail("PRMRR value doesn't match with expected value")

        # Enter into UEFI Shell command to run MKTMETool.efi
        self.apply_uefi_random_key()

        # SUT is staying back in UEFI shell, it need to be reboot to the OS.
        self.perform_graceful_g3()

        self._log.info(f"PRMRR Memory analysis after random Key generation")
        # SUT rebooted by previous step. So ipc/itp need to unlock
        self.unlock_itp()

        # Get new PRMRR value
        prmrr_mem_add = self.get_prmrr_value()

        # Apply key ID 1 (bit 46) to PRMRR value
        prmrr_mem_new_add = ((0x1 << 46) | prmrr_mem_add)

        # Read the new memory value
        prmrr_mem_new_add_str_fmt = str(hex(prmrr_mem_new_add)) + "P"
        prmrr_mem_value_after_random = self.get_prmrr_memory_values(prmrr_mem_new_add_str_fmt)

        # Verify the actual value vs expected values.
        self._log.info(f"PRMRR Memory Address {prmrr_mem_new_add_str_fmt}  value is {hex(prmrr_mem_value_after_random)}")
        if prmrr_mem_value_after_random != self.EXPECTED_PRMRR_MASK_VALUE:
            raise content_exceptions.TestFail("PRMRR value doesn't match with expected value after random key generation")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MkTmeSgxMemoryRangeRegister.main() else Framework.TEST_RESULT_FAIL)
