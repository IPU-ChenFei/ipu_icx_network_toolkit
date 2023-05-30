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
import time

from dtaf_core.providers.flash_provider import FlashProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.lib.configuration import ConfigurationHelper

from src.lib.bios_util import ItpXmlCli
from src.lib.flash_util import FlashUtil
from src.lib import content_exceptions
from src.provider.ifwi_provider import IfwiProfileProvider
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.rdmsr_and_cpuid_provider import RdmsrAndCpuidProvider
from src.lib.dtaf_content_constants import CbntConstants


class BootGuardValidator(ContentBaseTestCase):
    """
    Base class extension for boot guard profile which holds common arguments, functions.
    """
    PROFILE0 = "Profile0"
    PROFILE3 = "Profile3"
    PROFILE4 = "Profile4"
    PROFILE5 = "Profile5"
    BTG_P0_VALID = [0x00000000400000000]
    CBNT_BTG_P0_VALID = [0x0000000D00000000, 0x00000001D00000000]

    BTG_P4_VALID = [0x0000000700000051]
    CBNT_BTG_P4_VALID = [0x0000000F00000051, 0x00000001F00000051]

    BTG_P5_VALID = [0x000000070000007B, 0x000000070000007D, 0x0000000700000075]
    CBNT_BTG_P5_VALID = [0x0000000F0000007B, 0x0000000F0000007D, 0x00000001F0000007D, 0x0000000F00000075]

    BTG_P3_VALID = [0x000000070000006B, 0x000000070000006D, 0x000000070000006F]
    CBNT_BTG_P3_VALID = [0x0000000F0000006B, 0x0000000F0000006D, 0x00000001F0000006D, 0x0000000F0000006F]

    BTP_P3_WITHOUT_TPM_VALID = [0x0000000700000041]
    CBNT_BTG_P3_WITHOUT_TPM_VALID = [0x0000000F00000041, 0x00000001F00000041]

    BTG_SACM_INFO_MSR_ADDRESS = 0x13a
    RDMSR_COMMAND = "rdmsr {}"

    def __init__(self, test_log, arguments, cfg_opts):
        """
         Create an instance of sut os provider, flash emulator, common content, Config util, Flash Util, Fit Util

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(BootGuardValidator, self).__init__(test_log, arguments, cfg_opts,)
        banino_flash_cfg = ConfigurationHelper.filter_provider_config(sut=self.sut,
                                                                      provider_name=r"flash",
                                                                      attrib=dict(id="2"))
        banino_flash_cfg = banino_flash_cfg[0]
        self._flash = ProviderFactory.create(banino_flash_cfg, test_log)  # type: FlashProvider
        self._flash_obj = FlashUtil(self._log, self.os, self._flash, self._common_content_lib,
                                    self._common_content_configuration)  # type: FlashUtil
        content_cfg = self._common_content_configuration.get_content_config()
        ifwi_prf_cfg = content_cfg.find(IfwiProfileProvider.DEFAULT_CONFIG_PATH)
        self._ifwi_prf_obj = IfwiProfileProvider.factory(self._log, ifwi_prf_cfg, self.os)  # type IfwiProfileProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.itp_xml_cli_util = ItpXmlCli(self._log, cfg_opts)
        self._rdmsr_and_cpuid_obj = RdmsrAndCpuidProvider.factory(self._log, self.os, cfg_opts)
        self._ac_power_off_wait_time = self._common_content_configuration.ac_power_off_wait_time()
        self.before_flash_bios_version = self._flash_obj.get_bios_version()
        self._log.info("Bios Vesion before flashing {}".format(self.before_flash_bios_version))

    def prepare(self):
        """
        Pre-validating whether sut is alive and checks for Bios flash version before flashing ifwi.

        :return: None
        """
        super(BootGuardValidator, self).prepare()

    def flash_binary_image(self, boot_profile):
        """
        This function will create the binary file based on the profile and flash the binary to bios.

        :param boot_profile: boot profile name
        :raise: Content Exception if IFWI file is not found in given location
        """
        self._log.info("Create the binary image based on the profile")
        self.ac_power.ac_power_off(self._ac_power_off_wait_time)
        time.sleep(self._ac_power_off_wait_time)  # wait for system to enter G3
        if self._common_content_lib.get_platform_family() == ProductFamilies.SPR:
            ifwi_btg_image = self._common_content_configuration.get_ifwi_image_path(boot_profile)
            if not os.path.isfile(ifwi_btg_image):
                raise content_exceptions.TestFail("IFWI file not found in location {}".format(ifwi_btg_image))
            self._flash_obj.flash_ifwi_image(ifwi_btg_image)
        else:
            modified_image = self.modify_binary_image(boot_profile)
            self._flash_obj.flash_binary(modified_image)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        after_flash_bios_version = self._flash_obj.get_bios_version()
        self._log.info("New BIOS revision after Flashing IFWI bin is : {} ".format(after_flash_bios_version))
        if self.before_flash_bios_version == after_flash_bios_version:
            self._log.warning("BIOS version did not change. If IFWI.bin is the same version as the original SUT image, "
                              "then there is no issue.")

    def verify_boot_profile(self, valid_values):
        """
        This function reads the contents of the BOOT_GUARD_SACM_INFO from read msr from OS and ITP command.
        verify boot guard profile.

        :param valid_values: boot guard profile msr values
        :return: return True if the value matches with boot guard profile values
        """
        self._log.info("Reading MSR value of Boot Guard")
        try:
            self._rdmsr_and_cpuid_obj.install_msr_tools()
            msr_val = self._rdmsr_and_cpuid_obj.execute_rdmsr_command(self.RDMSR_COMMAND.format(hex(
                self.BTG_SACM_INFO_MSR_ADDRESS)))
            if not msr_val:
                self._sdp.halt()
                msr_val = hex(self._sdp.msr_read(self.BTG_SACM_INFO_MSR_ADDRESS, squash=True))
                self._sdp.go()
            result = int(msr_val, 16) in valid_values
            if result:
                self._log.info("Reading MSR value of Boot Guard profile {} ".format(msr_val))
            else:
                self._log.error(
                    "BtG Profile Verification failed for MSR value = {} valid values =  {}".format(str(msr_val),
                                                                                                   valid_values))
        except Exception as e:
            raise e
        finally:
            self._sdp.go()
        return result

    def verify_profile_0(self):
        """
        Validate that SUT booted with the Boot Guard profile 0

        :return: True if the device booted with Boot Guard profile 0
        """
        valid_values = self.BTG_P0_VALID + self.CBNT_BTG_P0_VALID
        return self.verify_boot_profile(valid_values)

    def verify_profile_5(self):
        """
        Validate that SUT booted with the Boot Guard profile 5

        :return: True if the device booted with Boot Guard profile 5
        """
        valid_values = self.BTG_P5_VALID + self.CBNT_BTG_P5_VALID
        return self.verify_boot_profile(valid_values)

    def verify_profile_4(self):
        """
        Validate that SUT booted with the Boot Guard profile 4

        :return: True if the device booted with Boot Guard profile 4
        """
        valid_values = self.BTG_P4_VALID + self.CBNT_BTG_P4_VALID
        return self.verify_boot_profile(valid_values)

    def verify_profile_3(self):
        """
        Validate that SUT booted with the Boot Guard profile 3

        :return: True if the device booted with Boot Guard profile 3
        """
        valid_values = self.BTG_P3_VALID + self.CBNT_BTG_P3_VALID
        return self.verify_boot_profile(valid_values)

    def verify_profile_3_without_tpm(self):
        """
        Validate that SUT booted with the Boot Guard profile 3 without tpm

        :return: True if the device booted with Boot Guard profile 3 without tpm
        """
        valid_values = self.BTP_P3_WITHOUT_TPM_VALID + self.CBNT_BTG_P3_WITHOUT_TPM_VALID
        return self.verify_boot_profile(valid_values)

    def modify_binary_image(self, profile):
        """
        This function modifies the binary mage and returns path of modiifed binary image.

        :param profile: boot guard profile name
        :return: path of the modified binary ifwi image name.
        """
        profile_info = self.get_boot_profile(profile)
        return self._ifwi_prf_obj.create_ifwi_profile(self._common_content_lib, self._common_content_configuration,
                                                      profile_info)

    def get_boot_profile(self, profile):
        """
        This function checks the profile info and return required profile according to parameter passed.

        :param profile: boot guard profile name
        :return: return boot profile.
        """
        if profile == self.PROFILE0:
            self._log.debug("Boot profile info {} ".format(self._common_content_configuration.get_profile0_params()))
            return self._common_content_configuration.get_profile0_params()
        elif profile == self.PROFILE4:
            self._log.debug("Boot profile info {} ".format(self._common_content_configuration.get_profile4_params()))
            return self._common_content_configuration.get_profile4_params()
        elif profile == self.PROFILE5:
            self._log.debug("Boot profile info {} ".format(self._common_content_configuration.get_profile5_params()))
            return self._common_content_configuration.get_profile5_params()
        elif profile == self.PROFILE3:
            self._log.debug("Boot profile info {} ".format(self._common_content_configuration.get_profile3_params()))
            return self._common_content_configuration.get_profile3_params()
        else:
            raise content_exceptions.TestFail("Code not implemented for the mentioned profile {}".format(profile))

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup"""
        # reverting to current IFWI
        self.flash_binary_image(CbntConstants.CURRENT_VERSION)
        current_ifwi_version = self._flash_obj.get_bios_version()
        if current_ifwi_version != self.before_flash_bios_version:
            raise content_exceptions.TestFail("Original IWFI is not restored to continue the execution")
        self._log.info("IFWI original version is reverted successfully")
        super(BootGuardValidator, self).cleanup(return_status)
