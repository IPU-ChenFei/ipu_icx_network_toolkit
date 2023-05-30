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
import re
import time

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.pcie_hw_injector_provider import PcieHwInjectorProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems, ProductFamilies

from src.lib.bios_util import BootOptions, ItpXmlCli

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.ras.lib.os_log_verification import OsLogVerifyCommon


class KeysightPcieErrorInjectorCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Pcie Test Cases
    """
    LCRC_ERR_SIG = ["severity: corrected", "section_type: PCIe error", "port_type: 4, root port"]
    LCRC_COR_ERR_WINDOWS = ["id: 17", "corrected hardware error", "PCI Express"]
    LCRC_COR_SERIAL_SIG = ["IEH CORRECT ERROR", "Sev: IEH CORRECT ERROR"]
    SURPRISE_LINK_DOWN_ERR_SIG = ["severity: fatal", "section_type: PCIe error", "port_type: 4, root port",
                                  "Hardware Error"]
    MALFORMED_TLP_FATAL_SIG_WINDOWS = ["fatal hardware error"]
    POISONED_TLP_SIG_WINDOWS = MALFORMED_TLP_FATAL_SIG_WINDOWS
    MALFORMED_TLP_FATAL_SIG_LINUX = ["event severity: fatal", "Hardware Error", "PCIe error"]
    POISONED_TLP_UCF_SIG_LINUX = MALFORMED_TLP_FATAL_SIG_LINUX
    EDPC_POISONED_TLP_UCF_SIG_LINUX = ["DPC: unmasked uncorrectable error", "DPC: containment event",
                                       r"PCIe Bus Error: severity=Uncorrected \(Fatal\)"]
    INJECTED_BUS_SIG = "SecondaryBus: {}"
    POISON_TLP_DATA = [0xde, 0xad, 0xbe, 0xef]
    LOG_WAIT_CHECK_TIMER_IN_SEC = 150

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file=None
    ):
        """
        Create an instance of KeysightPcieErrorInjectorCommon

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        if bios_config_file:
            bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), bios_config_file)
        super(
            KeysightPcieErrorInjectorCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file_path=bios_config_file)
        self.cfg_opts = cfg_opts

        #  Create an Keysight Provider object
        self._hw_inj_cfg = cfg_opts.find(PcieHwInjectorProvider.DEFAULT_CONFIG_PATH)

        #  sdp_cfg
        self._sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

        #  csp_cfg
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)

        #  os log obj
        self._os_log_ver_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                                 self._common_content_lib)

        #  Create UEFI obj
        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider

        #  Get boot menu entry wait time
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()

        self.itp_xml_cli_util = None
        self.previous_boot_order = None
        self.current_boot_order = None

    def prepare_for_uefi(self):
        """
        This method is to execute prepare.
        """
        try:
            self._common_content_lib.clear_all_os_error_logs()
        except RuntimeError as e:
            self._log.error("failed to clear the logs, error is %s", str(e))
        if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
            self.os.execute("rm -rf /var/log/*", self._command_timeout)
        self._log.info("Loading default bios settings")
        self.bios_util.load_bios_defaults()
        if self.bios_config_file_path:
            self._log.info("Setting required bios settings")
            self.bios_util.set_bios_knob()
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        if self.bios_config_file_path:
            self._log.info("Verifying bios settings")
            self.bios_util.verify_bios_knob()

    def create_keysight_provider_object(self):
        """
        This method is to create keysight provider object.

        :return object
        """
        #  Get AC power config details from content_configuration.xml
        key_sight_card_ac_power_cfg = self._common_content_configuration.get_ac_power_cfg()

        #  Create Keysight card AC power obj.
        key_sight_card_ac_power_obj = ProviderFactory.create(key_sight_card_ac_power_cfg, self._log)

        #  If during creation of Keysight provider object any exception occur then Applying AC cycle to Keysight
        #  card to get card visible and then creating an object of Keysight provider.
        for i in range(0, 3):
            try:
                key_sight_provider_obj = ProviderFactory.create(self._hw_inj_cfg, self._log)
                return key_sight_provider_obj
            except:
                self._log.error("Unable to detect the card. Apply AC cycle to Keysight Card")
                key_sight_card_ac_power_obj.ac_power_off(self.AC_TIMEOUT)
                time.sleep(self.WAIT_TIME)
                key_sight_card_ac_power_obj.ac_power_on(self.AC_TIMEOUT)
                time.sleep(2 * self.WAIT_TIME)
                continue

    def check_lcrc_error_status(self, csp=None, socket=0, port="pxp3.pcieg5.port0", expected_bdtlp_status=True):
        """
        This method is to check the LCRC status.

        :param csp - Cscripts silicon debug provider
        :param socket - Socket number
        :param port - port number
        :param expected_bdtlp_status - True if LCRC error is expected else False
        :raise content_exceptions
        """
        csp_reg = "pi5.{}.cfg.errcorsts.btlpe".format(port)
        csp_output = csp.get_by_path(csp.UNCORE, socket_index=socket, reg_path=csp_reg)
        self._log.info("Output of cscript command: {} is : {}".format(csp_reg, csp_output))
        if expected_bdtlp_status:
            if not csp_output:
                raise content_exceptions.TestFail("Error was not captured in LCRC error status register")
            self._log.info("LCRC error was captured as Expected")
        else:
            if csp_output:
                raise content_exceptions.TestFail("Unexpected Error was Captured before injected error")
            self._log.info("No LCRC error was Captured before error injection as Expected")

    def check_malformed_tlp_error_status(self, csp=None, socket=0, port="pxp3.pcieg5.port0",
                                         mtlpe_status_reg_indicates_error=True):
        """
        This method is to check Malform TLP error status.

        :param csp - cscripts object.
        :param socket - socket number.
        :param port - port number.
        :param mtlpe_status_reg_indicates_error - expected status of mtlpe register.
        :raise content_exceptions
        """
        malform_error_status_reg_path = {ProductFamilies.SPR: "pi5.{}.cfg.erruncsts.mtlpe".format(port),

                                         ProductFamilies.ICX: "pi5.{}.cfg.erruncsts.mtlpe".format(port)}

        product_family = self._common_content_lib.get_platform_family()
        mtlpe_status_output = csp.get_by_path(csp.UNCORE, socket_index=socket, reg_path=
        malform_error_status_reg_path[product_family])
        self._log.info("Output of cscript command: {} is : {}".format(malform_error_status_reg_path[product_family],
                                                                      mtlpe_status_output))

        if mtlpe_status_reg_indicates_error and not mtlpe_status_output:
            raise content_exceptions.TestFail("Expected error was not indicated in Malformed TLP status register")

        if not mtlpe_status_reg_indicates_error and mtlpe_status_output:
            raise content_exceptions.TestFail("Unexpected Error was indicated in Malformed TLP status register")
        self._log.info("Malformed error status register found as Expected")

    def clear_pcie_error(self, csp=None, sdp=None):
        """
        This method is to clear PCIe Error.

        :param csp - Cscripts silicon register provider object
        :param sdp - xdp silicon debug provider object
        :return None
        :raise content_exceptions
        """
        try:
            #  Create error object
            pci = csp.get_cscripts_utils().get_pci_obj()

            #  Halt the Machine
            sdp.halt_and_check()

            #  Clear pcie error
            self._log.info("Clear PCIe error before inject Error")

            #  Scan pci before clear error
            pci.scan()

            #  Clear All PCIe error
            pci.error_clear_all()
        except Exception as ex:
            raise content_exceptions.TestFail("Failed to Clear PCIe error with exception: {}".format(ex))

        finally:
            self._log.info("Resume the Machine...")
            sdp.go()

    def get_bus_number_for_required_slot(self, port="pxp3.pcieg5.port0", socket=0, csp=None):
        """
        This method is to get the bus number for required slot.

        :param csp - Cscripts object
        :param port - port number
        :param socket - socket number

        :return bus_number - bus number for given slot
        """
        try:
            product_family = self._common_content_lib.get_platform_family()
            sec_bus_csp_reg_path = {ProductFamilies.SPR: "pi5.{}.cfg.secbus".format(port),
                                    ProductFamilies.ICX: "pi5.{}.cfg.secbus".format(port)}
            bus_number = csp.get_by_path(csp.UNCORE, socket_index=socket, reg_path=sec_bus_csp_reg_path[product_family])
            self._log.info("Bus for socket: {} and port: {} is - {}".format(socket, port, bus_number))
        except Exception as ex:
            raise content_exceptions.TestFail("Failed to execute the Cscripts command: {}".format(ex))

        return bus_number

    def get_requester_id(self):
        """
        This method is to get Requester id, 16bit BDF for the Keysight requester. bit 0-7 for bus, 8-11 for device
        and 12-15 for function. example: ab:00.0 translate to 0xab00(then after converting to int).

        :return Requester id in int.
        """
        if self.os.os_type == OperatingSystems.LINUX:
            lspci_agilent_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd="lspci | grep 'Agilent'",
                                                                                cmd_str="check Agilent PCIe in lspci",
                                                                                execute_timeout=self._command_timeout).split(
                '\n')[0]
            bdf_value = lspci_agilent_cmd_output.split(' ')[0]
        elif self.os.os_type == OperatingSystems.WINDOWS:
            bdf_value = self._common_content_configuration.get_keysight_card_bdf_in_windows()
        else:
            raise content_exceptions.TestFail("This method is not implemented for OS- {}".format(self.os.os_type))

        bus = bdf_value[:2]
        device = bdf_value[4:5]
        function = bdf_value[6:7]
        req_id = "0x" + bus + device + function
        req_id_in_int = int(req_id, 16)

        return req_id_in_int

    def get_requester_bdf_id(self):
        """
        This method is to get Requester id, 16bit BDF for the Keysight requester. bit 0-7 for bus, 8-11 for device
        and 12-15 for function. example: ab:00.0 translate to 0xab00(then after converting to int).

        :return Requester id in int.
        """
        bdf_value = self._common_content_configuration.get_keysight_card_bdf_in_uefi()

        bus = bdf_value[:2]
        device = bdf_value[4:5]
        function = bdf_value[6:7]
        req_id = "0x" + bus + device + function
        req_id_in_int = int(req_id, 16)

        return req_id_in_int

    def get_memory_addr_to_inject(self, uefi_type=False):
        """
        This method is to get memory addr to inject the error.

        :param uefi_type
        :return int_mem_addr
        """
        if uefi_type:
            hex_mem_addr = self._common_content_configuration.get_memory_address_to_inject_poison_error_for_keysight_card()
            int_mem_addr = int(hex_mem_addr, 16)

        elif self.os.os_type == OperatingSystems.LINUX:
            addr_output = self._common_content_lib.execute_sut_cmd(sut_cmd="cat /proc/iomem | grep 'System RAM'",
                                                                   cmd_str="System RAM command", execute_timeout=
                                                                   self._command_timeout)
            self._log.info("System RAM output: {}".format(addr_output))

            #  As second Ram address is preferable, So getting same.
            mem_address_range = addr_output.split('\n')[1]
            int_mem_addr = int("0x" + mem_address_range.split('-')[0], 16)
            self._log.info("Memory Address to inject the error is: {}".format(int_mem_addr))
        elif self.os.os_type == OperatingSystems.WINDOWS:
            hex_mem_addr = self._common_content_configuration.get_memory_address_to_inject_error_for_keysight_card()
            int_mem_addr = int(hex_mem_addr, 16)
        else:
            raise content_exceptions.TestFail("This method is not implemented for OS type - {}".format(self.os.os_type))
        return int_mem_addr

    def check_poisoned_tlp_error_status(self, csp=None, socket=0, port="pxp3.pcieg5.port0",
                                        ptlpe_status_reg_indicates_error=True):
        """
        This method is to check Poisoned TLP error status.

        :param csp - cscripts object.
        :param socket - socket number.
        :param port - port number.
        :param ptlpe_status_reg_indicates_error - expected status of ptlpe register.
        :raise content_exceptions
        """
        poison_tlp_error_status_reg_path = {ProductFamilies.SPR: "pi5.{}.cfg.erruncsts.ptlpe".format(port),

                                            ProductFamilies.ICX: "pi5.{}.cfg.erruncsts.ptlpe".format(port)}

        product_family = self._common_content_lib.get_platform_family()
        ptlpe_status_output = csp.get_by_path(csp.UNCORE, socket_index=socket, reg_path=
        poison_tlp_error_status_reg_path[product_family])
        self._log.info("Output of cscript command: {} is : {}".format(poison_tlp_error_status_reg_path[product_family],
                                                                      ptlpe_status_output))

        if ptlpe_status_reg_indicates_error and not ptlpe_status_output:
            raise content_exceptions.TestFail("Expected error was not indicated in Poisoned TLP status register")

        if not ptlpe_status_reg_indicates_error and ptlpe_status_output:
            raise content_exceptions.TestFail("Unexpected Error was indicated in Poisoned TLP status register")
        self._log.info("Poisoned TLP error status register found as Expected")

    def is_keysight_card_fully_enumerated(self, port=None, socket=None, csp_obj=None, sdp_obj=None, exec_env="os"):
        """
        This method is to check if Keysight Card is Fully enumerated or not.

        :param port - port
        :param socket - Socket
        :param csp_obj - Cscripts provider object
        :param sdp_obj - Silicon debug provider obj
        :param exec_env SUT execution environment
        :return True if enumerated else False
        """
        sec_bus_reg_path_dict = {ProductFamilies.SPR: "pi5.{}.cfg.secbus".format(port),
                                 ProductFamilies.ICX: "pi5.{}.cfg.secbus".format(port)}
        product_family = self._common_content_lib.get_platform_family()

        sec_bus_output = csp_obj.get_by_path(csp_obj.UNCORE, socket_index=socket,
                                             reg_path=sec_bus_reg_path_dict[product_family])
        self._log.info("KeySight Card Bus: {} is : {}".format(sec_bus_reg_path_dict[product_family],
                                                              sec_bus_output))
        if not sec_bus_output:
            self._log.info("Keysight Card bus is not enumerated fully.........Apply reset")
            sdp_obj.itp.resettarget()
            self._log.info("Reset Target Applied")
            if exec_env == "os":
                self._common_content_lib.wait_for_os(self.reboot_timeout)
                time.sleep(30)
                sec_bus_output = csp_obj.get_by_path(csp_obj.UNCORE, socket_index=socket,
                                                     reg_path=sec_bus_reg_path_dict[product_family])
                self._log.info("KeySight Card Bus: {} is : {}".format(sec_bus_reg_path_dict[product_family],
                                                                      sec_bus_output))
                if self.os.os_type == OperatingSystems.LINUX:
                    try:
                        self._common_content_lib.execute_sut_cmd(sut_cmd="lspci | grep 'Agilent'",
                                                                 cmd_str="check Agilent PCIe in lspci",
                                                                 execute_timeout=self._command_timeout)
                        return True
                    except:
                        self._log.info("Keysight Card is not fully enumerated in OS")
                        return False
                else:
                    if sec_bus_output:
                        return True
                    return False
            else:
                time.sleep(self._common_content_configuration.get_itp_reset_timeout())
                if not sec_bus_output:
                    return False
                return True
        else:
            if exec_env == "os":
                if self.os.os_type == OperatingSystems.LINUX:
                    try:
                        self._common_content_lib.execute_sut_cmd(sut_cmd="lspci | grep 'Agilent'",
                                                                 cmd_str="check Agilent PCIe in lspci",
                                                                 execute_timeout=self._command_timeout)
                        self._log.info("Keysight Card detected in OS")
                        return True
                    except:
                        self._log.error("Keysight Card is not detected in OS")
                        return False
                else:
                    return True
            else:
                return True
