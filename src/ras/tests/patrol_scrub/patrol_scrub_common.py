#!/usr/bin/env python
##########################################################################
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
##########################################################################

import os
import time

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.bios_util import BiosUtil
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.ras.lib.ras_einj_util import RasEinjCommon
from src.lib.install_collateral import InstallCollateral
from src.lib.mirror_mode_common import MirrorCommon
from src.ras.lib.ras_common_utils import RasCommonUtil
from src.lib.content_base_test_case import ContentBaseTestCase


class PatrolScrubCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Patrol Scrub Functionality Test Cases
    """
    scrub_delay_sec = 180
    CE_ERROR_ERR_SIGNATURE_LIST = \
        ["ADDR 12346000",
         "scrub corrected error",
         "event severity: corrected"]

    UCE_ERROR_ERR_SIGNATURE_LIST = \
        ["ADDR 12345200",
         "Machine check events logged",
         "event severity: recoverable",
         "Uncorrected DIMM memory error"]

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file
    ):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            PatrolScrubCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts)

        self._cfg = cfg_opts

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)

        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

        self._command_timeout = self._common_content_configuration.get_command_timeout()

        self._platform = self._common_content_lib.get_platform_family()
        self._install_collateral = InstallCollateral(self._log, self.os, self._cfg)
        self._ras_common = RasCommonUtil(self._log, self.os, cfg_opts, self._common_content_configuration, self._bios_util)
        self._einj_obj = RasEinjCommon(self._log, self.os, cfg_opts, self._common_content_lib,
                                       self._common_content_configuration, self.ac_power)
        self.os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                            self._common_content_lib)
        self.is_patrol_scrub_enabled_path_dict = {
                ProductFamilies.CLX: "pcu_cr_capid3_cfg",
                ProductFamilies.SKX: "pcu_cr_capid3_cfg",
                ProductFamilies.CPX: "pcu_cr_capid3_cfg",
                ProductFamilies.ICX: "punit.capid3_cfg",
                ProductFamilies.SPR: "punit.capid3_cfg"
            }

    def is_patrol_scrub_feature_enabled(self):
        """
        Check platform patrols scrub status

        return: True if it is enabled
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:

            patrolscrub_status = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE,
                                                              reg_path=self.is_patrol_scrub_enabled_path_dict[
                                                                  self._platform],
                                                              field="disable_patrol_scrub", socket_index=0)

            patrolscrub_status = str(patrolscrub_status).replace("[0x", "").replace("]", "")

            if patrolscrub_status == 1:
                self._log.info("Platform does NOT have Patrol scrub enabled ")
                return False
            else:
                self._log.info("Platform does have Patrol scrub enabled ")
                return True

    def check_for_scrub_error(self, pop_ch_list):
        """
        Check status of scrub error

        :param pop_ch_list:  memicals utility objects
        :return: True if error found, otherwise False
        """
        with ProviderFactory.create(self.si_dbg_cfg, self._log) as sdp_obj:  # type: SiliconDebugProvider
            try:
                patrol_scrub_error_found = False
                sdp_obj.halt()
                self._log.info("Checking for patrol scrub error detected in registers(retry_rd_err_log.patspr")

                for pop_ch in pop_ch_list:
                    pop_ch.regs.set_access('mem')

                    rd_err_path_dict = {
                        ProductFamilies.CLX: "imc" + str(pop_ch.mc) + "_c" + str(pop_ch.ch) + "_retry_rd_err_log",
                        ProductFamilies.CPX: "imc" + str(pop_ch.mc) + "_c" + str(pop_ch.ch) + "_retry_rd_err_log",
                        ProductFamilies.ICX: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                            pop_ch.ch) + ".retry_rd_err_log",
                        ProductFamilies.SPR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                            pop_ch.ch) + ".retry_rd_err_log",
                        ProductFamilies.SNR: "memss.mc" + str(pop_ch.mc) + ".ch" + str(
                            pop_ch.ch) + ".retry_rd_err_log"
                    }
                    if pop_ch.sktobj.uncore.get_by_path(rd_err_path_dict[self._platform]).patspr == 1:
                        self._log.info("Error was detected by patrol scrubber at mc=" + str(pop_ch.mc) +
                                       " ch=" + str(pop_ch.ch) + "\n")
                        patrol_scrub_error_found = True
                        break

                return patrol_scrub_error_found
            except Exception as ex:
                log_err = "An Exception Occurred {}".format(ex)
                self._log.error(log_err)
                raise log_err

            finally:
                self._log.info("Resume the Machine")
                sdp_obj.go()

    def test_patrol_scrub(self, corrected_error=True):
        """
        Test Patrol scrub error flow.

        :param corrected_error  do corrected error if True , other wise do a uncorrected error
        :return: True if error is detected by patrol scrub engine
        """

        # Set time and data on the OS
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj, \
                ProviderFactory.create(self.si_dbg_cfg, self._log) as sdp_obj:
            mirror_mode_obj = MirrorCommon(self._log, cscripts_obj, sdp_obj)
            self._common_content_lib.set_datetime_on_linux_sut()
            self._install_collateral.copy_mcelog_conf_to_sut()

            self._log.info("Clearing OS logs .......")
            self._common_content_lib.clear_all_os_error_logs()
            if corrected_error:
                inject_addr = 0x12346000
            else:
                inject_addr = 0x12345200

            if corrected_error:
                error_type = self._einj_obj.EINJ_MEM_CORRECTABLE
            else:
                error_type = self._einj_obj.EINJ_MEM_UNCORRECTABLE_NONFATAL

            patrol_scrub_check = False

            if not self.is_patrol_scrub_feature_enabled():
                log_err = "Patrol scrub is disabled - Can not proceed with test"
                self._log.error(log_err)
                raise log_err

            if mirror_mode_obj.get_mirror_status_registers():
                log_err = "Detected mirroring is enabled - Please disable mirroring - Exiting ..."
                self._log.info(log_err)
                raise log_err

            if corrected_error is False:
                # EINJ uses patrol scrub to detect error when injecting Uncorrectable non fatal(0x10)
                #  so.. Using EINJ as is
                if not self._einj_obj.einj_prepare_injection():
                    log_err = "Failed to prepare for EINJ injection"
                    self._log.error(log_err)
                    raise log_err

                inj_result = self._einj_obj.einj_inject_error(error_type, inject_addr)

                if not inj_result:
                    log_err = "Failed to inject error with EINJ"
                    self._log.info(log_err)
                    raise log_err

                error_signature_list = self.UCE_ERROR_ERR_SIGNATURE_LIST
                patrol_scrub_check = True

            else:  # Corrected error

                try:
                    mu = cscripts_obj.get_xnm_memicals_utils_object()
                    sdp_obj.halt()
                    time.sleep(self._common_content_configuration.itp_halt_time_in_sec())
                    error_signature_list = self.CE_ERROR_ERR_SIGNATURE_LIST
                    if self._platform in self._common_content_lib.SILICON_14NM_FAMILY:
                        pop_ch_list = mu.getPopChList(socket=0)

                    else:
                        pop_ch_list = mu.get_pop_ch_list(socket=0, ddr4=True)

                    if self.check_for_scrub_error(pop_ch_list):
                        log_err = "Unexpected scrub error exists - please reboot and run again"
                        self._log.error(log_err)
                        raise log_err
                    else:
                        self._log.info("No Scrub Error exist as Expected")
                    ei = cscripts_obj.get_cscripts_utils().get_ei_obj()
                    self._log.info("Inject the error...")
                    ei.injectMemError(inject_addr, errType="ce", PatrolConsume=True)

                    self._log.info("Waiting for error to be detected by patrol scrub(" + str(self.scrub_delay_sec) +
                                   " seconds)")
                    time.sleep(self.scrub_delay_sec)
                    if self.check_for_scrub_error(pop_ch_list):
                        self._log.info("Scrub Error Found as Expected")
                        patrol_scrub_check = True
                    else:
                        log_err = "Error: Scrub Error not Found"
                        self._log.error(log_err)
                        raise log_err

                    if not self.os.is_alive():
                        sdp_obj.pulse_pwr_good()
                        self.os.wait_for_os(self._common_content_configuration.get_reboot_timeout())

                except Exception as e:
                    raise RuntimeError("Patrol scrub test failed with exception -" + str(e))

                finally:
                    self._log.info("Resume the Machine")
                    sdp_obj.go()

            os_log_check_result = False
            # Check for proper OS error message
            if error_signature_list is not None:
                os_log_check_result = self.os_log_obj.verify_os_log_error_messages(
                    __file__, self.os_log_obj.DUT_JOURNALCTL_FILE_NAME, error_signature_list)

            return patrol_scrub_check and os_log_check_result
