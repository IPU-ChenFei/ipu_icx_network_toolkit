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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.dc_power import DcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.common_content_lib import CommonContentLib
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class SubNumaClustering(TxtBaseTest):
    """
    PHOENIX ID : 18014070367-Sub Numa Clustering (SNC)

    """
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    SELF_CONFIG_FILE = "security_snc_enable.cfg"
    _TEST_CASE_ID = ["Sub Numa Clustering (SNC)", "18014070367"]
    step_data_dict = {1: {'step_details': 'Enable SNC in the BIOS menu',
                          'expected_results': 'SNC is enabled successfully'},
                      2: {'step_details': 'enable TXT BIOS knobs',
                          'expected_results': 'System entered the TXT environment successfully'},
                      3: {'step_details': 'Reboot system to apply changes, boot to Tboot.',
                          'expected_results': ''},
                      4: {'step_details': 'confirm that SUT boots trusted.',
                          'expected_results': 'Trusted Boot with tboot'},
                      5: {'step_details': 'Execute" numactl -a -H" on the SUT',
                          'expected_results': 'There should be twice the number of nodes as there are iMCs'},
                      6: {'step_details': 'Surprise reset the system',
                          'expected_results': ''},
                      7: {'step_details': 'Repeat steps 5-6 .',
                          'expected_results': ''},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SubNumaClustering

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        """
        super(SubNumaClustering, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self.snc_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.SELF_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self._TEST_CASE_ID, self.step_data_dict)
        self._common_obj = CommonContentLib(self._log, self._os, cfg_opts)
        dc_cfg = cfg_opts.find(DcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._dc = ProviderFactory.create(dc_cfg, test_log)  # type: DcPowerControlProvider
        self._dc_delay = self._common_content_configuration.dc_power_sleep_time()
        self.PACKAGE_NUMACTL = "numactl"
        self.numactl_cmd = "numactl -a -H"

    def prepare(self):
        """"""
        self.tboot_index = self.get_tboot_boot_position()
        self.set_default_boot_entry(self.tboot_index)
        self._bios_util.load_bios_defaults()
        self._bios_util.set_bios_knob()
        self._os.reboot(self._reboot_timeout)
        self._bios_util.verify_bios_knob()

    def surprise_reset(self):
        """
        This function performs the DC reset to the platform

        :raise: RuntimeError: If Fail to perform DC power off，If Fail to perform DC power ON
        :return: None
        """
        if self._dc.dc_power_off():
            self._log.info("DC power is turned OFF")
        else:
            self._log.error("DC power is not turned OFF")
            raise RuntimeError("DC power is not turned OFF")
        time.sleep(self._dc_delay)
        if self._dc.dc_power_on():
            self._log.info("DC power is turned ON")
        else:
            self._log.error("DC power is not turned ON")
            raise RuntimeError("DC power is not turned ON")

    def stage_numa_tracking(self, numa_nodes):  # type: (str) -> None
        """Set up list to track numa nodes for all applicable sockets and which sockets to which nodes.
           :param numa_nodes: nodes info
        """
        numa_nodes = numa_nodes.split('\n')
        node_data = []
        for node in numa_nodes:
            split_node = node.split(":")
            if len(split_node) >= 2:
                key = split_node[0].strip()
                value = split_node[1].lstrip()
                node_dict = {key: value}
                node_data.append(node_dict)
        self._log.debug("Numa mapping is done.")

    def execute(self):
        """
        This Function execute the test case
        1. Enable SNC in the BIOS menu
        2. enable TXT BIOS knobs
        3. Reboot system to apply changes, boot to Tboot
        4. confirm that SUT boots trusted
        5. Execute" numactl -a -H" on the SUT
        6. Surprise reset the system
        7. of this test case to confirm that SNC is still enabled and that the SUT recovered to a trusted state.
        :return: True if test is passed
        """
        self._test_content_logger.start_step_logger(1)
        # Enable and verify SNC
        self._log.info("Enable SNC")
        self._bios_util.set_bios_knob(bios_config_file=self.snc_bios_config_file)
        self.perform_graceful_g3()
        self._bios_util.verify_bios_knob(bios_config_file=self.snc_bios_config_file)
        self._log.info("SNC enable success")
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._log.info("enable txt")
        self._test_content_logger.start_step_logger(2)
        self.enable_and_verify_bios_knob()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self._log.info("Reboot system to apply changes, boot to Tboot.")
        self._os.reboot(self._reboot_timeout)
        self.tboot_index = self.get_tboot_boot_position()  # Get the Tboot_index from grub menu entry
        self.set_default_boot_entry(self.tboot_index)  # Set Tboot as default boot
        self.perform_graceful_g3()
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self._log.info("confirm that SUT boots trusted.")
        self._os.reboot(self._reboot_timeout)  # To apply Bios changes
        # check if trusted boot
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if the system booted in Trusted mode.
        self._os.reboot(self._reboot_timeout)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self._log.info("Execute ‘numactl -a -H’ on the SUT and ensure cores are divided evenly into nodes. ")
        cmd_res = self._os.execute(self.numactl_cmd, self._command_timeout)
        self._log.info("command : {} result is : {}".format(self.numactl_cmd, cmd_res.stdout))
        self.stage_numa_tracking(cmd_res.stdout)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self._log.info(
            "Surprise reset the system with the front panel power button or RSC/remote button control. Allow system to boot back to Tboot.")
        self.surprise_reset()  # Implementation varies based on child classes.
        self._log.info("Wait till the system comes alive...")
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if the system booted in Trusted mode.
        self._os.wait_for_os(self._reboot_timeout)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        self._log.info(
            "Repeat steps 5-6 of this test case to confirm that SNC is still enabled and that the SUT recovered to a trusted state.")
        self._log.info("confirm that SUT boots trusted.")
        self._log.info("Execute ‘numactl -a -H’ on the SUT and ensure cores are divided evenly into nodes. ")
        cmd_res = self._os.execute(self.numactl_cmd, self._command_timeout)
        self._log.info("command : {} result is : {}".format(self.numactl_cmd, cmd_res.stdout))
        self.stage_numa_tracking(cmd_res.stdout)
        self._test_content_logger.end_step_logger(7, return_val=True)

    def cleanup(self, return_status):  # type: (bool) -> None
        super(SubNumaClustering, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SubNumaClustering.main() else Framework.TEST_RESULT_FAIL)
