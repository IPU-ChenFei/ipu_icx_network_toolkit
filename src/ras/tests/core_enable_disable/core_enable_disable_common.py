#!/usr/bin/env python
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and propri-
# etary and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be ex-
# press and approved by Intel in writing.

import os
import configparser as config_parser
import random

from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.lib.content_base_test_case import ContentBaseTestCase


class CoreEnableDisableBase(ContentBaseTestCase):
    """
    Base Class for Glasgow_id : 59496, 58511
    Checks current core count, disables 4 cores via bios, and verifies that after bios updates, it has expected core
    count, Cleanup will recover disabled cores
    Test case flow:
    -get the initial core count , disable 4 cores , get the current core count , verify the count difference and enable
     all cores back to default state.
    """
    NUM_CORES_TO_DISABLE = [hex(cores) for cores in range(1, 4096)]

    def __init__(self, test_log, arguments, cfg_opts, core_enable_bios_config_file,
                 core_disable_bios_config_file):
        """
        Create an instance of sut os provider, BiosProvider and
         BIOS util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param core_enable_bios_config_file: Bios Configuration file name
        :param core_disable_bios_config_file: Bios Configuration file name
        """
        super(CoreEnableDisableBase, self).__init__(test_log, arguments, cfg_opts)
        self.disable_cores_bios_config_file_path = core_disable_bios_config_file
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)  # type: AcPowerControlProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._content_cfg = ContentConfiguration(self._log)
        self._reboot_timeout_in_sec = int(self._content_cfg.get_reboot_timeout())

        if not self._os.is_alive():
            self._log.info("System is not in OS, will perform ac off and on..")
            self._common_content_lib.perform_graceful_ac_off_on(self._ac_power)
            self._log.info("Waiting for OS to be alive...")
            self._os.wait_for_os(self._reboot_timeout_in_sec)

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        cur_path = os.path.dirname(os.path.realpath(__file__))

        self.enable_core_bios_config_file_path = self._common_content_lib.get_config_file_path(
                cur_path, core_enable_bios_config_file)
        self.disable_core_bios_config_file_path = self._common_content_lib.get_config_file_path(
                cur_path, core_disable_bios_config_file)

        self._bios_util = BiosUtil(cfg_opts, bios_config_file=None, bios_obj=self._bios, log=self._log,
                                   common_content_lib=self._common_content_lib)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._platform = self._cscripts.silicon_cpu_family

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog.conf file to sut and reboot
        2. Clear All Os Logs before Starting the Test Case
        3. Set the bios knobs to its default mode.
        4. Set the bios knobs as per the test case.
        5. Reboot the SUT to apply the new bios settings.
        6. Verify the bios knobs whether they updated properly.

        :return: None
        """
        self._install_collateral.copy_mcelog_conf_to_sut()
        super(CoreEnableDisableBase, self).prepare()

    def enable_all_cores(self):
        # set the bios to enable all cores
        self._log.info("Set the Bios Knobs to enable all cores..")
        self._bios_util.set_bios_knob(self.enable_core_bios_config_file_path)  # To set the bios knob setting.
        self._log.info("Bios Knobs are Set to enable all cores and Reboot to Apply the Settings")

        # for bios knob 'CoreDisableMask_0' to be effective, we need graceful ac off and on
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_power)
        self._os.wait_for_os(self._reboot_timeout_in_sec)
        self._bios_util.verify_bios_knob(self.enable_core_bios_config_file_path)  # To verify the bios knob settings.

    def disable_few_cores(self, core_count_original_int):
        # Set Bios knob to disable few cores.
        # set the bios to disable 4 cores
        num_cores_to_disable = 4
        if core_count_original_int <= num_cores_to_disable:
            log_error = "Minimum '{}' cores required, actual detected='{}', minimum cores not available and" \
                        "hence stopping the tests...".format(num_cores_to_disable + 1, core_count_original_int)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info(" Setting CoreDisableMask_0 to Non-Zero value in BIOS")
        self._log.info("Set the Bios Knobs to disable '{}' cores..".format(num_cores_to_disable))
        self._bios_util.set_bios_knob(self.disable_core_bios_config_file_path)  # To set the bios knob setting.
        self._log.info("Bios Knobs are set to disable '{}' cores and rebooting to apply "
                       "the settings".format(num_cores_to_disable))

        # for bios knob 'CoreDisableMask_0' to be effective, we need graceful G3
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_power)
        self._log.info("Waiting for OS to be alive..")
        self._os.wait_for_os(self._reboot_timeout_in_sec)
        self._bios_util.verify_bios_knob(self.disable_core_bios_config_file_path)  # To verify the bios knob settings.

    def disable_few_random_cores(self, core_count_original_int):
        # Set Bios knob to disable few cores.
        core_disable_mask = random.choice(self.NUM_CORES_TO_DISABLE)
        core_disable_mask = core_disable_mask[:2] + core_disable_mask[2:].zfill(16)
        num_cores_to_disable = bin(core_disable_mask & 0xFFFFFFFF).count("1")
        if core_count_original_int <= num_cores_to_disable:
            log_error = "Minimum '{}' cores required, actual detected='{}', minimum cores not available and" \
                        "hence stopping the tests...".format(num_cores_to_disable + 1, core_count_original_int)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        cp = config_parser.ConfigParser()
        cp.read(self.disable_core_bios_config_file_path)
        list_sections = cp.sections()
        if "Core Disable Bitmap(Hex)" in list_sections:
            cp.get("Core Disable Bitmap(Hex)", 'Target')
            cp.set("Core Disable Bitmap(Hex)", 'Target', '"{}"'.format(core_disable_mask))
            core_disable_mask = cp.get("Core Disable Bitmap(Hex)", 'Target')
            self._log.info("Core Disable Bitmap(Hex) is : {}".format(core_disable_mask))

        with open(self.disable_core_bios_config_file_path, 'w') as configfile:
            cp.write(configfile)

        # set the bios to disable 4 cores
        self._log.info(" Setting CoreDisableMask_0 to Non-Zero value in BIOS")
        self._log.info("Set the Bios Knobs to disable '{}' cores..".format(num_cores_to_disable))
        self._bios_util.set_bios_knob(self.disable_core_bios_config_file_path)  # To set the bios knob setting.
        self._log.info("Bios Knobs are set to disable '{}' cores and rebooting to apply "
                       "the settings".format(num_cores_to_disable))

        # for bios knob 'CoreDisableMask_0' to be effective, we need graceful G3
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_power)
        self._log.info("Waiting for OS to be alive..")
        self._os.wait_for_os(self._reboot_timeout_in_sec)
        self._bios_util.verify_bios_knob(self.disable_core_bios_config_file_path)  # To verify the bios knob settings.

    def verify_core_enable_disable(self):
        """
        Check that by default all the cores are enabled(and if not enable all cores)
        Disable few cores and check that they are getting disabled
        Reboot and wait till system boots to the OS
        Get core count after BIOS update(disabling some cores)
        Verify the core count is less than the original
        Enable the cores back and check that they are getting enabled
        Reboot and wait till system boots to the OS
        Verify original core count is restored for further tests
`
        :return:  True if pass, False if not
        """
        try:
            enable_all_cores_back = False
            self._log.info("1. Enable all cores...")
            self.enable_all_cores()
            original_core_count, return_status = self._common_content_lib.get_core_count_from_os()
            if not return_status:
                self._log.error("Failed to get original core count from SUT")
                return False

            self._log.info("Number of original cores count='{}'".format(original_core_count))

            self._log.info("2. Disable few cores...")
            self.disable_few_cores(original_core_count)
            enable_all_cores_back = True
            reduced_core_count, return_status = self._common_content_lib.get_core_count_from_os()
            if not return_status:
                self._log.error("Failed to get reduced core count from SUT after disabling few cores..")
                return False

            self._log.info("Original core count=%d, reduced count was %d", original_core_count,
                           reduced_core_count)
            if int(reduced_core_count) < int(original_core_count):
                self._log.info("Core count is less than original core count...")
            else:
                self._log.error("Error: Reduced core count was not less than the original core count")
                return False

            self._log.info("3. Enable all cores back...")
            self.enable_all_cores()
            enable_all_cores_back = False
            original_core_count1, return_status = self._common_content_lib.get_core_count_from_os()
            if not return_status:
                self._log.error("Failed to get updated original core count from sut")
                return False

            self._log.info("Number of updated original cores count after "
                           "enabling all cores='{}'".format(original_core_count1))
            if original_core_count1 == original_core_count:
                self._log.info("Number of cores restored back to original core count '{}' "
                               "after enabling all cores".format(original_core_count))
            else:
                self._log.error("Number of cores did not restored back to original core count '{}' "
                                "after enabling all cores".format(original_core_count))
                return False

            return True
        except Exception as ex:
            log_error = "Unable to Check Whether Core is Enabled or Disabled due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise ex
        finally:
            # restore back all the cores
            if enable_all_cores_back:
                self.enable_all_cores()

    def verify_core_count_before_and_after_disabling_cores(self):
        """
        This Method is used to get the Verify the Count of Os Core and Itp Core before and after disabling the Cores.

        :return: True or False
        """
        try:
            enable_all_cores_back = False
            self._log.info("1. Enable all cores...")
            self.enable_all_cores()
            core_count_original_int, core_count_function_status = self._common_content_lib.get_core_count_from_os()
            if not core_count_function_status:
                self._log.error("Failed to get original core count from DUT")
                return False

            # get ITP core enabled info
            itp_core_cnt_original, itp_core_mask_original = \
                self._common_content_lib.get_itp_core_count(csp=self._cscripts)

            if core_count_original_int != itp_core_cnt_original:
                self._log.info("Original OS and ITP core counts do NOT Match")

            core_disable_mask = 0x00000F  # 4 possible cores disabled
            # ICX can have a unusual core mask - so & with the disable mask to get real cores to disable
            num_cores_to_disable = bin((core_disable_mask & 0xFFFFFFFF) & itp_core_mask_original).count("1")

            if core_count_original_int <= num_cores_to_disable:
                self._log.info(" Minimum %d cores required, actual detected=%d",
                               num_cores_to_disable + 1, core_count_original_int)
                self._log.error(" Minimum cores not available, stopping test")
                return False

            self._log.info("2. Disable few random cores...")
            self._log.info(" Original OS core count before update = %d", core_count_original_int)
            self._log.info(" Original ITP core count before update = %d\n", itp_core_cnt_original)
            self._log.info(" Setting CoreDisableMask_0 to %s in BIOS", str(hex(core_disable_mask)))

            self.disable_few_random_cores(core_count_original_int)
            enable_all_cores_back = True
            core_count_int, core_count_function_status = self._common_content_lib.get_core_count_from_os()
            if not core_count_function_status:
                self._log.error(" Failed to get updated core count from DUT")
                return False

            itp_core_cnt, itp_core_mask = self._common_content_lib.get_itp_core_count(csp=self._cscripts)

            self._log.info(" Core count from OS after BIOS update=%s", str(core_count_int))
            self._log.info(" Core count from ITP after BIOS update=%s", str(itp_core_cnt))

            expected_os_core_count = core_count_original_int - num_cores_to_disable
            expected_itp_core_count = itp_core_cnt_original - num_cores_to_disable

            if int(core_count_int) == expected_os_core_count and itp_core_cnt == expected_itp_core_count:
                self._log.info(" OS and ITP Core count is as expected")
                self.enable_all_cores()
                enable_all_cores_back = False
                original_core_count1, return_status = self._common_content_lib.get_core_count_from_os()
                if not return_status:
                    self._log.error("Failed to get updated original core count from sut")
                    return False

                self._log.info("Number of updated original cores count after "
                               "enabling all cores='{}'".format(original_core_count1))
                if original_core_count1 == core_count_original_int:
                    self._log.info("Number of cores restored back to original core count '{}' "
                                   "after enabling all cores".format(core_count_original_int))
                else:
                    self._log.error("Number of cores did not restored back to original core count '{}' "
                                    "after enabling all cores".format(core_count_original_int))
                    return False
                return True
            else:
                self._log.info("Expected OS core count=%d, actual count was %d", expected_os_core_count, core_count_int)
                self._log.info("Expected ITP core count=%d, actual count was %d", expected_itp_core_count, itp_core_cnt)
                self._log.error(" Error: Core count was not expected")
                return False
        finally:
            if enable_all_cores_back:
                self.enable_all_cores()

