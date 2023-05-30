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
import six
import argparse
import logging
from xml.etree import ElementTree
from abc import ABCMeta

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.silicon import CPUID

from src.security.tests.mktme.mktme_constants import WindowsConst
from src.lib import content_exceptions
from src.security.tests.common.common_windows import WindowsBase
from src.security.tests.mktme.mktme_common import MktmeBaseTest


@six.add_metaclass(ABCMeta)
class WindowsMktmeBase(WindowsBase, MktmeBaseTest):
    _BIOS_CONFIG_FILE_TME_ENABLE = r"security_tme_mktme_bios_enable.cfg"

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree)-> None:
        """Create an instance of WindowsMktmeBase

        :param test_log: Logger object
        :param arguments: arguments as Namespace
        :param cfg_opts: Configuration object.
        :return: None
        """

        super(WindowsMktmeBase, self).__init__(test_log, arguments, cfg_opts)

        self.tme_bios_enable_cfg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     self._BIOS_CONFIG_FILE_TME_ENABLE)

        self.product = self._common_content_lib.get_platform_family()
        self.mktme_properties = self.load_mktme_properties()
        self.mktme_consts = WindowsConst(self.product)

        # fill the values from content_configuration.xml\security\mktme section
        self.vm_user_name = self.mktme_properties[self.mktme_consts.XmlEntry.VM_GUEST_USER]
        self.vm_user_pwd = self.mktme_properties[self.mktme_consts.XmlEntry.VM_GUEST_USER_PWD]
        self.vm_reboot_timeout = self.mktme_properties[self.mktme_consts.XmlEntry.VM_BOOT_TIME]
        self.vm_os = self.mktme_properties[self.mktme_consts.XmlEntry.VM_OS]
        self.vm_tools_base_loc = self.mktme_properties[self.mktme_consts.XmlEntry.VM_TOOLS_BASE_LOC]
        self.vm_guest_image_path_to_import = self.mktme_properties[self.mktme_consts.XmlEntry.VM_GUEST_IMAGE_PATH_SUT]
        self.legacy_vm_image_path_to_import = self.mktme_properties[self.mktme_consts.XmlEntry.LEGACY_VM_IMAGE_PATH_SUT]
        self.vm_import_image_base_loc = self.mktme_properties[self.mktme_consts.XmlEntry.VM_GUEST_IMAGE_DIR]
        self.ac_reset = self.mktme_properties[self.mktme_consts.XmlEntry.AC_RESET]

    def prepare(self):
        super(WindowsMktmeBase, self).prepare()
        self.check_knobs(knob_file=self.tme_bios_enable_cfg_file, set_on_fail=True)
        self.verify_mktme()
        self._log.info("MKTME is enabled on platform, continuing to execution of test script.")

    def load_mktme_properties(self) -> dict:
        """Loads the MKTME properties (MKTME VF paths, TD guest properties) from content_configuration.xml into a dict.
        :return: Dict of properties from content_configuration.xml file for MKTME """

        properties = self._common_content_configuration.get_security_mktme_params(self.sut_os)
        for key in properties.keys():
            # convert properties from str to bool
            if properties[key].lower() == "true":
                properties[key] = True
            elif properties[key].lower() == "false":
                properties[key] = False
            elif properties[key].isnumeric():
                properties[key] = int(properties[key])
        return properties

    def verify_mktme(self) -> bool:
        """This function verifies the SUT's CPU SKU supports MKTME.

        :return: True if MKTME is supported, False otherwise."""

        self._log.info("Verifying MK-TME support")
        ret_val = [False, False, False]

        try:
            self.sdp.halt()
            # Checking the CPU ID registry value for EDX, EAX and ECX
            itp_command_status = self.sdp.cpuid(CPUID.EDX, self.CPUID_EDX, 0, squash=True) & (1 << 18) != 0
            ret_val[0] = itp_command_status
            self._log.debug("ITP command cpuid for edx with registry value %x status is %s", self.CPUID_EDX,
                            itp_command_status)
            itp_command_status = self.sdp.cpuid(CPUID.EAX, self.CPUID_EAX, 0, squash=True) == 1
            ret_val[1] = itp_command_status
            self._log.debug("ITP command cpuid for eax with registry value %x status is %s", self.CPUID_EAX,
                            itp_command_status)
            itp_command_status = self.sdp.cpuid(CPUID.ECX, self.CPUID_ECX, 0, squash=True) & (1 << 13) != 0
            ret_val[2] = itp_command_status
            self._log.debug("ITP command cpuid for ecx with registry value %x status is %s", self.CPUID_ECX,
                            itp_command_status)
        except Exception as e:
            raise e
        finally:
            self.sdp.go()
        return all(ret_val)

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
                self.xmlcli_read_knob_catcher(knob_file)
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
                self.xmlcli_set_knob_catcher(knob_file, restore_modify=True)
            else:
                try:
                    self.bios_util.set_bios_knob(knob_file)
                except RuntimeError as e:
                    raise content_exceptions.TestSetupError(
                        "BIOS knobs failed to set due to {}.  Please verify that the "
                        "SUT OS has been set up to use xmlcli. ".format(e))
        else:
            self.xmlcli_set_knob_catcher(knob_file, restore_modify=restore_modify)
        time.sleep(5.0)
        if reboot_on_knob_set is True:
            if self.ac_reset and self.sut_os != OperatingSystems.WINDOWS:
                self.perform_graceful_g3()
            else:
                self.reboot_sut()

    def xmlcli_read_knob_catcher(self, knob_file: str) -> None:
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

    def xmlcli_set_knob_catcher(self, knob_file: str, restore_modify: bool = None) -> None:
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

    def launch_vm(self, key: int, vm_name: str, legacy_vm: bool, enable_ethernet: bool) -> bool:
        """ Import and start a new VM from exported location

         :param key: a index to indicate the VM number
         :param vm_name: a new name from VM
         :param legacy_vm: legacy vm or special VM
         :param enable_ethernet: attach ethernet to VM
         :return: True if everything is working fine otherwise False
         :raise TestFail: if VM is not up and running"""

        if legacy_vm:
            src_path = self.legacy_vm_image_path_to_import
        else:
            src_path = self.vm_guest_image_path_to_import

        dest_path = os.path.join(self.vm_import_image_base_loc, vm_name)
        self.import_vm(key, vm_name, src_path, dest_path)
        self.start_vm(vm_name)
        if enable_ethernet is True:
            self._log.info("Setting the network connectivity to the VM")
            self.attach_ethernet_adapter_to_vm(vm_name)
            self._log.info("Restarting the VM with NW connectivity")
            self.start_vm(vm_name)
            self._log.info("Waiting {} seconds".format(str(self.vm_reboot_timeout)))
            time.sleep(self.vm_reboot_timeout)

        self._log.info("Verify VM is running. {}".format(vm_name))
        if self.verify_vm_state(vm_name, self.VMPowerStates.VM_STATE_RUNNING):
            self._log.info("{} is running".format(vm_name))
        else:
            self._log.info("{} is not running".format(vm_name))
            return False

        # Ping from SUT to the guest machine.
        if enable_ethernet is True:
            self._log.info("Pinging guest {}.".format(key))
            if not self.vm_is_alive(vm_name):
                raise content_exceptions.TestFail("VM {} could not be reached after booting.".format(key))
            self._log.info("Ping was successful; VM is up.")
        return True
