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

import time
import os
import re
import threading
from xml.etree import ElementTree
import filecmp

from dtaf_core.lib.exceptions import OsCommandTimeoutException
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.dc_power import DcPowerControlProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import ProviderXmlConfigs, MemoryHealthCheck
from src.lib.dtaf_content_constants import PowerStates
from src.lib.dtaf_content_constants import ResetStatus
from src.lib.dtaf_content_constants import PlatformType
from src.lib.dtaf_content_constants import ExecutionEnv
from src.lib.dtaf_content_constants import HealthCheckFailures, PythonSvDump
from src.provider.memory_provider import MemoryProvider
from src.lib.post_codes import PostCodes
from src.provider.cpu_info_provider import CpuInfoProvider
from src.provider.pcie_provider import PcieProvider
from src.power_management.lib.power_state_utils import SleepStateExecutor
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions


class HealthCheck:
    UPI_SERIAL_LOG_CHECK = "System will be treated (\dS\dL) Configuration"
    UPI_HEALTH_PYSV_REGEX = "(.*) Topology"
    IGNORE_PORT = "Port 3,"
    LINK_SPEED_MATCH = {
        "Link Speed": "16.0 GT/s",
        "Setting": "Fast Mode",
        "Status": "Fast Mode",
        "Tx State": "L0",
        "Rx State": "L0"
    }
    PCI_HEALTH_CHECK = "pcie_health_check"
    MEMORY_HEALTH_CHECK = "memory_health_check"
    UPI_HEALTH_CHECK = "upi_health_check"

    CLOCK_HEALTH_CHECK = "clock_health_check"

    UPI_MESH_TOPOLOGY_EXPECTED = ["CPU0 : LEP0(1:CPU1) : LEP1(0:CPU3) : LEP2(2:CPU2)",
                                  "CPU1 : LEP0(1:CPU2) : LEP1(0:CPU0) : LEP2(2:CPU3)",
                                  "CPU2 : LEP0(1:CPU3) : LEP1(0:CPU1) : LEP2(2:CPU0)",
                                  "CPU3 : LEP0(1:CPU0) : LEP1(0:CPU2) : LEP2(2:CPU1)"]

    HEALTH_CHECKS = {
        PCI_HEALTH_CHECK: True,
        MEMORY_HEALTH_CHECK: False,
        UPI_HEALTH_CHECK: True
    }


class BootFlow:
    POWER_ON = "PowerOn"
    POWER_OFF = "PowerOff"


class ResetBaseTest(ContentBaseTestCase):
    """
    Base test class for reset cycle testing
    """

    OS_TYPES = ["s3", "s4", "warm_reset"]
    RSC_TYPES = ["graceful_s5", "graceful_g3", "surprise_reset", "surprise_s5", "surprise_g3"]
    SURPRISE_TYPES = ["surprise_reset", "surprise_s5", "surprise_g3"]
    OS_TYPES_LIST = ["Linux", "Windows"]
    SUPPORTED_TYPES = OS_TYPES.extend(RSC_TYPES)
    DEFAULT_RESET_TYPE = "warm_reset"
    DEFAULT_ITERATIONS = 25
    DEFAULT_RESET_VECTOR = "linux_os"
    SX_SLEEP_TIME = 150
    G3_DELAY = S5_DELAY = 180
    RESET_DELAY = 400
    POST_SLEEP_DELAY = 30
    AC_POWER_DELAY = 20
    DC_POWER_DELAY = 5
    SLEEP_TIME = 30
    BURNIN_TEST_CMD = "./bit_cmd_line_x64 -B -D %d -C cmdline_config.txt -d"
    BURNIN_LOCAL_DEBUG_LOG = "bit_debug_log.log"
    BURNIN_TEST_DEBUG_LOG = "debug.log"
    BURNIN_TEST_START_MATCH = " Parent PID "
    BURNIN_TEST_END_MATCH = "###################### STOP_TEST_DEBUG_FINISHES ######################"
    COLD_RESET_CMD_LINUX = r"outb 0xcf9 0xe"
    __HEALTH_CHECK_DIR = "health_check"
    _MCE_CHECK = True
    ENABLE_SLEEP_CMD = "RUNDLL32.EXE powrprof.dll,SetSuspendState 0,1,0"
    LINUX_SLEEP_CMD = "sudo systemctl suspend"
    HIBERNATE_CMD = "shutdown /h"
    SLEEP_CMD_TIMEOUT = 30
    WAITING_TIME_FOR_STATE_CHANGE = 600
    ENABLE_HIBERNATE_CMD = "powercfg /H ON"
    LINUX_HIBERNATE_CMD = "sudo systemctl hibernate"
    DISABLE_HIBERNATE_CMD = "powercfg /H OFF"
    STATE_VERIFICATION_CMD = "powercfg /a"
    REGEX_FOR_HIBERNATE_MODE = r"Hibernate"
    CLOCK_COMMAND_LINUX = r"cat /sys/devices/system/clocksource/clocksource0/current_clocksource"
    REGEX_FOR_AVAILABLE_SLEEP_MODES = r"The following sleep states are not available on this system:"
    PC_STUCK_TIMEOUT = 900
    NUMBER_OF_RECOVERY_ATTEMPTS = 5

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Creates a New ResetBaseTest Object

        """
        super(ResetBaseTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

        dc_power_cfg = cfg_opts.find(DcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._dc_power = ProviderFactory.create(dc_power_cfg, test_log)  # type: DcPowerControlProvider
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self._cpu_provider = CpuInfoProvider.factory(test_log, cfg_opts, self.os)
        self._psu = SleepStateExecutor(self._log, self.os)
        self.health_check_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.__HEALTH_CHECK_DIR,
                                             self.os.os_type.lower())

        self.health_check = self._common_content_configuration.get_health_check_value()
        self._log.info("Is health check required?: %s", self.health_check)
        self._log.info("Health check scripts directory: %s", self.health_check_dir)
        self.health_check_log_dir = os.path.join(self.log_dir, "health_check")

        self.ignore_mce_error = self._common_content_configuration.get_ignore_mce_errors_value()

        self.pc_stuck_time_out = self._common_content_configuration.get_pc_stuck_time()
        self.machine_check = self._common_content_configuration.get_ignore_machine_check()
        if self.pc_stuck_time_out == 0:
            self.pc_stuck_time_out = self.PC_STUCK_TIMEOUT

        self.log_or_fail = False
        post_codes = PostCodes()
        self.os_post_codes = post_codes.get_os_post_codes(self._platform_type)
        if self.health_check:
            os.makedirs(self.health_check_log_dir)
            HealthCheck.LINK_SPEED_MATCH["Link Speed"] = self._common_content_configuration.get_dpmo_link_speed()

        self.stop_post_code = False
        self.reset_type = None

        # ignore PC errors list
        self._list_ignore_pc_errors = []

        self.stop_on_failure_flag = False
        self._failed_pc = None
        self._boot_flow = None
        self._prev_cycle_num = 0
        self._number_of_failures = 0
        self._number_of_success = 0
        self._list_failures = []
        # axon logs
        self.sdp = None  # type: SiliconDebugProvider
        self.sv = None  # type: SiliconRegProvider
        self.fail_once = True

        self._pcie_obj = None
        self.cfg = cfg_opts
        self.memory_info = None
        self._perform_pcie_health_check = True
        self._pcie_init_snapshot_name = "PciInitialSnapshot.log"
        self.memory_provider = MemoryProvider.factory(self._log, cfg_opts=self.cfg, os_obj=self.os)
        self._pcie_init_snapshot_log_file = os.path.join(self.health_check_log_dir, self._pcie_init_snapshot_name)

        cycling_summary_file = os.path.join(self.log_dir, "cycling_summary.csv")
        self.summary_file = open(cycling_summary_file, 'w')
        self.summary_file.write("Cycle#,Status,Previous Failure Cycle#,Remarks\n")
        self.summary_file.flush()

        self.reset_handlers = {ResetStatus.SUCCESS: self.handle_reset_success,
                               ResetStatus.PC_STUCK: self.handle_reset_pc_stuck_failure,
                               ResetStatus.DC_FAILURE: self.handle_reset_dc_failure,
                               ResetStatus.AC_FAILURE: self.handle_reset_ac_failure,
                               ResetStatus.STATE_CHANGE_FAILURE: self.handle_reset_state_change_failure,
                               ResetStatus.OS_NOT_ALIVE: self.handle_reset_os_not_alive_failure}

        self.list_stop_on_failure = self._common_content_configuration.get_stop_on_failure_value()
        self.dict_health_check_handlers = {HealthCheckFailures.PCIE: self.pci_health_check,
                                           HealthCheckFailures.DMI: self.dmi_check,
                                           HealthCheckFailures.UPI: self.upi_topology_check,
                                           HealthCheckFailures.MCE: self.mc_status_health_check,
                                           HealthCheckFailures.DIMM_THERMAL: self.dimm_thermal_status_health_check,
                                           HealthCheckFailures.CPU_THERMAL: self.cpu_thermal_status_health_check,
                                           HealthCheckFailures.MEMORY_CHECK: self.system_memory_health_check}

    def cleanup(self, return_status):
        """Test Cleanup"""
        self.summary_file.close()
        if self.stop_on_failure_flag is True:
            self._log.info("Stopping the test - \"stop on failure\" is enabled")
            pass
        else:
            super(ResetBaseTest, self).cleanup(return_status)

    def suspend_sut_to_ram(self):
        """
        Suspend SUT to RAM and wait for system to resume.

        :return: result
        """
        result = self._psu.sleep_cycle(self._psu.S3, self.os)
        time.sleep(self.POST_SLEEP_DELAY)
        return result

    def suspend_sut_to_disk(self):
        """
        Suspend SUT to disk and wait for system to resume.

        :return: result
        """
        result = self._psu.sleep_cycle(self._psu.S4, self.os)
        time.sleep(self.POST_SLEEP_DELAY)
        return result

    def fail_or_log(self, message, log_or_fail=True):
        if log_or_fail:
            raise content_exceptions.TestFail(message)
        else:
            self._log.error(message)

    def __pythonsv_log_dump(self, itteration):
        """
        This method is to dump all pythonsv log.

        :param itteration
        """
        domains_list = self._common_content_configuration.get_python_sv_dump_list()
        if not domains_list:
            return

        if self._common_content_configuration.get_python_sv_dump_list():
            self.pythonsv_dump_log_dir = os.path.join(self.log_dir, "pythonsv_dump_{}".format(itteration))
            self._log.info("creating python_sv_dump directory - {}".format(self.pythonsv_dump_log_dir))
            os.makedirs(self.pythonsv_dump_log_dir)
            if os.path.exists(self.pythonsv_dump_log_dir):
                self._log.info("{} directory got created".format(self.pythonsv_dump_log_dir))
        self.initialize_sdp_sv_objects()

        def mca_dump():
            """
            This method is to dump the MCA log.
            """
            mca_log_file = "mca_dump_{}.log".format(itteration)
            mca_log_file_path = os.path.join(self.pythonsv_dump_log_dir, mca_log_file)
            mca_obj = self.sv.get_mca_dump_object()
            self.sdp.start_log(mca_log_file_path)
            mca_obj.mca_dump_spr()
            self.sdp.stop_log()

        def mcu_dump():
            """
            this method is to dump MCU dump Log.
            """
            mcu_dump_file = "mcu_dump_{}.log".format(itteration)
            mcu_dump_file_path = os.path.join(self.pythonsv_dump_log_dir, mcu_dump_file)
            mcu_obj = self.sv.get_mcu_dump_object()
            self.sdp.start_log(mcu_dump_file_path)
            mcu_obj.show_memory_errors()
            mcu_obj.show_errors()
            self.sdp.stop_log()

        def upi_dump():
            """
            This method is to dump upi Log.
            """
            upi_status_dump_file = "upi_status_dump_{}.log".format(itteration)
            upi_status_dump_file_path = os.path.join(self.pythonsv_dump_log_dir, upi_status_dump_file)
            upi_status_obj = self.sv.get_upi_status_obj()
            self.sdp.start_log(upi_status_dump_file_path)
            upi_status_obj.printErrors()
            upi_status_obj.printDebug()
            upi_status_obj.printCapid()
            upi_status_obj.printFuse()
            upi_status_obj.printLinkSpeed()
            upi_status_obj.printLink()
            upi_status_obj.printPhy()
            upi_status_obj.printInfo()
            upi_status_obj.printTopology()
            upi_status_obj.printMisc()
            self.sdp.stop_log()

        def upi_error_dump():
            """
            This method is to dump UPI error Log.
            """
            upi_error_dump_file = "upi_error_dump_{}.log".format(itteration)
            upi_error_dump_file_path = os.path.join(self.pythonsv_dump_log_dir, upi_error_dump_file)
            out_put = self.sv.get_by_path(self.sv.SOCKETS, "uncore.upi.upis.kti_mc_misc").read()
            with open(upi_error_dump_file_path, "w") as fp:
                fp.write(str(out_put))

            output = self.sv.get_by_path(self.sv.SOCKETS, "uncore.upi.upis.kti_mc_st")
            with open(upi_error_dump_file_path, "a") as fp:
                fp.write(str(output))

        def s3m_dump():
            """
            This method is to s3m dump.
            """
            s3m_dump_file = "s3m_dump_{}.log".format(itteration)
            s3m_dump_file_path = os.path.join(self.pythonsv_dump_log_dir, s3m_dump_file)
            s3m_obj = self.sv.get_s3m_obj()
            self.sdp.start_log(s3m_dump_file_path)
            s3m_obj.debug_log()
            self.sdp.stop_log()

        def pmc_dump():
            # TODO: command was not working.
            pass

        def punit_dump():
            """
            This method is to dump punit log.
            """
            punit_file = "punit_dump_{}.log".format(itteration)
            punit_file_path = os.path.join(self.pythonsv_dump_log_dir, punit_file)
            self.sdp.start_log(punit_file_path, "w")
            self.sv.get_by_path(self.sv.SOCKETS, "taps.punit_ebc_ds.ebc_state_status.ebc_state_val").show()
            self.sv.get_by_path(self.sv.SOCKET, "taps.punit_ebc_ds.ebc_input_status.dfxagg_early_boot_done").show()
            self.sdp.stop_log()
            out_put = self.sv.get_by_path(self.sv.SOCKETS, "uncore.punit.mc_status")
            with open(punit_file_path, "a") as fp:
                fp.write(str(out_put))

        def pcu_data():
            """
            This method is to dump PCU data.
            """
            pcu_data_dump_file = "pcu_data_dump_{}.log".format(itteration)
            pcu_data_dump_file_path = os.path.join(self.pythonsv_dump_log_dir, pcu_data_dump_file)
            self.sv.get_by_path(self.sv.SOCKETS, "pcudata").logregisters(pcu_data_dump_file_path)

        def pmc_debug():
            # TODO: Command is not working
            pass

        def pmc_histo():
            # TODO: Command is not working
            pass

        def ebc_state():
            """
            This method is to Dump ebc state Log.
            """
            ebc_state_file = "ebc_state_dump_{}.log".format(itteration)
            ebc_state_file_path = os.path.join(self.pythonsv_dump_log_dir, ebc_state_file)
            self.sdp.start_log(ebc_state_file_path)
            self.sv.get_by_path(self.sv.SOCKETS, "taps.punit_ebc_ds.ebc_state_status.ebc_state_val").show()
            self.sdp.stop_log()

        def ddr_phy_dump():
            """
            This method is to dump phy log.
            """
            ddr_phy_dump_file = "ddr_phy_dump_{}.log".format(itteration)
            ddr_phy_dump_path = os.path.join(self.pythonsv_dump_log_dir, ddr_phy_dump_file)
            self.sv.get_by_path(self.sv.SOCKETS, "uncore.ddrphy").logregisters(ddr_phy_dump_path)

        def memss_dump():
            """
            This method is to dump memss Log.
            """
            memss_dump_file = "memss_dump_{}.log".format(itteration)
            memss_dump_file_path = os.path.join(self.pythonsv_dump_log_dir, memss_dump_file)
            self.sv.get_by_path(self.sv.SOCKETS, "uncore.memss").logregisters(memss_dump_file_path)

        def s3m_cfr_check():
            """
            This method is to dump s3m cfr check Log.
            """
            s3m_cfr_check_file = "s3m_cfr_check_{}.log".format(itteration)
            s3m_cfr_check_path = os.path.join(self.pythonsv_dump_log_dir, s3m_cfr_check_file)
            reg_path_list = ["uncore.ibl.uarch_d0.ibl_apb_treg.s3m_s3mfw_revid",
                             "uncore.ibl.uarch_d0.ibl_apb_treg.s3m_pucode_revid.s3m_pucode_commited_revid",
                             "uncore.ibl.uarch_d0.ibl_apb_treg.s3m_pucode_revid.s3m_pucode_uncommited_revid"]
            for each_reg in reg_path_list:
                output = self.sv.get_by_path(self.sv.SOCKETS, each_reg)
                with open(s3m_cfr_check_path, "a") as fp:
                    out_put_to_log = "PythonSV Command:- {} \n Output - ".format(each_reg) + str(output)
                    fp.write(out_put_to_log)

        def sut_soft_hard_hung():
            """
            This method is to dump Sut soft hard hung Log.
            """
            sut_soft_hard_hung_file = "sut_soft_hard_hung_{}.log".format(itteration)
            sut_soft_hard_hung_file_path = os.path.join(self.pythonsv_dump_log_dir, sut_soft_hard_hung_file)

            self.sdp.start_log(sut_soft_hard_hung_file_path)
            self.sv.refresh()
            self.sdp.stop_log()

            out_put = self.sv.get_by_path(self.sv.SOCKETS, "uncore.ubox.ncevents.mcerrloggingreg").show()

            with open(sut_soft_hard_hung_file_path, "a") as fp:
                fp.write(str(out_put))

        pythonsv_dump_dict = {PythonSvDump.MCA_DUMP: mca_dump,
                              PythonSvDump.MCU_DUMP: mcu_dump,
                              PythonSvDump.UPI_DUMP: upi_dump,
                              PythonSvDump.UPI_ERROR_DUMP: upi_error_dump,
                              PythonSvDump.S3M_DUMP: s3m_dump,
                              PythonSvDump.PMC_DUMP: pmc_dump,
                              PythonSvDump.PUNIT_DUMP: punit_dump,
                              PythonSvDump.PCU_DATA: pcu_data,
                              PythonSvDump.PMC_DEBUG: pmc_debug,
                              PythonSvDump.PMC_HISTO: pmc_histo,
                              PythonSvDump.EBC_STATE: ebc_state,
                              PythonSvDump.DDR_PHY_DUMP: ddr_phy_dump,
                              PythonSvDump.MEMSS_DUMP: memss_dump,
                              PythonSvDump.S3M_CFR_CHECK: s3m_cfr_check,
                              PythonSvDump.SUT_SOFT_HARD_HUNG: sut_soft_hard_hung}

        #  preparing handler list
        if "all" in domains_list:
            pythonsv_dump_handlers = list(pythonsv_dump_dict.values())
        else:
            pythonsv_dump_handlers = [pythonsv_dump_dict[each_func] for each_func in domains_list if
                                      pythonsv_dump_dict.get(each_func)]

        for each_handler in pythonsv_dump_handlers:
            self._log.info("PythonSV Dump in progress for- {}".format(each_handler))
            each_handler()
            self._log.info("PythonSV Dump completed for - {}".format(each_handler))

    def __shutdown_sut(self):
        max_attempts = 5
        attempt_num = 1
        is_shutdown = False

        while attempt_num <= max_attempts:
            self._log.info("Attempt#%d: Shutting down the SUT.", attempt_num)
            attempt_num = attempt_num + 1
            self._common_content_lib.shutdown_os()
            for index in range(1, 5):
                if not self._common_content_lib.check_os_alive():
                    is_shutdown = True
                    break
                time.sleep(30)
            if is_shutdown:
                break
            time.sleep(30)

        if not is_shutdown:
            self._log.error("Failed to shutdown the SUT.")
            return False

        attempt_num = 1
        is_shutdown = False
        while attempt_num <= max_attempts:
            self._log.info("Attempt#%d: Waiting until SUT state is S5.", attempt_num)
            attempt_num = attempt_num + 1
            power_state = self._common_content_lib.get_power_state(self.phy)
            if power_state == PowerStates.S5:
                is_shutdown = True
                break
            self.fail_or_log(
                "SUT did not entered into %s state, actual state is %s" % (PowerStates.S5, power_state),
                self.log_or_fail)
            time.sleep(60)

        return is_shutdown

    def __perform_dc_on(self):
        attempt_num = 1
        max_attempts = 5
        while attempt_num <= max_attempts:
            self._log.info("Attempt #{}: Perform DC Power On.".format(attempt_num))
            try:
                if self._dc_power.dc_power_on(self.DC_POWER_DELAY):
                    self._log.info("Attempt #{}: DC Power on Successful.".format(attempt_num))
                    return True
            except Exception as ex:
                self._log.info("Attempt #{}: Failed to perform DC Power On due to "
                               "exception '{}'.".format(attempt_num, ex))
            attempt_num += 1
        self._log.error("Failed to DC Power on SUT.")
        return False

    def __wait_for_os(self):
        start_time = time.time()
        pc_available = True

        bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
        if bios_pc is None:
            pc_available = False
            self._log.info("Post code data not available.")

        if pc_available:
            prev_pc = None
            pc_stuck_start_time = start_time
            while True:
                elapsed_time = time.time() - start_time
                pc_stuck_elapsed_time = time.time() - pc_stuck_start_time
                bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
                if bios_pc is not None:
                    if prev_pc is None:
                        prev_pc = bios_pc
                    self._log.info("FPGA PC='{}' BIOS PC='{}'".format(fpga_pc, bios_pc))
                    if prev_pc == bios_pc:
                        if pc_stuck_elapsed_time > self.pc_stuck_time_out:
                            self._log.error("SUT is stuck at post code %s for more than %d seconds.", bios_pc,
                                            self.pc_stuck_time_out)
                            break
                    else:
                        pc_stuck_start_time = time.time()
                        prev_pc = bios_pc
                else:
                    self._log.error("Unable to read the post code")
                if self._common_content_lib.check_os_alive() or elapsed_time >= self.reboot_timeout:
                    break
        else:
            self._log.info("Waiting for OS to be alive.")
            while True:
                elapsed_time = time.time() - start_time
                if self._common_content_lib.check_os_alive() or elapsed_time >= self.reboot_timeout:
                    break

        if pc_available:
            bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
            if bios_pc is not None:
                self._log.info("FPGA PC='{}' BIOS PC='{}'".format(fpga_pc, bios_pc))
            else:
                self._log.error("Unable to read the post code")

        if not self._common_content_lib.check_os_alive():
            if pc_available:
                if bios_pc not in self.os_post_codes:
                    self._log.error("SUT Failed to boot to OS with post code %s "
                                    "within %d seconds" % (str(bios_pc), self.reboot_timeout))
                else:
                    self._log.error("Sut has booted to OS with post code %s and within %d seconds, "
                                    "but network service failed." % (str(bios_pc), self.reboot_timeout))
            else:
                self._log.error("SUT Failed to boot to OS within %d seconds." % self.reboot_timeout)

            self._boot_flow = BootFlow.POWER_ON
            self._failed_pc = bios_pc
            if self._failed_pc is None:
                return ResetStatus.OS_NOT_ALIVE
            else:
                return ResetStatus.PC_STUCK

        return ResetStatus.SUCCESS

    def graceful_s5(self):
        """
        Shut down SUT gracefully, press the power button, and wait for SUT to boot.
        """
        if not self._common_content_lib.check_os_alive():
            self._log.error("SUT is not up, cannot execute the shutdown command..")
            return ResetStatus.OS_NOT_ALIVE

        if not self.__shutdown_sut():
            power_state = self._common_content_lib.get_power_state(self.phy)
            if power_state != PowerStates.S5:
                self.fail_or_log(
                    "SUT did not entered into %s state, actual state is %s" % (PowerStates.S5, power_state),
                    self.log_or_fail)
                bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
                if bios_pc is not None:
                    self._log.info("FPGA PC='{}' BIOS PC='{}'".format(fpga_pc, bios_pc))
                    self._failed_pc = bios_pc
                    self._boot_flow = BootFlow.POWER_OFF
                    return ResetStatus.PC_STUCK
                else:
                    self._log.error("Unable to read the post code")
                    return ResetStatus.STATE_CHANGE_FAILURE

        self._log.info("SUT is in S5 state.")

        if not self.__perform_dc_on():
            self._log.error("Failed to perform DC ON operation on SUT..")
            return ResetStatus.DC_FAILURE

        if self.machine_check:
            time.sleep(30)
            self.initialize_sdp_sv_objects()
            try:
                self._log.info("Performing halt and check...")
                self.sdp.halt_and_check()
                self._log.info("Performing itp.threads.cv.machinecheckbreak=1")
                self.sdp.itp.threads.cv.machinecheckbreak = 1
            except:
                self._log.error("Unable to perform Halt on Machine")
            finally:
                self._log.info("Resume the Machine")
                self.sdp.go()

        status = self.__wait_for_os()
        if status != ResetStatus.SUCCESS:
            return status

        power_state = self._common_content_lib.get_power_state(self.phy)
        if power_state != PowerStates.S0:
            self.fail_or_log("SUT did not entered into %s state, actual state is %s" % (PowerStates.S0, power_state),
                             self.log_or_fail)
            return ResetStatus.STATE_CHANGE_FAILURE

        self._log.info("SUT is in S0 state and network is up.")
        self._log.info("Waiting for all OS services to be up...")
        self._common_content_lib.wait_for_sut_to_boot_fully()
        return ResetStatus.SUCCESS

    def graceful_g3(self):
        """
        Shut down SUT gracefully, remove AC power, reconnect AC power and wait for SUT to boot.

        """
        if not self._common_content_lib.check_os_alive():
            self._log.error("SUT is not up, cannot execute the shutdown command..")
            return ResetStatus.OS_NOT_ALIVE

        if not self.__shutdown_sut():
            power_state = self._common_content_lib.get_power_state(self.phy)
            if power_state != PowerStates.S5:
                self.fail_or_log(
                    "SUT did not entered into %s state, actual state is %s" % (PowerStates.S5, power_state),
                    self.log_or_fail)
                bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
                if bios_pc is not None:
                    self._log.info("FPGA PC='{}' BIOS PC='{}'".format(fpga_pc, bios_pc))
                    self._failed_pc = bios_pc
                    self._boot_flow = BootFlow.POWER_OFF
                    return ResetStatus.PC_STUCK
                else:
                    self._log.error("Unable to read the post code")
                    return ResetStatus.STATE_CHANGE_FAILURE

        self._log.info("SUT is in S5 state.")

        return self.surprise_g3()

    def s3_cycling(self):
        """
        Reset SUT gracefully and wait for SUT to boot.
        """
        try:
            if self.os.os_type == "WIN":
                s3_cmd = SLEEP
                self.os.execute()
            self.os.reboot(30)
        except Exception as ex:
            self._log.info("This is expected exception: {}".format(ex))
        time.sleep(30)
        return self.__wait_for_os()

    def warm_reset(self):
        """
        Reset SUT gracefully and wait for SUT to boot.
        """
        try:
            self.os.reboot(30)
        except Exception as ex:
            self._log.info("This is expected exception: {}".format(ex))
        time.sleep(30)
        return self.__wait_for_os()

    def cold_reset(self):
        """
        Perform Cold Reset and wait for SUT to boot.
        """
        self.surprise_reset()
        return True

    def surprise_reset(self):
        """Reset the SUT using reset button"""
        self._log.info("Restarting SUT using reset button")
        self._dc_power.dc_power_reset()
        time.sleep(self.POST_SLEEP_DELAY)
        self._common_content_lib.perform_boot_script()
        self.os.wait_for_os(self.reboot_timeout)
        time.sleep(self.POST_SLEEP_DELAY)
        return True

    def surprise_s5(self, timeout=None):
        """
        Use SUT's power button upto timeout time to execute a force shutdown, then use SUT power button
        back to on and wait for reboot.
        """
        self._log.debug("press the power button to make the SUT On and Off")
        if not timeout:
            timeout = self.DC_POWER_DELAY
        self._dc_power.dc_power_off(timeout)
        time.sleep(self.SX_SLEEP_TIME)
        self._dc_power.dc_power_on(timeout)
        self._common_content_lib.perform_boot_script()
        self.os.wait_for_os(self.reboot_timeout)
        time.sleep(self.POST_SLEEP_DELAY)
        return True

    def __ac_poweroff(self):
        self._log.info("Switch AC OFF.")
        max_attempts = 5
        attempt = 0
        status = ResetStatus.AC_FAILURE
        while attempt < max_attempts:
            try:
                if self.ac_power.ac_power_off(self.AC_POWER_DELAY):
                    self._log.debug("AC power off is succeeded..")
                    status = ResetStatus.SUCCESS
                    break
                time.sleep(10)
            except Exception as ex:
                self._log.error("Attempt#{}: AC power off failed due to exception: {}.".format(attempt, ex))
            attempt = attempt + 1
            self._log.debug("Attempt#{}: AC power off is failed..".format(attempt))

        if status != ResetStatus.SUCCESS:
            self._log.error("AC power off failed even after multiple attempts..")
            return status

        self._log.info("Switch AC OFF is succeeded.")

        status = ResetStatus.STATE_CHANGE_FAILURE
        attempt = 0
        while attempt < max_attempts:
            try:
                if not self.ac_power.get_ac_power_state():
                    self._log.debug("AC power is un-plugged and SUT is in G3 state..")
                    status = ResetStatus.SUCCESS
                    break
            except Exception as ex:
                self._log.error("AC power off failed due to exception: {}.".format(ex))
            self._log.debug("Attempt #{}: AC power is still plugged..".format(attempt))
            attempt = attempt + 1

        if status != ResetStatus.SUCCESS:
            self._log.error("SUT did not reach G3 state after multiple AC Switch off attempts.")
        return status

    def __ac_poweron(self):
        self._log.info("Switch AC ON.")
        max_attempts = 5
        attempt = 0
        status = ResetStatus.AC_FAILURE
        while attempt < max_attempts:
            try:
                if self.ac_power.ac_power_on(self.AC_POWER_DELAY):
                    self._log.debug("AC power ON is succeeded..")
                    status = ResetStatus.SUCCESS
                    break
                time.sleep(10)
            except Exception as ex:
                self._log.error("Attempt #{}: AC power ON failed due to exception: {}.".format(attempt, ex))
            self._log.debug("Attempt#{}: AC power ON is failed..")
            attempt = attempt + 1

        if status != ResetStatus.SUCCESS:
            self._log.error("AC power ON failed even after multiple attempts..")
            return status

        status = ResetStatus.STATE_CHANGE_FAILURE
        attempt = 0
        while attempt < max_attempts:
            try:
                if self.ac_power.get_ac_power_state():
                    self._log.debug("AC power is plugged and SUT is out of G3 state..")
                    status = ResetStatus.SUCCESS
                    break
            except Exception as ex:
                self._log.error("Attempt #{}: AC power on failed due to exception: {}.".format(attempt, ex))
            self._log.debug("Attempt #{}: AC power is still unplugged..".format(attempt))
            attempt = attempt + 1

        if status != ResetStatus.SUCCESS:
            self._log.error("SUT did not come out of G3 state after multiple AC Switch on attempts.")
        return status

    def surprise_g3(self):
        """
        Remove AC power from system while it is running, then reconnect power and wait for reboot.
        """
        status = self.__ac_poweroff()
        if status != ResetStatus.SUCCESS:
            return status

        # wait few secs before we power on AC
        time.sleep(self.SLEEP_TIME)

        status = self.__ac_poweron()
        if status != ResetStatus.SUCCESS:
            return status

        # SUT is AC powered on, wait for few minutes, DELL system may take few minutes for IDRAC to come up
        if self._platform_type == PlatformType.DELL:
            time.sleep(300)

        status = self.__wait_for_os()
        if status != ResetStatus.SUCCESS:
            return status

        power_state = self._common_content_lib.get_power_state(self.phy)
        if power_state != PowerStates.S0:
            self._log.error("SUT did not entered into expected power state(%s), actual state is %s after AC ON" % (
                PowerStates.S0, power_state))
            return ResetStatus.STATE_CHANGE_FAILURE

        self._log.info("SUT is S0 state and network is up.")
        self._log.info("Waiting for all OS services to be up...")
        self._common_content_lib.wait_for_sut_to_boot_fully()

        return ResetStatus.SUCCESS

    def validate_sut_state(self):
        """
        Check if SUT is in expected state for a given cycle.

        Subclasses should override this function to add extra checks for the SUT state
        :return: True if SUT passed all checks, False otherwise.
        """
        return self.os.is_alive()

    def execute_burnin_test(self, timeout):
        """Executes BurnInTest

        @raise content_exceptions.TestFail
        """
        bit_location = self.collateral_installer.install_burnintest()
        bit_location = bit_location + "/" + "burnintest/64bit"
        sut_cmd = self.os.execute(self.BURNIN_TEST_CMD % timeout,
                                  self._command_timeout + timeout,
                                  bit_location)

        self._log.debug(sut_cmd.stdout.strip())
        self._log.debug(sut_cmd.stderr.strip())
        if self.BURNIN_TEST_START_MATCH not in sut_cmd.stderr.strip():
            raise content_exceptions.TestFail("Looks like BurnInTest is not "
                                              "started")
        if self.os.check_if_path_exists(bit_location + "/" +
                                        self.BURNIN_TEST_DEBUG_LOG):
            self.os.copy_file_from_sut_to_local(
                bit_location + "/" + self.BURNIN_TEST_DEBUG_LOG,
                os.path.join(self.log_dir, self.BURNIN_LOCAL_DEBUG_LOG))
        with open(
                os.path.join(self.log_dir, self.BURNIN_LOCAL_DEBUG_LOG)) as f:
            data = f.read()
            if self.BURNIN_TEST_END_MATCH not in data:
                raise content_exceptions.TestFail("Looks like BurnInTest not "
                                                  "ended successfully")
        self._log.info("BurnIntest started and ended successfully")

    def execute_shell_script(self, script, timeout, cwd=None):
        """Executes shell script"""
        if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
            cmd = self.os.execute("sed -i -e 's/\r$//' %s;chmod +x %s; ./%s" % (script, script, script), timeout,
                                  cwd=cwd)
            self._log.debug(cmd.stdout)
            self._log.debug(cmd.stderr)

    def get_upi_topology(self, serial_log):
        """Get UPI Topology"""
        upi_topology = None
        with open(serial_log) as f:
            data = f.read()
            upi_regex_match = re.search(HealthCheck.UPI_SERIAL_LOG_CHECK, data, re.M)
            if upi_regex_match:
                upi_topology = upi_regex_match.group(1)
        self._log.debug("UPI Topology: %s", upi_topology)
        return upi_topology

    def upi_topology_check_errors(self, cycle_num):
        self.initialize_sdp_sv_objects()
        log_file_name = "upi.log"
        upi_log_file = "upi_cycle{}.log".format(cycle_num)
        upi_log_file = os.path.join(self.health_check_log_dir, upi_log_file)
        self.sv.refresh()
        upi_status_obj = self.sv.get_upi_obj()
        final_dict = {"topology": None, "link_speed_errors": []}
        health_check_functions = {"topology": upi_status_obj.upiStatus.printTopology,
                                  "link_speed_errors": upi_status_obj.upiStatus.printLinkSpeed}
        try:
            for key, func in health_check_functions.items():
                self.sdp.start_log(log_file_name)
                func()
                self.sdp.stop_log()
                data = None
                with open(log_file_name) as f:
                    data = f.read()
                if data is None:
                    self._log.error("Failed to capture UPI {} data from PythonSV.".format(key))
                    return final_dict
                # write the upi topology and link speed data to separate file per cycle
                with open(upi_log_file, 'a') as f:
                    f.write(data)
                if key == "topology":
                    topology_match_regex = re.search(HealthCheck.UPI_HEALTH_PYSV_REGEX, data)
                    if topology_match_regex:
                        final_dict["topology"] = topology_match_regex.group(1)
                else:
                    def poll_to_verify_state():

                        start_time = time.time()
                        while time.time() - start_time < 20:
                            final_dict["link_speed_errors"] = []
                            self.sdp.start_log(log_file_name)
                            upi_status_obj.upiStatus.printLinkSpeed()
                            self.sdp.stop_log()
                            data = None
                            with open(log_file_name) as f:
                                data = f.read()
                            if data is None:
                                self._log.error("Failed to capture UPI {} data from PythonSV.".format(key))
                                return final_dict
                            # write the upi topology and link speed data to separate file per cycle
                            with open(upi_log_file, 'a') as f:
                                f.write(data)

                            return_value = False
                            ret_list = []
                            for line in data.splitlines():
                                if "Link Speed:" in line and HealthCheck.IGNORE_PORT not in line:
                                    return_value = verify_link_speed(line.split(",", maxsplit=2)[-1],
                                                                     HealthCheck.LINK_SPEED_MATCH)
                                    if return_value:
                                        final_dict["link_speed_errors"].append(return_value)
                                    ret_list.append(return_value)
                            if not any(return_value):
                                break


                    def verify_link_speed(ls_data, actual):
                        ls_data = ls_data.replace("|", ",")
                        expected = {}
                        for item in ls_data.strip().split(","):
                            expected[item.split(":")[0].strip()] = item.split(":")[-1].strip()
                        if expected != actual:
                            if not (expected["Tx State"].startswith("L0") or expected["Tx State"].startswith("L1")):
                                return ls_data
                            elif not (expected["Rx State"].startswith("L0") or expected["Rx State"].startswith("L1")):
                                return ls_data

                    for line in data.splitlines():
                        if "Link Speed:" in line and HealthCheck.IGNORE_PORT not in line:
                            return_value = verify_link_speed(line.split(",", maxsplit=2)[-1],
                                                             HealthCheck.LINK_SPEED_MATCH)
                            if return_value:
                                poll_to_verify_state()
                                #final_dict["link_speed_errors"].append(return_value)
        except Exception as ex:
            self._log.error("Failed to get topology date due to exception: '{}'.".format(ex))
        return final_dict

    def mc_status_health_check(self, iteration=1):
        self.initialize_sdp_sv_objects()
        self.sv.refresh()
        mc_status_log_file = None
        sockets = self.sv.get_sockets()
        for i in range(0, len(sockets)):
            try:
                mc_status_file_name = "mc_status_" + str(iteration) + ".txt"
                mc_status_log_file = os.path.join(self.health_check_log_dir, mc_status_file_name)
                # self.sdp.start_log(upi_log_file)
                self.sdp.start_log(mc_status_log_file, "a")
                sockets[i].uncore.punit.mc_status.show()
                self.sdp.stop_log()
            except Exception as e:
                self._log.info("exception: %s" % str(e))

        with open(mc_status_log_file, "r") as f:
            lines = f.readlines()
            for l in lines:
                if l[0] in ["\r", "\n"]:
                    continue
                if l.split(":")[0].strip() != "0x00000000":
                    self._log.error("MC status shows non zero value: {}".format(l))
                    f.close()
                    return False
        f.close()
        return True

    def dimm_thermal_status_health_check(self, iteration):
        if iteration == 1 or not iteration % 10:
            self._log.info("Dumping DIMM Thermal status data for iteration: %d" % iteration)
            self.initialize_sdp_sv_objects()
            self.sv.refresh()
            dimm_thermal_status_log_file = None
            sockets = self.sv.get_sockets()
            for i in range(0, len(sockets)):
                try:
                    dimm_thermal_status_file_name = "dimm_thermal_status_" + str(iteration) + ".txt"
                    dimm_thermal_status_log_file = os.path.join(self.health_check_log_dir,
                                                                dimm_thermal_status_file_name)
                    # self.sdp.start_log(upi_log_file)
                    self.sdp.start_log(dimm_thermal_status_log_file, "a")
                    sockets[i].uncore.memss.mcs.chs.dimmtempstat_0.show()
                    sockets[i].uncore.memss.mcs.chs.memhot_status.show()
                    self.sdp.stop_log()
                except Exception as e:
                    self._log.error("Exception while reading DIMM thermal log: %s" % str(e))
                    return False
        return True

    def clock_health_check(self,iteration=1):

        if self.os.os_type == OperatingSystems.LINUX:
            cmd_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd=self.CLOCK_COMMAND_LINUX,
                                                                   cmd_str=self.CLOCK_COMMAND_LINUX,
                                               execute_timeout=self._command_timeout)

            memory_status_file_name = "clock_health_status_" + str(iteration) + ".txt"
            memory_status_log_file = os.path.join(self.health_check_log_dir, memory_status_file_name)
            if "tsc" not in cmd_out_put:
                self._log.error("Clock health check failed in iter %d. Output of cmd %s execution is %s"%(iteration,self.CLOCK_COMMAND_LINUX,cmd_out_put))
                with open(memory_status_log_file,"w") as f:
                    f.writelines("Clock health check failed in iter %d. Output of cmd %s execution is %s"%(iteration,self.CLOCK_COMMAND_LINUX,cmd_out_put))
                return False
            else:
                self._log.info("Clock health check Passed in iteration %d."%iteration)
                with open(memory_status_log_file, "w") as f:
                    f.writelines("Clock health check Passed in iteration %d."%iteration)
                return True
        else:
            return True

    def system_memory_health_check(self, iteration=1):
        """
        This method is to check the System Memory Health.

        :param iteration
        :return True or False
        """
        if self.os.os_type != OperatingSystems.LINUX:
            self._log.error("System Memory Health is still not developed for OS type- {}".format(self.os.os_type))
            #  returning True for other than Linux as code is not implemented for Windows yet.
            return True

        memory_health_check_list_from_config = self._common_content_configuration.get_memory_health_check_type_list()
        if not memory_health_check_list_from_config:
            return True

        self._log.info("Dumping System Memory Health Check Status for iteration: {}".format(iteration))
        self.initialize_sdp_sv_objects()
        self.sv.refresh()
        memory_status_log_file = None
        memory_status_file_name = "system_memory_health_status_" + str(iteration) + ".txt"
        memory_status_log_file = os.path.join(self.health_check_log_dir, memory_status_file_name)

        #  Re-initialize the Memory providers
        self.memory_provider.re_initialize_memory_provider()

        #  Initialised the CPU info dict before using.
        self._cpu_provider.populate_cpu_info()

        self.sdp.start_log(memory_status_log_file, "a")
        try:
            #  Using halt and check to reduce the IPC issue by re-config IPC
            self.sdp.halt_and_check()
            memory_info_obj = self.sv.get_dimminfo_object()
            self.sdp.itp.unlock()
            self.memory_info = memory_info_obj.get_all_mem_info()
        except Exception as ex:
            self._log.error("Failed to get the Memory details from itp with exception - {}".format(ex))
        finally:
            #  Resuming the Machine.
            self.sdp.go()

        self.sdp.stop_log()

        status_in_list = []

        def cpu_check(log_file_name=None, iteration=1):
            """
            This method is to check CPU.

            :param log_file_name
            :param iteration
            """
            self._log.info("Performing CPU Check...")
            #  Initialise the sv and sdp obj if already not available
            self.initialize_sdp_sv_objects()
            self.sv.refresh()
            self.sdp.start_log(log_file_name, "a")

            #  Get number of Sockets, Cores, and Threads using itp.
            no_of_sockets_from_itp = len(self.sv.get_sockets())
            no_of_cores_from_itp = len(self.sdp.itp.cores)
            no_of_threads_from_itp = len(self.sdp.itp.threads)
            self.sdp.stop_log()

            #  Check and resume if Machine is halted
            if self.sdp.is_halted():
                self.sdp.go()
                time.sleep(20)

            #  Get number of Sockets, Cores, Threads from OS.
            no_of_sockets_from_os = int(self._cpu_provider.get_number_of_sockets())
            no_of_cores_from_os = int(self._cpu_provider.get_number_of_cores())
            no_of_threads_from_os = int(self._cpu_provider.get_number_of_threads())

            #  Appending the details of CPU to system_memory_health_status_(-).txt
            with open(log_file_name, "a") as fp:
                fp.write("\n Number of \(Sockets, Core and Threads\) in OS- \({} \t {} \t {}\) \n\n"
                         " \(Number of Sockets, Core and Threads\) from itp- \({} \t {} \t {}\)".format(
                    no_of_sockets_from_os, no_of_cores_from_os, no_of_threads_from_os, no_of_sockets_from_itp,
                    no_of_cores_from_itp, no_of_threads_from_itp))

            if not ((no_of_threads_from_os == no_of_threads_from_itp) and (no_of_cores_from_itp == no_of_cores_from_os) \
                    and (no_of_sockets_from_itp == no_of_sockets_from_os)):
                self._log.error("CPU check status- Failed failed Cycle: #{}".format(iteration))
                return False
            self._log.info("CPU check status- Passed for Cycle: #{}".format(iteration))
            return True

        def disk_space_check(log_file_name=None, iteration=1):
            """
            This method is to check the Disk Space.

            :param log_file_name
            :param iteration
            """
            self._log.info("Performing Disk Space Check for Cycle Number: # {}".format(iteration))
            #  Execute the command to check the disk space on SUT.
            avail_output = self.memory_provider.get_available_disk_space()[:-1]

            #  Appending the details of Available Disk Space to system_memory_health_status_(-).txt
            with open(log_file_name, "a") as f:
                f.write("\n Available disk space is - {}\n".format(avail_output))

            #  Check and return False if Disk Space is less than 5
            if int(avail_output) < 5:
                self._log.error("Available disk space status- Failed for cycle Number: # {}".format(iteration))
                return False
            self._log.info("Available Space check status- Passed for Cycle Number: # {}".format(iteration))
            return True

        def numa_snc_check(log_file_name=None, iteration=1):
            """
            This method is to check the NUMA Node(SNC) on Default Bios.

            :param log_file_name
            :param iteration
            """
            #  Get Numa node value from OS
            numa_value = self._cpu_provider.get_numa_node()

            #  Appending the details of CPU to system_memory_health_status_(-).txt
            with open(log_file_name, 'a') as f:
                f.write("\n NUMA value from OS - {}\n".format(numa_value))

            #  Get number of Sockets to verify Numa node as Numa node value will equal to number of Socket for
            #  snc=0 which is Default Value.
            no_of_sockets = self._cpu_provider.get_number_of_sockets()
            if no_of_sockets == numa_value:
                self._log.info("Numa Value status- Passed for Cycle Number: # {}".format(iteration))
                return True
            self._log.info("Numa Value status- Failed for Cycle Number: # {}".format(iteration))
            return False

        def ddr_frequency_check(log_file_name=None, iteration=1):
            """
            This method is to check the ddr frequency.

            :param log_file_name
            :param iteration
            """
            #  Get expected ddr frequency from content config.
            expected_ddr_frequency = self._common_content_configuration.get_ddr_freq_for_dpmo()

            #  Get DDR Frequency details dict
            ddr_frequency_dict = self.memory_provider.get_speed_of_installed_dimm()
            speed_list_of_installed_dimm = list(ddr_frequency_dict.values())

            #  Appending the details of CPU to system_memory_health_status_(-).txt
            with open(log_file_name, 'a') as f:
                f.write("\nDDR Frequency details - {}\n".format(ddr_frequency_dict))

            if str(expected_ddr_frequency) not in speed_list_of_installed_dimm:
                self._log.error("DDR Frequency Check Status- Failed for Cycle Number: # {}".format(iteration))
                return False
            self._log.info("DDR Frequency Check Status- Passed for Cycle Number: # {}".format(iteration))
            return True

        def system_memory_check(log_file_name=None, iteration=1):
            """
            This method is to check the System memory.

            :param log_file_name
            :param iteration
            """
            total_mem_from_os = self.memory_provider.get_total_system_memory() / 1024
            total_mem_from_itp = self.memory_info.get('phyMemSize')
            with open(log_file_name, 'a') as f:
                f.write("\nTotal Memory from OS - {}\n Total Memory from itp - {}".format(
                    total_mem_from_os, total_mem_from_itp))
            range_value = total_mem_from_os * 0.1
            if (total_mem_from_os - range_value) < total_mem_from_itp < (total_mem_from_os + range_value):
                self._log.info("System Memory Check Status- Passed for Cycle: #{}".format(iteration))
                return True
            self._log.error("System Memory Check Status- Failed for Cycle: #{}".format(iteration))
            return False

        def reset_check(log_file_name, iteration):
            """
            This method is to reset check.

            :param log_file_name
            :param iteration
            """
            if self.reset_type is None:
                return True
            self.initialize_sdp_sv_objects()
            sticky_reg = "ubox.ncdecs.biosscratchpad6_cfg"
            non_sticky_reg = "ubox.ncdecs.biosnonstickyscratchpad7_cfg"
            sticky_value = self.sv.get_by_path(self.sv.UNCORE, reg_path=sticky_reg)

            non_sticky_value = self.sv.get_by_path(self.sv.UNCORE, reg_path=non_sticky_reg)
            with open(log_file_name, "a") as fp:
                fp.write("Sticky Register- {} and Non Sticky Register- {}".format(sticky_value,
                                                                                  non_sticky_value))
            if self.reset_type == "warm_reset":
                if (sticky_value == 0xbf111111) and (non_sticky_value != 0xbf111111):
                    self._log.info("Warm reset Test status- Passed for Cycle: #{}".format(iteration))
                    return True
                self._log.error("Warm Reset status- Failed for Cycle Number - # {}".format(iteration))
                return False

        #  Memory health check list from config which needs to check
        memory_health_check_list_from_config = self._common_content_configuration.get_memory_health_check_type_list()

        memory_health_check_dict = {MemoryHealthCheck.SYSTEM_MEMORY_CHECK: system_memory_check,
                                    MemoryHealthCheck.CPU_CHECK: cpu_check,
                                    MemoryHealthCheck.NUMA_SNC_CHECK: numa_snc_check,
                                    MemoryHealthCheck.DISK_SPACE_CHECK: disk_space_check,
                                    MemoryHealthCheck.DDR_FREQ_CHECK: ddr_frequency_check,
                                    MemoryHealthCheck.RESET_CHECK: reset_check}
        #  preparing handler list
        if "all" in memory_health_check_list_from_config:
            memory_health_check_handlers = list(memory_health_check_dict.values())
        else:
            memory_health_check_handlers = [memory_health_check_dict[each_func] for each_func in
                                            memory_health_check_list_from_config if
                                            memory_health_check_dict.get(each_func)]

        #  iterate each memory health check handlers to perform it.
        for func in memory_health_check_handlers:
            #  storing the status of each Memory health check in list.
            status_in_list.append(func(log_file_name=memory_status_log_file, iteration=iteration))
        self._log.info(status_in_list)
        return all(status_in_list)

    def cpu_thermal_status_health_check(self, iteration=1):
        if iteration == 1 or not iteration % 10:
            self._log.info("Dumping CPU Thermal status data for iteration: {}".format(iteration))
            self.initialize_sdp_sv_objects()
            self.sv.refresh()
            thermal_status_log_file = None
            sockets = self.sv.get_sockets()
            for i in range(0, len(sockets)):
                try:
                    thermal_status_file_name = "thermal_status_" + str(iteration) + ".txt"
                    thermal_status_log_file = os.path.join(self.health_check_log_dir, thermal_status_file_name)
                    # self.sdp.start_log(upi_log_file)
                    self.sdp.start_log(thermal_status_log_file, "a")
                    sockets[i].uncore.punit.package_therm_status.show()
                    self.sdp.stop_log()
                except Exception as e:
                    self._log.error("Exception while reading thermal log: %s" % str(e))
                    return False
        return True

    def upi_topology_check(self, iteration=1):
        ret_val = True
        if self.health_check:
            self._log.debug(HealthCheck.UPI_HEALTH_CHECK)
            if not HealthCheck.HEALTH_CHECKS[HealthCheck.UPI_HEALTH_CHECK]:
                self._log.info("UPI Topology health check is skipped")
                return True
            data = self.upi_topology_check_errors(iteration)
            self._log.info("upi topology data: %s", str(data))
            if data["topology"] is None:
                self._log.error("Failed to get the upi topology value during iteration %d" % iteration)
                ret_val = False
            if data["topology"] != self._common_content_configuration.get_dpmo_topology():
                self._log.error("Looks like UPI is degraded to  %s" % data["topology"])
                ret_val = False
            if data["link_speed_errors"]:
                self._log.error("Error in UPI link speeds during iteration %d" % iteration)
                ret_val = False
        return ret_val

    def upi_topology_check_serial(self, base, serial_log, iteration=1):
        """
        checks and logs the errors
        """
        if self.health_check:
            self._log.debug(HealthCheck.UPI_HEALTH_CHECK)
            if not HealthCheck.HEALTH_CHECKS[HealthCheck.UPI_HEALTH_CHECK]:
                self._log.info("UPI Topology health check is skipped")
                return
            if int(self.num_of_sockets) > 2:
                data = ''
                with open(serial_log) as f:
                    data = f.read()
                actual_topology_output = re.findall("Link Exchange Parameter(.*?)Routine in", data, re.S | re.M)
                self._log.debug("Extracted KTI topology degradation output: %s", actual_topology_output)
                if not actual_topology_output:
                    self._log.debug(
                        "KTI Topology Degradation output not found in the serial log during the iteration(%s)",
                        iteration)
                    raise content_exceptions.TestFail(
                        "KTI Topology Degradation output not found in the serial log during the iteration(%s)" % iteration)
                    topology = []
                else:
                    topology = [line.strip() for line in actual_topology_output[-1].strip("\r\n\t -").splitlines() if
                                line.strip() != ""]
                upi_dir = os.path.join(self.health_check_log_dir, "upi")
                if not os.path.exists(upi_dir):
                    os.makedirs(upi_dir)
                if topology != HealthCheck.UPI_MESH_TOPOLOGY_EXPECTED:
                    with open(os.path.join(upi_dir, "upi_topology_error_iteration_%d" % iteration), "w") as f:
                        f.write("KTI Topology Degraded (%s) during iteration(%s)" % (topology, iteration))
                    raise content_exceptions.TestFail(
                        "KTI Topology Degraded (%s) during iteration(%s)" % (topology, iteration))
                else:
                    self._log.debug("UPI Topology looks good during iteration(%s)" % (iteration))
            else:
                current = self.get_upi_topology(serial_log)
                upi_dir = os.path.join(self.health_check_log_dir, "upi")
                if not os.path.exists(upi_dir):
                    os.makedirs(upi_dir)
                if current != base:
                    with open(os.path.join(upi_dir, "upi_topology_error_iteration_%d" % iteration), "w") as f:
                        f.write("UPI Topology mismatch between base(%s) and current(%s) iteration(%s)" % (
                            base, current, iteration))
                else:
                    self._log.debug("UPI Topology matched between base(%s) and current(%s) iteration(%s)" % (
                        base, current, iteration))

    def _initialize_pci_obj(self):
        if self._pcie_obj is not None:
            return True
        try:
            self._pcie_obj = PcieProvider.factory(self._log, self.os, self._cfg, ExecutionEnv.OS)
            return True
        except Exception as ex:
            self._log.error("Exception occurred while initializing the pci_obj: {}.".format(ex))
            self._pcie_obj = None
        return False

    def _capture_pcie_snapshot_linux(self, pcie_file_name):
        pcie_file_sut = "/var/log/cycling/linkstates/{}".format(pcie_file_name)
        cmd = r'lspci -vv | grep -e "LnkSta:" -e "^[[:xdigit:]][[:xdigit:]]:[[:xdigit:]][[:xdigit:]].[[:xdigit:]]" ' \
              r'| sed "s/^.*\(LnkSta:.*\)$/\1/" > '
        cmd += pcie_file_sut

        try:
            ret_val = self.os.execute(cmd, self._command_timeout)
            status = ret_val.cmd_passed()
        except Exception as ex:
            self._log.error("Failed to execute lspci command due to exception: {}.".format(ex))
            status = False

        if status:
            pcie_file_host = os.path.join(self.health_check_log_dir, pcie_file_name)
            self.os.copy_file_from_sut_to_local(pcie_file_sut, pcie_file_host)
            return pcie_file_host

        return None

    def _capture_pcie_snapshot_windows(self, pcie_file_name):
        if not self._initialize_pci_obj():
            self._log.error("Failed to create pci object and hence pci health check will not be performed.")
            return None

        pcie_file_host = os.path.join(self.health_check_log_dir, pcie_file_name)
        dict_pcie_devices = self._pcie_obj.get_pcie_devices(re_enumerate=True)
        with open(pcie_file_host, 'w') as f:
            for key, value in dict_pcie_devices.items():
                f.write("{}:{}\n".format(key, value))

        return pcie_file_host

    def baseline_pcie_health_check(self):
        if self.os.os_type.lower() not in [OperatingSystems.LINUX.lower(), OperatingSystems.WINDOWS.lower()]:
            self._log.info("PCI health check is not yet implemented for the OS %s", self.os.os_type.upper())
            self._perform_pcie_health_check = False
            return

        # Windows OS, PCI enumeration crashes OS with BSOD, skip winows for now
        if self.os.os_type.lower() == OperatingSystems.WINDOWS.lower():
            self._log.info("Windows OS: PCI enumeration crashes with BSOD WHEA_UNCORRECTABLE_ERROR. "
                           "Skipping PCI health check.")
            self._perform_pcie_health_check = False
            return

        if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
            commands = ["rm -r -f /var/log/cycling", "mkdir /var/log/cycling", "mkdir /var/log/cycling/linkstates"]
            # remove existing folders and create them again
            try:
                for cmd in commands:
                    self.os.execute(cmd, self._command_timeout)
            except Exception as ex:
                self._log.error("Failed to remove and created folders on SUT due to exception: {}.".format(ex))
                self._log.error("Failed to create the PCIE snapshot and PCIE health-check will not be performed.")
                self._perform_pcie_health_check = False
                return

        pcie_snapshot_handler = {OperatingSystems.LINUX.lower(): self._capture_pcie_snapshot_linux,
                                 OperatingSystems.WINDOWS.lower(): self._capture_pcie_snapshot_windows}

        get_pcie_snapshot = pcie_snapshot_handler[self.os.os_type.lower()]
        pcie_host_file = get_pcie_snapshot(self._pcie_init_snapshot_name)
        if pcie_host_file is None:
            self._log.error("Failed to create the PCIE snapshot and PCIE health-check will not be performed.")
            self._perform_pcie_health_check = False
            return
        self.perform_pcie_error_check(iteration=0, clear_flag=True)
        self._log.info("PCIE Snapshot '{}' successfully created.".format(pcie_host_file))

    def pci_health_check(self, cycle_num=0):
        if not self._perform_pcie_health_check:
            self._log.info("Cycle#{}: PCIE Health check is skipped as initial snapshot failed.".format(cycle_num))
            return True

        if self.os.os_type.lower() not in [OperatingSystems.LINUX.lower(), OperatingSystems.WINDOWS.lower()]:
            self._log.info("PCI health check is not yet implemented for the OS %s", self.os.os_type.upper())
            return True

        if not self._common_content_lib.check_os_alive():
            self._log.error("PCI health check cannot be performed as OS is not alive.")
            return False

        pcie_file_name = "PciSnapshot_Cycle{}.log".format(cycle_num)

        pcie_snapshot_handler = {OperatingSystems.LINUX.lower(): self._capture_pcie_snapshot_linux,
                                 OperatingSystems.WINDOWS.lower(): self._capture_pcie_snapshot_windows}
        get_pcie_snapshot = pcie_snapshot_handler[self.os.os_type.lower()]
        pcie_file_host = get_pcie_snapshot(pcie_file_name)
        if pcie_file_host is None:
            self._log.error("Cycle #{}: Failed to collect PCIE Snapshot.".format(cycle_num))
            return False

        try:
            ret_val = filecmp.cmp(self._pcie_init_snapshot_log_file, pcie_file_host, shallow=False)
        except Exception as ex:
            self._log.error("Cycle #{}: PCI health check failed due to exception: {}.".format(cycle_num, ex))
            ret_val = False
        if ret_val:
            self._log.info("Cycle #{}: PCI health check successful as snapshot is same as "
                           "initial snapshot.".format(cycle_num))
        else:
            self._log.error("Cycle #{}: PCI health check failed as PCI snapshot is different from "
                            "initial snapshot.".format(cycle_num))
            self.perform_pcie_error_check(iteration=0)
        return ret_val

    def perform_s3_cycle(self):
        """
        This Method is Used to Send System to Sleep Mode(S3) and Wakeup using Dc Power On.

        :raise content_exceptions.TestError: When System doesn't perform as expected.
        """
        cmd = self.ENABLE_SLEEP_CMD
        if OperatingSystems.WINDOWS == self.os.os_type:
            cmd = self.ENABLE_SLEEP_CMD
        elif OperatingSystems.LINUX == self.os.os_type:
            cmd = self.LINUX_SLEEP_CMD
        else:
            raise NotImplementedError("Test is not implemented for %s" % self.os.os_type)

        self._log.info("Executing Sleep Command to send the System to Sleep Mode.: %s" % cmd)
        try:
            if self.os.is_alive():
                sleep_cmd_thread = threading.Thread(target=self.os.execute(cmd,
                                                                           self.WAITING_TIME_FOR_STATE_CHANGE))
                sleep_cmd_thread.start()

            else:
                self._log.error("Cannot Send System to Sleep as SUT OS is not reachable.")
                return ResetStatus.OS_NOT_ALIVE
        except Exception as ex:
            raise content_exceptions.TestFail("Unable to Execute Sleep Command due to exception : {}".format(str(ex)))

        power_state = self._common_content_lib.get_power_state(self.phy)
        self._log.debug("Power State after Executing Sleep Command is '{}'".format(power_state))
        start_time = time.time()
        sleep_state = False
        while time.time() - start_time <= self.WAITING_TIME_FOR_STATE_CHANGE:
            if power_state != PowerStates.S0:
                self._log.info("System is Successfully Sent to Sleep Mode and "
                               "System Power State is '{}'".format(power_state))
                sleep_state = True
                break
            else:
                power_state = self._common_content_lib.get_power_state(self.phy)
        if not sleep_state:
            self.fail_or_log("SUT did not entered into %s state, actual state is %s" % (PowerStates.S3, power_state),
                             self.log_or_fail)
            bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
            if bios_pc is not None:
                self._log.info("FPGA PC='{}' BIOS PC='{}'".format(fpga_pc, bios_pc))
                self._failed_pc = bios_pc
                self._boot_flow = BootFlow.POWER_OFF
                return ResetStatus.PC_STUCK
            else:
                self._log.error("Unable to read the post code")
                return ResetStatus.STATE_CHANGE_FAILURE

        self._log.info("Waiting in s3 state for 10 sec...")
        time.sleep(10)
        self._log.debug("Performing DC Power On to Wakeup the System from Sleep Mode")
        self._dc_power.dc_power_on(self.DC_POWER_DELAY)
        time.sleep(self.DC_POWER_DELAY)
        power_state = self._common_content_lib.get_power_state(self.phy)
        self._log.debug("Current SX Power state after DC Power On is '{}'"
                        .format(power_state))
        if power_state != PowerStates.S0:
            self._log.error("SUT did not entered into {} state, actual state is {}".format(PowerStates.S0, power_state))
            bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
            if bios_pc is not None:
                self._log.info("FPGA PostCode is '{}' and BIOS PostCode is '{}' while DC Power On"
                               .format(fpga_pc, bios_pc))
                self._failed_pc = bios_pc
                self._boot_flow = BootFlow.POWER_OFF
                return ResetStatus.PC_STUCK
            else:
                self._log.error("Unable to read the post code")
                return ResetStatus.STATE_CHANGE_FAILURE
        self._log.info("DC Power on is Successful during S3 cycle")

        self._common_content_lib.perform_boot_script()
        try:
            self._log.debug("Waiting for the System to Boot to OS after DC Power On")
            self.os.wait_for_os(self.reboot_timeout)
            status = self.os.is_alive()
            if not status:
                return ResetStatus.OS_NOT_ALIVE
            self._log.info("System is Booted Back to OS after DC Power ON.")
            return ResetStatus.SUCCESS
        except Exception as ex:
            raise content_exceptions.TestError("System is Not Booted Back to OS after DC Power ON due to Exception {}."
                                               .format(str(ex)))

    def perform_s4_cycle(self):
        """
        This Method is Used to Send System to Hibernate Mode(S4) and Wakeup using Dc Power On.

        :raise content_exceptions.TestError: When System doesn't perform as expected.
        """
        cmd = self.ENABLE_SLEEP_CMD
        if OperatingSystems.WINDOWS == self.os.os_type:
            cmd = self.HIBERNATE_CMD
        elif OperatingSystems.LINUX == self.os.os_type:
            cmd = self.LINUX_HIBERNATE_CMD
        else:
            raise NotImplementedError("Test is not implemented for %s" % self.os.os_type)

        self._log.info("Executing Hibernate Command to send the System to Hibernate Mode.: %s" % cmd)
        try:
            if self.os.is_alive():
                self.enable_hibernate_mode()
                sleep_cmd_thread = threading.Thread(target=self.os.execute(cmd,
                                                                           self.WAITING_TIME_FOR_STATE_CHANGE))
                sleep_cmd_thread.start()

            else:
                self._log.error("Cannot Send System to Hibernate as SUT OS is not reachable.")
                return ResetStatus.OS_NOT_ALIVE
        except Exception as ex:
            raise content_exceptions.TestFail("Unable to Execute Hibernate Command due to exception : {}"
                                              .format(str(ex)))

        power_state = self._common_content_lib.get_power_state(self.phy)
        self._log.debug("Power State after Executing Hibernate Command is '{}'".format(power_state))
        start_time = time.time()
        s4_state = False
        while time.time() - start_time <= self.WAITING_TIME_FOR_STATE_CHANGE:
            if power_state != PowerStates.S0:
                self._log.info("System is Successfully Sent to Hibernate Mode and "
                               "System Power State is '{}'".format(power_state))
                s4_state = True
                break
            else:
                power_state = self._common_content_lib.get_power_state(self.phy)
        if not s4_state:
            self.fail_or_log("SUT did not entered into %s state, actual state is %s" % (PowerStates.S4, power_state),
                             self.log_or_fail)
            bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
            if bios_pc is not None:
                self._log.info("FPGA PC='{}' BIOS PC='{}'".format(fpga_pc, bios_pc))
                self._failed_pc = bios_pc
                self._boot_flow = BootFlow.POWER_OFF
                return ResetStatus.PC_STUCK
            else:
                self._log.error("Unable to read the post code")
                return ResetStatus.STATE_CHANGE_FAILURE
        self._log.info("SUT went to Hibernate State")
        self._log.debug("Performing DC Power On to Wakeup the System from Hibernate Mode")
        self._log.info("Waiting in s4 state for 10 sec...")
        time.sleep(10)
        self._log.info("Performing DC Power On to Wakeup the System from Hibernate Mode.")
        self._dc_power.dc_power_on(self.DC_POWER_DELAY)
        time.sleep(self.DC_POWER_DELAY)
        power_state = self._common_content_lib.get_power_state(self.phy)
        self._log.debug("Current SX Power state after DC Power On is '{}'"
                        .format(power_state))
        if power_state != PowerStates.S0:
            self._log.error("SUT did not entered into {} state, actual state is {}".format(PowerStates.S0, power_state))
            bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
            if bios_pc is not None:
                self._log.info("FPGA PostCode is '{}' and BIOS PostCode is '{}' while DC Power On"
                               .format(fpga_pc, bios_pc))
                self._failed_pc = bios_pc
                self._boot_flow = BootFlow.POWER_OFF
                return ResetStatus.PC_STUCK
            else:
                self._log.error("Unable to read the post code")
                return ResetStatus.STATE_CHANGE_FAILURE
        self._log.info("DC Power on successful while S4 cycle")
        self._common_content_lib.perform_boot_script()
        try:
            self._log.debug("Waiting for the System to Boot to OS after DC Power On")
            self.os.wait_for_os(self.reboot_timeout)
            status = self.os.is_alive()
            if not status:
                return ResetStatus.OS_NOT_ALIVE
            self._log.info("System is Booted Back to OS after DC Power ON.")
            return ResetStatus.SUCCESS
        except Exception as ex:
            raise content_exceptions.TestError("System is Not Booted Back to OS after DC Power ON due to Exception {}."
                                               .format(str(ex)))

    def enable_hibernate_mode(self):
        """
        This Method is Used to Enable Hibernate mode in System.

        :raise content_exceptions.TestError: If Hibernate Mode is Not Enabled
        """
        self._log.info("Enabling Hibernate Mode in the System")
        self._common_content_lib.execute_sut_cmd(self.ENABLE_HIBERNATE_CMD, self.ENABLE_HIBERNATE_CMD,
                                                 self._command_timeout)
        self._log.debug("Hibernate Mode is Successfully Enabled in System")
        self._log.info("Verifying whether Hibernate State is Enabled in the System")
        cmd_result = self._common_content_lib.execute_sut_cmd(self.STATE_VERIFICATION_CMD,
                                                              self.STATE_VERIFICATION_CMD,
                                                              self._command_timeout)
        self._log.debug("Command Output is : {}".format(cmd_result))
        available_state_log = cmd_result.split(self.REGEX_FOR_AVAILABLE_SLEEP_MODES)[0]
        if self.REGEX_FOR_HIBERNATE_MODE not in available_state_log:
            raise content_exceptions.TestError("Hibernate Mode is Not Enabled in this System")
        self._log.info("Hibernate Mode is Enabled in this System")

    def disable_hibernate_mode(self):
        """
        This Method is Used to Disable Hibernate Mode in System.

        :raise content_exceptions.TestError: If Hibernate Mode is Not Disabled.
        """
        self._log.info("Disabling Hibernate Mode in the System")
        self._common_content_lib.execute_sut_cmd(self.DISABLE_HIBERNATE_CMD, self.DISABLE_HIBERNATE_CMD,
                                                 self._command_timeout)
        self._log.info("Verifying whether Hibernate State is Disabled in the System")
        cmd_result = self._common_content_lib.execute_sut_cmd(self.STATE_VERIFICATION_CMD,
                                                              self.STATE_VERIFICATION_CMD,
                                                              self._command_timeout)
        self._log.debug("Command Output is : {}".format(cmd_result))
        available_state_log = cmd_result.split(self.REGEX_FOR_AVAILABLE_SLEEP_MODES)[0]
        if self.REGEX_FOR_HIBERNATE_MODE in available_state_log:
            raise content_exceptions.TestError("Hibernate Mode is Not Disabled in this System")
        self._log.info("Hibernate Mode is Disabled in this System")

    def initialize_sdp_sv_objects(self):
        # initialize sdp, if not already initialized
        if self.sdp is None:
            si_cfg = ElementTree.fromstring(ProviderXmlConfigs.SDP_XML_CONFIG)
            self.sdp = ProviderFactory.create(si_cfg, self._log)  # type: SiliconDebugProvider
        # initialize sv, if not already initialized
        if self.sv is None:
            cpu = self._common_content_lib.get_platform_family()
            pch = self._common_content_lib.get_pch_family()
            sv_cfg = ElementTree.fromstring(ProviderXmlConfigs.PYTHON_SV_XML_CONFIG.format(cpu, pch))
            self.sv = ProviderFactory.create(sv_cfg, self._log)  # type: SiliconRegProvider

    def collect_axon_logs(self, post_code, cycle_num, analyzers):
        try:
            self.initialize_sdp_sv_objects()
            if self._common_content_lib.collect_axon_logs(post_code, cycle_num, analyzers, self.sdp, self.sv):
                self._log.info("Successfully collected the axon logs for PC %s and cycle %d.", post_code, cycle_num)
                return True
        except Exception as ex:
            self._log.error("Failed to collect axon logs due to exception: '{}'.".format(ex))
        self._log.info("Failed to collect axon logs for PC %s and cycle %d.", post_code, cycle_num)
        return False

    def dmi_check(self, iteration):
        """
        This method is to check dmi error.
        """
        try:
            self.initialize_sdp_sv_objects()
            dmi_status_file_name = "dmi_status_" + str(iteration) + ".txt"
            dmi_status_log_file = os.path.join(self.health_check_log_dir, dmi_status_file_name)
            self._log.info(dmi_status_log_file)
            self.sdp.itp.unlock()
            return self._common_content_lib.check_for_dmi_error(sv=self.sv, sdp=self.sdp,
                                                                dmi_log_file=dmi_status_log_file)
        except Exception as ex:
            self._log.error(ex)
            return False

    def __perform_health_check(self, cycle_num, health_check_errors):
        """
        This method checks for all health checks.
        """
        status_list = []
        for health_check, func in self.dict_health_check_handlers.items():
            if (health_check == HealthCheckFailures.CPU_THERMAL or health_check == HealthCheckFailures.DIMM_THERMAL) \
                    and (cycle_num % 10 != 0 and cycle_num != 1):
                continue
            self._log.info("Performing {} Health check.".format(health_check))
            status = func(cycle_num)
            status_list.append(status)
            if not status:
                self._log.error("Cycle#{}: {} Health check failed.".format(cycle_num, health_check))
                health_check_errors.append(health_check)
                if health_check in self.list_stop_on_failure:
                    self.stop_on_failure_flag = True
            else:
                self._log.info("Cycle#{}: {} Health Check Passed.".format(cycle_num, health_check))

        return all(status_list)

    def handle_reset_success(self, cycle_num):
        status = True

        if self._common_content_lib.check_os_alive():
            if not self.ignore_mce_error:
                mce_errors = self._common_content_lib.check_if_mce_errors()
                self._log.debug(mce_errors)
                self._log.error("Machine Check errors are Logged during S5 Cycle '{}'".format(cycle_num))
                status = False
                self._log.error("******* Cycle number:{} failed due to Machine check errors ******".format(cycle_num))
        else:
            self._log.error("Could not check MCE Errors as not able to SSH to SUT.")

        health_check_errors = []
        if self.health_check:
            status = self.__perform_health_check(cycle_num, health_check_errors)

        if not status:
            if HealthCheckFailures.ANY in self.list_stop_on_failure:
                self.stop_on_failure_flag = True
            self._number_of_failures += 1
            log_error = "******* Cycle number:{} failed due to Health Check " \
                        "errors:{} ********".format(cycle_num, health_check_errors)
            self._log.error(log_error)
            log_error = "Cycle number:{} failed due to Health Check " \
                        "errors:{}. Previous failure was at " \
                        "cycle #{}".format(cycle_num, health_check_errors, self._prev_cycle_num)
            self._list_failures.append(log_error)

            hc_errors = "Health Check Errors:" + "|".join(health_check_errors)
            self.summary_file.write("{},Failed,{},{}\n".format(cycle_num, self._prev_cycle_num, hc_errors))
            self.summary_file.flush()
            self._log.info("dumping PythonSV command output: ")
            self.__pythonsv_log_dump(itteration=cycle_num)

            self._prev_cycle_num = cycle_num
        else:
            self._number_of_success += 1
            self._log.info("******* Cycle number %d succeeded *******", cycle_num)
            self.summary_file.write("{},Succeeded,NA,No Errors\n".format(cycle_num))
            self.summary_file.flush()

        if self.stop_on_failure_flag:
            self._log.info("Stopping test due to a failures in one or more of the health_checks "
                           "as specified in config \<stop_on_failure\>")
            return False
        if not self._common_content_lib.check_os_alive():
            return self.prepare_sut_for_retrigger()
        return True

    def handle_reset_dc_failure(self, cycle_num):
        self._number_of_failures += 1
        log_error = "Cycle #{}: Failed due to failure with DC power operation. Previous failure was at " \
                    "cycle #{}".format(cycle_num, self._prev_cycle_num)
        self._log.error(log_error)
        self._list_failures.append(log_error)
        self.summary_file.write("{},Failed,{},DC Power failure\n".format(cycle_num, self._prev_cycle_num))
        self.summary_file.flush()

        self.dmi_check(cycle_num)

        self._prev_cycle_num = cycle_num
        if HealthCheckFailures.BOOT_FAILURE in self.list_stop_on_failure or HealthCheckFailures.ANY in self.list_stop_on_failure:
            self._log.info("Terminating the test due to Reset DC failure")
            return False
        return self.prepare_sut_for_retrigger()

    def handle_reset_ac_failure(self, cycle_num):
        self._number_of_failures += 1
        log_error = "Cycle #{}: Failed due to failure with AC power operation. Previous failure was at " \
                    "cycle #{}".format(cycle_num, self._prev_cycle_num)
        self._log.error(log_error)
        self._list_failures.append(log_error)
        self.summary_file.write("{},Failed,{},AC Power failure\n".format(cycle_num, self._prev_cycle_num))
        self.summary_file.flush()

        self.dmi_check(cycle_num)

        self._prev_cycle_num = cycle_num
        if HealthCheckFailures.BOOT_FAILURE in self.list_stop_on_failure or HealthCheckFailures.ANY in self.list_stop_on_failure:
            self.stop_on_failure_flag = True
            self._log.info("Terminating the test due to reset AC failure for PC")
            return False
        return self.prepare_sut_for_retrigger()

    def handle_reset_pc_stuck_failure(self, cycle_num):
        self._number_of_failures += 1

        log_error = "Cycle #{}: SUT is stuck at post code '{}' during '{}' boot flow. Previous failure was at " \
                    "cycle #{}".format(cycle_num, self._failed_pc, self._boot_flow, self._prev_cycle_num)
        self._log.error(log_error)
        self._list_failures.append(log_error)

        self.summary_file.write(
            "{},Failed,{},PC Stuck at {}\n".format(cycle_num, self._prev_cycle_num, self._failed_pc))
        self.summary_file.flush()

        self._prev_cycle_num = cycle_num

        collect_axon = True
        if len(self._list_ignore_pc_errors) > 0 and self._failed_pc in self._list_ignore_pc_errors:
            collect_axon = False

        self.dmi_check(cycle_num)

        if collect_axon:
            analyzers = self._common_content_configuration.get_axon_analyzers()
            print("Analyzers=", analyzers)
            if len(analyzers) == 0:
                self._log.info("No analyzers are configured, axon logs will not be captured.")
                self._list_ignore_pc_errors.append(self._failed_pc)
            else:
                self._log.info("******* Start collecting axon logs for PC %s and Cycle %d", self._failed_pc, cycle_num)
                if self.collect_axon_logs(self._failed_pc, cycle_num, analyzers):
                    self._list_ignore_pc_errors.append(self._failed_pc)
        if HealthCheckFailures.PC_STUCK in self.list_stop_on_failure or HealthCheckFailures.ANY in self.list_stop_on_failure:
            self.stop_on_failure_flag = True
            self._log.info("Terminating the test due to system hang for PC: {}".format(self._failed_pc))
            return False
        return self.prepare_sut_for_retrigger()

    def handle_reset_os_not_alive_failure(self, cycle_num):
        if HealthCheckFailures.OS_NOT_ALIVE in self.list_stop_on_failure or HealthCheckFailures.ANY in self.list_stop_on_failure:
            self.stop_on_failure_flag = True
        self._number_of_failures += 1
        log_error = "Cycle #{}: SUT failed to boot to OS. Previous failure was at " \
                    "cycle #{}".format(cycle_num, self._prev_cycle_num)
        self._log.error(log_error)
        self._list_failures.append(log_error)

        self.dmi_check(cycle_num)

        self.summary_file.write("{},Failed,{},SUT failed to BOOT to OS\n".format(cycle_num, self._prev_cycle_num,
                                                                                 self._failed_pc))
        self.summary_file.flush()
        self._prev_cycle_num = cycle_num
        if HealthCheckFailures.OS_NOT_ALIVE in self.list_stop_on_failure or HealthCheckFailures.ANY in self.list_stop_on_failure:
            self._log.info("Terminating the test due to OS NOT ALIVE")
            return False
        return self.prepare_sut_for_retrigger()

    def handle_reset_state_change_failure(self, cycle_num):
        self._number_of_failures += 1
        self._prev_cycle_num = cycle_num
        log_error = "Cycle #{}: SUT State change did not reach the expected state. Previous failure was at " \
                    "cycle #{}".format(cycle_num, self._prev_cycle_num)
        self._log.error(log_error)
        self._list_failures.append(log_error)

        self.dmi_check(cycle_num)

        self.summary_file.write(
            "{},Failed,{},SUT state did change to expected state.\n".format(cycle_num, self._prev_cycle_num))
        self.summary_file.flush()
        if HealthCheckFailures.STATE_CHANGE in self.list_stop_on_failure or HealthCheckFailures.ANY in self.list_stop_on_failure:
            self.stop_on_failure_flag = True
            self._log.info("Terminating the test due to system hang for PC: {}" .format(self._failed_pc))
            return False
        return self.prepare_sut_for_retrigger()

    def default_reset_handler(self, cycle_num):
        self._number_of_failures += 1

        log_error = "Cycle #{}: Failed due to unknown error. Previous failure was at " \
                    "cycle #{}".format(cycle_num, self._prev_cycle_num)
        self._log.error(log_error)
        self._list_failures.append(log_error)

        self.dmi_check(cycle_num)

        self.summary_file.write("{},Failed,{},SUT failed to BOOT to OS.\n".format(cycle_num, self._prev_cycle_num))
        self.summary_file.flush()

        self._prev_cycle_num = cycle_num
        if HealthCheckFailures.BOOT_FAILURE in self.list_stop_on_failure or HealthCheckFailures.ANY in self.list_stop_on_failure:
            self.stop_on_failure_flag = True
            self._log.info("Terminating the test due to system hang for PC: %d" % self._failed_pc)
            return False
        return self.prepare_sut_for_retrigger()

    def prepare_sut_for_retrigger(self):
        # get the SUT boot to OS first
        self._log.info("Preparing the SUT for re-trigger of cycle test.")
        attempt = 0
        while attempt < self.NUMBER_OF_RECOVERY_ATTEMPTS:
            try:
                self.perform_graceful_g3()  # To make the system alive
            except Exception as ex:
                pass
            if self._common_content_lib.check_os_alive():
                self._log.info("Prepare SUT for re-trigger: SUT did booted to OS.")
                return True
            self._log.error("Ateempt#{}: Prepare SUT for re-trigger: SUT did not boot to OS.".format(attempt + 1))
            attempt += 1
        self._log.error(
            "Prepare SUT for re-trigger: SUT did not boot to OS after multiple attempts, aborting the test.")
        return False

    def print_result_summary(self):
        self._log.info("******************* Start Summary of Cycling test *************************")
        self._log.info(
            "Number of cycles succeeded={} and failed = {}.".format(self._number_of_success, self._number_of_failures))
        if self._number_of_failures > 0:
            self._log.error("\n".join(self._list_failures))
        self._log.info("******************* End Summary of Cycling test *************************")

    def set_register_before_reset(self, cycle_number, reset_type=None):
        """
        This method is to get check the Reset.
        """
        try:
            self.initialize_sdp_sv_objects()
            sticky_reg = "ubox.ncdecs.biosscratchpad6_cfg"
            non_sticky_reg = "ubox.ncdecs.biosnonstickyscratchpad7_cfg"
            self.sv.get_by_path(self.sv.UNCORE, reg_path=sticky_reg).write(0xbf111111)
            self._log.info(self.sv.get_by_path(self.sv.UNCORE, reg_path=sticky_reg))
            self.sv.get_by_path(self.sv.UNCORE, reg_path=non_sticky_reg).write(0xbf111111)
            self.reset_type = reset_type
        except:
            self._log.error("Unable to set the warm reset check register")

    def perform_pcie_error_check(self, iteration=0, clear_flag=False):
        """
        This method is to check pcie error.

        :param iteration
        :param clear_flag
        """

        self.initialize_sdp_sv_objects()
        self.sdp.itp.unlock()
        pcie_error_status_file_name = "pcie_error_" + str(iteration) + ".txt"
        pcie_error_log_file = os.path.join(self.health_check_log_dir, pcie_error_status_file_name)
        path_in_list = self.sv.get_by_path(self.sv.SOCKETS, "uncore.pi5.pxps.pciegs.ports.path")
        port_path_regex = r"pxp\S.pcieg\S.port\S"
        socket_regex = r"socket(\S).*"
        ltssm = self.sv.get_ltssm_object()

        for each_list in path_in_list:
            for each_path in each_list:
                port_path_output = re.findall(port_path_regex, each_path)[0]
                self._log.info("Port path output is : {}".format(port_path_output))
                socket = None
                if port_path_output:
                    socket = re.findall(socket_regex, each_path)[0]
                    self._log.info("Socket number is : {}".format(socket))
                try:
                    self.sdp.start_log(pcie_error_log_file, "a")
                    ret_val = ltssm.checkForErrors(int(socket), port_path_output, clear=0)
                    self.sdp.stop_log()
                    with open(pcie_error_log_file, 'a') as f:
                        f.write("0x{:X}\n".format(ret_val))
                    if clear_flag and ret_val:
                        self.sdp.start_log(pcie_error_log_file, "a")
                    ltssm.checkForErrors(int(socket), port_path_output, clear=1)
                    self.sdp.stop_log()
                    with open(pcie_error_log_file, 'a') as f:
                        f.write("0x{:X}\n".format(ret_val))
                except Exception as ex:
                    self._log.error("The exception is : {}".format(ex))
