#!/usr/bin/env python
###############################################################################
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
###############################################################################
import sys
import time

from src.lib.content_base_test_case import ContentBaseTestCase
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.install_collateral import InstallCollateral
from src.provider.memory_provider import MemoryProvider
from src.lib.test_content_logger import TestContentLogger
from src.provider.ptu_provider import PTUProvider
from src.lib.dtaf_content_constants import PcmMemoryConstants, TimeConstants


class PowerManagementMEMTRIPEventLinux(ContentBaseTestCase):
    """
    HPALM ID : H102256-PI_PowerManagement_MEMTRIP_Event_L
    This function will install ptu and mlc checks the dimms temperatures
    """

    TEST_CASE_ID = ["H102256", "PI_PowerManagement_MEMTRIP_Event_L"]
    PCM_CMD = "./pcm-memory.x --external_program -all"
    PTU_CMD = "./ptu -mon -t 60"
    CHMOD_MLC = "chmod 777 mlc"
    MLC_SEQ_READ_1HR = "./mlc --loaded_latency -T -Z -d0 -B -t60"
    ZERO = 0
    TWO = 2
    FOUR = 4

    step_data_dict = {1: {'step_details': 'Show all DPC locators ',
                          'expected_results': 'To get list of locators'},
                      2: {'step_details': 'Run PCM-memory.x Command and check for errors',
                          'expected_results': 'PCM-memory command should run without any error'},
                      3: {'step_details': 'Install ptu tool and run monitor for 600s',
                          'expected_results': 'Ptu tool should run without any error'},
                      4: {'step_details': 'Run MLC with seq read for 1hour',
                          'expected_results': 'MLC command should run seq mpde for 3600s'},
                      5: {'step_details': 'Set the temperature high,mid,low and Threshold for socket0-1,'
                                          'memory channel0-1-2-3,channel0-1',
                          'expected_results': 'Read the temperature high,mid,low,threshold for dimm channels'},
                      6: {'step_details': 'Read the Memtrip values for dimm channels',
                          'expected_results': 'Threshold memtrip should be 0x1'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PowerManagementMEMTRIPEventLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(PowerManagementMEMTRIPEventLinux, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._memory_provider = MemoryProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self._ptu_provider = PTUProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PowerManagementMEMTRIPEventLinux, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        This function install ptu tool and execute the pcm&mcl commands to apply dimm temperature
        after apply temperature read the threshold values
        :return: True if test completed successfully, False otherwise.
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        dpc_locators = self._memory_provider.get_list_off_locators()
        self._log.info("Connected DPC list: {}".format(dpc_locators))
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        pcm_memory_tool_path = self._install_collateral.install_pcm_memory_tool()
        self.os.execute(self.PCM_CMD, self._command_timeout, pcm_memory_tool_path)
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        ptu_tool_path = self._ptu_provider.install_ptu()
        self._install_collateral.screen_package_installation()
        self._log.info("executing command : {}".format(self.PTU_CMD))
        self.os.execute_async(self.PTU_CMD, cwd=ptu_tool_path)
        time.sleep(TimeConstants.TEN_MIN_IN_SEC)
        # To kill the PTU Tool
        self._ptu_provider.kill_ptu_tool()
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        mlc_tool_path = self._install_collateral.install_mlc_linux()
        self._common_content_lib.execute_sut_cmd(self.CHMOD_MLC, self.CHMOD_MLC, self._command_timeout, mlc_tool_path)
        self._log.info("Executable privileges has been assigned successfully...")
        self._log.info("executing command : {}".format(self.MLC_SEQ_READ_1HR))
        self._common_content_lib.execute_sut_cmd(self.MLC_SEQ_READ_1HR, self.MLC_SEQ_READ_1HR,
                                                 self._command_timeout + TimeConstants.ONE_HOUR_IN_SEC, mlc_tool_path)
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)
        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self.SDP.itp.unlock()
        for socket_info in range(self.ZERO, self.TWO):
            for memory_info in range(self.ZERO, self.FOUR):
                for channel_info in range(self.ZERO, self.TWO):
                    socket_attr = getattr(self.SV._sv, f'socket{socket_info}')
                    mc_attr = getattr(socket_attr.uncore.memss, f'mc{memory_info}')
                    ch_attr = getattr(mc_attr, f'ch{channel_info}')
                    # dimm_temp = self._sv.socket0.uncore.memss.mc0.ch0.dimmtempstat_0.dimm_temp
                    dimm_temp = ch_attr.dimmtempstat_0.dimm_temp
                    ch_attr.dimm_temp_th_0.temp_hi = dimm_temp - PcmMemoryConstants.HEX_VALUES[0]
                    ch_attr.dimm_temp_th_0.temp_mid = dimm_temp - PcmMemoryConstants.HEX_VALUES[1]
                    ch_attr.dimm_temp_th_0.temp_lo = dimm_temp - PcmMemoryConstants.HEX_VALUES[2]
                    ch_attr.dimm_temp_refresh_0.temp_memtrip = dimm_temp - PcmMemoryConstants.HEX_VALUES[3]

        # Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)
        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)
        memtrip_value_st0 = self.SV._sv.socket0.uncore.punit.stat_temptrip_cfg.stat_memtrip0
        self._log.info("Mem trip value socket 0 : {}".format(memtrip_value_st0))
        memtrip_value_st1 = self.SV._sv.socket1.uncore.punit.stat_temptrip_cfg.stat_memtrip0
        self._log.info("Mem trip value socket 1 : {}".format(memtrip_value_st0))
        if memtrip_value_st0 and memtrip_value_st1:
            self._log.info("Memtrip values is reached successfully to 0x1")
        else:
            self._log.error("Memtrip values were unsuccessful to reach 0x1")
            return False
        # Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PowerManagementMEMTRIPEventLinux, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementMEMTRIPEventLinux.main() else Framework.TEST_RESULT_FAIL)
