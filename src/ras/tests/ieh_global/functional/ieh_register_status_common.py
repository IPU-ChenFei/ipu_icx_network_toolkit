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

import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.os_log_verification import OsLogVerifyCommon


class IehCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class for ieh global error Test Cases.
    """

    IEH_RCEC_SOCKET_REGISTER_DICT = {ProductFamilies.SPR: "iax{}.did"}

    IEH_ERROR_REGISTER_PARENT_DICT = {ProductFamilies.SPR : "ieh{}"}

    IAX_ERROR_REGISTER_PARENT_DICT = {ProductFamilies.SPR : "iax{}"}

    IEH_REGISTERS = ['ieh3.rootctl', 'ieh3.rooterrcmd', 'ieh_global.gsysevtctl', 'ieh3.pcicmd.intxd',
                         'ieh3.pcicmd.bme', 'ieh3.msiaddr', 'ieh3.msidata', 'ieh3.msictl.mseie']

    IEH_REGISTER_VALUES = [7, 7, 7, 1, 1, 0xfee00000, 0x51, 1]

    IAX_REGISTERS = ['iax1.pcicmd.see', 'iax1.pcicmd.pere', 'iax1.devctl.urre', 'iax1.devctl.fere',
                     'iax1.devctl.nere', 'iax1.devctl.cere', 'iax1.erruncmsk', 'iax1.errcormsk',
                     'iax1.erruncsev.ur', 'iax1.pcicmd.mse', 'iax1.pcicmd.bme']

    IAX_REGISTER_VALUES = [1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0]

    SERIAL_LOGS_IEH_FATAL_ERROR_STRINGS = ["IehRciepDevicesErrorHandler - Socket 0, Bus 6F, device 0, fuction 4\n",
                         "IEH FATAL ERROR \n"]

    OS_LOGS_IEH_FATAL_ERROR_STRINGS = [r"event severity: fatal", r"Error 0, type: fatal", r"section_type: PCIe error",
                                 r"port_type: 10, root complex event collector", r"Hardware Error"]

    MACHINE_TOLERANT_PATH = "cat /sys/devices/system/machinecheck/machinecheck*/tolerant"

    SMM_BREAK_DELAY_SEC = 5
    WAIT_TIME_AFTER_RESUME_SEC = 60
    ADDR_MASK = 0x00000004
    MM_OFFSET = 0
    BAR = 0
    CFG_VID_ADDR = 0x0
    CFG_CMD_ADDR = 0x4
    CFG_BAR_ADDR = 0x10
    SIZE_IN_BYTE = 4

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        if bios_config_file:
            bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), bios_config_file)
        super(IehCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path=bios_config_file)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # get os object

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # get bios object

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        cur_path = os.path.dirname(os.path.realpath(__file__))  # get current path.
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # get the CScript object.
        self.sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        self.pci = self._cscripts.get_cscripts_utils().get_pci_obj()

        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        # reboot time out in second

        self._cpu = self._common_content_lib.get_platform_family()

        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._check_os_log = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                               self._common_content_lib)

        import common.baseaccess as _baseaccess
        self._mem = _baseaccess.getglobalbase()

        self.bdf_value = self._common_content_configuration.get_iax_bdf()
        self.IAX_BUS = int(self.bdf_value[:2], 16)
        self.IAX_DEV = int(self.bdf_value[4:5], 16)
        self.IAX_FUN = int(self.bdf_value[6:7], 16)

    def get_ieh_global_time_register_value(self):
        """
        This Function is for read and return ieh global time register value.

        :return: Ieh global time register value
        """
        try:
            ieh_global_time_register_value = self._cscripts.get_by_path(self._cscripts.UNCORE, "ieh_global.gtime")
            return ieh_global_time_register_value
        except Exception as ex:
            self._log.error("Failed to Execute the Cscript command {}".format(ex))
            raise ex

    def check_ieh_global_time_register_value_status(self):
        """
        This function is to validate the ieh global time register value is incrementing or not.

        :return: if ieh global register value is increment correctly return true else false.
        """
        ret_val = False
        try:
            _ieh_global_time_reg_val_list = []
            for timer_index in range(0, 3):
                global_time_reg_val = self.get_ieh_global_time_register_value()
                self._log.info("Ieh global Timer reading for {} time: is {}".format(timer_index+1, global_time_reg_val))
                _ieh_global_time_reg_val_list.append(global_time_reg_val)

            if _ieh_global_time_reg_val_list[0] < _ieh_global_time_reg_val_list[1] < _ieh_global_time_reg_val_list[2]:
                self._log.info("Ieh Global Time register value reading is valid")
                ret_val = True
            else:
                self._log.error("Ieh Global Time register value reading is not valid")

        except Exception as ex:
            self._log.error("Failed to Execute the Cscript command {}".format(ex))
            raise ex

        return ret_val

    def determine_iax_bdf_and_device_id(self):
        """
        This function is to determine and print the bdf of iaxdevice and it's device id.

        :return: None
        """

        # Determine iax1 did (device ID)
        s0_iax1_did = self.read_register_via_cscripts(0, self.IEH_RCEC_SOCKET_REGISTER_DICT[self.
                                                      _cscripts.silicon_cpu_family].format(1))
        self._log.info("Device ID of Socket0.iax1 : {}".format(s0_iax1_did))

        # Determine iax1 BDF
        iax1_bdf = (self.os.execute("lspci -vv | grep {}".format((hex(s0_iax1_did))[2:]),
                                     self._common_content_configuration.get_command_timeout()).stdout).split()[7]
        self._log.info("BDF of Socket0.iax1 : {}".format(iax1_bdf))
        if not iax1_bdf == self.bdf_value:
            self._log.info("BDF mismatch: BDF extracted from SUT did not match with the one from Configuration")
            raise ex

    def update_linux_tolerants(self):
        """
        This function is to copy the update_linux_tolerant.py to SUT from collateral, and execute it.
        This changes all the tolerant files value from 1 to 3 across all machine checks in order to
        stop the system from rebooting.

        :return: None.
        """
        # Update Linux Tolerant = 3
        self._install_collateral.copy_and_execute_tolerant_script()
        updated_value = set(self.os.execute(self.MACHINE_TOLERANT_PATH, self._common_content_configuration.
                                            get_command_timeout()).stdout.split('\n'))
        if updated_value.intersection({'3'}) == {'3'} and len(updated_value) == 2:
            self._log.info("Linux Tolerant value correctly update for all Machinechecks with value : {}".
                           format(updated_value))
        else:
            self._log.info("Linux Tolerant value did not correctly update for all Machinechecks with values : {}".
                           format(updated_value))
            raise ex

    def adjust_iax_and_ieh_register_values(self):
        """
        This function is to Assign new values to IEH and IAX registers.

        :return: None.
        """
        # Adjust register to allow UR fatal error flow
        self._log.info("Adjusting register to allow UR fatal error flow")
        self._log.info("Adjusting IEH registers - ")
        self.write_value_list_to_register_list_via_cscripts(0, self.IEH_REGISTERS, self.IEH_REGISTER_VALUES)
        self._log.info("Adjusting IAX registers - ")
        self.write_value_list_to_register_list_via_cscripts(0, self.IAX_REGISTERS, self.IAX_REGISTER_VALUES)

    def create_unsupported_req(self):
        """
        This function is to create UR.

        :return: cmd: to enable mmio access.
        """
        # Creating UR
        self.sdp_obj.halt()
        self.sdp_obj.itp.breaks.smmentry = 1
        did = self.pci.config(self.IAX_BUS, self.IAX_DEV, self.IAX_FUN, self.CFG_VID_ADDR)
        cmd = self.pci.config(self.IAX_BUS, self.IAX_DEV, self.IAX_FUN, self.CFG_CMD_ADDR)
        bar_address = self.pci.config(self.IAX_BUS, self.IAX_DEV, self.IAX_FUN, (self.CFG_BAR_ADDR + (self.BAR * 4)))
        self._log.info("bar_address - %s" % hex(bar_address))

        if bar_address & self.ADDR_MASK:
            self._log.info("bar_address & 004 is true - updating bar_address.")
            new_bar_address = self.pci.config(self.IAX_BUS, self.IAX_DEV, self.IAX_FUN, ((self.CFG_BAR_ADDR + (self.BAR * 4)) + 4))
            bar_address = bar_address + (new_bar_address << 32)

        self._log.info("new_bar_address = %s" % hex(bar_address))
        self._log.info("cmd: %s" % hex(cmd))
        self._log.info("did: %s" % hex(did))

        # Checking driver availability
        test = cmd & self.ADDR_MASK
        self._log.info("cmd & 0x00000004 - %s" % test)
        if test == 0:
            self._log.info("Warning: Mem access disable, driver not available in OS")

        # Cause UR with read of MMIO space (with MMIO disabled)
        mmio_data = self._mem.mem(((bar_address & 0xFFFFFFFFFFFFFFF0) + self.MM_OFFSET))
        self._log.info("MMIO data: %s" % hex(mmio_data))

        return cmd

    def resume_cores_after_ur_verification(self, cmd):
        """
        This function is to resume the core after UR verification.

        :param: cmd: to enable mmio access
        :return: None.
        """
        # Enable MMIO access
        self.pci.config(self.IAX_BUS, self.IAX_DEV, self.IAX_FUN, self.CFG_CMD_ADDR, self.SIZE_IN_BYTE, cmd)

        # Resuming Cores
        self.sdp_obj.go()
        time.sleep(self.SMM_BREAK_DELAY_SEC)
        wait_time_for_smm_break_sec = 60
        while 0 < wait_time_for_smm_break_sec:
            if not self.sdp_obj.itp.isrunning():
                break
            time.sleep(self.SMM_BREAK_DELAY_SEC)
            wait_time_for_smm_break_sec -= self.SMM_BREAK_DELAY_SEC
        if self.sdp_obj.itp.isrunning():
            self._log.info("SMM break didn't happen even after 60 seconds!!")

        # setting SMM break off and resuming
        self.sdp_obj.itp.breaks.smmentry = 0
        self.sdp_obj.go()

        # 60 sec wait time
        time.sleep(self.WAIT_TIME_AFTER_RESUME_SEC)

    def check_ieh_RCEC_pcie_fatal_error(self):
        """
        This function is to validate the ieh RCEC pcie fatal error occuring or not after resuming.

        :return: if ieh RCEC pcie fatal error occurred correctly return true else false.
        """
        self._log.info("Looking for Errors in - {}".format(self.serial_log_path))
        data = open(self.serial_log_path).readlines()
        flag = 0
        for line in data:
            if line in self.SERIAL_LOGS_IEH_FATAL_ERROR_STRINGS:
                flag += 1
                self._log.info("Error match {} - {}".format(flag, line))
        self.os.wait_for_os(self.reboot_timeout)
        verified_dmesg_contains_os_log_errors = \
            self._check_os_log.verify_os_log_error_messages(__file__, self._check_os_log.DUT_DMESG_FILE_NAME,
                                                            self.OS_LOGS_IEH_FATAL_ERROR_STRINGS)
        self._log.info("dmesg(os logs) error status - %s" % verified_dmesg_contains_os_log_errors)
        return verified_dmesg_contains_os_log_errors

    def print_ieh_rcec_error_regs(self):
        """Method to print register values for Error check."""

        registers = [self.IEH_ERROR_REGISTER_PARENT_DICT[self._cscripts.silicon_cpu_family].format('3'),
                     self.IEH_ERROR_REGISTER_PARENT_DICT[self._cscripts.silicon_cpu_family].format('_global'),
                     self.IAX_ERROR_REGISTER_PARENT_DICT[self._cscripts.silicon_cpu_family].format('1')]
        for register in registers:
            self._log.info("Reading {} -".format(register))
            self.read_register_via_cscripts(0, register).showsearch('sts')
