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
import re
import time
import ipccli

from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import PcieSlotAttribute, WindowsMemrwToolConstant
from src.pcie.lib.slot_mapping_utils import SlotMappingUtils
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from src.lib.dtaf_content_constants import RaidConstants
from src.lib import content_exceptions
from src.environment.os_installation import OsInstallation
from src.lib.install_collateral import InstallCollateral
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon
from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class MultiSocketCommon(object):
    """
    Base class for all Storage related test cases.
    """

    C_DRIVE_PATH = "C:\\"
    DISK_INFO_REGEX = "Disk\s([0-9])"
    VOLUME_INFO = "Volume\s\d+\s+C\s+\S+.*\s*Boot"
    DEVICE_INDEX = 1
    MODE_CHECK_STR = 'Detected\sI.O\sExpanders:\s(\d+)'
    WAIT_TIME = 30
    MODE_DICT = {0 : "Spare Mode", 1 : "PCH IOE Mode on 4S", 3 : "PCH IOE Mode on 8S"}
    LSSCSI = "lsscsi"
    LSPCI = "lspci | grep Ethernet"
    LSUSB = "lsusb"
    GET_SSD_USB_CMD = "wmic DISKDRIVE GET MODEL,SIZE,STATUS"
    PCIE_CONTROLLER_DETAILS = "wmic nic get AdapterType, Name, Installed"
    MEM_CMD = "lsmem"

    def __init__(self, test_log, arguments, cfg_opts):

        self._cfg = cfg_opts
        self._log = test_log
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        self._common_content_configuration = ContentConfiguration(self._log)
        self._product_family = self._common_content_lib.get_platform_family()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider
        self._io_pm_obj = IoPmCommon(test_log, arguments, cfg_opts, config=None)
        self.hsio_obj = HsioUpiCommon(test_log, arguments, cfg_opts)

    def get_mode_info(self, serial_log_dir, log_file):
        """
             Purpose: Get PCH-IOE mode or Spare Mode Details in BIOS serial log
             Args:
                 serial_log_dir: Testcase log directory where serial logs are saved
                 log_file: Testcase Serial Log file name
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Get PCH-IOE mode or Spare Mode Details in BIOS serial log
                     get_mode_info()
        """
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._common_content_lib.wait_for_os(self._common_content_configuration.get_reboot_timeout())
        time.sleep(self.WAIT_TIME)
        serial_log_path = os.path.join(serial_log_dir, log_file)
        key_search = ""
        with open(serial_log_path, 'r') as log_file:
            logfile_data = log_file.read()
            key_search = re.findall(self.MODE_CHECK_STR, logfile_data)
            if not key_search :
                error_statement = "\nThe serial log did not have correct keyword" \
                                  "match for {}".format(self.MODE_CHECK_STR)
                raise content_exceptions.TestFail(error_statement)
            self._log.debug("Re search Output :{}".format(key_search))
        return self.MODE_DICT[int(key_search[0])]

    def get_ioe_device_dict(self):
        """
        This method is to get the list of the ioe devices
        :return: list of the IOE devices
        """
        ioe_dev_dict = {}
        if self._os.os_type.lower() == OperatingSystems.LINUX.lower():
            ssd_list_complete = self._common_content_lib.execute_sut_cmd(self.LSSCSI, self.LSSCSI, self._command_timeout)
            self._log.info("SSD devices list='{}'".format(ssd_list_complete))
            ssd_list_info = []
            for each in ssd_list_complete.split("\n"):
                ssd_list_info.append(re.findall(r"\S+\s+disk\s+\S+\s+(.*)\s+\S+dev/\S+",each)[0])
            pci_list_info = self._common_content_lib.execute_sut_cmd(self.LSPCI, self.LSPCI, self._command_timeout)
            self._log.info("PCI devices list='{}'".format(pci_list_info))
            pci_list_info = pci_list_info.split("\n")
            ioe_dev_dict = {"SSD": ssd_list_info,
                            "PCIe": pci_list_info}
        elif self._os.os_type.lower() == OperatingSystems.WINDOWS.lower():
            ssd_usb_list_info = self._common_content_lib.execute_sut_cmd(self.GET_SSD_USB_CMD, self.GET_SSD_USB_CMD,
                                                                         self._command_timeout)
            self._log.info("SSD & USB devices list='{}'".format(ssd_usb_list_info))
            ssd_usb_list_info = ssd_usb_list_info.split("\n")
            pci_list_info = self._common_content_lib.execute_sut_cmd(self.PCIE_CONTROLLER_DETAILS,
                                                                     self.PCIE_CONTROLLER_DETAILS,
                                                                     self._command_timeout)
            self._log.info("PCI devices list='{}'".format(pci_list_info))
            pcie_eth_controller_list = pci_list_info.split("\n")
            ioe_dev_dict = {"SSD_USB": ssd_usb_list_info,
                            "PCIe": pcie_eth_controller_list}
        else:
            raise NotImplementedError("get_ioe_device_dict is not implemented for "
                                      "specified OS '{}'".format(self._os.os_type))
        return ioe_dev_dict

    def get_mem_details(self):
        """
        This method returns the total memory size from the output of the lsmem command.
        """
        cmd_result = self._common_content_lib.execute_sut_cmd(self.MEM_CMD, "details of mem", self._command_timeout)
        self._log.debug("Details of lsmem : {}".format(cmd_result))
        result = re.findall("Total online memory:\s+(\S+)",cmd_result)
        return result[0]

    def print_topology_logs(self, filename):
        """
        This method prints topology logs into dtaf_log.
        :param filename: pythonsv log file
        """
        with open(filename, "r") as log_file:
            log_file_list = log_file.readlines()
            for each_line in log_file_list:
                self._log.info(each_line)

    def check_topology_speed_lanes(self, sdp):
        """
        This method checks the upi topology, link speed and verifies the link lane
        """
        sdp.start_log("print_topology.log")
        self.itp = ipccli.baseaccess()
        self.itp.forcereconfig()
        self.itp.unlock()
        self.hsio_obj.print_upi_topology()
        self.hsio_obj.print_upi_link_speed()
        self.hsio_obj.print_link()
        self.hsio_obj.verify_upi_topology()
        if not (self.hsio_obj.verify_rx_ports_l0_state() and self.hsio_obj.lanes_operational_check() and self.hsio_obj.verify_tx_ports_l0_state()):
            raise content_exceptions.TestFail(" verification of lo state failed")
        sdp.stop_log()
        self.print_topology_logs("print_topology.log")
