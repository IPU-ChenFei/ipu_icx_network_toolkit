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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


# from math import isclose


class OutOfBandMultiCpuResetWithSingleCpuUpgrade(ContentBaseTestCase):
    """
    Glasgow_ID: 69611
    Phoenix_ID: 18014074497
    Expectation is to upgrade only single CPU with capabilities and make sure that it is not affecting the
    other CPUs.
    """
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InBandMultCpuResetWithSingleCpuUpgrade

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(OutOfBandMultiCpuResetWithSingleCpuUpgrade, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power,
                                       cfg_opts)


    def prepare(self):
        # type: () -> None
        """preparing the setup"""

        self._log.info("Start with a cold reset")
        self.perform_graceful_g3()

        self._log.info("Clear any existing payloads from the CPU")
        self._sdsi_obj.erase_payloads_from_nvram()

        super(OutOfBandMultiCpuResetWithSingleCpuUpgrade, self).prepare()

        self._log.info("Verify the SPR_SDSi_Installer by initiating --help command.")
        self._sdsi_installer.verify_sdsi_installer()

        self._log.debug("Number of sockets connected on the platform is : {}".format(self._sdsi_obj.number_of_cpu))
        assert self._sdsi_obj.number_of_cpu >= 2, "This test requires minimum 2 sockets"

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Verify the failure counters for CPU_{} after graceful G3.".format(cpu_counter + 1))
            license_key_auth_failures = self._sdsi_obj.get_license_key_auth_fail_count(cpu_counter)
            payload_auth_fail_count = self._sdsi_obj.get_license_auth_fail_count(cpu_counter)

            assert license_key_auth_failures == 0, \
                "License key failure counter is not reset to 0 for CPU_{}.".format(cpu_counter + 1)
            self._log.info("License key authentication counter is set to 0 for CPU_{}.".format(cpu_counter + 1))

            assert payload_auth_fail_count == 0, \
                "CAP authentication failure counter is not reset to 0 for CPU_{}.".format(cpu_counter + 1)
            self._log.info("CAP authentication failure counter is set to 0 for CPU_{}.".format(cpu_counter + 1))

            self._log.info("Get the CPU PPIN/Hardware ID of the CPU.")
            cpu_ppin = self._sdsi_obj.get_cpu_hw_asset_id(cpu_counter)
            self._log.info("CPU PPIN/Hardware Asset ID of the CPU_{} is '{}'".format(cpu_counter + 1, cpu_ppin))


    def execute(self):
        """
            Test case steps.
            	4. Cold reset and erase capabilities from all sockets
                5. Copying license to new SUT
                6. Apply license to all sockets
                7. Verify the license is applied.
                8. Apply a capability to socket 0
                9. Read and verify the applied capability
                10. Perform cold reset
                11. Read capability on socket 0
                    a. Read capability on other sockets, it should be null
                12. Apply Erase certificate to socket 0
                13. Confirm Erase is working
                14. Cold reset
                15. Read the capability, make sure it is empty
                16. Apply License to Socket 1
                17. Verify the license key is applied on socket 1
                18. Apply a capability to socket 1
                19. Read the capability and verify on socket 1
                20. Cold reset
                21. Read and verify the capability on socket 1
                    a. For socket 0 nothing.
                22. Apply the same capability to socket 0
                23. Read the capability on socket 0 and socket 1
                    a. Should match for both machines.
                24. Cold reset
                25. Read the capabilities in socket 0 and socket 1
                    a. Both should be matching
        """
        SOCKET_1=0
        SOCKET_2=1
        #TC Step 6 & 7
        for cpu_counter_index in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Write the licence key certificate for CPU_{}.".format(cpu_counter_index + 1))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter_index)
            available_ssku_updates = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter_index)
            self._log.info("ssku updates available after license provisioning on CPU_{} is '{}'".format(cpu_counter_index + 1, available_ssku_updates))

        # TC Step 8A  -- get applicable payloads
        self._log.info("#8A - Get applicable payloads on socket 0")
        sock1_available_payloads = self._sdsi_obj.get_applicable_payloads(socket=SOCKET_1)
        sock1_payload_keys = list(sock1_available_payloads.keys())
        self._log.info(sock1_payload_keys)
        self._log.info("Read the SSKU updates remaining and payload failure counter for CPU_{} before applying CAP.".format( SOCKET_1 + 1))
        sock1_payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=SOCKET_1)
        sock1_ssku_updates_available_before = self._sdsi_obj.get_ssku_updates_available(socket=SOCKET_1)
        sock1_valid_payload_file = sock1_available_payloads[sock1_payload_keys[1]]
        sock1_valid_payload_name = re.search(r'rev_\d*_(.*)', sock1_payload_keys[1]).group(1)
        sock1_valid_payload_rev = int(re.search(r'rev_(.+?)_', sock1_payload_keys[1]).group(1))
        sock1_valid_payload_info = [sock1_valid_payload_rev, sock1_valid_payload_name, sock1_valid_payload_file]

        #apply a cap file and verify it is applied and added to only one CPU and all others are unchanged.
        #TC Step 8B
        self._sdsi_obj.print_all_sockets_info()
        self._log.info("#8B - Apply a CAP configuration to the SUT CPU_{}.".format(SOCKET_1 + 1))
        self._sdsi_obj.apply_capability_activation_payload(sock1_valid_payload_info, SOCKET_1)
        self._sdsi_obj.print_all_sockets_info()

        #TC Step 9
        self._log.info("#9 - Read the SSKU updates remaining and payload failure counter for CPU_{} after applying CAP.".format( SOCKET_1 + 1))
        sock1_payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=SOCKET_1)
        sock1_ssku_updates_available_after = self._sdsi_obj.get_ssku_updates_available(socket=SOCKET_1)

        self._log.info("Verify the failure counter and ssku updates remaining values for CPU_{}.".format(SOCKET_1 + 1))
        assert sock1_payload_fail_count_before == sock1_payload_fail_count_after, "Expected failure counter to be {}, but found {}.".format(sock1_payload_fail_count_before, sock1_payload_fail_count_after)
        assert sock1_ssku_updates_available_before - 1 == sock1_ssku_updates_available_after, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {}".format(
            sock1_ssku_updates_available_before -1, sock1_ssku_updates_available_after)

        self._log.info( "Verify the CAP {} is available for CPU_{}.".format(sock1_valid_payload_name, SOCKET_1 + 1))
        assert self._sdsi_obj.is_payload_available( sock1_valid_payload_name, SOCKET_1),\
            "CPU_{} is not provisioned after the write operation. Payload information for {} is not found.".format( SOCKET_1 + 1, sock1_valid_payload_info[1])

        self._log.info("Verify any payload loaded into other CPUs. It suppose to be empty as all of them were erased earlier")
        for cpu_counter_index in range(self._sdsi_obj.number_of_cpu):
            if (cpu_counter_index != SOCKET_1):
                assert self._sdsi_obj.is_payload_available(sock1_valid_payload_name, cpu_counter_index) == False, \
                    "Payload '{}' is available in CPU_{}. It is not expected in a previously erased sockets".format(sock1_valid_payload_name, cpu_counter_index + 1)

        # TC Step 10
        self._log.info("#10 - Starting a Cold reset - to check the capabilities still available.")
        self.perform_graceful_g3()
        self._sdsi_obj.print_all_sockets_info()


        # TC Step 11
        self._log.info("#11 - Verify capability available only in CPU_1. Other sockets should be empty")
        for cpu_counter_index in range(self._sdsi_obj.number_of_cpu):
            if(cpu_counter_index != SOCKET_1):
                assert self._sdsi_obj.is_payload_available(sock1_valid_payload_name,cpu_counter_index) == False, \
                    "Payload '{}' is available in CPU_{}. It is not expected on a clean system".format(sock1_valid_payload_name, cpu_counter_index + 1)

        #TC Step 12
        self._log.info("#12 - Clear any existing payloads from the CPU_1")
        self._sdsi_obj.erase_payloads_from_nvram_single_socket(SOCKET_1)
        self._sdsi_obj.print_all_sockets_info()

        #TC Step 13
        self._log.info("#13 - Checking any payloads available in CPU_1")
        assert self._sdsi_obj.is_cpu_provisioned(SOCKET_1) == False, "Payload availabline CPU_1, it is not expecting"

        # TC Step 14
        self._log.info("#14 - Starting a Cold reset - to check the capabilities still available.")
        self.perform_graceful_g3()
        self._sdsi_obj.print_all_sockets_info()

        # TC Step 15
        self._log.info("#15 - Checking any payloads available in other sockets")
        for cpu_counter_index in range(self._sdsi_obj.number_of_cpu):
            assert self._sdsi_obj.is_cpu_provisioned(cpu_counter_index) == False, "Payload available in CPU_{}, it is not expecting".format(cpu_counter_index+ 1)

        # TC Step 16 & 17
        self._log.info("#16 & 17 - Checking License available in other sockets")
        for cpu_counter_index in range( self._sdsi_obj.number_of_cpu):
            assert self._sdsi_obj.is_license_key_available(cpu_counter_index) == True, "License is not availabline in CPU_{}, it was not expecting".format(cpu_counter_index+ 1)

        #TC Step 18
        sock2_available_payloads = self._sdsi_obj.get_applicable_payloads(socket=SOCKET_2)
        sock2_payload_keys = list(sock2_available_payloads.keys())
        self._log.info(sock2_payload_keys)
        self._log.info("Read the SSKU updates remaining and payload failure counter for CPU_{} before applying CAP.".format(SOCKET_2 + 1))
        sock2_payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=SOCKET_2)
        sock2_ssku_updates_available_before = self._sdsi_obj.get_ssku_updates_available(socket=SOCKET_2)
        sock2_valid_payload_file = sock2_available_payloads[sock2_payload_keys[1]]
        sock2_valid_payload_name = re.search(r'rev_\d*_(.*)', sock2_payload_keys[1]).group(1)
        sock2_valid_payload_rev = int(re.search(r'rev_(.+?)_', sock2_payload_keys[1]).group(1))
        sock2_valid_payload_info = [sock2_valid_payload_rev, sock2_valid_payload_name, sock2_valid_payload_file]

        self._log.info("#18 - Apply a CAP configuration to the SUT CPU_{}.".format(SOCKET_2 + 1))
        self._sdsi_obj.apply_capability_activation_payload(sock2_valid_payload_info, SOCKET_2)

        #TC Step 19A
        self._sdsi_obj.print_all_sockets_info()
        self._log.info("#19A - Read the SSKU updates remaining and payload failure counter for CPU_{} after applying CAP.".format(SOCKET_2 + 1))
        sock2_ssku_updates_available_after = self._sdsi_obj.get_ssku_updates_available(socket=SOCKET_2)

        self._log.info("Verify the failure counter and ssku updates remaining values for CPU_{}.".format(SOCKET_2 + 1))
        assert sock2_ssku_updates_available_before - 1 == sock2_ssku_updates_available_after, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {}".format(
            sock2_ssku_updates_available_before -1, sock2_ssku_updates_available_after)

        self._log.info( "Verify the CAP {} is available for CPU_{}.".format(sock2_valid_payload_name, SOCKET_2 + 1))
        assert self._sdsi_obj.is_payload_available(sock2_valid_payload_name, SOCKET_2) == True,\
            "CPU_{} is not provisioned after the write operation. Payload information for {} is not found.".format( SOCKET_2 + 1, sock2_valid_payload_info[1])


        #TC Step 19B
        self._log.info("Verifying any payload is loaded in another sockets. We are not expecting any payloads on other sockets")
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            if (cpu_counter != SOCKET_2):
                assert self._sdsi_obj.is_payload_available(sock2_valid_payload_name, cpu_counter) == False, \
                    "Payload '{}' is available in CPU_{}. It is not expected on a clean system".format( sock2_valid_payload_name, cpu_counter + 1)


        #TC Step 20
        self._log.info("#20 - Starting a Cold reset  to check the capabilities  available even after cold reset.")
        self.perform_graceful_g3()

        #TC Step 21A
        self._sdsi_obj.print_all_sockets_info()
        self._log.info("#21A - Verify the CAP {} is available for CPU_{}.".format(sock2_valid_payload_name, SOCKET_2 + 1))
        assert self._sdsi_obj.is_payload_available(sock2_valid_payload_name, SOCKET_2) == True, \
            "CPU_{} is not provisioned after the reboot operation. Payload information for {} is not found.".format(
                SOCKET_2 + 1, sock2_valid_payload_info[1])

        #TC Step 21B
        self._log.info("#21B - Verify capability available only in CPU_1. Other sockets should be empty")
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            if (cpu_counter != SOCKET_2):
                assert self._sdsi_obj.is_payload_available(sock2_valid_payload_name, cpu_counter) == False, \
                    "Payload '{}' is available in CPU_{}. It was not expected on a clean system".format(
                        sock2_valid_payload_name, cpu_counter + 1)

        #TC Step 22
        self._log.info("#22 - Apply a CAP configuration to the SUT CPU_{}.".format(SOCKET_1 + 1))
        self._sdsi_obj.apply_capability_activation_payload(sock1_valid_payload_info, SOCKET_1)

        #TC Step 23
        self._sdsi_obj.print_all_sockets_info()
        self._log.info("#23 - Verify Socket 0 and 1 having the same payload available")
        assert self._sdsi_obj.is_payload_available(sock1_valid_payload_name,SOCKET_1) == True, "Pay load {} is not available  in socket 1".format(sock1_valid_payload_name)
        assert self._sdsi_obj.is_payload_available(sock2_valid_payload_name,SOCKET_2) == True, "Pay load {} is not available  in socket 2".format(sock2_valid_payload_name)

        #TC Step 24
        self._log.info("#24 - Starting a Cold reset - to check the capabilities available even after cold reset")
        self.perform_graceful_g3()

        #TC Step 25
        self._sdsi_obj.print_all_sockets_info()
        self._log.info("#23 - Verify Socket 1 and 2 having the same ssku_updates_available")
        socket_1_ssku_available = self._sdsi_obj.get_ssku_updates_available(socket=SOCKET_1)
        socket_2_ssku_available = self._sdsi_obj.get_ssku_updates_available(socket=SOCKET_2)
        assert socket_1_ssku_available == 2, "ssku_updates_available {} is less than 2 for the socket 1".format(socket_1_ssku_available)
        assert socket_2_ssku_available == 2, "ssku_updates_available {} is less than 2 for the socket 2".format(socket_2_ssku_available)
        assert self._sdsi_obj.is_payload_available(sock1_valid_payload_name,SOCKET_1) == True, "Pay load {} is not available  in socket 1".format(sock1_valid_payload_name)
        assert self._sdsi_obj.is_payload_available(sock2_valid_payload_name,SOCKET_2) == True, "Pay load {} is not available  in socket 2".format(sock2_valid_payload_name)

        return True


    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(OutOfBandMultiCpuResetWithSingleCpuUpgrade, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutOfBandMultiCpuResetWithSingleCpuUpgrade.main()
             else Framework.TEST_RESULT_FAIL)
