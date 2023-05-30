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

from dtaf_core.lib.dtaf_constants import Framework
from src.memory.tests.memory_cr.apache_pass.cycling.cr_cycling_common import CrCyclingCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_2lm_mixed_mode_50_50_interleaved_dax_linux \
    import CRProvisioning2LM50AppDirect50MemoryModeDaxLinux


class CrWarmResetGracefulOsRestartEadrMultiCPULinux(CrCyclingCommon):
    """
    Glasgow ID: 59995
    Verification of the platform supported DCPMM Peformance capabilities by using DCPMM Platform Cycler in a Linux Os
    environment.

    1. Configure platform with CPUs, Memory and Linux OS.
    2. Configure Provisioning with memory and app drirect mode
    2. Run dcpmm reboot cycler.
    3. Collect and analyze log output files to confirm performance is as per established expectations.
    4. Verify no unexpected errors were logged while executing tool.

    """

    BIOS_CONFIG_FILE = "cr_warm_reset_graceful_os_restart_eadr_multicpu_linux.cfg"
    TEST_CASE_ID = "G59995"

    _dcpmm_platform_cycler_file_path = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CrDiskSpdAppDirectBenchmarkWindows object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(CrWarmResetGracefulOsRestartEadrMultiCPULinux, self).__init__(test_log, arguments, cfg_opts,
                                                                            self.BIOS_CONFIG_FILE)

        # calling CRProvisioning2LM50AppDirect50MemoryModeDaxLinux
        self._cr_provisioning_50appdirect = CRProvisioning2LM50AppDirect50MemoryModeDaxLinux(self._log, arguments,
                                                                                             cfg_opts)
        self._cr_provisioning_50appdirect.prepare()
        self._cr_provisioning_50appdirect.execute()

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.
        5. Copy zipped DCPMM Platform Cycler Tool to SUT
        6. Unzip it.

        :return: None
        """

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        self._dcpmm_platform_cycler_file_path = self._install_collateral.install_dcpmm_platform_cycler()  # To install
        # DCPMM Platform cycler tool

    def execute(self):
        """
        Function is responsible for the below tasks,

        1. Confirm persistent memory regions are configured as expected.
        2. Performance metrics for each DCPMM DIMM.
        3. Execute dcpmm reboot cycle as specified in the test case.
        4. Check all the cyler logs for unexpected errors.

        :return: True, if the test case is successful else false
        :raise: None
        """

        return_value = []

        # Show present namespaces
        namespace_info = self._cr_provisioning_50appdirect.dcpmm_get_disk_namespace()

        #  Verify namespace presence
        return_value.append(self._cr_provisioning_50appdirect.verify_pmem_device_presence(namespace_info))

        #  Execute DCPMM reboot cycler
        return_value.append(self.execute_dcpmm_reboot_cycler(self._dcpmm_platform_cycler_file_path))

        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LINUX_PLATFORM_REBOOTER_LOG_PATH, extension=".log")

        # Verify All reboot cycler logs
        return_value.append(self.log_parsing_rebooter(log_path_to_parse))

        return all(return_value)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CrWarmResetGracefulOsRestartEadrMultiCPULinux.main()
             else Framework.TEST_RESULT_FAIL)
