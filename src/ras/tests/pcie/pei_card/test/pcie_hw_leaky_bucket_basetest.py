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

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.bios_util import BiosUtil
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions

from src.ras.tests.pcie.pei_card.pei_card_common import PeiPcieErrorInjectorCommon
from src.ras.lib.os_log_verification import OsLogVerifyCommon


class PcieHWLeakyBucketBaseTest(PeiPcieErrorInjectorCommon):
    """
    Phoenix_id : 22012668040

    The objective of this test is to enable verification of Leaky Bucket flow in response to bad DLLP and bad TLP packets
    by way of injecting them with PEI 4.0 card.

     Requirements:

     1. BIOS config file path configured in system_configuration.xml
     2. Socket of PEI 4.0 card configured in content_configuration.xml
     3. pxp port of PEI 4.0 card configured in content_configuration.xml
     4. PEI 4.0 HW injector card

     Usage:

     Error type injection is controlled by the "test" parameter in the execute() method and is set to "badDLLP" by default
     To execute the test for bad TLP, set test="badTLP"

    """

    BIOS_CONFIG_FILE = "leaky-bucket-default_bios_knobs_spr.cfg"

    # defines how registers are accessed on SPR
    REGISTER_ACCESS_PATH_SPR = {"lekbar": "flexbus",
                                "g4sts": "pcieg5",
                                "linksts": "pcieg5",
                                "linkctl": "pcieg5",
                                "lekberr": "flexbus",
                                "lekberr0": "flexbus",
                                "lekberr1": "flexbus",
                                "lekbproerr": "flexbus",
                                "lekblnerrcnt0": "flexbus",
                                "lekblnerrcnt1": "flexbus",
                                "lekblnerrcnt2": "flexbus",
                                "ltssmsmsts": "flexbus",
                                "devsts": "pcieg5",
                                "errcorsts": "pcieg5",
                                "erruncsts": "pcieg5",
                                "rooterrsts": "pcieg5",
                                "erruncsev": "pcieg5"}

    CONFIG_REG_LEKBERR = {"lekberr": {"g3lbeen": 0x1, "g3errthresh": 0x10, "errthresh": 0x0, "aggrerr": 0xffff}}
    CONFIG_REG_LEKBERR1 = {"lekberr1": {"g3aggrerr": 0x2, "exp_ber": 0x7}}
    CONFIG_REG_LEKBERR0 = {"lekberr0": {"exp_ber": 0xffffffff}}
    CONFIG_REG_LEKBPROERR = {"lekbproerr": {"g3errlnsts": 0x0, "errlnsts": 0x0}}
    CONFIG_REG_LEKBLNERRCNT0 = {"lekblnerrcnt0": {"errcnt5": 0x0, "errcnt4": 0x0, "errcnt3": 0x0,
                                                             "errcnt2": 0x0, "errcnt1": 0x0, "errcnt0": 0x0}}

    CONFIG_REG_LEKBLNERRCNT1 = {"lekblnerrcnt1": {"errcnt11": 0x0, "errcnt10": 0x0, "errcnt9": 0x0,
                                                             "errcnt8": 0x0, "errcnt7": 0x0, "errcnt6": 0x0}}

    CONFIG_REG_LEKBLNERRCNT2 = {"lekblnerrcnt2": {"errcnt15": 0x0, "errcnt14": 0x0, "errcnt13": 0x0,
                                                             "errcnt12": 0x0}}

    STATUS_REG_TRIGGERED_LEKBAR = {"lekbar": {"lbeg4dis": 0x1, "lbeg3dis": 0x0, "lbeg2dis": 0x0, "lbeg4degradeen": 0x1,
                                              "lbeg3degradeen": 0x1, "lbeg2degradeen": 0x1}}

    STATUS_REG_NOT_TRIGGERED_LEKBAR = {"lekbar": {"lbeg4dis": 0x0, "lbeg3dis": 0x0, "lbeg2dis": 0x0, "lbeg4degradeen": 0x1,
                                                  "lbeg3degradeen": 0x1, "lbeg2degradeen": 0x1}}

    STATUS_REG_TRIGGERED_G4STS = {"g4sts": {"linkeqreq16": 0x1, "eq16ph3succ": 0x1, "eq16ph2succ": 0x1,
                                            "eq16ph1succ": 0x1, "eq16cmplt": 0x1}}

    STATUS_REG_NOT_TRIGGERED_G4STS = {"g4sts": {"linkeqreq16": 0x0, "eq16ph3succ": 0x1, "eq16ph2succ": 0x1,
                                                "eq16ph1succ": 0x1, "eq16cmplt": 0x1}}

    STATUS_REG_TRIGGERED_LINKSTS = {"linksts": {"lbms": 0x1}}

    STATUS_REG_TRIGGERED_LINKCTL = {"linkctl": {"lbmie": 0x0}}

    REG_DEVSTS = {"devsts": {"urd": 0x0, "fed": 0x0, "nfed": 0x0, "ced": 0x0, "tp": 0x0, "apd": 0x0}}
    REG_ERRCORSTS = {"errcorsts": {"hloe": 0x0, "cie": 0x0, "anfe": 0x0, "rtte": 0x0, "rnre": 0x0, "bdllpe": 0x0,
                                   "btlpe": 0x0, "re": 0x0}}
    REG_ERRUNCSTS = {"erruncsts": {"ptlpeb": 0x0, "tpbe": 0x0, "aebe": 0x0, "mce": 0x0, "uie": 0x0, "acse": 0x0,
                                   "ure": 0x0, "ecrce": 0x0, "mtlpe": 0x0, "roe": 0x0, "uce": 0x0, "cae": 0x0,
                                   "cte": 0x0, "fce": 0x0, "ptlpe": 0x0, "slde": 0x0, "dlpe": 0x0}}
    REG_ROOTERRSTS = {"rooterrsts": {"aemn": 0x0, "femr": 0x0, "nfemr": 0x0, "fuf": 0x0, "mefr": 0x0, "efr": 0x0,
                                     "mcer": 0x0, "cer": 0x0}}

    REG_ERRUNCSTS_AFTER_POISON_INJECT = {"erruncsts": {"ptlpe": 0x1}}
    REG_ERRUNCSTS_ACSE_AFTER_INJECT = {"erruncsts": {"acse": 0x1}}
    REG_ERRUNCSEV_PTLPES = {"erruncsev": {"ptlpes": 0x1}}
    REG_ERRUNCSEV_PTLPES_ZERO = {"erruncsev": {"ptlpes": 0x0}}
    REG_ERRUNCSTS_AFTER_MALFORMED_INJECT = {"erruncsts": {"mtlpe": 0x1}}
    REG_ERRUNCSEV_MTLPES = {"erruncsev": {"mtlpes": 0x1}}

    # Registers to be checked before error injection
    REGISTER_CHECKLIST = [REG_DEVSTS, REG_ERRCORSTS, REG_ERRUNCSTS, REG_ROOTERRSTS]

    # config registers reflect leaky bucket BIOS knob settings
    LEAKY_BUCKET_CONFIG_REGISTER_CHECKLIST = [CONFIG_REG_LEKBERR, CONFIG_REG_LEKBERR0,
                                              CONFIG_REG_LEKBERR1, CONFIG_REG_LEKBPROERR]

    # status register checklist after leaky bucket flow was triggered
    LEAKY_BUCKET_STATUS_REGISTER_TRIGGERED = {True: [STATUS_REG_TRIGGERED_LEKBAR, STATUS_REG_TRIGGERED_G4STS,
                                                     STATUS_REG_TRIGGERED_LINKSTS, STATUS_REG_TRIGGERED_LINKCTL],
                                              False: [STATUS_REG_NOT_TRIGGERED_LEKBAR, STATUS_REG_NOT_TRIGGERED_G4STS]}
    

    # Error counter
    LEAKY_BUCKET_ERROR_COUNTER_CHECKLIST = [CONFIG_REG_LEKBLNERRCNT0, CONFIG_REG_LEKBLNERRCNT1,
                                            CONFIG_REG_LEKBLNERRCNT2]

    THRESHOLD_KNOB_NAME = {ProductFamilies.SPR: "Gen345ErrorThreshold",
                           ProductFamilies.ICX: "Gen34ErrorThreshold"}

    THRESHOLD_KNOB_MAX_VALUE = '0x1E'

    LEAKY_BUCKET_DEFAULT_BER_LEAK_RATE_IN_SECONDS = 35  # rounded up, real value is 34.6 seconds


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieHWLeakyBucketBaseTest object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieHWLeakyBucketBaseTest, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_config = ContentConfiguration(self._log)
        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)
        self._reboot_timeout_in_sec = self._common_content_config.get_reboot_timeout()
        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration)
        self.PCIE_SOCKET = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        self.PCIE_PXP_PORT = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()
        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)
        self._cfg = cfg_opts
        self._bios_util = BiosUtil(cfg_opts, self.BIOS_CONFIG_FILE, self._bios, self._log, self._common_content_lib)
        self.LEAKY_BUCKET_ERROR_THRESHOLD = self._bios_util.get_bios_knob_current_value(self.THRESHOLD_KNOB_NAME[self.cscripts_obj.silicon_cpu_family])
        self.pcie = self.cscripts_obj.get_cscripts_utils().get_pcie_obj()
        self._telemetry_dict = {"test_name": "Leaky_bucket_DLLP_error", "test_owner": "DTAF_AUTOMATION"}

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(PcieHWLeakyBucketBaseTest, self).prepare()

    def execute(self, expect_link_degrade=True):
        """
        This method checks the OS log for errors given a supported error type

        param: string err_type - one of the supported error types (i.e.: "badDLLP", "badTLP")
        return: True
        raise: TestFail
        """
        err_type = self._common_content_configuration.pei_card_err_type()

        self._log.info("Testing %s case" % err_type)
        self._log.info("Clearing OS logs")
        self._common_content_lib.clear_os_log()
        self._common_content_lib.clear_dmesg_log()

        self._log.info("Checking config register values before PEI error injection")
        self.check_config_registers()

        self._log.info("Checking leaky bucket lane error count is zero before error injection")
        if self.get_leaky_bucket_error_count(self.PCIE_SOCKET, self.PCIE_PXP_PORT) != 0:
            raise content_exceptions.TestFail("Lane error count was not zero before error injection")

        self._log.info("Injecting errors")
        self.inject_pei_errors(err_type)

        self._log.info("Verify OS Log")
        self.check_os_errors_reported(err_type)

        self._log.info("Checking status register values after PEI error injection")
        self.check_status_registers_triggered(triggered=expect_link_degrade)
        return True

    def check_config_registers(self, registers={}):
        """
        This method checks config registers for expected values

        param: registers: register_dict
        return: nothing
        raise: TestFail
        """
        register_check_status = True
        if not registers:
            registers = self.LEAKY_BUCKET_CONFIG_REGISTER_CHECKLIST

        for register in registers:
            if not self.verify_leaky_bucket_register_values(register, self.PCIE_SOCKET, self.PCIE_PXP_PORT):
                register_check_status = False

        if not register_check_status:
            raise content_exceptions.TestFail("Config registers check failed")

    def check_status_registers_triggered(self, triggered=True):
        """
        This method checks status registers for expected values after the leaky bucket flow was triggered

        param: bool triggered - whether to check registers for triggered state or not
        return: nothing
        raise: TestFail
        """
        register_check_status = True

        for register in self.LEAKY_BUCKET_STATUS_REGISTER_TRIGGERED[triggered]:
            if not self.verify_leaky_bucket_register_values(register, self.PCIE_SOCKET, self.PCIE_PXP_PORT):
                register_check_status = False

        if not register_check_status:
            raise content_exceptions.TestFail("Status registers check failed")

    def check_os_errors_reported(self, err_type):
        """
        This method checks the OS log for errors given a supported error type

        param: string error_type - one of the supported error types (i.e.: "badDLLP", "badTLP")
        return: nothing
        raise: TestFail
        """
        errors_reported = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                        self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                                        self.OS_ERR_SIGNATURE[err_type])

        if not errors_reported:
            log_err = "Correctable error not reported to the OS after bad %s error injection" % err_type
            self._log.error(log_err)
            raise content_exceptions.TestFail(log_err)

        self._log.info("Correctable error reported to OS after bad %s error injection" % err_type)

    def inject_pei_errors(self, error_type, run_lspci=True):
        """
        This method is used to inject errors of a given supported type until the threshold set by the internal
        LEAKY_BUCKET_ERROR_THRESHOLD value is reached. This variable value can be overridden to set a different threshold
        and doesn't have to equal the threshold value set in the BIOS, this way we can inject errors below or above the
        leaky bucket threshold set in the BIOS

        param: string error_type - one of the supported error types (i.e.: "badDLLP", "badTLP", "poisnonedDLP")
        param: run_lspci: to run lspci in parallel
        return: nothing
        """
        if run_lspci:
            self._log.debug("Running lspci in a loop to generate some PCIe traffic while injecting bad packets")
            self._os.execute_async("while true; do lspci; sleep 1; done")

        """keeping an internal counter is necessary as the lane error counter may not always increment after injection
         if the error was not received."""
        internal_count = 0

        while True:
            lane_error_count = self.get_leaky_bucket_error_count(self.PCIE_SOCKET, self.PCIE_PXP_PORT)
            if internal_count < int(self.LEAKY_BUCKET_ERROR_THRESHOLD, 16) or (
                    lane_error_count < int(self.LEAKY_BUCKET_ERROR_THRESHOLD, 16) and lane_error_count != 0):
                self._log.info("Injecting %s" % error_type)
                getattr(self.hw_injector, self.PEI_TEST_TYPES[error_type])(count=self.ERRORS_TO_INJECT[error_type])
                internal_count += 1
            else:
                break

    def verify_leaky_bucket_register_values(self, register, socket, port):
        """
        This method is used to verify expected leaky bucket register values

        param: dict register dictionary containing fields and expected values
        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' for ICX or 'pxp3.pcieg5.port0,
                or 'pxp3.flexbus.port0' for SPR
        return: Bool
        """

        register_check_pass = True

        for reg_name, reg_fields in register.items():
            for field, expected_value in reg_fields.items():
                reg = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.%s.%s" % (reg_name, field),
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

    def _port_by_register_access_path(self, port, access_path):
        """
        This method converts the pxp port path based on the appropriate register access method

        param: String port i.e.: pxp0.flexbus.port0
        param: String access_path i.e.: flexbus, pcieg5, pcieg4
        return: String
        raise: ValueError
        """

        if access_path not in ["flexbus", "pcieg5", "pcieg4"]:
            raise ValueError("Access path not valid")

        pxp_port_element = port.split(".")
        pxp_port_element[1] = access_path

        return ".".join(pxp_port_element)

    def is_link_reversed(self, socket, port):
        """
        This method is used to check if the link is reversal status register

        param: Obj cscripts_obj
        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' or 'pxp3.pcieg5.port0'
        return: Bool
        raise: RuntimeError
        """

        link_reversed_reg = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.ltssmsmsts.lnkreversed",
                             ProductFamilies.SPR: "pi5." + self._port_by_register_access_path(str(port),
                                                                                              self.REGISTER_ACCESS_PATH_SPR[
                                                                                                  "ltssmsmsts"]) +
                                                  ".cfg.ltssmsmsts.lnkreversed"}

        reg = self.cscripts_obj.get_by_path(self.cscripts_obj.UNCORE,
                                            link_reversed_reg[self.cscripts_obj.silicon_cpu_family],
                                            socket_index=socket)

        if reg is None:
            self._log.error("Link reversal register could not be read")
            raise RuntimeError
        return bool(reg)

    def get_leaky_bucket_error_count(self, socket, port):
        """
        This method is used to get the lane error count

        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' or 'pxp3.pcieg5.port0'
        return: int
        """
        register_name = "lekblnerrcnt0"
        register_field = "errcnt0"

        if self.is_link_reversed(socket, port):
            register_name = "lekblnerrcnt2"
            register_field = "errcnt12"

        reg = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.%s.%s" % (register_name, register_field),
               ProductFamilies.SPR: "pi5." + self._port_by_register_access_path(str(port),
                                                                                self.REGISTER_ACCESS_PATH_SPR[register_name]) +
                                    ".cfg.%s.%s" % (register_name, register_field)}

        self._log.debug("Command is {}".format(reg[self.cscripts_obj.silicon_cpu_family]))

        count = self.cscripts_obj.get_by_path(self.cscripts_obj.UNCORE,
                                              reg[self.cscripts_obj.silicon_cpu_family],
                                              socket_index=socket)

        self._log.debug("Leaky bucket lane error counter - {}".format(count))
        return int(count)

    def verify_leaky_bucket_flow(self, err_type, triggered=True):
        """
        This method is used to call functions responsible for performing all checks to verify that leaky bucket flow
        was triggered

        param: string error_type - one of the supported error types (i.e.: "badDLLP", "badTLP")
        param: bool triggered - if check should be performed for triggered case or not triggered (i.e.: negative)
        return: nothing
        """
        self._log.info("Checking status registers for %s link degradation" % "positive" if triggered else "negative")
        self.check_status_registers_triggered(triggered)
        self._log.info("Check OS log reported error")
        self.check_os_errors_reported(err_type)

    def get_link_speed_detail(self, gen=5):
        """
        This method get the link speed

        gen (int) - generation of the card
        return (int): link speed
        raise: TestFail
        """
        port_mapped = self.PCIE_PXP_PORT.split('.')
        port_mapped[1] = 'pcieg{}'.format(gen)
        port_str = '.'.join(port_mapped)
        link_speed = self.pcie.get_current_link_speed(socket=self.PCIE_SOCKET, portstr=port_str)
        if link_speed is None:
            raise content_exceptions.TestFail("Link speed register could not be read")
        self._log.info("Link speed is - {}".format(str(link_speed), 16))
        return int(str(link_speed), 16)

    def change_ber_in_bios_knob(self, bios_field="ExpectedBer", value="0x0000000000000000"):
        """
        This method is used to set the BER in the bios knob

        bios_field: bios knob filed which is to be configured
        value: Actual value of the files
        return: None
        raise: TestFail
        """
        self._bios_util.set_single_bios_knob(bios_field, value)
        self._log.info("Powercycle the SUT for the BIOS changes to take effect.")
        self.perform_graceful_g3()

        self._log.info("Verify the bios knob {} is set to {} after powercycle.".format(bios_field, value))
        current_ber_value = self.bios_util.get_bios_knob_current_value("ExpectedBer")
        if current_ber_value != value:
            raise content_exceptions.TestFail("Set BER value for Leaky Bucket failed")

    def check_link_degrade(self, initial_gen, expect_link_degrade=True):
        """
       This method is to check and compare the current link speed with the initial_gen value

       initial_gen (int) - generation of the card
       expect_link_degrade (bool) - speed degradation status
       return : None
       raise: TestFail
       """
        self._log.info("Checking PCIE gen after injecting error")
        gen_check = (initial_gen == (self.get_link_speed_detail() + 1)) if expect_link_degrade else \
            (initial_gen == self.get_link_speed_detail())
        if not gen_check:
            raise content_exceptions.TestFail("PCIE Link is not in expected generation")

    def verify_all_error_counters(self, socket, port):
        """
        This method is used to verify does the leaky bucket error counters and return the error counters

        param: socket (int) :   socket number
        param: port (str) :  PEI card port
        return: int Max error counter
        """

        error_counter = []

        for counters in self.LEAKY_BUCKET_ERROR_COUNTER_CHECKLIST:
            for reg_name, reg_fields in counters.items():
                for field, expected_value in reg_fields.items():
                    reg = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.%s.%s" % (reg_name, field),
                           ProductFamilies.SPR: "pi5." + self._port_by_register_access_path(str(port), self.REGISTER_ACCESS_PATH_SPR[reg_name]) +
                                                ".cfg.%s.%s" % (reg_name, field)}

                    value = self.cscripts_obj.get_by_path(self.cscripts_obj.UNCORE,
                                                          reg[self.cscripts_obj.silicon_cpu_family],
                                                          socket_index=socket)

                    error_counter.append(int(value))
                    self._log.debug("error counter of {} - {}".format(field, value))
        self._log.info("Leaky bucket error counter is {}".format(max(error_counter)))
        return max(error_counter)

    def verify_leaky_bucket_error_leak_rate (self):
        """
        This method is used to check does the leaky bucket error counter is getting decremented after X sec
        X sec would be decided based on the EXPECTED_BER value configured in BIOS knob

        return : None
        raise: TestFail - while initial error counter is reported 0 / old and current error counter has same values
        """
        ber_value = int(self.bios_util.get_bios_knob_current_value("ExpectedBer"), 16)
        if ber_value != 0:
            sleep_timer = ber_value / 1000000000
            # Default value
            old_error_counter = 1000
            # To avoid infinite loop - Kept loop counter for 25 attempts
            for i in range(30):
                current_error_counter = self.verify_all_error_counters(self.PCIE_SOCKET, self.PCIE_PXP_PORT)
                if old_error_counter == 1000 and current_error_counter == 0:
                    raise content_exceptions.TestFail("Leaky bucket error counter is Zero even after error injection")

                if current_error_counter < old_error_counter:
                    old_error_counter = current_error_counter
                    self._log.info("Sleep for {}s before checking the leaky bucket error counter".format(sleep_timer))
                    time.sleep(sleep_timer)
                elif current_error_counter == 0 and old_error_counter == 0:
                    break
                else:
                    raise content_exceptions.TestFail(
                        "Leaky bucket error counter is not decrementing for every {}sec".format(ber_value))
            else:
                raise content_exceptions.TestFail(
                    "Leaky bucket error counter is not decrementing for every {}sec".format(ber_value))
        else:
            self._log.info(
                "Expected BER is configured as 0 in bios knob, hence skipping to check the leaky bucket error rate")

    def extract_network_interface_from_dmesg(self, str_pattern):
        """
        This method is used to get the network interface from dmesg

        str_pattern (str): Pattern type to find in the log message
        returns : Matched values
        raise : Test Fail
        """
        eth_interface = self._os_log_obj.get_all_matches_from_log(__file__,
                                                                   self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                                   str_pattern)
        if not eth_interface:
            log_err = "Fail to get the network adapter interface"
            raise content_exceptions.TestFail(log_err)
        return eth_interface


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieHWLeakyBucketBaseTest.main() else Framework.TEST_RESULT_FAIL)
