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

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.pcie_hw_injector_provider import PcieHwInjectorProvider

from src.lib.content_base_test_case import ContentBaseTestCase
from os import path


class PeiImageType:
    def __init__(self):
        self.INTERPOSER = 2
        self.ENDPOINT = 1

class HwErrType:
    def __init__(self):
        self.POISONED = "poisonedTLP"

class PeiPcieErrorInjectorCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the PEI Test Cases where access to  PEI 4.0 injection capabilities are
    needed
    """

    # do not modify (1 badDLLP sent = 1 badDLLP received, 10 badTLP sent = 1 badTLP received)
    ERRORS_TO_INJECT = {"badDLLP": 1,
                        "badTLP": 10,
                        "poisonedTLP": 1,
                        "malformedTLP": 1,
                        "tlp_gen": 1}

    # test to injection function mapping
    PEI_TEST_TYPES = {"badTLP": "inject_bad_lcrc_err",
                      "badDLLP": "inject_bad_dllp_err",
                      "poisonedTLP": "poisoned_tlp",
                      "malformedTLP": "malformed_tlp",
                      "tlp_gen": "tlp_gen"}

    OS_ERR_SIGNATURE = {"badDLLP": ["aer_status",
                                    "BadDLLP",
                                    "It has been corrected by h/w and requires no further action"],
                        "badTLP": ["aer_status",
                                   "BadTLP",
                                   "It has been corrected by h/w and requires no further action"],
                        "poisonedTLP": ["PCIe Bus Error: severity=Uncorrected"],
                        "malformedTLP": ["severity=Uncorrected",
                                         "MalfTLP"],
                        "malformedTLP_no_dpc": ["BERT: Error records from previous boot",
                                                "severity: fatal"],
                        "malformedTLP_pre_os": ["error found at IEH",
                                                "IEH CORRECT ERROR"],
                        "poisonedTLP_pre_os": ["error found at IEH",
                                                "IEH CORRECT ERROR"],
                        "poisonedTLP_endpoint": ["DPC: unmasked uncorrectable error detected"]}

    OS_WAIT_2_SOCKET_SEC = 420
    OS_WAIT_4_SOCKET_SEC = 840
    OS_WAIT_8_SOCKET_SEC = 1260
    WAIT_TIME_SEC = 30
    WAIT_TIME_FOR_STABILIZING_SYSTEM_SEC = 30
    INJECT_ERR_WAIT_TIME_SEC = 30
    CLR_PCIE_ERR_WAIT_TIME_SEC = 30
    PEI_SW_LOCATION = 'C:\\Program Files\\PEI\\PCIe'

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of PeiPcieErrorInjectorCommon

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """

        super(PeiPcieErrorInjectorCommon, self).__init__(test_log, arguments, cfg_opts,
                                                         bios_config_file_path=path.join(path.dirname(
                                                                      path.abspath(__file__)),
                                                                      bios_config_file))
        self.cfg_opts = cfg_opts

        self._hw_inj_cfg = cfg_opts.find(PcieHwInjectorProvider.DEFAULT_CONFIG_PATH)

        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

        self.cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)  # instantiate CScript object
        self.sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)  # instantiate XDP object

        self.hw_injector = ProviderFactory.create(self._hw_inj_cfg, self._log)  # instantiate PEI HW injector object

        self.pei_image_type = PeiImageType()
        self.hw_err_injection = HwErrType()

    def verify_register_values_after_injection(self, register, socket, port):
        """
        This method is used to verify expected leaky bucket register values

        param: dict register dictionary containing a field and a expected value
        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' for ICX or 'pxp3.pcieg5.port0,
                or 'pxp3.flexbus.port0' for SPR
        return: Bool
        """

        register_check_pass = True
        reg_name = list(register.keys())[0]
        field = list(register[reg_name].keys())[0]
        expected_value = register[reg_name][field]
        reg = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.%s.%s" % (register.keys(), register),
               ProductFamilies.SPR: "pi5." + self._port_by_register_access_path(str(port), self.REGISTER_ACCESS_PATH_SPR[reg_name]) +
                                    ".cfg.%s.%s" % (reg_name, field)}

        value = self.cscripts_obj.get_by_path(self.cscripts_obj.UNCORE,
                                              reg[self.cscripts_obj.silicon_cpu_family],
                                              socket_index=socket)

        if value != expected_value:
            self._log.error("Field %s value in %s register was %s instead of %s" % (field, reg_name, value,
                                                                                    expected_value))
            register_check_pass = False
        self._log.info("Register %s field %s value matches expected value" % (reg_name, field))

        return register_check_pass

    def assign_value_to_register_and_verify(self, register, socket, port):
        """
        This method is used to assign value to a particualr register and verify

        param: dict register dictionary containing a field and a expected value
        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' for ICX or 'pxp3.pcieg5.port0,
                or 'pxp3.flexbus.port0' for SPR
        return: Bool
        """

        register_check_pass = True
        reg_name = list(register.keys())[0]
        field = list(register[reg_name].keys())[0]
        expected_value = register[reg_name][field]
        reg = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.%s.%s" % (register.keys(), register),
               ProductFamilies.SPR: "pi5." + self._port_by_register_access_path(str(port), self.REGISTER_ACCESS_PATH_SPR[reg_name]) +
                                    ".cfg.%s.%s" % (reg_name, field)}
        self._log.info("Writing value - {} to register - {} and field - {}..".format(expected_value, reg_name, field))
        self.cscripts_obj.get_by_path(self.cscripts_obj.UNCORE,
                                      reg[self.cscripts_obj.silicon_cpu_family],
                                      socket_index=socket).write(expected_value)

        self._log.info("Verifying value of register - {}, after setting it".format((field)))
        value = self.cscripts_obj.get_by_path(self.cscripts_obj.UNCORE,
                                              reg[self.cscripts_obj.silicon_cpu_family],
                                              socket_index=socket)

        if value != expected_value:
            self._log.error("Field %s value in %s register was %s instead of %s" % (field, reg_name, value,
                                                                                    expected_value))
            register_check_pass = False
        self._log.info("Register %s field %s value matches expected value" % (reg_name, field))

        return register_check_pass

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