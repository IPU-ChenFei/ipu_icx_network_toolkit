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
import six
import os
import time
import ipccli

from xml.etree import ElementTree
from abc import ABCMeta

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.dtaf_content_constants import ProviderXmlConfigs
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import ItpXmlCli
from src.lib.install_collateral import InstallCollateral
from src.lib.bit_utils import GetBits
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_constants import TDX
from src.lib.bios_util import SerialBiosUtil


@six.add_metaclass(ABCMeta)
class TdxBaseTest(ContentBaseTestCase):
    """Base class extension for TDX which holds common arguments, functions."""

    def __init__(self, test_log, arguments, cfg_opts):
        """Create an instance of TdxBaseTest
        :param cfg_opts: Configuration Object of provider
        :type cfg_opts: str
        :param test_log: Log object
        :type arguments: Namespace
        :param arguments: None
        :type cfg_opts: Namespace
        :return: None
        """
        super(TdxBaseTest, self).__init__(test_log, arguments, cfg_opts)
        self.product = self._common_content_lib.get_platform_family()
        self.tdx_consts = TDX.get_subtype_cls("TDX" + self.product, False)

        self.tdx_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TDX_DISABLE)
        self.tdx_only_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                 self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TDX_ENABLE_ONLY)
        self.tdx_only_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TDX_DISABLE_ONLY)
        self.vmx_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_VMX_DISABLE)
        self.vmx_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_VMX_ENABLE)
        self.tme_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TME_DISABLE)
        self.tme_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TME_ENABLE)
        self.tmemt_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TMEMT_DISABLE)
        self.tmemt_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TMEMT_ENABLE)
        self.split_key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_SPLIT_KEYS)

        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, self._log)  # type: SiliconDebugProvider
        self.command_timeout = self._common_content_configuration.get_command_timeout()
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.itp_xml_cli_util = ItpXmlCli(self._log, cfg_opts)
        self.serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self.sut_os = self.os.os_type
        self.TDVM_OSes = self.tdx_consts.TDVMOS
        self.tdvms = []  # list of TDVMs and properties
        self.itp = ipccli.baseaccess()
        self.tdx_properties = self.load_tdx_properties()
        try:
            self.tdx_properties[self.tdx_consts.MEM_INTEGRITY_MODE] = arguments.INTEGRITY_MODE.upper()
        except AttributeError:  # no argument given for memory integrity
            self._log.debug("No memory integrity setting given, leaving knob alone.")
            self.tdx_properties[self.tdx_consts.MEM_INTEGRITY_MODE] = None
        self.bit_util = GetBits()
        cpu = self._common_content_lib.get_platform_family()
        pch = self._common_content_lib.get_pch_family()
        sv_cfg = ElementTree.fromstring(ProviderXmlConfigs.PYTHON_SV_XML_CONFIG.format(cpu, pch))
        self.sv = ProviderFactory.create(sv_cfg, self._log)  # type: SiliconRegProvider

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(TdxBaseTest, cls).add_arguments(parser)
        parser.add_argument("--integrity-mode", "--im", action="store", dest="INTEGRITY_MODE", default=None)

    def load_tdx_properties(self) -> dict:
        """Loads the TDX properties (TDVF paths, TD guest properties) from content_configuration.xml into a dict.
        :return: Dict of properties from content_configuration.xml file for TDX.
        """
        properties = self._common_content_configuration.get_security_tdx_params(self.sut_os)
        for key in properties.keys():
            # convert properties from str to bool
            if properties[key].lower() == "true":
                properties[key] = True
            elif properties[key].lower() == "false":
                properties[key] = False
            elif properties[key].isnumeric():
                properties[key] = int(properties[key])
        return properties

    def prepare(self):
        if self.tdx_properties[self.tdx_consts.AC_RESET]:
            self._log.warning("Using AC cycle to reboot SUT instead of graceful reboot from OS.")
        self.check_tdx_knobs(tdx_enabled=True, set_on_fail=True)
        if not self.validate_tdx_setup():
            # still couldn't enable TDX... check if MCHECK error MSR has data
            msr_error_code = self.msr_read(self.tdx_consts.RegisterConstants.MSR_MCHECK_ERROR)
            self._log.debug("MSR {} value: {}".format(hex(self.tdx_consts.RegisterConstants.MSR_MCHECK_ERROR),
                            msr_error_code))
            if msr_error_code == self.tdx_consts.MCHECKErrorMsrValues.LT_AGENT_NOT_SET or \
                    msr_error_code == self.tdx_consts.MCHECKErrorMsrValues.LT_PLAT_NOT_SET:
                self._log.error("MCHECK error code MSR value indicates LT straps are not set appropriately for the "
                                "platform and/or silicon mismatch.\n\tLT_AGENT (also known as TXT_AGENT) should be ON "
                                "for primary socket and OFF for all other sockets.\n\tLT_PLTEN should OFF for all "
                                "sockets.\n\tRefer to BKC for correct IFWI to use for QS/VIS silicon.\n\t"
                                "Please correct before re-running any scripts.")
            elif msr_error_code != 0x0:
                self._log.error("MCHECK error MSR is non-zero.  Please check error code against definitions on the "
                                "MCHECK error code SharePoint.")
            raise RuntimeError("TDX could not be enabled after setting knobs.  "
                               "Please confirm SUT settings support TDX.")
        self._log.info("TDX is enabled on platform, continuing to execution of test script.")

    def check_tdx_knobs(self, tdx_enabled: bool = True, set_on_fail: bool = False,
                        reboot_on_knob_set: bool = True) -> bool:
        """Check that TDX BIOS knobs are in the expected state.

        :param tdx_enabled: True if TDX is expected to be enabled, False otherwise.
        :param set_on_fail: If True, will set TDX knob to expected setting, if False, will not.
        :param reboot_on_knob_set: If True, will reboot SUT after setting knobs (if needed), if False, will not.
        :return: True if expected BIOS knobs are enabled/disabled as expected, False otherwise."""
        # get BIOS knob file
        files = []

        # figure out basic tdx file to use
        if tdx_enabled:
            knob_file = self.tdx_bios_enable
        else:
            knob_file = self.tdx_bios_disable

        files.append(knob_file)
        for setting in self.tdx_consts.CUSTOMIZABLE_KNOBS:
            try:
                mode = self.tdx_properties[setting]
            except (AttributeError, KeyError, IndexError):
                mode = None
                self._log.debug(f"Config file param {setting} not found in content_configuration.xml file.  Setting will"
                                f" be left default.")

            if mode is not None:
                knob_type = f"{setting}_{mode}"
                file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.tdx_consts.KNOBS[knob_type])
                files.append(file)
        knob_file = self.bios_file_builder(files)

        try:
            self.check_knobs(knob_file, set_on_fail, reboot_on_knob_set=reboot_on_knob_set)
            os.remove(knob_file)
        except RuntimeError:
            return False
        return True

    def check_vmx_knobs(self, vmx_enabled: bool = True, set_on_fail: bool = False,
                        reboot_on_knob_set: bool = True) -> bool:
        """Check that VMX BIOS knobs are in the expected state.
        :param vmx_enabled: True if TDX is expected to be enabled, False otherwise.
        :param set_on_fail: If True, will set VMX knob to expected setting, if False, will not.
        :param reboot_on_knob_set: after setting BIOS knobs, reboot the SUT.
        :return: True if expected BIOS knobs are enabled/disabled as expected, False otherwise.
        """

        if vmx_enabled:
            knob_file = self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_VMX_ENABLE
        else:
            knob_file = self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_VMX_DISABLE

        knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), knob_file)

        return self.check_knobs(knob_file, set_on_fail, reboot_on_knob_set=reboot_on_knob_set)

    def check_knobs(self, knob_file: str = None, set_on_fail: bool = False, reboot_on_knob_set: bool = True) -> bool:
        """Check the knob settings and attempt to set them if set_on_fail is set.
        :param knob_file: xmlcli file to compare BIOS settings against.
        :param set_on_fail: if knobs are not set, set them.  This will not reboot the SUT.
        :param reboot_on_knob_set: after setting BIOS knobs, reboot the SUT.
        :return:  True if knobs are set, raise RuntimeError otherwise.
        :raise ValueError: no BIOS knob file provided.
        :raise RuntimeError: BIOS knobs are not set as in the provided BIOS knob config file.
        """
        if knob_file is None:
            raise ValueError("No knob file was provided for checking!")

        try:
            if self.os.is_alive():
                self.bios_util.verify_bios_knob(knob_file)
            else:
                self._xmlcli_read_knob_catcher(knob_file)
        except RuntimeError:  # bios knob is not set
            if set_on_fail:  # should it be set?
                try:
                    self._log.warning("Knob was not set.  Setting knob file.  This will require a warm reset.")
                    self.set_knobs(knob_file, reboot_on_knob_set=reboot_on_knob_set)
                    return True
                except RuntimeError:
                    raise content_exceptions.TestSetupError("BIOS knobs failed to set.  Please check XmlCli configs.")
            else:
                raise RuntimeError("BIOS knob was not set!")
        else:
            return True

    def set_knobs(self, knob_file: str = None, restore_modify: bool = False, reboot_on_knob_set: bool = True) -> None:
        """Set the knob settings and attempt to set them if set_on_fail is set.
        :param knob_file: xmlcli file to compare BIOS settings against.
        :param restore_modify: restore BIOS knobs to default and then apply changes.
        :param reboot_on_knob_set: after setting BIOS knobs, reboot the SUT.
        :raise content_exceptions.TestSetUpError: XmlCli fails to install - likely due to missing OS installation.
        """
        if self.os.is_alive():
            if restore_modify:
                self._log.debug("Setting BIOS knobs with knob file {}".format(knob_file))
                self._xmlcli_set_knob_catcher(knob_file, restore_modify=True)
            else:
                try:
                    self.bios_util.set_bios_knob(knob_file)
                except RuntimeError as e:
                    raise content_exceptions.TestSetupError(
                        "BIOS knobs failed to set due to {}.  Please verify that the "
                        "SUT OS has been set up to use xmlcli.  These instructions are "
                        "in Phoenix TC 22012170927".format(e))
        else:
            self._xmlcli_set_knob_catcher(knob_file, restore_modify=restore_modify)
        time.sleep(5.0)
        if reboot_on_knob_set is True:
            if self.tdx_properties[self.tdx_consts.AC_RESET] and self.sut_os != OperatingSystems.WINDOWS:
                self.perform_graceful_g3()
            else:
                self.reboot_sut()

    @staticmethod
    def bios_file_builder(files: list) -> str:
        """Combines multiple BIOS knob config files into one file.
        :param files: list of BIOS knob files to be combined.
        :return: path to BIOS knob file with all knobs combined.
        """
        temp_file = "knob_file.cfg"
        if os.path.exists(temp_file):
            os.remove(temp_file)
        for file in files:
            with open(file) as in_file:
                with open(temp_file, "a") as out_file:
                    for line in in_file:
                        out_file.write(line)
        return temp_file

    def _xmlcli_set_knob_catcher(self, knob_file: str, restore_modify: bool = None) -> None:
        """Catch IPC_Errors, forcereconfig, and try again 1 time.  IPC seems to not be able to halt without a
        forcereconfig occasionally.
        :param knob_file:  name of config file to use to set BIOS knobs.
        :param restore_modify: if True, will set all BIOS knobs to default settings and then applies BIOS knob changes
        on top.
        """
        try:
            self.itp_xml_cli_util.set_bios_knobs(knob_file, restore_modify)
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.itp.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            self.itp_xml_cli_util.set_bios_knobs(knob_file, restore_modify)

    def _xmlcli_read_knob_catcher(self, knob_file: str) -> None:
        """Catch IPC_Errors, forcereconfig, and try again 1 time.  IPC seems to not be able to halt without a
        forcereconfig occasionally.
        :param knob_file:  name of config file to use to set BIOS knobs.
        """
        try:
            self.itp_xml_cli_util.verify_bios_knobs(knob_file)
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.itp.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            self.itp_xml_cli_util.verify_bios_knobs(knob_file)

    def check_tme_knobs(self, tme_enabled: bool = True, set_on_fail: bool = False,
                        reboot_on_knob_set: bool = True) -> bool:
        """Check that TME BIOS knobs are in the expected state.
        :param tme_enabled: True if TME is expected to be enabled, False otherwise.
        :param set_on_fail: If True, will set TME knob to expected setting, if False, will not.
        :param reboot_on_knob_set: after setting BIOS knobs, reboot the SUT.
        :return: True if expected BIOS knobs are enabled/disabled as expected, False otherwise.
        """
        if tme_enabled:
            knob_file = self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TME_ENABLE
        else:
            knob_file = self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TME_DISABLE

        knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), knob_file)
        return self.check_knobs(knob_file, set_on_fail, reboot_on_knob_set=reboot_on_knob_set)

    def check_tmemt_knobs(self, tmemt_enabled: bool = True, set_on_fail: bool = False,
                          reboot_on_knob_set: bool = True) -> bool:
        """Check that TME-MT BIOS knobs are in the expected state.
        :param tmemt_enabled: True if TME-MT is expected to be enabled, False otherwise.
        :param set_on_fail: If True, will set TME-MT knob to expected setting, if False, will not.
        :param reboot_on_knob_set: after setting BIOS knobs, reboot the SUT.
        :return: True if expected BIOS knobs are enabled/disabled as expected, False otherwise.
        """
        if tmemt_enabled:
            knob_file = self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TMEMT_ENABLE
        else:
            knob_file = self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TMEMT_DISABLE

        knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), knob_file)
        return self.check_knobs(knob_file, set_on_fail=set_on_fail, reboot_on_knob_set=reboot_on_knob_set)

    def validate_tdx_setup(self, set_on_fail: bool = False) -> bool:
        """Verify if TDX is enabled and all dependencies are satisfied.
        :param set_on_fail:  If BIOS knobs are not currently set as defined in the config file, set them.
        :return: True if TDX is successfully enabled, False otherwise.
        """
        key_check = True
        key_id_check = False

        self._log.debug("Checking TDX BIOS knobs are enabled.")
        tdx_enabled = self.check_tdx_knobs(set_on_fail=set_on_fail)
        self._log.debug("Knob check: {}".format("PASSED" if tdx_enabled else "FAILED"))

        # verify keys
        # check key total
        self._log.debug("Checking TDX key allocation and max keys available.")
        max_keys = self.get_keys()
        tmemt_keys = self.get_keys("tme-mt")
        tdx_keys = self.get_keys("tdx")
        if tmemt_keys + tdx_keys != max_keys:
            key_check = False
            self._log.error("Keys do not add up.  TDX keys: {} TME-MT keys: {} Max keys: {}".format(
                tdx_keys, tmemt_keys, max_keys))
        else:
            self._log.debug("Keys check PASSED.  TDX keys: {} TME-MT keys: {} Max keys: {}".format(
                tdx_keys, tmemt_keys, max_keys))

        # if TDX is enabled, TDX keys > 0
        if tdx_keys == 0x0 and tdx_enabled:
            self._log.error("No keys are assigned to TDX while TDX is enabled.")
            key_check = False

        # check SEAM MSRs
        seamrr_mask = self.msr_read(self.tdx_consts.RegisterConstants.MSR_SEAMRR_MASK)
        seamrr_base = self.msr_read(self.tdx_consts.RegisterConstants.MSR_SEAMRR_BASE)

        seam_valid = self.bit_util.is_bit_set(seamrr_mask, self.tdx_consts.SEAMRRMaskBits.SEAMRR_ACTIVE)
        lock_check = self.bit_util.is_bit_set(seamrr_mask, self.tdx_consts.SEAMRRMaskBits.SEAMRR_LOCKED)
        seam_configured = self.bit_util.is_bit_set(seamrr_base, self.tdx_consts.SEAMRRBASEBits.CONFIGURED_BIT)

        self._log.debug("Seam check: SEAMRR valid: {}, "
                        "SEAMRR locked: {}, SEAMRR configured: {}".format(seam_valid, lock_check, seam_configured))

        # check keyIDs
        tme_activate_msr = self.msr_read(self.tdx_consts.RegisterConstants.MSR_TME_ACTIVATE)
        if tme_activate_msr != 0x0 and tdx_enabled:
            key_id_check = True
            self._log.debug("Assigned key IDs are non-zero. Value: {}".format(hex(tme_activate_msr)))
        elif tme_activate_msr == 0x0 and tdx_enabled:
            self._log.debug("Assigned key IDs are zero with TDX enabled. Value: "
                            "{}".format(hex(tme_activate_msr)))
        else:
            self._log.debug("Assigned key IDs are zero values with TDX disabled. Value: "
                            "{}".format(hex(tme_activate_msr)))
            key_id_check = True

        # check memory integrity mode
        self._log.debug(f"Memory integrity is in {self.check_mem_integrity()} mode.")

        self._log.debug("TDX overall check: {}".format("PASSED" if seam_valid and lock_check and key_check and
                                                       seam_configured and tdx_enabled and key_id_check else "FAILED"))

        return seam_valid and lock_check and key_check and seam_configured and tdx_enabled and key_id_check

    def split_keys(self, num_tdx_key: int = None) -> None:
        """Process to split keys between TME-MT and TDX.
        :param num_tdx_key: Number of keys to split and assign to TDX.
        """
        temp_file = "split_knob_file.cfg"
        if num_tdx_key is None:
            raise ValueError("Missing number of TDX keys!")
        try:
            bios_idx = self.tdx_consts.KEY_IDX[num_tdx_key]
        except KeyError:
            raise ValueError("Invalid number of keys provided!  Key number provided: {}.  Valid key "
                             "amounts are {}".format(num_tdx_key, self.tdx_consts.KEY_IDX.keys()))

        with open(self.split_key_file) as in_file:
            with open(temp_file, "w") as out_file:
                for line in in_file:
                    if "{}" in line:
                        line = line.format(bios_idx)
                    out_file.write(line)
        self.set_knobs(temp_file)
        os.remove(temp_file)

    def get_keys(self, key_type: str = None) -> int:
        """Get the number of keys of a specific type from MSRs.
        :param key_type: Types are TME-MT or TDX, if no type is provided, max keys available on system will be returned.
        :return: number of keys for type supplied.
        """
        if key_type is None:
            start = self.tdx_consts.MSRTMECapabilitiesBits.MAX_KEYS_START
            end = self.tdx_consts.MSRTMECapabilitiesBits.MAX_KEYS_END
        elif key_type.lower() == 'tdx':
            start = self.tdx_consts.MSRTMEKeyPartitioning.MSR_TDX_KEYS_START
            end = self.tdx_consts.MSRTMEKeyPartitioning.MSR_TDX_KEYS_END
        elif key_type.lower() == 'tme-mt':
            start = self.tdx_consts.MSRTMEKeyPartitioning.MSR_TME_KEYS_START
            end = self.tdx_consts.MSRTMEKeyPartitioning.MSR_TME_KEYS_END
        else:
            raise ValueError("Key type {} provided is not recognized.".format(key_type))
        if key_type is None:
            register = self.tdx_consts.RegisterConstants.MSR_TME_CAPABILITIES
        else:
            register = self.tdx_consts.RegisterConstants.MSR_TME_KEYID_PARTITIONING

        register_value = self.msr_read(register)
        value = self.bit_util.get_bits(register_value, start, end)

        return value

    def boot_to_tdx_knob(self) -> None:
        """Boots system into BIOS menu and navigates to EDKII -> Processor Configuration -> Socket Configuration.
        :raise content_exception.TestError: system fails to boot to BIOS menu.
        """
        self._log.info("Attempting to boot to BIOS menu and navigate to TDX BIOS knob.")
        try:
            serial_path = self.tdx_consts.PROC_BIOS_PATH
        except (AttributeError, KeyError):
            raise content_exceptions.TestError("No BIOS serial path provided for product {}".format(self.platform))

        success, msg = self.serial_bios_util.navigate_bios_menu()
        if not success:
            raise content_exceptions.TestFail(msg)
        self.serial_bios_util.select_enter_knob(serial_path)

    def select_serial_bios_knob(self, knob, knob_type):
        """Setting BIOS knob with serial and include type of knob.
        :param knob_type: Type of knob to select (directory, pop up menu, etc).
        :param knob: knob label in BIOS menu.
        """
        self.serial_bios_util.select_knob(knob, knob_type)

    def read_bios_menu(self):
        """Read BIOS menu over serial connection."""
        return self.serial_bios_util.get_page_information()

    def reboot_sut(self, wait_for_os: bool = True) -> None:
        """Tries to reboot SUT from OS, then reverts to AC cycle if OS reset fails.
        :param wait_for_os: wait for OS to boot up before exiting function.
        """
        self._log.info("Rebooting SUT from OS.")
        if self.tdx_properties[self.tdx_consts.AC_RESET] and wait_for_os:
            self._log.warning("Content configuration file is set to AC cycle instead of do graceful warm reset "
                              "from OS. If this should be changed, check the TDX block in the "
                              "content_configuration.xml file.")
            self.perform_graceful_g3()
        if self.tdx_properties[self.tdx_consts.AC_RESET] and not wait_for_os:
            self._log.warning("Content configuration file is set to AC cycle instead of do graceful warm reset "
                              "from OS. If this should be changed, check the TDX block in the "
                              "content_configuration.xml file.")
            self.ac_power.ac_power_off()
            time.sleep(20.0)
            self.ac_power.ac_power_on()
        else:
            try:
                self.os.reboot(self.reboot_timeout)
            except EOFError as e:  # paramiko gets into error state and throws EOF error
                self._log.warning("Caught EOF error from paramiko, AC cycling SUT to reboot. "
                                  "Exception data: {}".format(e))
                self.perform_graceful_g3()

    def execute_os_cmd(self, cmd: str = None, timeout: float = None) -> str:
        """Wrapper for executing OS commands because I'm tired of writing a timeout parameter each time...
        :param cmd: Command to be executed.
        :param timeout: provide time out in seconds for command to finish; default is the command time out defined in
        content_configuration.xml.
        :return: output from command.
        """
        if timeout is None:
            timeout = self.command_timeout
        results = self.os.execute(cmd, timeout)
        self._log.debug(f"Results from command {cmd}: stdout: {results.stdout}; stderr {results.stderr}")
        return results.stdout.strip()

    def msr_read(self, register: int = None) -> int:
        """Read MSR through ITP.  Can cause OS instability, recommend overriding this at OS level with OS tools.
        :param register: address of MSR to be read
        :return: Value of MSR.
        """
        try:
            self._log.debug("SUT is not booted to OS.  Attempting to read MSR {} through ITP.".format(register))
            self.sdp.halt()
            result = self.sdp.msr_read(register)[0]
            self._log.debug("MSR {} == 0x{}".format(hex(register), hex(result)))
            self.sdp.go()
        except Exception as e:
            self._log.debug("Caught exception when reading MSR {}.  Force reconfiguring ITP and attempting to "
                            "re-read.  Exception data: {}".format(register, e))
            self.itp.forcereconfig()
            self.sdp.halt()
            result = self.sdp.msr_read(register)[0]
            self.sdp.go()
            self._log.debug("MSR {} == 0x{}".format(hex(register), hex(result)))
        return result

    def read_prmrr_base_msrs(self, nonzero_results: bool = True) -> dict:
        """Reads all PRMRR base MSRs and returns a dictionary of values.
        :param nonzero_results: If True, only return nonzero results.
        :return: dict of msr register and register value.
        """
        prmrr_base_values = {}
        for register in self.tdx_consts.PRMRR_BASE_MSRS:
            value = self.msr_read(register)
            if nonzero_results:
                if value != 0:
                    prmrr_base_values[register] = value
        return prmrr_base_values

    def tme_bypass_check(self) -> bool:
        """Check if TME Bypass is enabled.
        :return: True if TME Bypass is enabled, False if TME Bypass is disabled.
        """
        tme_act_value = self.msr_read(self.tdx_consts.RegisterConstants.MSR_TME_ACTIVATE)
        tme_cap_value = self.msr_read(self.tdx_consts.RegisterConstants.MSR_TME_CAPABILITIES)
        hardware_supported = tme_act_value >> self.tdx_consts.MSRTMEActivateBits.HARDWARE_ENCRYPTION_ENABLE & 1
        tme_encryption_bypass_enabled = tme_act_value >> \
                                        self.tdx_consts.MSRTMEActivateBits.TME_ENCRYPTION_BYPASS_ENABLE & 1
        tme_bypass_supported = tme_cap_value >> \
                               self.tdx_consts.MSRTMECapabilitiesBits.TME_ENCRYPTION_BYPASS_SUPPORTED & 1

        if tme_bypass_supported != 1 or hardware_supported != 1:
            raise content_exceptions.TestError("TME bypass is not supported.  Both of these values should be 1: "
                                               "TME Encryption Bypass supported: {}  Hardware encryption "
                                               "supported: {}".format(tme_bypass_supported, hardware_supported))
        if tme_encryption_bypass_enabled != 1:
            self._log.debug("TME bypass is not enabled.")
            return False
        self._log.debug("TME bypass is enabled.")
        return True

    def uma_check(self) -> bool:
        """Check if UMA is enabled.
        :return: True if UMA is enabled, False if UMA is disabled."""
        uma_enabled = True
        scope, path = self.tdx_consts.SncRegisterValues.REGISTER_PATH.split(".", 1)
        # TODO: remove this manual override when dtaf_core SiliconRegProvider classes are fixed...
        scope = "uncore"
        for key in self.tdx_consts.SncRegisterValues.UMA_EN_FIELDS.keys():
            result = self.sv.get_field_value(scope=scope, reg_path=path, field=key)
            if result != self.tdx_consts.SncRegisterValues.UMA_EN_FIELDS[key]:
                uma_enabled = False
                self._log.error(f"UMA values not as expected.  Actual: {result}, "
                                f"Expected: {self.tdx_consts.SncRegisterValues.UMA_EN_FIELDS[key]}")

        return uma_enabled

    def get_snc_setting(self) -> int:
        """Check if SNC2 or 4 is enabled or if SNC is disabled.
        :return: 2 if SNC2 is enabled 4 if SNC4 is enabled, 1 if SNC is disabled."""
        scope, path = self.tdx_consts.SncRegisterValues.REGISTER_PATH.split(".", 1)
        # TODO: remove this manual override when dtaf_core SiliconRegProvider classes are fixed...
        scope = "uncore"
        snc_clusters = self.sv.get_field_value(scope=scope, reg_path=path,
                                               field=self.tdx_consts.SncRegisterValues.NUM_SNC_CLUSTERS_FIELD)
        if snc_clusters == self.tdx_consts.SncRegisterValues.SNC_TWO_FIELDS[self.tdx_consts.SncRegisterValues.NUM_SNC_CLUSTERS_FIELD]:
            self._log.debug("Appears SNC2 is enabled, checking remaining fields.")
            values_to_check = self.tdx_consts.SncRegisterValues.SNC_TWO_FIELDS
        elif snc_clusters == self.tdx_consts.SncRegisterValues.SNC_FOUR_FIELDS[self.tdx_consts.SncRegisterValues.NUM_SNC_CLUSTERS_FIELD]:
            self._log.debug("Appears SNC4 is enabled, checking remaining fields.")
            values_to_check = self.tdx_consts.SncRegisterValues.SNC_FOUR_FIELDS
        else:
            # no clusters found, must be UMA
            self._log.debug("Appears SNC is disabled.  Checking if UMA is enabled.")
            if self.uma_check():
                self._log.debug("UMA is enabled. SNC ")
                return 1
            else:
                raise content_exceptions.TestError("SNC2, SNC4, and UMA are not enabled... something strange "
                                                   "has happened!")

        # cluster found, check if SNC2 or SNC4
        for key in values_to_check.keys():
            self._log.debug(f"Checking SNC field {key}")
            result = self.sv.get_field_value(scope=scope, reg_path=path, field=key)
            if result != values_to_check[key]:
                raise content_exceptions.TestError(f"SNC values not as expected.  Actual: {result} Expected: "
                                                   f"{self.tdx_consts.SncRegisterValues.UMA_EN_FIELDS[key]}")

        return snc_clusters

    def check_mem_integrity(self) -> str:
        """Check if memory integrity is set (TDX LI vs TDX CI).
        :return: CI if in cryptographic integrity mode (memory integrity is enabled), LI if in logical integrity mode
        (memory integrity is not enabled)"""
        expected_mode = self.tdx_properties[self.tdx_consts.MEM_INTEGRITY_MODE]
        if expected_mode is None:
            self._log.warning("No expected memory integrity mode defined in arguments, so memory integrity mode will "
                              "only be reported and not enforced.")
        tme_cap_value = self.msr_read(self.tdx_consts.RegisterConstants.MSR_TME_CAPABILITIES)
        tme_act_value = self.msr_read(self.tdx_consts.RegisterConstants.MSR_TME_ACTIVATE)
        integrity_supported = self.bit_util.is_bit_set(tme_cap_value,
                                                       self.tdx_consts.MSRTMECapabilitiesBits.PLAT_INTEGRITY_SUPPORTED)
        integrity_enabled = self.bit_util.is_bit_set(tme_act_value,
                                                     self.tdx_consts.MSRTMEActivateBits.MEM_INTEGRITY_ENABLED)

        if integrity_enabled and integrity_supported:
            mode = "CI"
        elif not integrity_enabled and integrity_supported:
            mode = "LI"
        else:  # if integrity is not supported, TDX cannot be enabled
            raise content_exceptions.TestError("Integrity is not enabled on this platform!  Please check CPU SKU.")

        if expected_mode is not None:
            if expected_mode != mode:
                raise content_exceptions.TestError(f"Expected {expected_mode} memory integrity mode but got {mode}!")

        return mode

    def cleanup(self, return_status: bool) -> None:
        """Test Cleanup"""
        self._log.debug("Starting TdxBaseTest cleanup.")
        try:
            if self.phy:
                current_post_code = self.phy.read_postcode()
                self._log.info(f"POST code when starting clean up: {current_post_code}")
        except NotImplementedError:
            self._log.info("Post code read failed as phy control doesn't support it")

        self._log.debug("Exiting TdxBaseTest cleanup, starting super set clean up.")
        if self.os.is_alive():
            self._log.debug("Clearing BIOS knobs.")
            self.bios_util.load_bios_defaults()
            self.perform_graceful_g3()
        else:
            if self.phy:
                self._log.debug("Clearing CMOS.")
                self.phy.set_clear_cmos()
                self.perform_graceful_g3()
        super(TdxBaseTest, self).cleanup(return_status)
