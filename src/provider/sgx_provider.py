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
import re
import os
import time
import shutil
import time
from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass
import ipccli
from typing import Union
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

from dtaf_core.lib.exceptions import OsCommandException, OsCommandTimeoutException
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.silicon import CPUID
from dtaf_core.lib.os_lib import LinuxDistributions, OsCommandResult
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib.dtaf_content_constants import PowerStates, TimeConstants
from src.lib import content_exceptions
from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from pathlib import Path
from src.provider.rdmsr_and_cpuid_provider import RdmsrAndCpuidProvider
from src.security.tests.sgx.sgx_constant import SGXConstant



@add_metaclass(ABCMeta)
class SGXProvider(BaseProvider):
    """Provides SGX driver provider"""

    PSW_DIR = None
    SGX_FVT_BINARY = None
    CPUID_SGX_CMD = "cpuid -l 0x12"
    EAX_HEX_VALUE_CPUID = 0x12
    MSR_HEX_VALUE = 0x3a
    SGX_MSR_1F5_VALUE = 0x1F5
    SGX_MSR_A0_VALUE = 0xA0
    EAX_EXP_VALUES = {"0": "1", "1": "1"}
    MSR_EXP_VALUES = {"0": "1", "17": "1", "18": "1"}
    EAX_SGX_DISABLE_EXP_VALUES = {"0": "0", "1": "0"}
    MSR_SGX_DISABLE_EXP_VALUES = {"0": "1", "17": "0", "18": "0"}
    SGX_KNOB_NAME = "EnableSgx"
    LMCE_SGX_MSR_EXP_VALUES = {"20": "1"}
    SGX_RAS_MSR_EXP_VALUE = {"0": "1"}
    LCP_LOCKED_MSR_EXP_VALUE = {"18": "1", "17": "0"}
    CPUID_EXP_DICT = {CPUID.EAX: "0xe3"}
    SGX_MSR_1F5_EXP_VALUES = {"11": "1"}
    SGX_MSR_A0_EXP_VALUE = 0x0
    MSR981_HEX_VALUE = 0x981
    MSR982_HEX_VALUE = 0x982
    MSR981_EXP_VALUES = {"1": "1"}
    DAM_MSR_503_VALUE = 0x503
    DAM_MSR_EXP_VALUE = 0x0
    MSR_HEX_VALUE_SVN = 0x302
    MSR_EXP_VALUES_SVN = {"0": "0"}
    SGX = "SGX"
    MSR_CMD = "rdmsr {} -0"
    CPUID_CMD = "cpuid -r -1 -l {} -s 0"
    MSR_REPO = "msr-tools.x86_64"
    CPUID_REPO = "cpuid.x86_64 "
    CPUID_EXP = r"{}=([^\s]+)"

    def __init__(self, log: str, cfg_opts: ET.ElementTree, os_obj: SutOsProvider, sdp: SiliconDebugProvider):
        """
        Create a new SGX Provider object.

        :param log: Logger object to use for output messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration
        options for execution environment
        :param os_obj: os object
        :param sdp: SiliconDebugProvider
        """
        super(SGXProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self.sdp = sdp
        self._common_content_lib = CommonContentLib(log, os_obj, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.execution_timeout = self._common_content_configuration.get_command_timeout()
        self._install_collateral = InstallCollateral(self._log, self._os, self._cfg_opts)
        self.reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, log)  # type: AcPowerControlProvider
        self.product = self._common_content_lib.get_platform_family()
        self.sgx_consts = SGXConstant.get_subtype_cls(self.SGX + self.product, False)
        self._rdmsr_and_cpuid_obj = RdmsrAndCpuidProvider.factory(log, os_obj, cfg_opts)
        self.log_dir = self._common_content_lib.get_log_file_dir()

    @staticmethod
    def factory(log, cfg_opts, os_obj, sdp=None):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.sgx_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsSGXDriver"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxSGXDriver"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log, cfg_opts, os_obj, sdp)

    def is_sgx_enabled(self) -> bool:
        """
        Functions checks whether sgx enabled by reading CPUID, MSR Registry values
        1. Verifies CPUID EAX Resgistry 0x12
        2. Verifies MSR Registry PRMRR_MASK 0x1F5
        3. Verifies MSR Registry MCHECK Error 0xA0
        4. Verifies MSR Registry Feature Control 0x3a
        :return: True if SGX is enabled else False.
        """
        eax_value = self.read_cpuid(self.sgx_consts.RegisterConstants.CPUID_EAX, CPUID.EAX)
        self._log.info("SGX EAX CPUID %s value is :%s", hex(self.sgx_consts.RegisterConstants.CPUID_EAX), eax_value)
        prmrr_mask_msr = self.read_msr(self.sgx_consts.RegisterConstants.PRMRR_MASK)
        self._log.info("SGX MSR %s value is :%s", hex(self.sgx_consts.RegisterConstants.PRMRR_MASK), prmrr_mask_msr)
        mcheck_msr = self.read_msr(self.sgx_consts.RegisterConstants.MCHECK_ERROR)
        self._log.info("SGX MSR %s value is :%s", hex(self.sgx_consts.RegisterConstants.MCHECK_ERROR), mcheck_msr)
        feature_control = self.read_msr(self.sgx_consts.RegisterConstants.MSR_FEATURE_CONTROL)
        self._log.info("SGX MSR %s value is :%s", hex(self.sgx_consts.RegisterConstants.MSR_FEATURE_CONTROL),
                       feature_control)
        self._log.info("SGX MSR %s value is :%s", hex(self.sgx_consts.RegisterConstants.MCHECK_ERROR), mcheck_msr)
        if not (self.check_eax_value(eax_value, self.sgx_consts.EAXCpuidBits.EAX_CPUID_BITS) and
                self.check_msr_value(prmrr_mask_msr, self.sgx_consts.PRMRRMaskBits.PRMRR_MASK_BITS) and
                self.check_mcheck_msr_value(mcheck_msr, hex(self.sgx_consts.MSRMCHECK.MCHECK_STATUS_VALUE)) and
                self.check_msr_value(feature_control, self.sgx_consts.MSRIAFeatureControlBits.FEATURE_CONTROL_BITS)):
            return False
        return True

    def verify_dam_enabled(self):
        """This methods checks for DAM MSR value
        :raise: content_exceptions.TestSetupError if DAM MSR value is not as expected"""

        msr_dam_value = ""
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.halt()
            msr_dam_value = hex(self.sdp.msr_read(self.DAM_MSR_503_VALUE, squash=True))
        except Exception as e:
            self._log.error("Unknown exception while verifying DAM {}".format(e))
        finally:
            self.sdp.go()
        self._log.info("Delayed Authentication mode MSR %s value is :%s", hex(self.DAM_MSR_503_VALUE), msr_dam_value)

        if msr_dam_value != hex(self.DAM_MSR_EXP_VALUE):
            raise content_exceptions.TestSetupError("Delayed Authentication mode MSR excepted value {} is not "
                                                    "matching actual value {}".format(self.DAM_MSR_EXP_VALUE,
                                                                                      msr_dam_value))
        self._log.info("Delayed Authentication mode MSR actual value {} is as expected value {}".
                       format(msr_dam_value, self.DAM_MSR_EXP_VALUE))

    def check_mcheck_msr_value(self, mcheck_msr: hex, expected_value: hex) -> bool:
        """
        This methods checks excepted value of msr A0 binary indexes are matched or not

        :param mcheck_msr: output of msr 0xA0 read value
        :param expected_value: expected value of msr 0xA0
        :return True, if excepted value matches actual value else return False
        :type: bool
        """
        if mcheck_msr != expected_value:
            self._log.info("SGX mcheck_msr excepted value {} is not matching actual value {}".
                           format(mcheck_msr, expected_value))
            return False
        self._log.info("SGX mcheck_msr excepted value {} is matching actual value {}".
                       format(mcheck_msr, expected_value))
        return True

    def is_sgx_enabled_over_advanced_ras(self):
        """This methods checks whether sgx enabled over advanced ras or not
        :return: True if SGX chosen over Advanced RAS
        """
        eax_value = msr_value = ""
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.halt()
            eax_value = hex(self.sdp.cpuid(CPUID.EAX, 0x12, 0, squash=True))
            msr_value = hex(self.sdp.msr_read(0xa3, squash=True))
        except Exception as e:
            self._log.error("Unknown exception while verifying SGX")
        finally:
            self.sdp.go()
        self._log.info("Actual EAX value :%s", eax_value)
        self._log.info("Actual MSR value :%s", msr_value)
        if not (self.check_eax_value(eax_value, self.EAX_EXP_VALUES) and self.check_msr_value(msr_value,
                                                                                              self.SGX_RAS_MSR_EXP_VALUE)):
            return False
        return True

    def check_eax_value(self, eax_value, expected_values):
        """
        This methods checks whether bit 0 and 1 of eax binary indexes are set or not

        :param eax_value output of EAX cupid leaf
        :return True, if bits 0 and 1 are set else return False
        """
        not_matching_bits = []
        self._log.info("Checking bits in eax output")
        bin_value = self._common_content_lib.convert_hexadecimal([eax_value])
        self._log.info("converted binary value {}".format(bin_value))
        for key, value in expected_values.items():
            if int(bin_value[eax_value][::-1][int(key)]) != int(value):
                not_matching_bits.append("Bit %s value is not expected %s, actual value is %s" % (key, value,
                                                                                                  int(bin_value[eax_value][::-1][int(key)])))
            else:
                self._log.info("Bit %s value is expected %s, actual value is %s" % (key, value,
                                                                                    int(bin_value[eax_value][::-1][int(key)])))
        if not_matching_bits:
            self._log.debug("Not matching bit for EAX value {}".format(not_matching_bits))
            return False
        return True

    def check_sgxi_enumeration(self):
        """
        This methods checks SGXi enumeration by verifying the values of cpuid - eax, ebx, ecx and edx
        command -> itp.threads[0].cpuid(0x12,0)

        :raise: content_exceptions.TestFail if EAX,EBX,ECX,EDX value does not match the CPUID expected values
        """
        cpuid_actual_output = {}
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.halt()
            for key, value in self.CPUID_EXP_DICT.items():
                cpuid_actual_output[key] = hex(self.sdp.cpuid(key, self.EAX_HEX_VALUE_CPUID, 0, squash=True))
                self._log.info("{} actual value :{} and expected value:{}".format(key, cpuid_actual_output[key],
                                                                                  self.CPUID_EXP_DICT[key]))
        except Exception as e:
            self._log.error("Unknown exception while verifying SGX {}".format(e))
        finally:
            self.sdp.go()
        self.verify_sgxi_enumeration(cpuid_actual_output)

    def verify_sgxi_enumeration(self, cpuid_actual_output):
        """
        comparing cpuid EAX,EBX,ECX,EDX expected values with actual value
        :param cpuid_actual_output: actual value of cpuid EAX,EBX,ECX,EDX
        :raise: content_exceptions.TestFail if EAX,EBX,ECX,EDX value does not match the CPUID expected values

        """
        for key in self.CPUID_EXP_DICT:
            def get_search_string(act_value, exp_value):
                """
                This Function replaces 0x from the expected value and gets the length of the excepted value.
                This length is used for extracting the string value of this particular length from actual and
                excepted value
                :param act_value: Actual value of cpuid EAX,EBX,ECX,EDX
                :param exp_value: Expected value of cpuid EAX,EBX,ECX,EDX
                :return: String value based on the length of expected value
                """
                cur_length = len(exp_value.replace("0x", ""))
                return act_value[-cur_length:], exp_value[-cur_length:]

            act_val, exp_val = get_search_string(cpuid_actual_output.get(key), self.CPUID_EXP_DICT.get(key))
            if not (act_val == exp_val):
                raise content_exceptions.TestFail("SGXi enumeration verification failed for cpuid {} "
                                                  "and actual value {} and excepted value {}".format(key, act_val, exp_val))
        self._log.info("SGXi enumeration verification is successful")

    def check_msr_value(self, msr_value, msr_expected_value):
        """
        This methods checks excepted value bits of msr binary indexes are set or not

        :param msr_value output of msr read value
        :return True, if bits of excepted value are set else return False
        """
        not_matching_bits = []
        self._log.info("Checking bits in msr output")
        bin_value = self._common_content_lib.convert_hexadecimal([msr_value])
        self._log.debug("converted binary value {}".format(bin_value))
        for key, value in msr_expected_value.items():
            if int(bin_value[msr_value][::-1][int(key)]) != int(value):
                not_matching_bits.append("Bit %s value is not expected %s, actual value is %s" % (key, value,
                                                        int(bin_value[msr_value][::-1][int(key)])))
            else:
                self._log.info("Bit %s value is expected %s, actual value is %s" % (key, value,
                                                        int(bin_value[msr_value][::-1][int(key)])))
        if not_matching_bits:
            self._log.info("Not matching bits for MSR value {}".format(not_matching_bits))
            return False
        return True

    def is_sgx_disabled(self):
        """This method checks whether sgx is disabled or not

        :return True, if EAX and MSR values are matching else return False
        """
        eax_value = msr_value = ""
        try:
            self._log.debug("Halt the devices")
            self.sdp.halt()
            eax_value = hex(self.sdp.cpuid(CPUID.EAX, self.EAX_HEX_VALUE_CPUID, 0, squash=True))
            msr_value = hex(self.sdp.msr_read(self.MSR_HEX_VALUE, squash=True))
        except Exception as e:
            self._log.error("Unknown exception while verifying SGX {}".format(e))
        finally:
            self.sdp.go()
        self._log.info("Actual EAX value :%s", eax_value)
        self._log.info("Actual MSR value :%s", msr_value)
        # for disable SGX - bits 0 and 1 should be 0 for EAX value and Bit 0 should be 1, bit 17 and 18 is should
        # be 0 for MSr value
        if not (self.check_eax_value(eax_value, self.EAX_SGX_DISABLE_EXP_VALUES) and self.check_msr_value(msr_value,
                                                                                                         self.MSR_SGX_DISABLE_EXP_VALUES)):
            return False
        return True

    def is_lmce_sgx_bit_set(self):
        """
        This method verifies LMCE remains enabled with SGX

        :return: True, if MSR values bit are matching expected result else return False
        """
        self._log.info("Verifying LMCE remains enabled with SGX")
        msr_value = ''
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.halt()
            msr_value = hex(self.sdp.msr_read(self.MSR_HEX_VALUE, squash=True))
        except Exception as e:
            self._log.error("Unknown exception while verifying LMCE")
        finally:
            self.sdp.go()
        self._log.info("Actual MSR value :%s", msr_value)
        if not self.check_msr_value(msr_value, self.LMCE_SGX_MSR_EXP_VALUES):
            return False
        return True

    def check_sgx_enable(self) -> None:
        """Checks for the sgx support
        :raise: raise content_exceptions.TestFail if Sgx is not Enabled.
        """
        if not self.is_sgx_enabled():
            raise content_exceptions.TestFail("SGX is not enabled")
        self._log.info("SGX is enabled")

    def get_sgx_svn_patch_number(self, stepping):
        """
        This function is used to get the sgx svn patch code from content configuration file
        :param stepping: cpu stepping information retrieved from sys configuration file, :type: str
        :return: return the string value of patch svn for particular cpu stepping
        :raise: raise content_exceptions.TestFail if stepping information tag is not added
        """
        try:
            return str(self._common_content_configuration.config_file_path(attrib="SGX/SGX_SVN/STEPPINGS/{}".format(stepping)))
        except Exception as e:
            raise content_exceptions.TestFail("Unable to get the Stepping information {} from content configuration"
                                              " file in the path SGX/SGX_SVN/STEPPINGS".format(stepping))
    @abstractmethod
    def execute_functional_validation_tool(self):
        """
        Execute FVT and verify if SGX is enabled

        :return: True if validation process is successful False otherwise
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def is_sgx_disabled_cpuid(self):
        """
        Check for cpuid output whether all the cpu capability is SGX supported.

        :return: True if cpu capability is supported else false
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def is_sgx_enabled_cpuid(self):
        """
        Check for cpuid output whether all the cpu capability is SGX supported.

        :return: True if cpu capability is supported else false
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def run_semt_app(self, semt_timeout):
        """
        Copies semt app in SUT and runs semt command for given time

        :param: semt_timeout execution time for semt command
        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def run_hydra_test(self, test_duration=60, enclave_mb="128", num_enclave_threads="12", num_regular_threads="12"):
        """
        Copies hydra test tool in SUT and runs hydra test for given time

        :param test_duration: test duration in seconds to run the test, :type: int
        :param enclave_mb: Enclave MB, :type: str
        :param num_enclave_threads: Enclave threads in number, :type: str
        :param num_regular_threads: Regular Threads in number, :type: str
        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def perform_s5_reboot_test(self, socket):
        """
        This method Performs s5 sealing reboot test.

        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def verify_seal_unseal_reboot_test(self):
        """
        Verify seal/unseal reboot test is successful

        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def perform_s5_shutdown_test(self, socket):
        """
        This method Performs s5 sealing reboot test.

        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def verify_seal_unseal_shutdown_test(self):
        """
        Verify seal/unseal shutdown test is successful

        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def verify_lcp_locked_mode(self):
        """
        Run lcp_legacy_locked command and verify the output for LCP Legacy Lock mode and also
        check MSR bit 0 value in MSR_OPTIN_FEATURE_CONTROL value

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def verify_sgx_content(self, time_duration=60, enclave_mb="128", num_enclave_threads="64",
                           num_regular_threads="64"):
        """
        Verify SGX content by running :-
            1. for linux - run semt app
            2. for windows - run hydra app

        :param time_duration: time duration in seconds to run the test, :type: int
        :param enclave_mb: Enclave MB, :type: str
        :param num_enclave_threads: Enclave threads in number, :type: str
        :param num_regular_threads: Regular Threads in number, :type: str
        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def perform_s5_shutdown_boundary(self, phy, socket):
        """
        This method Performs s5 sealing shutdown test.

        :param phy: PHY provider for SXSTATE
        :param socket: Socket number where the test is running.
        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def check_msr_svn_enabled(self):
        """
        This methods checks MSR(302) value
        :return True if the patch reset value passed by the user matches the excepted value.
        """
        msr_value = ""
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.halt()
            msr_value = hex(self.sdp.msr_read(self.MSR_HEX_VALUE_SVN, squash=True))
        except Exception as e:
            self._log.error("Unknown exception while verifying MSR value {}".format(e))
        finally:
            self.sdp.go()
        self._log.info("Actual SGX SVN MSR value :%s", msr_value)
        stepping = self._common_content_lib.get_platform_stepping()
        if stepping:
            if not self.get_sgx_svn_patch_number(stepping.upper()) == str(msr_value)[-1]:
                self._log.error("SVN Patch-at-Reset for the msr (302) is not set for the stepping {} with the value {}"
                            .format(stepping, str(msr_value)[-1]))
                return False
            self._log.info("SVN Patch-at-Reset for the msr (302) is set for the stepping {} with the value {}"
                       .format(stepping, str(msr_value)[-1]))
            return True

    def read_msr(self, msr_add: hex, squash: bool = True) -> hex:
        """
        Attempts to Read MSR values at the specified address

        :param msr_add: Integer with the address of the MSR to read
        :param squash: If True, will check that all threads returned the same value, and return that single value.
                       Otherwise, a list of each thread's result will be returned.
        :return: Value of MSR.
        :raise: raise content_exceptions.TestSetupError if ITP device is not connected.
        """
        if not self._common_content_lib.is_itp_connected(self.sdp):
            raise content_exceptions.TestSetupError("ITP is not connected")
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.itp.unlock()
            self.sdp.halt()
            msr_value = hex(self.sdp.msr_read(msr_add, squash=True))
        except Exception as e:
            self.itp = ipccli.baseaccess()
            self.itp.forcereconfig()
            self.sdp.itp.unlock()
            self.sdp.halt()
            msr_value = hex(self.sdp.msr_read(msr_add, squash=True))
        finally:
            self.sdp.go()
        return msr_value

    def read_cpuid(self, cpuid_leaf: hex, cpuid_registry: str):
        """
        Attempts to read CPUID instruction from ITP Debugger.
        :param cpuid_leaf: address of MSR to be read.
        :param cpuid_registry: String which specifies the register with the base opcode (eax, ebx, ecx, edx)
        :return: Result of the CPUID command (list if squash is False, int if squash is True)
        :raise: raise content_exceptions.TestSetupError if ITP device is not connected.
        """
        if not self._common_content_lib.is_itp_connected(self.sdp):
            raise content_exceptions.TestSetupError("ITP is not connected")
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.itp.unlock()
            self.sdp.halt()
            msr_value = hex(self.sdp.cpuid(cpuid_registry, cpuid_leaf, 0, squash=True))
        except Exception as e:
            self.itp.forcereconfig()
            self.sdp.itp.unlock()
            self.sdp.halt()
            msr_value = hex(self.sdp.cpuid(cpuid_registry, cpuid_leaf, 0, squash=True))
        finally:
            self.sdp.go()
        return msr_value

class WindowsSGXDriver(SGXProvider):
    """Windows SGX provider"""

    VERIFY_SGX_INSTALL = "powershell.exe Get-Pnpdevice -Class 'softwarecomponent' -STATUS OK -ErrorAction " \
                         "SilentlyContinue"
    INSTALLED_SGX_COMPONENTS = ["Software Guard Extensions Software"]
    LOCAL_ATTESTATION_VERIFY_MESSAGES = ["succeed to load enclaves",
                                         "succeed to establish secure channel",
                                         "Succeed to exchange secure message",
                                         "Succeed to close Session"]
    SGX_CMD_INFO = "Verifying SGX Components"
    WIN_SEARCH_CMD = "powershell.exe (get-childitem '{}' -File {} -recurse).fullname"
    SGX_TEST_DIR = "\sgx_test"
    SGX_TEST_PARM = "-auto"
    SGX_AESM_STATUS = "SGX AESM service entered the running"
    CHECK_AESM_STATUS = 'powershell.exe "Get-EventLog -LogName System'
    PSW_INSTALLED_MATCH = "SGX PSW Version is"
    SGX_ENABLED_STATUS = "SGX has been enabled"
    VERIFY_STARTED_ENCLAVES = "SUCCESS: Load the validation enclave in debug mode"
    SGX_BINARY = "sgx_test.exe"
    WIN_POWERSHELL_CMD = "powershell.exe (get-childitem '{}' -Filter {} -recurse).fullname"
    SGX_APP_TEST_EXE = "App.exe"
    SGX_PSW_INF = "sgx_psw.inf"
    PNP_INSTALL_DRIVER_CMD = "pnputil /add-driver {} /install"
    HYDRA_CMD = "SGXHydraConsoleEx.exe {} {} {} {} >{} 2>{}"
    POWERSHELL_GET_FILE_CONTENT = "powershell Get-Content {} -Raw"
    HYDRA_OUTPUT_FILE = "sgx_hydra_output.txt"
    HYDRA_EXECUTION_FILE = "sgx_hydra_execution_msg.txt"
    SGX_BASE_INF = "sgx_base.inf"
    SGX_MPA_INF = "sgx_mpa.inf"
    INSTALLED_SGX_MPA = "Intel(R) Software Guard Extensions Software Multi-Package Registration"
    VERIFY_SGX_BASE_INSTALL = "powershell.exe Get-Pnpdevice -Class 'system' -FriendlyName '{}' -STATUS OK " \
                              "-ErrorAction SilentlyContinue"
    INSTALLED_SGX_BASE = "Intel(R) Software Guard Extensions Launch Configuration Service"
    SGX_STREAM_APP_EXE = "sgxApp.exe"
    STREAM_APP_DATA = {"Array size": 40000000, "Total memory required": 0.9, "Each kernel will be executed": 3000}
    STREAM_APP_SEARCH_DATA = {"Array size": "\(", "Total memory required": "GiB", "Each kernel will be executed": "times"}
    S5_SEAL_UNSEAL_REBOOT_SUCCESS_MSG = ".*(SUCCESS.*Test sealing and unsealing data across S5 reboot boundary)"
    S5_SEAL_UNSEAL_SHUTDOWN_SUCCESS_MSG = ".*(SUCCESS.*Test sealing and unsealing data across S5 shutdown boundary)"
    S5_REBOOT_SEAL_UNSEAL_MSG = "Successfully sealed and unsealed data across reboot."
    S5_SHUTDOWN_SEAL_UNSEAL_MSG = "Successfully sealed and unsealed data across shutdown."
    EXECUTION_TIMEOUT = 120
    SGX_PSW_INSTALLATION_FILE = "sgx_inf_install.cmd"
    DATE_FORMAT_RE_EXP = "\d+:\d+:\d+:\d+"
    HYDRA_TEST_RUN = "Test ran"

    def __init__(self, log, cfg_opts, os_obj, sdp):
        """
        Create a new Windows SGX Provider object.

        :param log: Logger object to use for output messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration
        :param os_obj: os object
        :param sdp: SiliconDebugProvider
        """
        super(WindowsSGXDriver, self).__init__(log, cfg_opts, os_obj, sdp)

    def check_aesm_running(self):
        """Checks AESM is running

        :raise: raise content_exceptions.TestFail if AESM is not running
        """
        self._log.info("Checks AESM running status")
        fvt_output = self.execute_functional_validation_tool()
        if self.VERIFY_STARTED_ENCLAVES not in fvt_output:
            raise content_exceptions.TestFail("SGX AESM is not running")
        self._log.info("Architectural Enclaves are successfully running on the platform")
        try:
            event_log = self._common_content_lib.execute_sut_cmd(self.CHECK_AESM_STATUS,
                                                                 "Execute the power shell command",
                                                                 self.execution_timeout,
                                                                 cmd_path=os.path.join(
                                                                     self._common_content_lib.C_DRIVE_PATH,
                                                                     self._common_content_lib.WINDOWS_SUT_EVENT_LOG_FOLDER))
            self._log.debug("System Event Log output {}".format(event_log))
        except Exception as ex:
            raise content_exceptions.TestFail("Error while executing the Store windows logs with exception = '{}'"
                                              .format(ex))
        if self.SGX_AESM_STATUS not in event_log:
            raise content_exceptions.TestFail("SGX AESM is not running")
        self._log.info("SGX AESM service is running")

    def check_simple_enclave_creation(self):
        """Checks simple enclave creation"""
        raise NotImplementedError("check_simple_enclave_creation not implemented for windows")

    def install_sdk(self):
        """ Install SGX SDK. """
        self._log.info("Installing SGX SDK")
        self.load_sgx_properites()
        shutil.copy(self.SGX_SDK_BUILD, self._common_content_lib.get_collateral_path())
        self._install_collateral.download_and_copy_zip_to_sut(self.LOCAL_ATTESTATION_PATH, os.path.basename(
            self.SGX_SDK_BUILD))
        self._log.info("Successfully Installed SDK on SUT!")

    def run_enclave_app_test(self, cmd, cwd=None, timeout=60, verify_message=[]):
        """
        Runs the SGX enclave app test

        :param cmd: Command to be executed for enclave app test
        :param cwd: Current working directory
        :param timeout: Time out in seconds
        :param verify_message: List of success or error messages to check against the results.
        :raises: content_exceptions.TestFail - if failed.
        """
        self._log.info("Executing enclave app test. Running command %s", cmd)
        sut_cmd_result = self._os.execute(cmd, timeout, cwd)
        if not sut_cmd_result:
            raise content_exceptions.TestFail("unable to executed the command {}".format(cmd))
        self._log.debug("Enclave app test result : {}".format(sut_cmd_result.stdout))
        self._log.error(sut_cmd_result.stderr)
        for message in verify_message:
            if message not in sut_cmd_result.stdout:
                raise content_exceptions.TestFail("App test results are not as expected")

    def local_attestation(self):
        """
        Checks local attestation enclave creation

        :raises: content_exceptions.TestFail - if failed.
        """
        self._log.info("check local attestation")
        self.check_psw_installation()
        self.install_sdk()
        cmd = self.WIN_SEARCH_CMD.format(self.LOCAL_ATTESTATION_PATH, self.SGX_APP_TEST_EXE)
        self._log.debug("command {}".format(cmd))
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
        self._log.debug("App exe path {}".format(output))
        if not output.strip():
            raise content_exceptions.TestFail("Could not find %s on SUT" % self.SGX_APP_TEST_EXE)
        self.run_enclave_app_test(self.SGX_APP_TEST_EXE, cwd=os.path.dirname(output.strip()),
                                  timeout=self.execution_timeout,
                                  verify_message=self.LOCAL_ATTESTATION_VERIFY_MESSAGES)
        self._log.info("Successfully established a protected channel and exchanged Secret message using enclave to "
                       "enclave function calls")

    def run_semt_app(self, semt_timeout):
        """
        Copy and run semt command in SUT

        :param: semt_timeout execution time for semt command
        :raise: content_exceptions.NotImplementedError
        """
        raise NotImplementedError("Semt app is not implemented for windows")

    def is_psw_installed(self):
        """
        Checks the SGX PSW installed or not and returns the bool value

        :return: True if SGX PSW is installed otherwise False
        """
        str_data = "SGX PSW"
        return self.is_driver_installed(self.VERIFY_SGX_INSTALL, self.INSTALLED_SGX_COMPONENTS ,str_data )

    def check_psw_installation(self):
        """
        Checks SGX PSW installation

        :raise: raise content_exceptions.TestFail if SGX PSW is not installed
        """
        self._log.info("Check SGX PSW installation")
        if self.is_psw_installed():
            self._log.info("SGX PSW is installed and verified successfully!")
            return
        self._log.info("SGX PSW is not installed, installing it")
        self.install_psw()
        if not self.is_psw_installed():
            raise content_exceptions.TestFail("SGX PSW verification failed, "
                                              "looks like SGX PSW not installed")
        self._log.info("SGX PSW is installed and verified successfully")

    def install_psw(self):
        """
        Install PSW on Windows

        :return: True if installation process is successful False otherwise
        """
        self.load_sgx_properites()
        str_psw = "SGX_PSW"
        self._log.info("SGX_PSW execution path is %s" % self.get_sgx_executable_dir(self.PSW_INSTALL_BINARY_MATCH))
        sut_cmd_result = self._os.execute(self.PSW_INSTALL_BINARY_MATCH, self.execution_timeout,
                                          self.get_sgx_executable_dir(self.PSW_INSTALL_BINARY_MATCH))
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        self.install_driver(self.SGX_PATH, self.SGX_PSW_INF, str_psw)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._os.wait_for_os(self.reboot_timeout)

    def load_sgx_properites(self):
        """Loads the SGX properties"""
        os_type = self._os.os_type.lower()
        self.SGX_PATH = self._common_content_configuration \
            .get_security_sgx_params(os_type, "SGX_PATH", None)
        self.FVT_PATH = self._common_content_configuration \
            .get_security_sgx_params(os_type, "FVT_PATH", None)
        self.PSW_INSTALL_BINARY_MATCH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "PSW_INSTALL_BINARY_MATCH", None)
        self.SGX_FVT_ZIP = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_FVT_ZIP", None)
        self.SGX_FVT_BINARY = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_FVT_BINARY", None)
        self.SGX_SDK_BUILD = self._common_content_configuration.get_security_sgx_params(
            os_type, "SGX_SDK", None)
        self.SGX_APPS_DIR = self._common_content_configuration.get_security_sgx_params(
            os_type, "SGX_APPS_DIR", None)
        self.LOCAL_ATTESTATION_PATH = self.SGX_APPS_DIR + "\\" + str(os.path.basename(self.SGX_SDK_BUILD).split(".")[0])
        self.SGX_FVT_PSW_VERIFY_CMD = "%s -l -v -" \
                                      "skip_power_tests" % \
                                      self.SGX_FVT_BINARY
        self.SGX_STREAM_APP_TEST_TIMEOUT_IN_SECS = self._common_content_configuration \
                            .get_security_sgx_params(os_type, "SGX_STREAM_APP_TEST_TIMEOUT_IN_SECS", None)
        self.SGX_S5_REBOOT_CMD = "echo y | %s -l -v -skip_s3 -skip_s4  -skip_s5_shutdown -auto_power_tests &" % \
                                 self.SGX_FVT_BINARY
        self.SGX_S5_SHUTDOWN_CMD = "echo y | %s -l -v -skip_s3 -skip_s4 -skip_s5_reboot -auto_power_tests &" % \
                                   self.SGX_FVT_BINARY
        self.SGX_SDK_INSTALLER = self._common_content_configuration.get_security_sgx_params(os_type,
                                                                                            "SGX_SDK_INSTALLER",
                                                                                            None)
        self.PSW_SGX_APP_INSTALLER = self._common_content_configuration.get_security_sgx_params(os_type,
                                                                                                "PSW_SGX_APP_INSTALLER",
                                                                                                None)
        # gets fvt tool directory in sut
        self.get_sgx_fvt_dir()

    def get_sgx_executable_dir(self, search_file):
        """
        searches for file specifed in sgx functional validation directory

        :return: directory path of the where the search file
        :raise: raise content_exceptions.TestFail if search file does not exists
        """
        self._log.info("Search file %s in sgx directory" % search_file)
        cmd = self.WIN_SEARCH_CMD.format(self.SGX_PATH, search_file)
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
        self._log.debug(output)
        if not output.strip():
            raise content_exceptions.TestFail("Could not find %s on SUT" % search_file)
        self._log.debug("Search file directory path is %s" % os.path.dirname(output.strip()))
        return os.path.dirname(output.strip())

    def check_sgx_tem_base_test(self):
        """
        Checks the SGX TEM Base Test Case

        :raise: raise content_exceptions.TestFail if sgx test fails.
        """
        self._log.info("Checking SGX TEM Base Test Case")
        self.load_sgx_properites()
        self.check_psw_installation()
        if not self.run_sgx_app_test():
            raise content_exceptions.TestFail("{} have failures".format(self.SGX_TEST))

    def run_sgx_app_test(self):
        """
        Runs the SGX app test

        :return : True if the SGX app test planed and success is same other wise False
        :raise: raise content_exceptions.TestFail if planned does not match with success
        """
        self._log.info("Run SGX app test")
        sgx_app_dir = self.get_sgx_executable_dir(self.SGX_BINARY)
        self._log.debug("SGX_PATH execution path is %s" % sgx_app_dir)
        sut_cmd_result = self._os.execute(self.SGX_BINARY + "  " + self.SGX_TEST_PARM, self.execution_timeout,
                                          sgx_app_dir)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        planned_regex = re.compile("Planed:\s(\d+)")
        planned_list = planned_regex.findall(sut_cmd_result.stdout)
        if not len(planned_list):
            raise content_exceptions.TestFail("{} output is not expected".format(self.SGX_BINARY))
        planned = planned_list[0].strip()
        self._log.info("Planned tests are: %s", planned)
        success_regex = re.compile("Success:\s(\d+)")
        success_list = success_regex.findall(sut_cmd_result.stdout)
        if not len(success_list):
            raise content_exceptions.TestFail("{} output is not expected".format(self.SGX_BINARY))
        success = success_list[0].strip()
        self._log.info("Success tests are: %s", success)
        return success == planned

    def execute_functional_validation_tool(self):
        """
        Execute FVT and verify SGX is enabled

        :return: output if validation process is successful otherwise Fails
        :raise: content_exceptions.TestFail if SGX is not enabled
        """
        self.load_sgx_properites()
        self.check_psw_installation()
        self._log.info("SGX_FVT execution path is %s" % self.FVT_PATH)
        cmd = self.WIN_POWERSHELL_CMD.format(self.FVT_PATH, self.SGX_FVT_BINARY)
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
        self._log.debug("SGX FVT full path {}".format(output.strip()))
        dir_name = os.path.dirname(output.strip())

        sut_cmd_result = self._os.execute(self.SGX_FVT_PSW_VERIFY_CMD, self.execution_timeout, cwd=dir_name)
        self._log.debug("FVT Output {}".format(sut_cmd_result.stdout))
        if self.PSW_INSTALLED_MATCH and self.SGX_ENABLED_STATUS not in sut_cmd_result.stdout:
            raise content_exceptions.TestFail("PSW version not found in SGX FVT execution")
        self._log.info("SGX is enabled and PSW version has been found")
        return sut_cmd_result.stdout

    def verify_lcp_locked_mode(self):
        """
        Run command SGXFunctionalValidationTool.exe -l -v -skip_power_tests -lcp_legacy_locked and
        verify the output for LCP Legacy Lock mode and check MSR bit 0 value in MSR_OPTIN_FEATURE_CONTROL value

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("sgx lcp locked mode not implemented for windows")

    def is_sgx_disabled_cpuid(self):
        """
        Check for cpuid output whether all the cpu capability is SGX supported.

        :return: True cpu capability is supported else false
        """
        raise NotImplementedError("sgx disable cpuid local_attestation not implemented for windows")

    def is_sgx_enabled_cpuid(self):
        """
        Check for cpuid output whether all the cpu capability is SGX supported.

        :return: True if cpu capability is supported else false
        """
        raise NotImplementedError("SGX enabled cpuid local_attestation not implemented for windows")

    def run_hydra_test(self, test_duration=60, enclave_mb="128", num_enclave_threads="12", num_regular_threads="12"):
        """
        Copies hydra test tool in SUT and runs hydra test for given time

        :param test_duration: time duration in seconds to run the test, :type: int
        :param enclave_mb: Enclave MB, :type: str
        :param num_enclave_threads: Enclave threads in number, :type: str
        :param num_regular_threads: Regular Threads in number, :type: str
        :raise: content exception if the sgx hydra test fails to run for specified duration or any error
                found during the test execution.
        """
        binary_path = "bin"
        execution_timeout = 20
        # The last execution time wrote in the output file doesn't round with 30seconds hence the exit criteria will fail.
        adjusted_test_duration = test_duration + 30
        self._log.info("SGX Hydra console application execution started for the duration {}".format(test_duration))
        hydra_cmd = self.HYDRA_CMD.format(enclave_mb, num_enclave_threads, num_regular_threads, test_duration,
                                          self.HYDRA_OUTPUT_FILE, self.HYDRA_EXECUTION_FILE)
        hydra_test_path = self._install_collateral.copy_sgx_hydra_windows()
        hydra_test_path = os.path.join(hydra_test_path, binary_path)
        self._log.debug("SGX Hydra tool installed location is {}".format(hydra_test_path))
        try:
            self._os.execute(hydra_cmd, (execution_timeout + int(test_duration)), cwd=hydra_test_path)
        except OsCommandTimeoutException as e:
            if "timed out" in str(e):
                self._log.info("SGX Hydra console execution is complete")
                self.check_sgx_hydra_exec_status(hydra_test_path, test_duration, self.HYDRA_EXECUTION_FILE)
                return
            else:
                raise content_exceptions.TestFail("Unable to execute SGX Hydra console command {}".format(e))
        self.check_sgx_hydra_exec_status(hydra_test_path, test_duration, self.HYDRA_EXECUTION_FILE)

    def perform_s5_reboot_test(self, socket):
        """
        This method Performs s5 sealing reboot test.

        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def verify_seal_unseal_reboot_test(self):
        """
        Verify seal/unseal reboot test is successful

        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def perform_s5_shutdown_test(self, socket):
        """
        This method Performs s5 sealing Shutdown test.

        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def verify_seal_unseal_shutdown_test(self):
        """
        Verify seal/unseal shutdown test is successful

        :raise: content_exceptions.NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def verify_sgx_content(self, time_duration=60, enclave_mb="128", num_enclave_threads="12",
                           num_regular_threads="12"):
        """
        Verify SGX content by running SGX hydra app for Windows

        :param time_duration: time duration in seconds to run the test, :type: int
        :param enclave_mb: Enclave MB, :type: str
        :param num_enclave_threads: Enclave threads in number, :type: str
        :param num_regular_threads: Regular Threads in number, :type: str
        """
        self.run_hydra_test(time_duration, enclave_mb, num_enclave_threads, num_regular_threads)

    def check_sgx_hydra_exec_status(self, hydra_test_path: str, test_duration: int, output_file: str) -> bool:
        """
        Validate hydra test output file

        :param hydra_test_path: hydra test tool path
        :param test_duration: time duration in seconds for hydra test run
        :param output_file: output file of hydra test
        :return: True if SGX Hydra console ran successfully
        :raise: content_exceptions.TestFail if SGX Hydra test console did not execute completely
        """
        time.sleep(60)
        self.copy_sgx_hydra_log(hydra_test_path, self.HYDRA_OUTPUT_FILE)
        dest_hydra_execution_file = self.copy_sgx_hydra_log(hydra_test_path, output_file)
        hydra_test_duration = timedelta(seconds=test_duration)
        self._log.info(f"Hydra test execution duration is {hydra_test_duration}")
        hydra_test_executed_duration = self.get_hydra_execution_time(dest_hydra_execution_file)
        if hydra_test_executed_duration >= hydra_test_duration:
            self._log.info(f"SGX Hydra console executed for total duration of {hydra_test_executed_duration}")
            return True
        else:
            raise content_exceptions.TestFail("SGX Hydra test console did not execute completely")

    def perform_s5_shutdown_boundary(self, phy, socket=None):
        """
        This method Performs s5 sealing reboot test.

        :param phy: PHY provider for SXSTATE
        :param socket: Socket number where the test is running.
        :raise: content_exceptions.NotImplementedError
        """
        self._log.info("Starting Sealing and Unsealing data across S5 shutdown boundary")
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SGX_S5_SHUTDOWN_CMD, self.SGX_S5_SHUTDOWN_CMD,
                                                              self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self.verify_s5_shutdown_power_state(phy, self.EXECUTION_TIMEOUT)
        self._log.debug("{} command has been sent to OS.{}".format(self.SGX_S5_SHUTDOWN_CMD, fvt_result))
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._os.wait_for_os(self.reboot_timeout)

    def verify_s5_shutdown_power_state(self, phy, wait_time):
        """
        Verify if the system has shutdown S5 power state

        :param phy: PHY provider for SXSTATE
        :param wait_time: wait time for system to enter S5 state
        :raise: TestFail SUT did not entered into S5 state
         """
        start_time = time.time()
        self._log.info("Checking for S5 power state")
        while time.time() - start_time <= wait_time:
            if not self._common_content_lib.check_os_alive():
                power_state = phy.get_power_state()
                if power_state != PowerStates.S5:
                    continue
                else:
                    return
        power_state = phy.get_power_state()
        raise content_exceptions.TestFail(
            "SUT did not entered into {} state, actual state is {}".format(PowerStates.S5, power_state))

    def verify_seal_unseal_shutdown_boundary(self):
        """
        Verify seal/unseal shutdown boundary is successful

        :raise: content_exceptions if S5 shutdown sealing/unsealing test is failed
        """
        self._log.info("Verifying S5 shutdown sealing/unsealing")
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SGX_S5_SHUTDOWN_CMD, self.SGX_S5_SHUTDOWN_CMD,
                                                              self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug("{} command output is {}".format(self.SGX_S5_SHUTDOWN_CMD, fvt_result))
        search_output1 = re.search(self.S5_SEAL_UNSEAL_SHUTDOWN_SUCCESS_MSG, fvt_result)
        search_output2 = re.search(self.S5_SHUTDOWN_SEAL_UNSEAL_MSG, fvt_result)
        if not (search_output1 and search_output2):
            raise content_exceptions.TestFail("S5 shutdown sealing/unsealing boundary is failed")
        self._log.info("S5 shutdown sealing/unsealing is successfully verified")

    def check_mp_registration_installation(self):
        """
        Checks SGX multi package registration installation

        :raise: content_exceptions.TestFail if SGX multi package registration is not installed
        """
        str_ma = "SGX multi package registration"
        self._log.info("Check SGX multi package registration installation")
        if self.is_driver_installed(self.VERIFY_SGX_INSTALL, self.INSTALLED_SGX_MPA, str_ma):
            self._log.info("SGX multi package registration is installed and verified successfully!")
            return
        self._log.info("SGX multi package registration is not installed, installing it")
        self.load_sgx_properites()
        self.install_driver(self.SGX_REG_AGENT_PATH, self.SGX_MPA_INF, str_ma)
        if not self.is_driver_installed(self.VERIFY_SGX_INSTALL, self.INSTALLED_SGX_MPA, str_ma):
            raise content_exceptions.TestFail("SGX multi package Registration verification failed, "
                                              "looks like SGX MPA not installed")
        self._log.info("SGX multi package Registration is installed and verified successfully")

    def check_sgx_base_installation(self):
        """
        Checks  SGX base installation

        :raise: content_exceptions.TestFail if SGX base is not installed
        """
        self._log.info("Check SGX base installation")
        str_base = "SGX BASE"
        if self.is_driver_installed(self.VERIFY_SGX_BASE_INSTALL, self.INSTALLED_SGX_BASE, str_base ):
            self._log.info("SGX base is installed and verified successfully!")
            return
        self._log.info("SGX base is not installed, installing it")
        self.load_sgx_properites()
        self.install_driver(self.SGX_PATH, self.SGX_BASE_INF, str_base)
        if not self.is_driver_installed(self.VERIFY_SGX_BASE_INSTALL, self.INSTALLED_SGX_BASE, str_base):
            raise content_exceptions.TestFail("SGX base verification failed, "
                                              "looks like SGX PSW not installed")
        self._log.info("SGX base is installed and verified successfully")

    def is_driver_installed(self, execute_cmd, installed_components, str_data):
        """
        Checks the driver installed or not and returns the bool value

        :param execute_cmd: Power shell command to find the installed string.
        :param installed_components: String after successfully installation
        :param str_data: Driver name
        :return: True if driver is installed False otherwise
        """
        self._log.info("Check if {} is installed or not".format(str_data))
        cmd_output = self._os.execute(execute_cmd.format(installed_components), self.execution_timeout)
        self._log.debug(cmd_output.stdout)
        self._log.debug(cmd_output.stderr)
        if not cmd_output.stdout.strip():
            return False
        return True

    def install_driver(self, driver_directory, inf_file_name, str_data):
        """
        Install driver on Windows

        :param driver_directory: Driver package path
        :param inf_file_name: executable file name
        :param str_data: Driver name
        :return: True if installation process is successful False otherwise
        """
        cmd = self.WIN_SEARCH_CMD.format(driver_directory, inf_file_name)
        search_output = str(self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout))
        self._log.debug("File directory path is {}".format(search_output))
        if not search_output.strip():
            raise content_exceptions.TestFail("Could not find %s on SUT" % inf_file_name)

        install_cmd_output = self._common_content_lib.execute_sut_cmd(
            self.PNP_INSTALL_DRIVER_CMD.format(search_output),
            self.PNP_INSTALL_DRIVER_CMD.format(search_output),
            self.execution_timeout)
        install_cmd_output = str(install_cmd_output)
        self._log.debug("{} installation {}".format(str_data, install_cmd_output))
        if not install_cmd_output.strip():
            return False
        return True

    def run_sgx_stream_app(self, sgx_stream_timeout):
        """
        To copy and  install sgx stream app in SUT from artifactory
        To run the command sgxApp.exe for given time (6 hrs) without crashing and check the array size,
        required memory, and  execution loop count.
        """
        self._log.info("Copying sgx stream app from host and unzipping in SUT")
        sgx_stream_path = self._install_collateral.copy_sgx_stream_tool_windows()
        file_path = self.get_file_path(sgx_stream_path, self.SGX_STREAM_APP_EXE)
        output = self.execute_sgx_app_test(os.path.dirname(file_path), sgx_stream_timeout)
        self.verify_sgx_app_test_output(output)

    def get_file_path(self, foldername, filename):
        """
        To find the command file path

        :param foldername: Stream app tool path
        :param filename: executable file name
        :return: command to be executed
        """
        cmd = self.WIN_SEARCH_CMD.format(foldername, filename)
        self._log.debug("command {}".format(cmd))
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
        self._log.debug("App exe path {}".format(output))
        self._log.debug("Executing Directory {}".format(os.path.dirname(output.strip())))
        return output.strip()

    def execute_sgx_app_test(self, tool_path, sgx_stream_timeout):
        """
        To copy and  install sgx stream app in SUT from artifactory
        To run the command sgxApp.exe for given time (6 hrs) without crashing and check the array size,
        required memory, and  execution loop count.

        :param tool_path:Stream app tool path
        :param sgx_stream_timeout: execution time for sgx stream command
        :return: Installed command out
        """
        install_cmd_output = self._common_content_lib.execute_sut_cmd(self.SGX_STREAM_APP_EXE,
                                                                      self.SGX_STREAM_APP_EXE,
                                                                      sgx_stream_timeout,
                                                                      tool_path.strip())
        install_cmd_output = str(install_cmd_output)
        self._log.debug("installation {}".format(install_cmd_output))
        return install_cmd_output

    def verify_sgx_app_test_output(self, installed_cmd_output):
        """
        To find the array size, required memory, and execution loop count. Verifying the actual output with expected
        output.

        :param: installed_cmd_output: Installed command output
        :raise: ContentException.TestFail if sgx stream aap actual value is not equal to expected sgx stream app value
        """
        stream_data = {}
        search_pattern = r'(?<={0}).*?(?={1})'
        number_pattern = r'[0-9]*[.,]{0,1}[0-9]'
        stream_app_flag = False
        for search_key, search_value in self.STREAM_APP_SEARCH_DATA.items():
            pattern = search_pattern.format(search_key, search_value)
            output = re.search(pattern, installed_cmd_output)
            data = re.findall(number_pattern, output.group())
            if not data[-1]:
                stream_app_flag = True
                self._log.error("{} string is not found in execution output".format(search_key))
            self._log.info("{} string is found in execution output".format(search_key))
            stream_data[search_key] = float(data[-1])
        if stream_app_flag:
            raise content_exceptions.TestFail("string data is not found!!")
        if stream_data != self.STREAM_APP_DATA:
            raise content_exceptions.TestFail(
                "SGX stream actual value {} is as expected value {} did not match".format(stream_data,
                                                                                          self.STREAM_APP_DATA))
        self._log.info(
            "SGX stream actual value {} is as expected value {}".format(stream_data, self.STREAM_APP_DATA))

    def get_sgx_fvt_dir(self):
        """
        Get sgx functional validation binary directory

        :raise: TestFail if could not found fvt binary match in the sgx path
        """
        self._log.info("SGX_FVT execution path is %s" % self.FVT_PATH)
        cmd = self.WIN_POWERSHELL_CMD.format(self.FVT_PATH, self.SGX_FVT_BINARY)
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
        self.SGX_FVT_DIR = os.path.dirname(output.strip())
        self._log.debug("SGX FVT Directory is {}".format(self.SGX_FVT_DIR))

    def perform_s5_reboot_boundary(self, socket=None):
        """
        This method Performs s5 sealing reboot boundary test.

        :param socket: Socket number where the test is running.
        :raise: content_exceptions if Fail to start S5 sealing reboot boundary test
        """
        self._log.info("Starting S5 sealing reboot test")
        sgx_s5_reboot_cmd = self.SGX_S5_REBOOT_CMD.format(self.SGX_FVT_DIR)
        self._common_content_lib.execute_sut_cmd(sgx_s5_reboot_cmd, self.SGX_S5_REBOOT_CMD,
                                                 self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.info("'{}' command has been sent to OS.".format(sgx_s5_reboot_cmd))
        self._log.info("Wait for the OS ...")
        self._os.wait_for_os(self.reboot_timeout)
        self._log.info("S5 sealing reboot test was started successfully")

    def verify_seal_unseal_reboot_boundary(self):
        """
        Verify seal/unseal reboot boundary is successful

        :raise: content_exceptions if S5 reboot sealing/unsealing boundary is failed
        """
        self._log.info("Verifying S5 reboot sealing/unsealing")
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SGX_S5_REBOOT_CMD, self.SGX_S5_REBOOT_CMD,
                                                              self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.info("{} command output is {}".format(self.SGX_S5_REBOOT_CMD, fvt_result))
        output1 = re.search(self.S5_SEAL_UNSEAL_REBOOT_SUCCESS_MSG, fvt_result)
        output2 = re.search(self.S5_REBOOT_SEAL_UNSEAL_MSG, fvt_result)
        if not (output1 and output2):
            raise content_exceptions.TestFail("S5 reboot sealing/unsealing boundary is failed")
        self._log.info("S5 reboot sealing/unsealing is successfully verified")

    def copy_sgx_hydra_log(self, hydra_folder_path: str, hydra_output_file: str) -> str:
        """
        Function to copy the SGX Hydra log from sut to Host log folder.

        :param hydra_folder_path: Hydra Tool Directory in the sut
        :param hydra_output_file: Hydra output file.
        :raise: content_exceptions TestFails if the hydra test logs are not present.
        :return: path of the copied file.
        """
        hydra_source_file_path = self.get_file_path(hydra_folder_path, hydra_output_file)
        hydra_destination_file_path = os.path.join(self.log_dir, hydra_output_file)
        self._os.copy_file_from_sut_to_local(hydra_source_file_path, hydra_destination_file_path)
        self._log.info("Successfully copied the file from sut {}".format(hydra_output_file))
        return hydra_destination_file_path

    def execute_fvt_and_app_test(self) -> None:
        """
        This function install SGX PSW and SGX FVT tool installation, run sgx test app.

        :raise: content_exceptions.TestFail if Sgx Run App test has failures.
        :return: None
        """
        self.check_psw_installation()
        self.execute_functional_validation_tool()
        if not self.run_sgx_app_test():
            raise content_exceptions.TestFail("./sgx_app -auto have failures")

    def get_hydra_execution_time(self, hydra_execution_file: str) -> timedelta:
        """
        Function searches the SGX Hydra file to get the execution time.

        :param hydra_execution_file: Path of the SGX Hydra execution file.
        :raise: content_exceptions.TestFail if SGX Hydra console did not execute completely.
        :return: Total execution time of the Hydra in the form of timedelta obj.
        """
        date_format = "%H:%M:%S"
        self._log.info("Extracting SGX Hydra execution time from the Hydra log file {}".format(hydra_execution_file))
        hydra_execution_time = None
        with open(hydra_execution_file, "r") as file_obj:
            for line in file_obj.readlines():
                if self.HYDRA_TEST_RUN in line:
                    hydra_execution_time = re.findall(self.DATE_FORMAT_RE_EXP, line)
                    if hydra_execution_time:
                        self._log.debug("Hydra execution time {}".format(hydra_execution_time))
        if not hydra_execution_time:
            raise content_exceptions.TestFail("Unable to locate Test ran str in the sgx hydra output file"
                                              "SGX Hydra console did not execute completely")
        exe_time = datetime.strptime(hydra_execution_time[0].replace("00:", "", 1), date_format)
        exe_time = timedelta(hours=exe_time.hour, minutes=exe_time.minute, seconds=exe_time.second)
        self._log.info(f"Total execution of Hydra tool is {exe_time}")
        return exe_time

class LinuxSGXDriver(SGXProvider):
    """Linux SGX provider object"""

    FIND_CMD = "find . -type f -name '{}'"
    READ_LINK_CMD = "readlink -f {}"
    SGX_ENABLED_STR = "SGX has been enabled"
    PSW_INSTALL_CMD = "tar -xzvf %s"
    PROXY = 'proxy'
    YUM_CONF_CMD = "cat /etc/yum.conf"
    DKMS_INSTALL_PACKAGES = "sudo yum install dkms -y"
    EXECUTION_TIMEOUT = 120
    SHOW_FVT_OUTPUT = "cat SgxFunctionalValidationToolOutput.txt"
    S5_SEAL_REBOOT_MSG = "Starting S5 Sealing Reboot Test on socket {}"
    S5_SEAL_UNSEAL_REBOOT_SUCCESS_MSG = ".*(SUCCESS.*Test sealing and unsealing data across S5 reboot boundary)"
    S5_SEAL_SHUTDOWN_MSG = "Starting S5 Sealing Shutdown Test on socket {}"
    S5_SEAL_UNSEAL_SHUTDOWN_SUCCESS_MSG = ".*(SUCCESS.*Test sealing and unsealing data across S5 shutdown boundary)"
    S5_REBOOT_SEAL_UNSEAL_MSG = "Successfully sealed and unsealed data across reboot."
    S5_SHUTDOWN_SEAL_UNSEAL_MSG = "Successfully sealed and unsealed data across shutdown."
    LCP_LOCKED_MODE_STR = "Successfully tested LCP legacy locked mode."
    LCP_LOCKED_MODE_SUCCESS_MSG = ".*(SUCCESS.*Test LCP legacy locked)"
    LCP_LOCKED_MSR_VALUE = "MSR_OPTIN_FEATURE_CONTROL value"
    UNINSTALL_PSW_CMD = ["yum remove libsgx* -y", "yum remove sgx-aesm* -y"]
    LCP_UNLOCKED_MODE_STR = "Successfully tested LCP unlocked mode"
    LCP_UNLOCKED_MODE_SUCCESS_MSG = ".*(SUCCESS.*Test LCP unlocked)"
    LCP_UNLOCKED_MSR_VALUE = {"MSR_IA32_SGX_LE_PUBKEYHASH_0 value": "14caea7de719d783",
                              "MSR_IA32_SGX_LE_PUBKEYHASH_1 value": "43774d2af6baf670",
                              "MSR_IA32_SGX_LE_PUBKEYHASH_2 value": "9c0f0269db99c803",
                              "MSR_IA32_SGX_LE_PUBKEYHASH_3 value": "9ecec708fc1dee70"}
    REGEX_CMD_FOR_SOCKET0 = "Socket\[0\]\.Prids_0=(.*)"
    REGEX_CMD_FOR_SOCKET1 = "Socket\[1\]\.Prids_0=(.*)"

    def __init__(self, log, cfg_opts, os_obj, sdp):
        super(LinuxSGXDriver, self).__init__(log, cfg_opts, os_obj, sdp)
        self.kernel = self._common_content_lib.get_linux_kernel()
        self.PSW_INSTALL_PACKAGES = "echo y | sudo yum --nogpgcheck install libsgx-epid libsgx-uae-service libsgx-launch libsgx-urts"
        self.PSW_INSTALLED_MATCH = "SGX PSW is installed"
        self.VERIFY_STARTED_ENCLAVES = ["Starting Intel(R) Architectural Enclave Service Manager",
                                        "Started Intel(R) Architectural Enclave Service Manager"]
        self.SGX_AESM_STATUS = "SGX AESM service is running"
        self.ENCLAVE_VERIFICATION_MESSAGE = "SampleEnclave successfully returned"
        self.LOCAL_ATTESTATION_VERIFY_MESSAGES = ["succeed to load enclaves",
                                                  "succeed to establish secure channel",
                                                  "Succeed to exchange secure message",
                                                  "Succeed to close Session"]
        self.SEAL_UNSEAL_VERIFY_MESSAGES = ["Sealing data succeeded", "Unseal "
                                                                      "succeeded"]

        self.SGX_APP_TEST_RESULTS = "Planed: 7   Success: 7   Fail: 0  Ignore: 0"
        self.AESM_RESTART_CMD = "sudo usermod -a -Groot aesmd;sudo service aesmd restart"
        self.RHEL_REQUIREMENTS = ["yum clean all", "yum makecache"]
        self.RHEL_INSTALL_REQUIREMENTS = ["protobuf", "yum-utils", "openssl-devel libcurl-devel protobuf*",
                                  "yum-utils.noarch", "screen"]
        self.SEMT_CMD = "./semt -S2 1024 1024"
        self.SEMT_GREP = "ps -ef | grep semt"
        self.SEMT_KILL = "pkill semt"
        self.SEMT_STR = "semt"
        self.STREES_APP_STR= "stressapptest"
        self.STRESS_APP_GREP = "ps -ef | grep {}"
        self.PRMRR_BASES_LIST = [0x2a0, 0x2a1, 0x2a2, 0x2a3, 0x2a4, 0x2a5, 0x2a6, 0x2a7]
        self.PRMRR_DEFAULT_VALUE = '0x0'
        self.SGX_HYDRA = "SGXHydra"
        self.HYDRA_GREP = "ps -ef | grep SGXHydra"
        self.HYDRA_FILE = "hydra_output.txt"
        self.HYDRA_CMD = "./SGXHydra {} {} {} {} > {}"
        self.MAKEFILE = "Makefile"
        self.MAKE_SUCESS_STRING = "The project has been built in debug hardware mode"
        self.STRING_REPLACEMENT_CMD = "sed -i 's/Enclave\_Config\_File \:\= " \
                                      "Enclave\/Enclave.config.xml/Enclave\_Config\_File " \
                                      "\:\= Enclave\/config.04.xml/' {}"
        self.CAT_CMD = "cat {}"
        self.SEMT_CMD_SGXI = "timeout {} ./semt -S0 4096 >& semt_output.txt"
        self.ENCLAVE_CONFIG_FILE_CHANGE =  "sed -i 's/^  <HeapMaxSize>.*/<HeapMaxSize>0x10000000<\/HeapMaxSize>/g' " \
                              "Enclave.config.xml"
        self.MAKE_CLEAN_CMD = "make clean"
        self.GREP_ALLOCATED_MEM_CMD = "grep -ir 'allocate' semt_output.txt | grep -oP '(?<=allocate )[^ ]*'"
        self.ENCLAVE_PATH = "Enclave"
        self.MEM_SIZE = 4000
        self.MP_RPM_LIST = ["libsgx-ra-network-{}*.el8.x86_64.rpm", "libsgx-ra-uefi-{}*.el8.x86_64.rpm",
                            "sgx-ra-service-{}*.el8.x86_64.rpm"]
        self.VERIFY_MP_REGISTRATION_INSTALL = [
            "Registration Flow - PLATFORM_ESTABLISHMENT or TCB_RECOVERY passed successfully",
            "Registration Flow - Registration status indicates registration is complete.  Nothing to do."]
        self.MP_REGISTRATION_REPO = ["libsgx-ra-network.x86_64", "libsgx-ra-uefi.x86_64", "sgx-ra-service.x86_64"]
        self.MPA_REGISTRATION_LOG_CMD = "cat /var/log/mpa_registration.log"
        self.ATTESTATION_MAKE_CMD = "make SGX_DEBUG=1"
        self.SGX_TEST_SERVER_CMD = "sgxcrossproctestserver"
        self.SGX_PROC_TEST_CMD = "sgxcrossproctest"
        self.SGX_ATTESTATION_CMD = "stdbuf -oL ./{} > stdout_{}.log"
        self.PROCID_CMD = "pidof {}"
        self.KILL_CMD = "kill {}"
        self.TEST_SERVER_EXPECTED_OUTPUT = "Server is ON"
        self.PROC_TEST_EXPECTED_OUTPUT = ["Test1: PASS", "Test2: PASS", "Test3: PASS", "Test4: PASS"]
        self.pnpwls_master_path: str = None

    def run_make_command(self, cwd=None, timeout=60):
        """Runs the make command but it will not throw any error"""
        self._log.info("Running make command")
        sut_cmd_result = self._os.execute("make", timeout, cwd)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        return sut_cmd_result.stdout

    def load_sgx_properites(self):
        """Loads the SGX properties"""
        os_type = self._os.os_type.lower()
        linux_flavour = self._common_content_lib.get_linux_flavour()
        self._log.debug("load sgx properties")
        self._log.debug("linux flavour is %s", linux_flavour)
        if not linux_flavour:
            raise content_exceptions.TestFail("could not get the linux flavour")
        sub_type = "%s_%s_KERNEL"
        if "intel-next" not in self.kernel:
            sub_type = sub_type % (LinuxDistributions.RHEL, "BASE")
        else:
            sub_type = sub_type % (LinuxDistributions.RHEL, "NXT")

        self.SGX_PATH = self._common_content_configuration \
            .get_security_sgx_params(os_type, "SGX_PATH", sub_type)
        self.SGX_SDK = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_SDK", sub_type)
        self.SIMPLE_ENCLAVE_PATH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SIMPLE_ENCLAVE_PATH", sub_type)
        self.LOCAL_ATTESTATION_PATH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "LOCAL_ATTESTATION_PATH", sub_type)
        self.PSW_INSTALL_BINARY_MATCH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "PSW_INSTALL_BINARY_MATCH", sub_type)
        self.SGX_FVT_BINARY = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_FVT_BINARY", sub_type)
        self.SGX_FVT_ZIP = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_FVT_ZIP", sub_type)

        self.SGX_FVT_PSW_VERIFY_CMD = "./%s -l -v -" \
                                      "skip_power_tests" % \
                                      self.SGX_FVT_BINARY
        self.PSW_LOCAL_REPO_NAME = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "PSW_LOCAL_REPO_NAME", sub_type)
        self.SGX_SDK_BINARY_MATCH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_SDK_BINARY_MATCH", sub_type)
        self.SDK_ADD_ENVIRONMENT = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SDK_ADD_ENVIRONMENT", sub_type)
        self.SEAL_UNSEAL_PATH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SEAL_UNSEAL_PATH", sub_type)

        self.PSW_ZIP = self._common_content_configuration.get_security_sgx_params(
            os_type, "PSW_ZIP", sub_type)
        self.MP_REGISTRATION_ZIP = self._common_content_configuration.get_security_sgx_params(
            os_type, "MP_REGISTRATION_ZIP", sub_type)
        self.MP_VERSION_NUMBER = self._common_content_configuration.get_security_sgx_params(
            os_type, "MP_VERSION_NUMBER", sub_type)
        # copies psw tool to sut
        self.copy_psw_tool()
        # copies fvt tool to sut
        self.copy_fvt_tool()
        # gets psw directory in sut
        self.get_psw_dir()
        # gets fvt tool directory in sut
        self.get_sgx_fvt_dir()

        self._log.debug("psw directory Inside Property file {}".format(self.PSW_DIR))
        self._log.debug("PSW_LOCAL_REPO_NAME Inside Property file {}".format(self.PSW_LOCAL_REPO_NAME))
        self.PSW_ADD_REPO = "sudo yum-config-manager --add-repo file://" + \
                            self.PSW_DIR + "/" + \
                            os.path.splitext(self.PSW_LOCAL_REPO_NAME)[0]
        self._log.info("add repo path {}".format(self.PSW_ADD_REPO))
        # install the psw repos
        self.install_psw_repo()
        self.SGX_S5_REBOOT_CMD = "./%s -l -v -skip_s3 -skip_s4  -skip_s5_shutdown -auto_power_tests &" % \
                                 self.SGX_FVT_BINARY

        self.SGX_S5_SHUTDOWN_CMD = "./%s -l -v -skip_s3 -skip_s4 -skip_s5_reboot -auto_power_tests &" % \
                                   self.SGX_FVT_BINARY
        self.LCP_LEGACY_LOCKED_MODE_CMD = "./%s -l -v -skip_power_tests -lcp_legacy_locked" % \
                                   self.SGX_FVT_BINARY
        self.LCP_LEGACY_UNLOCKED_MODE_CMD = "./%s -l -v -skip_power_tests -lcp -ignore_le_key_check" % \
                                            self.SGX_FVT_BINARY

    def copy_fvt_tool(self):
        """Copies SGX Functional Validation Tool to SUT"""
        self._log.info("Copy fvt tool")
        path = os.path.splitext(os.path.basename(self.SGX_FVT_ZIP))[0]
        if path.endswith(".tar"):
            path = path.strip(".tar")
        source_path = self.SGX_PATH + "/" + path
        destination_path = os.path.basename(self.SGX_FVT_ZIP)
        self._log.debug("FVT tool source path {}".format(source_path))
        self._log.debug("FVT tool destination path {}".format(destination_path))
        self.FVT_PATH = self._install_collateral.download_and_copy_zip_to_sut(source_path,
                                                              destination_path)
        self.get_sgx_fvt_dir()

    def copy_psw_tool(self):
        """Copies psw tool to SUT"""
        self._log.info("Copy psw tool")
        source_path = self.SGX_PATH + "/" + \
                      os.path.splitext(os.path.basename(self.PSW_ZIP))[0]
        destination_path = os.path.basename(self.PSW_ZIP)
        self._log.debug("PSW tool source path {}".format(source_path))
        self._log.debug("PSW tool destination path {}".format(destination_path))
        self.PSW_PATH = self._install_collateral.download_and_copy_zip_to_sut(source_path,
                                                            destination_path)

    def get_sgx_fvt_dir(self):
        """
        Get sgx functional validation binary directory

        :raise: TestFail if could not found fvt binary match in the sgx path
        """
        self._log.info("get sgx fvt directory")
        cmd = self.FIND_CMD.format(self.SGX_FVT_BINARY)
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, self.FVT_PATH)
        self._log.debug("Output of find command is {} ".format(output.strip()))

        if not output.strip():
            raise content_exceptions.TestFail("could not find {} on SUT".format(self.SGX_FVT_BINARY))
        cmd = self.READ_LINK_CMD.format(output.strip())
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, self.FVT_PATH)
        self._log.debug("Absolute path of the FVT dir is {} ".format(output.strip()))
        self.SGX_FVT_DIR = os.path.dirname(output.strip())
        self._log.info("SGX FVT Directory is {}".format(self.SGX_FVT_DIR))

    def get_psw_dir(self):
        """
        Get sgx psw directory

        :raise: TestFail if could not found psw binary match in the sgx path
        """
        self._log.info("get psw fvt directory")
        cmd = self.FIND_CMD.format(self.PSW_INSTALL_BINARY_MATCH)
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, self.PSW_PATH)
        self._log.debug("Output of find command {}".format(output))
        if not output.strip():
            raise content_exceptions.TestFail("could not find {} on SUT".format(self.PSW_INSTALL_BINARY_MATCH))
        cmd = self.READ_LINK_CMD.format(output.strip())
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, self.PSW_PATH)
        self._log.debug("Absolute path of the psw dir is {} ".format(output.strip()))
        self.PSW_DIR = os.path.dirname(output.strip())
        self._log.info("PSW Dir {}".format(self.PSW_DIR))

    def check_messages(self):
        for message in self.VERIFY_STARTED_ENCLAVES:
            sut_cmd_result = self._os.execute("grep -w '%s' "
                                              "/var/log/messages" % message,
                                              self.EXECUTION_TIMEOUT)
            self._log.debug(sut_cmd_result.stdout)
            self._log.debug(sut_cmd_result.stderr)
            if sut_cmd_result.stdout == "":
                raise content_exceptions.TestFail(message + " message not "
                                                            "found in "
                                                            "/var/log/messages")

    def is_psw_installed(self):
        """Checks the psw installed or not and returns the bool value"""
        self._log.debug("Check if psw is installed or not")
        sut_cmd_result = self._os.execute("chmod +x %s;%s" % (self.SGX_FVT_DIR, self.SGX_FVT_PSW_VERIFY_CMD),
                                          self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        if self.PSW_INSTALLED_MATCH not in sut_cmd_result.stdout:
            return False
        return True

    def install_requirements(self):
        """Installing requirements"""
        self.load_sgx_properites()
        self._log.debug("Installing RHEL requirements")
        for req in self.RHEL_REQUIREMENTS:
            max_attempts = 5
            flag = 0
            wait_delay = 5
            for no_attempts in range(max_attempts):
                try:
                    self._log.debug("Running command {} for attempt {}".format(req, no_attempts))
                    sut_cmd_result = self._os.execute(req, self.EXECUTION_TIMEOUT, self.PSW_DIR)
                    self._log.debug(sut_cmd_result.stdout)
                    self._log.debug(sut_cmd_result.stderr)

                    if not (sut_cmd_result.cmd_failed() or sut_cmd_result.stderr):
                        flag = 1
                        break
                except (TimeoutError, OsCommandException, OsCommandTimeoutException) as ex:
                    self._log.debug("Error: {} for attempt {}, trying once again for command: {}".
                                    format(ex, no_attempts, req))
                finally:
                    if no_attempts == max_attempts-1 and flag == 0:
                        raise content_exceptions.TestSetupError("Command {} execution failed".format(req))
                time.sleep(wait_delay)

        for req in self.RHEL_INSTALL_REQUIREMENTS:
            self._install_collateral.yum_install(req)

    def install_psw_repo(self):
        """Installing repos"""
        self._log.info("Install psw repos")
        cmd = self.PSW_INSTALL_CMD % self.PSW_LOCAL_REPO_NAME
        sut_cmd_result = self._os.execute(cmd, self.EXECUTION_TIMEOUT, self.PSW_DIR)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)

    def install_psw(self):
        """Installs PSW"""
        self._log.info("install psw")
        self._log.debug("unzipping local repo")

        self._log.debug("Adding local repo")
        sut_cmd_result = self._os.execute(self.PSW_ADD_REPO,
                                          self.EXECUTION_TIMEOUT)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        self._log.debug("Installing SGX PSW packages")
        sut_cmd_result = self._os.execute(self.PSW_INSTALL_PACKAGES,
                                          self.EXECUTION_TIMEOUT, self.PSW_DIR)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)

    def install_sdk(self):
        """Install SGX SDK. Ignoring few errors and they will be caught at runtime"""
        self._log.debug("Installing SGX SDK")
        cmd_output = self._common_content_lib.execute_sut_cmd("ls %s" % self.SGX_SDK_BINARY_MATCH,
                                                              "ls %s" % self.SGX_SDK_BINARY_MATCH,
                                                              self.EXECUTION_TIMEOUT, self.PSW_DIR)
        if cmd_output == "":
            raise content_exceptions.TestFail("Could not find SGX SDK Binary to install")
        sut_cmd_result = self._os.execute(
            "chmod +x %s;{ echo no;echo %s; } | ./" % (cmd_output.strip(), self.SGX_SDK) + cmd_output.strip(),
            self.EXECUTION_TIMEOUT, self.PSW_DIR)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        self._common_content_lib.execute_sut_cmd(self.SDK_ADD_ENVIRONMENT,
                                                 self.SDK_ADD_ENVIRONMENT,
                                                 self.EXECUTION_TIMEOUT, self.PSW_DIR)

    def check_psw_installation(self):
        """Checks psw installation. Ignoring few errors and they will be caught at runtime
        :raise: content_execptions.TestFail
        """
        self._log.info("Check psw installation")
        self.install_requirements()
        self._log.info("SGX_FVT execution path is %s", self.SGX_FVT_DIR)
        if self.is_psw_installed():
            self._log.info("PSW is installed and verified successfully!")
            return
        self._log.info("PSW is not installed, installing it")
        self.install_psw()
        if not self.is_psw_installed():
            raise content_exceptions.TestFail("SGX PSW verification failed, "
                                              "looks like SGX PSW not installed")
        self._log.info("SGX PSW is installed and verified successfully")

    def check_aesm_running(self):
        """Checks AESM is running"""
        self._log.info("Checks AESM running status")
        self.check_psw_installation()
        self.install_sdk()
        self._log.info("SGX_FVT execution path is %s",
                       self.SGX_FVT_DIR)
        self._os.execute(self.AESM_RESTART_CMD, self.EXECUTION_TIMEOUT)
        sut_cmd_result = self._os.execute(self.SGX_FVT_PSW_VERIFY_CMD, self.EXECUTION_TIMEOUT,
                                          self.SGX_FVT_DIR)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        if self.SGX_AESM_STATUS not in sut_cmd_result.stdout:
            raise content_exceptions.TestFail("SGX AESM is not running")
        self._log.info("SGX AESM service is running")
        self.check_messages()

    def run_sgx_app_test(self):
        """Runs the SGX app test

        :raise: TestFail if expected result is not met
        """
        find_cmd = "find . -name {}"
        self._log.info("run sgx app test")
        cmd = find_cmd.format("sgx_app")
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, self.PSW_PATH)
        self._log.debug("Output of find command is {} ".format(output.strip()))
        cmd = self.READ_LINK_CMD.format(output.strip())
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, self.PSW_PATH)
        self._log.debug("Absolute path of the SGX test dir is {} ".format(output.strip()))

        if not output.strip():
            raise content_exceptions.TestFail("could not find {} on SUT".format("sgx_app"))

        self.SGX_TEST_DIR = os.path.dirname(output.strip())
        self._log.info("SGX Test Directory is {}".format(self.SGX_TEST_DIR))
        if not output.strip():
            raise content_exceptions.TestFail("could not find {} on SUT".format("sgx_app"))

        self._log.info("SGX_Test execution path is %s", self.SGX_TEST_DIR)
        sut_cmd_result = self._os.execute("chmod +x sgx_app;"
                                          "LD_LIBRARY_PATH=./ "
                                          "./sgx_app -auto", self.EXECUTION_TIMEOUT,
                                          self.SGX_TEST_DIR)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        planned_regex = re.compile("Planed:\s(\d+)")
        planned_list = planned_regex.findall(sut_cmd_result.stdout)
        if not len(planned_list):
            raise content_exceptions.TestFail("./sgx_app -auto output is not expected")
        planned = planned_list[0].strip()
        self._log.info("Planned tests are: %s", planned)
        success_regex = re.compile("Success:\s(\d+)")
        success_list = success_regex.findall(sut_cmd_result.stdout)
        if not len(success_list):
            raise content_exceptions.TestFail("./sgx_app -auto output is not expected")
        success = success_list[0].strip()
        self._log.info("Success tests are: %s", success)
        return success == planned

    def run_enclave_app_test(self, cmd, cwd=None, timeout=60, verify_message=[]):
        """Runs the SGX enclave app test"""
        self._log.info("running enclave app test")
        self._log.info("Running %s", cmd)
        sut_cmd_result = self._os.execute(self.SDK_ADD_ENVIRONMENT + ";" + cmd, timeout, cwd)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        for message in verify_message:
            if message not in sut_cmd_result.stdout:
                return False
        return True

    def check_sample_enclave_creation(self):
        """Checks sample enclave creation"""
        self._log.info("checking sample enclave creation")
        self.check_psw_installation()
        self.install_sdk()
        if not self.run_sgx_app_test():
            raise content_exceptions.TestFail("./sgx_app -auto have failures")
        self.run_make_command(self.SIMPLE_ENCLAVE_PATH, self.EXECUTION_TIMEOUT)
        if not self.run_enclave_app_test('echo -e "\n" | LD_LIBRARY_PATH=./ ./app',
                                         cwd=self.SIMPLE_ENCLAVE_PATH, timeout=self.EXECUTION_TIMEOUT,
                                         verify_message=[self.ENCLAVE_VERIFICATION_MESSAGE]):
            raise content_exceptions.TestFail("./app results are not as expected")

    def local_attestation(self):
        """Checks local attestation"""
        self._log.info("checking local attestation")
        self.check_psw_installation()
        self.install_sdk()
        if not self.run_sgx_app_test():
            raise content_exceptions.TestFail("./sgx_app -auto have failures")
        self.run_make_command(self.LOCAL_ATTESTATION_PATH, self.EXECUTION_TIMEOUT)
        if not self.run_enclave_app_test('echo -e "\n" | LD_LIBRARY_PATH=./ ./app',
                                         cwd=self.LOCAL_ATTESTATION_PATH + "/bin", timeout=self.EXECUTION_TIMEOUT,
                                         verify_message=self.LOCAL_ATTESTATION_VERIFY_MESSAGES):
            raise content_exceptions.TestFail("./app results are not as expected")

    def check_data_sealing(self):
        """Checks data sealing"""
        self._log.info("checking SGX data sealing")
        self.check_psw_installation()
        self.install_sdk()
        if not self.run_sgx_app_test():
            raise content_exceptions.TestFail("./sgx_app -auto have failures")
        self.run_make_command(self.SEAL_UNSEAL_PATH, self.EXECUTION_TIMEOUT)
        if not self.run_enclave_app_test('echo -e "\n" | LD_LIBRARY_PATH=./ ./app',
                                         cwd=self.SEAL_UNSEAL_PATH,
                                         timeout=self.EXECUTION_TIMEOUT,
                                         verify_message=self.SEAL_UNSEAL_VERIFY_MESSAGES):
            raise content_exceptions.TestFail("./app results are not as expected")

    def check_sgx_tem_base_test(self):
        """Checks the SGX TEM Base Test Case"""
        self._log.info("checking SGX TEM Base Test Case")
        self.check_psw_installation()
        self.install_sdk()
        if not self.run_sgx_app_test():
            raise content_exceptions.TestFail("./sgx_app -auto have failures")

    def is_sgx_disabled_cpuid(self):
        """
        Check for cpuid output whether all the cpuid is SGX not supported.

        :return: True if cpu capability is not supported else false
        """
        return self.__check_sgx_capability_cpu_id("true")

    def is_sgx_enabled_cpuid(self):
        """
        Check for cpuid output whether all the cpuid is SGX supported.

        :return: True if cpu capability is supported else false
        """
        return self.__check_sgx_capability_cpu_id("false")

    def __check_sgx_capability_cpu_id(self, sgx_capability_status):
        """
        Check cpuid output whether all the CPU's capability is supported for SGX

        :return: True cpu capability is supported else false
        """
        self._log.info("Verify SGX CPU capability using cpuid")
        self._install_collateral.install_cpuid()
        cpuid_sgx_supported_regex = "SGX[0-9][\s]supported[\s]+=[\s]{}".format(sgx_capability_status)
        sgx_ouput = self._common_content_lib.execute_sut_cmd(self.CPUID_SGX_CMD, self.CPUID_SGX_CMD,
                                                             self.execution_timeout)
        self._log.debug("Cpuid output {}".format(sgx_ouput))
        if not sgx_ouput.strip():
            raise content_exceptions.TestFail("Unable to get cpuid information")
        re_output = re.findall(cpuid_sgx_supported_regex, sgx_ouput)
        if len(re_output) > 0:
            return False
        return True

    def execute_functional_validation_tool(self):
        """
        Execute FVT and Validate if SGX is enabled or not

        :return: True if validation process is successful False otherwise
        """
        self._log.info("Check if sgx is enabled or not")
        sut_cmd_result = self._os.execute("chmod +x %s;%s" % (self.SGX_FVT_DIR, self.SGX_FVT_PSW_VERIFY_CMD),
                                          self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug("FVT Output {}".format(sut_cmd_result.stdout))
        self._log.debug("FVT Error {}".format(sut_cmd_result.stderr))
        if self.SGX_ENABLED_STR not in sut_cmd_result.stdout:
            raise content_exceptions.TestFail("SGX is not enabled in system")
        self._log.info('After Running FVT Tool SGX is Working as Expected')

    def run_semt_app(self, semt_timeout):
        """
        To copy and extract semt app in SUT
        To run the command ./semt -S2 1024 1024 in semt for given time without crashing and then kills the session

        :param: semt_timeout: execution time for semt command
        :raise: ContentException.TestFail if SEMT app is not running
        """
        self.check_psw_installation()
        self.install_sdk()
        self._log.info("Copying semt app from host and unzipping in SUT")
        semt_path = self._install_collateral.copy_semt_files_to_sut()
        self._log.info("Running semt app by executing {} for {}s".format(self.SEMT_CMD, semt_timeout))
        self._os.execute_async(self.SEMT_CMD, semt_path)
        if not semt_timeout:
            return
        start_time = time.time()
        while (time.time() - start_time) <= semt_timeout:
            grep_semt_output = self._os.execute(self.SEMT_GREP, self.EXECUTION_TIMEOUT)
            semt_count = grep_semt_output.stdout.count(self.SEMT_STR)
            if semt_count <= 1:
                raise content_exceptions.TestFail("SEMT app is not running !!!")
        self._common_content_lib.execute_sut_cmd(self.SEMT_KILL, self.SEMT_KILL, self.EXECUTION_TIMEOUT)

    def check_prmrr_bases(self, snc2=None):
        """
        This methods checks prmrr bases value

        :param snc2: if snc2 enable, the first 4 prmrr base register value should be non-zero and unique
        and if snc4 is enable, all 8 prmrr base register value should be non-zero and unique
        :raise Test Fail if values are not as expected for snc2 and snc4
        """
        self._log.info("Checking PRMRR base values")
        msr_value = []
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.halt()
            for each_prmrr_bases in self.PRMRR_BASES_LIST:
                msr_value.append(hex(self.sdp.msr_read(each_prmrr_bases, squash=True)))
        except Exception as e:
            self._log.error("Unknown exception while checking PRMRR bases")
        finally:
            self.sdp.go()

        self._log.info("PRMRR Bases without the mask :{}".format(msr_value))
        if snc2:
            if self.PRMRR_DEFAULT_VALUE in msr_value[0:4] and len(set(msr_value[0:4])) != len(msr_value[0:4]):
                raise content_exceptions.TestFail("PRMRR Bases without the mask values for SNC2 are not as expected")
        else:
            if self.PRMRR_DEFAULT_VALUE in msr_value and len(set(msr_value)) != len(msr_value):
                raise content_exceptions.TestFail("PRMRR Bases without the mask values for SNC4 are zero")

        self._log.info("PRMRR Bases without the mask values are as expected")

    def get_proxy_path(self):
        """
        Get the proxy path from /etc/yum.conf file in sut

        :return: proxy path
        """
        self._log.info("Getting proxy path from yum.conf file")
        cmd_output = self._os.execute(self.YUM_CONF_CMD, self.execution_timeout)
        self._log.debug("output of yum.conf {}".format(cmd_output.stdout))
        for line in cmd_output.stdout.split("\n"):
            if self.PROXY in line:
                proxy = line.split("=")[-1].strip()
                self._log.info("Proxy used is {}".format(proxy))
                return proxy
        raise content_exceptions.TestSetupError("Could not found proxy in yum.conf file!!")

    def run_hydra_test(self, test_duration=60, enclave_mb="128", num_enclave_threads="64", num_regular_threads="64"):
        """
        This method installs psw and sdk on the sut.
        Copies hydra test tool in SUT and runs hydra test for given time

        :param test_duration: time duration in seconds to run the test, :type: int
        :param enclave_mb: Enclave MB, :type: str
        :param num_enclave_threads: Enclave threads in number, :type: str
        :param num_regular_threads: Regular Threads in number, :type: str
        :raise: content exception if the sgx hydra test fails to run for specified duration or any error
                found during the test execution.
        """
        app_str = "/App"
        cat_cmd = "cat {}".format(self.HYDRA_FILE)
        error = "error"
        # Installation of PSW
        self.check_psw_installation()
        # Installation of sgx sdk
        self.install_sdk()
        self._log.info("Copying Hydra tool and unzipping in SUT")
        # Copying sgx hydra tool to sut
        hydra_test_path = self._install_collateral.copy_and_install_hydra_tool() + app_str
        self._log.debug("SGX Hydra tool is installed in location {}".format(hydra_test_path))
        # Executing sgxhydra cmd
        self._os.execute_async(self.HYDRA_CMD.format(enclave_mb, num_enclave_threads, num_regular_threads,
                                                     test_duration, self.HYDRA_FILE), hydra_test_path)
        self._log.debug("SGX Hydra test is running for {}s".format(test_duration))
        start_time = time.time()
        while (time.time() - start_time) <= test_duration:
            time.sleep(300)
            grep_hydra_output = self._os.execute(self.HYDRA_GREP, self.EXECUTION_TIMEOUT)
            hydra_count = grep_hydra_output.stdout.count(self.SGX_HYDRA)
            if hydra_count <= 1:
                raise content_exceptions.TestFail("SGX Hydra test is not running")
        hydra_res = self._common_content_lib.execute_sut_cmd(cat_cmd, cat_cmd, self.EXECUTION_TIMEOUT,
                                                             hydra_test_path)
        self._log.debug("SGX Hydra test output is {}".format(hydra_res))
        if re.search(error, hydra_res.lower()):
            raise content_exceptions.TestFail("Error found during the test execution of sgx Hydra test")
        self._log.info("SGX Hydra test ran successfully for {}s duration".format(test_duration))
        try:
            log_dir = self._common_content_lib.get_log_file_dir()
            self._os.copy_file_from_sut_to_local(hydra_test_path + "//" + self.HYDRA_FILE, log_dir + "//" + self.HYDRA_FILE)
        except Exception as e:
            self._log.error("Unable to copy the Sgx Hydra file due to the error {} ".format(e))

    def dynamic_enclave_memory_allocation(self):
        """
        Verifies Dynamic Enclave memory allocation
        :raise: content_exceptions.TestFail
        """
        # In the Makefile,
        # Change Enclave_Config_File := Enclave/Enclave.config.xml to
        # Enclave_Config_File := Enclave/config.04.xml
        self.load_sgx_properites()
        command_output = self._common_content_lib.execute_sut_cmd(self.CAT_CMD.format(self.MAKEFILE),
                                                                  self.CAT_CMD.format(self.MAKEFILE),
                                                                  self.execution_timeout,
                                                 cmd_path=self.SIMPLE_ENCLAVE_PATH)
        self._log.debug("Makefile content before string replacement : {}".format(command_output))
        cmd_to_exec = self.STRING_REPLACEMENT_CMD.format(self.MAKEFILE)
        self._common_content_lib.execute_sut_cmd(cmd_to_exec, cmd_to_exec,
                                                 self.execution_timeout, self.SIMPLE_ENCLAVE_PATH)
        self._log.debug("Makefile content after string replacement : {}".format(command_output))

        # Build the SampleEnclave App
        self._log.info("Build the SampleEnclave App")
        self.run_make_command(cwd=self.SIMPLE_ENCLAVE_PATH)

        # Run the app using: ./app
        self._log.info("Run the app using: ./app")
        if not self.run_enclave_app_test('echo -e "\n" | ./app',
                                         cwd=self.SIMPLE_ENCLAVE_PATH, timeout=self.EXECUTION_TIMEOUT,
                                         verify_message=[self.ENCLAVE_VERIFICATION_MESSAGE]):
            raise content_exceptions.TestFail("./app results are not as expected")

        self._log.info("The platforms ability to increase of enclave size on demand "
                       "relative to data size being moved into and/or out of the enclave verified")

    def perform_s5_reboot_test(self, socket):
        """
        This method Performs s5 sealing reboot test.

        :param socket: Socket number where the test is running.
        :raise: content_exceptions if Fail to start S5 sealing reboot test
        """
        self._log.info("Starting S5 sealing reboot test for socket {}".format(socket))
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        try:
            self._os.execute(self.SGX_S5_REBOOT_CMD, self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        except OsCommandTimeoutException as e:
            self._log.debug("Exception occurred while executing the command {} as system is restarting".format(e))
        self._log.debug("'{}' command has been sent to OS.".format(self.SGX_S5_REBOOT_CMD))
        time.sleep(10)
        self._os.wait_for_os(self.reboot_timeout)
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SHOW_FVT_OUTPUT, self.SHOW_FVT_OUTPUT,
                                                          self.execution_timeout,
                                                          self.SGX_FVT_DIR)
        self._log.debug("{} command output is {}".format(self.SHOW_FVT_OUTPUT, fvt_result))
        if self.S5_SEAL_REBOOT_MSG.format(socket) not in fvt_result:
            raise content_exceptions.TestFail("Fail to start S5 sealing reboot test")
        self._log.info("S5 sealing reboot test for socket {} was started successfully".format(socket))

    def verify_seal_unseal_reboot_test(self):
        """
        Verify seal/unseal reboot test is successful

        :raise: content_exceptions if S5 reboot sealing/unsealing test is failed
        """
        self._log.info("Verifying S5 reboot sealing/unsealing from FVT log")
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SGX_S5_REBOOT_CMD, self.SGX_S5_REBOOT_CMD,
                                                              self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug("{} command output is {}".format(self.SGX_S5_REBOOT_CMD, fvt_result))
        exp_str = re.search(self.S5_SEAL_UNSEAL_REBOOT_SUCCESS_MSG, fvt_result)
        if not exp_str:
            raise content_exceptions.TestFail("S5 reboot sealing/unsealing test is failed")
        self._log.info("S5 reboot sealing/unsealing from FVT log is successfully verified and found the expected "
                       "string {}".format(exp_str.group(1)))

    def perform_s5_shutdown_test(self, socket):
        """
        This method Performs s5 sealing reboot test.

        :param socket: Socket number where the test is running.
        :raise: content_exceptions if Fail to start S5 sealing shutdown test
        """
        self._log.info("Starting S5 sealing shutdown test for socket {}".format(socket))
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        try:
            self._os.execute(self.SGX_S5_SHUTDOWN_CMD, self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        except OsCommandTimeoutException as e:
            self._log.debug("Exception occurred while executing the command {} as system is shutdown".format(e))
        self._log.debug("{} command has been sent to OS.".format(self.SGX_S5_SHUTDOWN_CMD))
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        time.sleep(10)
        self._os.wait_for_os(self.reboot_timeout)
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SHOW_FVT_OUTPUT, self.SHOW_FVT_OUTPUT,
                                                              self.execution_timeout,
                                                              self.SGX_FVT_DIR)
        self._log.debug("{} command output is {}".format(self.SHOW_FVT_OUTPUT, fvt_result))
        if self.S5_SEAL_SHUTDOWN_MSG.format(socket) not in fvt_result:
            raise content_exceptions.TestFail("Fail to start S5 sealing shutdown test")
        self._log.info("S5 sealing Shutdown test for socket {} was started successfully".format(socket))

    def verify_seal_unseal_shutdown_test(self):
        """
        Verify seal/unseal shutdown test is successful

        :raise: content_exceptions if S5 shutdown sealing/unsealing test is failed
        """
        self._log.info("Verifying S5 shutdown sealing/unsealing from FVT log")
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SGX_S5_SHUTDOWN_CMD, self.SGX_S5_REBOOT_CMD,
                                                              self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug("{} command output is {}".format(self.SGX_S5_SHUTDOWN_CMD, fvt_result))
        exp_str = re.search(self.S5_SEAL_UNSEAL_SHUTDOWN_SUCCESS_MSG, fvt_result)
        if not exp_str:
            raise content_exceptions.TestFail("S5 shutdown sealing/unsealing test is failed")
        self._log.info("S5 shutdown sealing/unsealing from FVT log is successfully verified and found the expected "
                       "string {}".format(exp_str.group(1)))

    def perform_s5_reboot_boundary(self, socket):
        """
        This method Performs s5 sealing reboot boundary test.

        :param socket: Socket number where the test is running.
        :raise: content_exceptions if Fail to start S5 sealing reboot boundary test
        """
        self._log.info("Starting S5 sealing reboot test for socket {}".format(socket))
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SGX_S5_REBOOT_CMD, self.SGX_S5_REBOOT_CMD,
                                                              self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug("'{}' command has been sent to OS.".format(self.SGX_S5_REBOOT_CMD))
        self._os.wait_for_os(self.reboot_timeout)
        self._log.debug("{} command output is {}".format(self.SGX_S5_REBOOT_CMD, fvt_result))
        if self.S5_SEAL_REBOOT_MSG.format(socket) not in fvt_result:
            raise content_exceptions.TestFail("Fail to start S5 sealing reboot boundary")
        self._log.info("S5 sealing reboot test for socket {} was started successfully".format(socket))

    def verify_seal_unseal_reboot_boundary(self):
        """
        Verify seal/unseal reboot boundary is successful

        :raise: content_exceptions if S5 reboot sealing/unsealing boundary is failed
        """
        self._log.info("Verifying S5 reboot sealing/unsealing")
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SGX_S5_REBOOT_CMD, self.SGX_S5_REBOOT_CMD,
                                                              self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug("{} command output is {}".format(self.SGX_S5_REBOOT_CMD, fvt_result))
        output1 = re.search(self.S5_SEAL_UNSEAL_REBOOT_SUCCESS_MSG, fvt_result)
        output2 = re.search(self.S5_REBOOT_SEAL_UNSEAL_MSG, fvt_result)
        if not (output1 and output2):
            raise content_exceptions.TestFail("S5 reboot sealing/unsealing boundary is failed")
        self._log.info("S5 reboot sealing/unsealing is successfully verified")

    def perform_s5_shutdown_boundary(self, phy, socket):
        """
        This method Performs s5 sealing shutdown boundary test.

        :param phy: PHY provider for SXSTATE
        :param socket: Socket number where the test is running.
        :raise: content_exceptions if Fail to start S5 sealing shutdown boundary
        """
        self._log.info("Starting Sealing and Unsealing data across S5 shutdown boundary for socket {}".format(socket))
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SGX_S5_SHUTDOWN_CMD, self.SGX_S5_SHUTDOWN_CMD,
                                                              self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self.verify_s5_shutdown_power_state(phy, self.EXECUTION_TIMEOUT)
        self._log.debug("{} command has been sent to OS.{}".format(self.SGX_S5_SHUTDOWN_CMD, fvt_result))
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._os.wait_for_os(self.reboot_timeout)
        if self.S5_SEAL_SHUTDOWN_MSG.format(socket) not in fvt_result:
            raise content_exceptions.TestFail("Fail to start S5 sealing shutdown boundary")
        self._log.info("S5 sealing Shutdown boundary for socket {} was started success"
                       "fully".format(socket))

    def verify_s5_shutdown_power_state(self, phy, wait_time):
        """
        Verify if the system has shutdown S5 power state

        :param phy: PHY provider for SXSTATE
        :param wait_time: wait time for system to enter S5 state
        :raise: TestFail SUT did not entered into S5 state
         """
        start_time = time.time()
        self._log.info("Checking for S5 power state")
        while time.time() - start_time <= wait_time:
            if not self._common_content_lib.check_os_alive():
                power_state = phy.get_power_state()
                if power_state != PowerStates.S5:
                    continue
                else:
                    return
        power_state = phy.get_power_state()
        raise content_exceptions.TestFail(
            "SUT did not entered into {} state, actual state is {}".format(PowerStates.S5, power_state))

    def verify_seal_unseal_shutdown_boundary(self):
        """
        Verify seal/unseal shutdown boundary is successful

        :raise: content_exceptions if S5 shutdown sealing/unsealing test is failed
        """
        self._log.info("Verifying S5 shutdown sealing/unsealing")
        self._log.debug("FVT path is {}".format(self.SGX_FVT_DIR))
        fvt_result = self._common_content_lib.execute_sut_cmd(self.SGX_S5_SHUTDOWN_CMD, self.SGX_S5_SHUTDOWN_CMD,
                                                              self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug("{} command output is {}".format(self.SGX_S5_SHUTDOWN_CMD, fvt_result))
        search_output1 = re.search(self.S5_SEAL_UNSEAL_SHUTDOWN_SUCCESS_MSG, fvt_result)
        search_output2 = re.search(self.S5_SHUTDOWN_SEAL_UNSEAL_MSG, fvt_result)
        if not (search_output1 and search_output2):
            raise content_exceptions.TestFail("S5 shutdown sealing/unsealing boundary is failed")
        self._log.info("S5 shutdown sealing/unsealing is successfully verified")

    def verify_sgx_content(self, time_duration=60, enclave_mb="128", num_enclave_threads="64",
                           num_regular_threads="64"):
        """
        Verify SGX content by running semt app for Linux

        :param time_duration: time duration in seconds to run the test, :type: int
        :param enclave_mb: Enclave MB, :type: str
        :param num_enclave_threads: Enclave threads in number, :type: str
        :param num_regular_threads: Regular Threads in number, :type: str
        """
        self.run_semt_app(time_duration)

    def verify_lcp_locked_mode(self):
        """
        Run command ./SGXFunctionalValidation -l -v -skip_power_tests -lcp_legacy_locked and
        verify the output for LCP Legacy Lock mode and check MSR bit 0 value in MSR_OPTIN_FEATURE_CONTROL value

        :raise: TestFail if success string not found in fvt_output or
                        if MSR 0 bit is not set in MSR_OPTIN_FEATURE_CONTROL value
        """
        self._log.info("Verifying LCP Locked Mode")
        self.install_requirements()
        self.uninstall_psw()
        self.install_psw()
        self.install_sdk()
        lcp_locked_output = self._os.execute(self.LCP_LEGACY_LOCKED_MODE_CMD, self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug("LCP Locked mode output {}".format(lcp_locked_output.stdout))
        search_str_lcp_locked = re.search(self.LCP_LOCKED_MODE_SUCCESS_MSG, lcp_locked_output.stdout)
        if not (search_str_lcp_locked and self.LCP_LOCKED_MODE_STR in lcp_locked_output.stdout):
            raise content_exceptions.TestFail("LCP Locked Mode output is not as expected")
        self._log.info("LCP legacy locked mode is successful")

        lcp_locked_msr_str = re.search(self.LCP_LOCKED_MSR_VALUE, lcp_locked_output.stdout)
        if lcp_locked_msr_str:
            for each in lcp_locked_output.stdout.split("\n"):
                if self.LCP_LOCKED_MSR_VALUE in each:
                    lcp_locked_msr_hex_value = hex(int(each.split("=")[-1].strip()))
                    self._log.info("MSR_OPTIN_FEATURE_CONTROL value {}".format(lcp_locked_msr_hex_value))
                    self.check_msr_value(lcp_locked_msr_hex_value, self.LCP_LOCKED_MSR_EXP_VALUE)
        else:
            raise content_exceptions.TestFail("LCP Locked MSR value is not found")

    def verify_lcp_unlocked_mode(self):
        """
        Run command ./SGXFunctionalValidation -l -v -skip_power_tests -lcp -ignore_le_key_check and
        verify the output for LCP Legacy unlock mode and check MSR bit 0 value in MSR_OPTIN_FEATURE_CONTROL value
        and check MSR_IA32_SGX_LE_PUBKEYHASH_0 value, MSR_IA32_SGX_LE_PUBKEYHASH_1 value, MSR_IA32_SGX_LE_PUBKEYHASH_2
        value, MSR_IA32_SGX_LE_PUBKEYHASH_3 value

        :raise: TestFail if success string not found in fvt_output or
                        if MSR 0 bit is not set in MSR_OPTIN_FEATURE_CONTROL value
        """
        self._log.info("Verifying LCP Unlocked Mode")
        self.install_requirements()
        self.check_psw_installation()
        self.install_sdk()
        lcp_unlocked_output = self._os.execute(self.LCP_LEGACY_UNLOCKED_MODE_CMD, self.EXECUTION_TIMEOUT, self.SGX_FVT_DIR)
        self._log.debug("LCP Locked mode output {}".format(lcp_unlocked_output.stdout))
        search_str_lcp_unlocked = re.search(self.LCP_UNLOCKED_MODE_SUCCESS_MSG, lcp_unlocked_output.stdout)
        if not (search_str_lcp_unlocked and self.LCP_UNLOCKED_MODE_STR in lcp_unlocked_output.stdout):
            raise content_exceptions.TestFail("LCP unlocked Mode output is not as expected")
        self._log.info("LCP legacy unlocked mode is successful")

        lcp_locked_msr_str = re.search(self.LCP_LOCKED_MSR_VALUE, lcp_unlocked_output.stdout)
        if lcp_locked_msr_str:
            for each in lcp_unlocked_output.stdout.split("\n"):
                if self.LCP_LOCKED_MSR_VALUE in each:
                    lcp_locked_msr_hex_value = hex(int(each.split("=")[-1].strip()))
                    self._log.info("MSR_OPTIN_FEATURE_CONTROL value {}".format(lcp_locked_msr_hex_value))
                    self.check_msr_value(lcp_locked_msr_hex_value, self.LCP_LOCKED_MSR_EXP_VALUE)
        else:
            raise content_exceptions.TestFail("LCP unlocked MSR value is not found")
        lcp_unlock_msr_output = {}
        for success_key, success_value in self.LCP_UNLOCKED_MSR_VALUE.items():
            lcp_unlocked_msr_str = re.search(success_key, lcp_unlocked_output.stdout)
            if lcp_unlocked_msr_str:
                for each in lcp_unlocked_output.stdout.split("\n"):
                    if success_key in each:
                        lcp_unlock_msr_output[success_key] = each.split("=")[-1].strip()
                        self._log.debug("{} {}".format(success_key, lcp_unlock_msr_output[success_key]))
            else:
                raise content_exceptions.TestFail("LCP unlocked MSR value is not found")
        self._log.info("The lcp unlock msr actual value is {} and expected value is {}".
                       format(lcp_unlock_msr_output, self.LCP_UNLOCKED_MSR_VALUE))
        if self.LCP_UNLOCKED_MSR_VALUE != lcp_unlock_msr_output:
            raise content_exceptions.TestFail("LCP unlocked MSR actual value {} is not as expected value {}".
                                              format(lcp_unlock_msr_output, self.LCP_UNLOCKED_MSR_VALUE))

    def uninstall_psw(self):
        """
        Uninstalling PSW tool

        :raise: content_exceptions.TestSetupError if PSW uninstallation is unsuccessful
        """

        if self.is_psw_installed():
            self._log.info("Uninstalling PSW tool")
            for cmd in self.UNINSTALL_PSW_CMD:
                self._log.debug("Running command {}".format(cmd))
                uninstall_output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.EXECUTION_TIMEOUT)
                self._log.debug("Output of uninstall command {} is {}".format(cmd, uninstall_output))
        if self.is_psw_installed():
            raise content_exceptions.TestSetupError("PSW uninstallation is unsuccessful")
        self._log.debug("Successfully uninstalled PSW")

    def run_semt_app_sgxi(self, semt_timeout):
        """
        To copy and extract semt app in SUT
        To run the command ./semt -S0 4096 in semt for semt_timeout and check allocated memory should be greater than 4K
        and session will be abort automatically

        :param: semt_timeout: execution time for semt command
        :raise: ContentException.TestFail if SEMT app is not running
        """

        self.check_psw_installation()
        self.install_sdk()
        self._log.info("Copying semt app from host and unzipping in SUT")
        semt_path = self._install_collateral.copy_semt_files_to_sut()
        enclave_pkg_path = Path(os.path.join(semt_path, self.ENCLAVE_PATH)).as_posix()
        self._common_content_lib.execute_sut_cmd(self.ENCLAVE_CONFIG_FILE_CHANGE,
                                                    self.ENCLAVE_CONFIG_FILE_CHANGE,
                                                       self.EXECUTION_TIMEOUT, enclave_pkg_path)
        self._log.info("<HeapMaxSize> tag value repalced with '0x10000000' and changes is saved in "
                       "'Enclave.config.xml'file")
        self._log.info("Cleaning the make build")
        self._common_content_lib.execute_sut_cmd(self.MAKE_CLEAN_CMD,self.MAKE_CLEAN_CMD,
                                           self.EXECUTION_TIMEOUT,semt_path)
        self.run_make_command(semt_path)
        self._log.info("Running semt app by executing {} for {}s".format(self.SEMT_CMD_SGXI.format(semt_timeout),
                                                                         semt_timeout))
        semt_cmd = self.SEMT_CMD_SGXI.format(semt_timeout)
        timeout = semt_timeout + 60
        self._os.execute(semt_cmd, timeout, semt_path)
        semt_grep_output = self._os.execute(self.GREP_ALLOCATED_MEM_CMD,timeout,semt_path)
        if int(semt_grep_output.stdout) < self.MEM_SIZE:
            raise content_exceptions.TestFail("SEMT app is not running and not able to allocate the memory !!!")
        self._log.info("SEMT App ran sucessfully and able to allocate {}".format(semt_grep_output.stdout))

    def check_sgxi_sgx_enabled(self):
        """This methods checks the MSR981 and MSR982 value
        @raise: content_exceptions.TestFail if SGX integrity enumeration verification is failed
        """
        msr981_value = msr982_value = ""
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.halt()
            msr981_value = hex(self.sdp.msr_read(self.MSR981_HEX_VALUE, squash=True))
            msr982_value = self.sdp.msr_read(self.MSR982_HEX_VALUE, squash=True) & (1 << 49) != 0
        except Exception as e:
            self._log.error("Unknown exception while verifying  msr981 and msr982 value {}".format(e))
        finally:
            self.sdp.go()
        self._log.info("Actual MSR981 value :%s", msr981_value)
        self._log.info("Actual MSR982 value :%s", msr982_value)
        if not (self.check_msr_value(msr981_value, self.MSR981_EXP_VALUES)) and msr982_value:
            raise content_exceptions.TestFail("SGX integrity enumeration verification is failed")
        self._log.info("SGX integrity enumeration verification is successful")

    def copy_mp_registration_tool(self):
        """Copies MP registration tool to SUT

        :return: mp_registration_path
        """
        self.load_sgx_properties_default()
        self._log.info("Copying Multi Package Registration tool")
        source_path = self.SGX_SDK + "/" + \
                      os.path.splitext(os.path.basename(self.MP_REGISTRATION_ZIP))[0]
        destination_path = os.path.basename(self.MP_REGISTRATION_ZIP)
        mp_registration_path = self._install_collateral.download_and_copy_zip_to_sut(source_path,
                                                              destination_path)
        self._log.info("MP Registration path = {}".format(mp_registration_path))
        return mp_registration_path

    def install_mp_registration(self):
        """Install Auto Multi Registration"""
        mp_registration_path = self.copy_mp_registration_tool()
        self._log.info("Install Auto Multi Registration")
        for repo in self.MP_REGISTRATION_REPO:
            self._install_collateral.yum_remove(repo)
        for mp_rpm in self.MP_RPM_LIST:
            mp_rpm_file = mp_rpm.format(self.MP_VERSION_NUMBER)
            cmd = self.FIND_CMD.format(mp_rpm_file)
            output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, mp_registration_path)
            self._log.debug("Output of find command is {} ".format(output.strip()))

            if not output.strip():
                raise content_exceptions.TestFail("could not find {} on SUT".format(mp_rpm_file))
            cmd = self.READ_LINK_CMD.format(output.strip())
            output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, mp_registration_path)
            self._log.debug("Absolute path of the MP Registration dir is {} ".format(output.strip()))
            self.MP_REGISTRATION_DIR = os.path.dirname(output.strip())
            self._log.info("SGX auto multi registration Directory is {}".format(self.MP_REGISTRATION_DIR))

            self._install_collateral.yum_install(mp_rpm_file + " --nogpgcheck", cmd_path=self.MP_REGISTRATION_DIR)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._os.wait_for_os(self.reboot_timeout)
        for repo in self.MP_REGISTRATION_REPO:
            self._install_collateral.yum_verify_package(repo)
        self.update_aesmd_conf()
        self.update_mpa_registration_conf()
        self._log.info("SGX MP Registration is successful")

    def update_aesmd_conf(self):
        """
        Replaces the proxy type and proxy in aesmd.conf
        """
        path = "/etc/{}"
        aesmd_conf = "aesmd.conf"
        aesm_proxy_type_search_str = "#proxy type.*.manual.*"
        aesm_proxy_search_str = "#aesm proxy.*"
        aesm_proxy_type_replace_str = "proxy type = manual"
        aesm_proxy_replace_str = "aesm proxy = {}"
        proxy_path = self.get_proxy_path()
        log_dir = self._common_content_lib.get_log_file_dir()
        self._os.copy_file_from_sut_to_local(path.format(aesmd_conf), os.path.join(log_dir, aesmd_conf))
        aesm_host_path = os.path.join(log_dir, aesmd_conf)
        list_of_lines = []
        with open(aesm_host_path, 'r+') as f:
            for line in f.readlines():
                if re.search(aesm_proxy_type_search_str, line):
                    repl_str = re.sub(aesm_proxy_type_search_str, aesm_proxy_type_replace_str, line)
                    list_of_lines.append(repl_str)
                elif re.search(aesm_proxy_search_str, line):
                    repl_str = re.sub(aesm_proxy_search_str, aesm_proxy_replace_str.format(proxy_path), line)
                    list_of_lines.append(repl_str)
                else:
                    list_of_lines.append(line)
        f = open(aesm_host_path, "w")
        f.writelines(list_of_lines)
        f.close()
        self._os.copy_local_file_to_sut(os.path.join(log_dir, aesmd_conf), path.format(aesmd_conf))

    def update_mpa_registration_conf(self):
        """
        Replaces the log level string in mpa_registration.conf
        """
        path = "/etc"
        proxy_path = self.get_proxy_path()
        mpa_registration_log_level = "sed -i 's/log.*.level.*/log level = info/g' "  "mpa_registration.conf"
        mpa_registration_proxy_type = "sed -i 's/#proxy.*.type.*.=.*.manual/proxy type  = manual/g' " \
                                      "mpa_registration.conf"
        mpa_registration_proxy_url = "sed -i 's+#proxy.*.url.*+proxy url = {}+g' "  "mpa_registration.conf"

        self._common_content_lib.execute_sut_cmd(mpa_registration_log_level, mpa_registration_log_level,
                                                 self.EXECUTION_TIMEOUT, path)
        self._common_content_lib.execute_sut_cmd(mpa_registration_proxy_type, mpa_registration_proxy_type,
                                                 self.EXECUTION_TIMEOUT, path)
        self._common_content_lib.execute_sut_cmd(mpa_registration_proxy_url.format(proxy_path),
                                                 mpa_registration_proxy_url,
                                                 self.EXECUTION_TIMEOUT, path)

    def verify_mp_registration(self):
        """
        Verifies MP registration from mpa_registration.log

        :raise: content_exceptions.TestFail if MP Registration string not found in the output
        """
        cmd_output = self._common_content_lib.execute_sut_cmd(self.MPA_REGISTRATION_LOG_CMD,
                                                              self.MPA_REGISTRATION_LOG_CMD,
                                                              self.EXECUTION_TIMEOUT)
        self._log.debug(cmd_output)

        for success_msg in self.VERIFY_MP_REGISTRATION_INSTALL:
            if success_msg in cmd_output:
                self._log.info("MP Registration has been successfully verified")
                return True
        return False

    def load_sgx_properties_default(self):
        """"""
        os_type = self._os.os_type.lower()
        linux_flavour = self._common_content_lib.get_linux_flavour()
        self._log.debug("load sgx properties")
        self._log.debug("linux flavour is %s", linux_flavour)
        if not linux_flavour:
            raise content_exceptions.TestFail("could not get the linux flavour")
        sub_type = "%s_%s_KERNEL"
        if "intel-next" not in self.kernel:
            sub_type = sub_type % (LinuxDistributions.RHEL, "BASE")
        else:
            sub_type = sub_type % (LinuxDistributions.RHEL, "NXT")

        self.SGX_PATH = self._common_content_configuration \
            .get_security_sgx_params(os_type, "SGX_PATH", sub_type)
        self.SGX_SDK = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_SDK", sub_type)
        self.SIMPLE_ENCLAVE_PATH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SIMPLE_ENCLAVE_PATH", sub_type)
        self.LOCAL_ATTESTATION_PATH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "LOCAL_ATTESTATION_PATH", sub_type)
        self.PSW_INSTALL_BINARY_MATCH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "PSW_INSTALL_BINARY_MATCH", sub_type)
        self.SGX_FVT_BINARY = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_FVT_BINARY", sub_type)
        self.SGX_FVT_ZIP = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_FVT_ZIP", sub_type)

        self.SGX_FVT_PSW_VERIFY_CMD = "./%s -l -v -" \
                                      "skip_power_tests" % \
                                      self.SGX_FVT_BINARY
        self.PSW_LOCAL_REPO_NAME = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "PSW_LOCAL_REPO_NAME", sub_type)
        self.SGX_SDK_BINARY_MATCH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SGX_SDK_BINARY_MATCH", sub_type)
        self.SDK_ADD_ENVIRONMENT = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SDK_ADD_ENVIRONMENT", sub_type)
        self.SEAL_UNSEAL_PATH = \
            self._common_content_configuration.get_security_sgx_params(
                os_type, "SEAL_UNSEAL_PATH", sub_type)

        self.PSW_ZIP = self._common_content_configuration.get_security_sgx_params(
            os_type, "PSW_ZIP", sub_type)
        self.MP_REGISTRATION_ZIP = self._common_content_configuration.get_security_sgx_params(
            os_type, "MP_REGISTRATION_ZIP", sub_type)
        self.MP_VERSION_NUMBER = self._common_content_configuration.get_security_sgx_params(
            os_type, "MP_VERSION_NUMBER", sub_type)
        self.LOCAL_ATTESTATION_MP_ZIP = self._common_content_configuration.get_security_sgx_params(
            os_type, "LOCAL_ATTESTATION_MP_ZIP", sub_type)

    def verify_msmi_cmd_output(self, msmi_cmd_output_data):
        """
        This method is use to verify the msmi cmd output data

        :param msmi_cmd_output_data: Output data of msmi command
        :return: True if data is found False otherwise
        """
        re_exp = "\-(.*)"
        msmi_expected_output = "0x00000001"
        output = re.findall(re_exp, msmi_cmd_output_data, re.MULTILINE)
        for data in output:
            if not msmi_expected_output in data:
                self._log.error("Expected msmi cmd output {} is not equal to actual msmi cmd output data"
                                       .format(msmi_expected_output, data))
                return False
            self._log.info("Expected msmi cmd output {} and actual msmi cmd output data {} are equal"
                                       .format(msmi_expected_output, data))
            return True

    def install_local_attestation_mp_tool(self):
        """
        Install local attestation mp tool

        :return: local file attestation path
        """
        self.load_sgx_properties_default()
        self._log.info("Copy local attestation mp tool")
        path = os.path.splitext(os.path.basename(self.LOCAL_ATTESTATION_MP_ZIP))[0]
        if path.endswith(".tar"):
            path = path.strip(".tar")
        sut_path = self.SGX_PATH + "/" + path
        host_path = os.path.basename(self.LOCAL_ATTESTATION_MP_ZIP)
        local_mp_path = self._install_collateral.download_and_copy_zip_to_sut(sut_path, host_path)
        cmd = self.FIND_CMD.format(self.MAKEFILE)
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, local_mp_path)
        self._log.debug("Output of find command is {} ".format(output.strip()))
        if not output.strip():
            raise content_exceptions.TestFail("could not find {} on SUT".format(self.MAKEFILE))
        cmd = self.READ_LINK_CMD.format(output.strip())
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, local_mp_path)
        local_attestation_path = os.path.dirname(output.strip())
        self._log.info("Local Attestation MP path is {}".format(local_attestation_path))
        self._log.info("Running make command")
        sut_cmd_result = self._os.execute(self.ATTESTATION_MAKE_CMD, self.execution_timeout, local_attestation_path)
        self._log.debug(sut_cmd_result.stdout)
        self._log.debug(sut_cmd_result.stderr)
        return local_attestation_path

    def verify_local_attestation_output(self, local_mp_path):
        """
        Runs ./sgxcrossproctestserver and ./sgxcrossproctest commands and verifies their output.

        :param local_mp_path: local attestation path
        :raise: raises content_exceptions.TestFail if ./sgxcrossproctest fails to run
        """
        self._os.execute_async(self.SGX_ATTESTATION_CMD.format(self.SGX_TEST_SERVER_CMD, self.SGX_TEST_SERVER_CMD),
                               local_mp_path)
        self._os.execute_async(self.SGX_ATTESTATION_CMD.format(self.SGX_PROC_TEST_CMD, self.SGX_PROC_TEST_CMD),
                               local_mp_path)
        pid_test_server = self._common_content_lib.execute_sut_cmd(self.PROCID_CMD.format(self.SGX_TEST_SERVER_CMD),
                                                                   self.PROCID_CMD.format(self.SGX_TEST_SERVER_CMD),
                                                                   self.execution_timeout)
        pid_proc_test = self._common_content_lib.execute_sut_cmd(self.PROCID_CMD.format(self.SGX_PROC_TEST_CMD),
                                                                 self.PROCID_CMD.format(self.SGX_PROC_TEST_CMD),
                                                                 self.execution_timeout)
        time.sleep(60)
        self._os.execute(self.KILL_CMD.format(pid_proc_test), self.execution_timeout, local_mp_path)
        self._os.execute(self.KILL_CMD.format(pid_test_server), self.execution_timeout, local_mp_path)
        test_server_path = local_mp_path + "/" + "stdout_{}.log".format(self.SGX_TEST_SERVER_CMD)
        proc_test_path = local_mp_path + "/" + "stdout_{}.log".format(self.SGX_PROC_TEST_CMD)
        log_dir = self._common_content_lib.get_log_file_dir()
        test_server_host_path = os.path.join(log_dir, "stdout_{}.log".format(self.SGX_TEST_SERVER_CMD))
        proc_test_host_path = os.path.join(log_dir, "stdout_{}.log".format(self.SGX_PROC_TEST_CMD))
        self._os.copy_file_from_sut_to_local(test_server_path, test_server_host_path)
        self._os.copy_file_from_sut_to_local(proc_test_path, proc_test_host_path)

        list_of_success_msg = []
        with open(test_server_host_path, 'r+') as f:
            for line in f.readlines():
                if re.search(self.TEST_SERVER_EXPECTED_OUTPUT, line):
                    self._log.info("The server is ON")
                    break
                else:
                    self._log.error("Server is not ON")
                    break

        for success_msg in self.PROC_TEST_EXPECTED_OUTPUT:
            with open(proc_test_host_path, 'r+') as f:
                for line in f.readlines():
                    if re.search(success_msg, line):
                        list_of_success_msg.append(success_msg)
        if self.PROC_TEST_EXPECTED_OUTPUT != list_of_success_msg:
            raise content_exceptions.TestFail("Sgxcrossproctest failed")
        self._log.info("Sgxcrossproctest passed all 4 tests")

    def verify_stress_tool_executing(self, timeout):
        """
        This function verifies whether the semt app tool and stress test app is running for every 5 minutes

        :param timeout: wait timeout in seconds.
        :raise: raises content_exceptions.TestFail if stress test tool or semt app tool is not running
        """
        self._log.debug("Verifying Stress app tools")
        start_time = time.time()
        while (time.time() - start_time) <= timeout:
            time.sleep(300)
            self._log.debug("Verifying semt app tool")
            grep_semt_output = self._os.execute(self.SEMT_GREP, self.EXECUTION_TIMEOUT)
            semt_count = grep_semt_output.stdout.count(self.SEMT_STR)
            if semt_count <= 1:
                raise content_exceptions.TestFail("SEMT app is not running !!!")
            self._log.debug("Verifying stress app tool")
            grep_stress_app_output = self._os.execute(self.STRESS_APP_GREP.format(self.STREES_APP_STR), self.EXECUTION_TIMEOUT)
            stress_count = grep_stress_app_output.stdout.count(self.STREES_APP_STR)
            if stress_count <= 1:
                raise content_exceptions.TestFail("{} is not running !!!".format(self.STREES_APP_STR))

    def kill_semt_app(self):
        """
        This Function will kill the semt app
        """
        self._common_content_lib.execute_sut_cmd(self.SEMT_KILL, self.SEMT_KILL, self.EXECUTION_TIMEOUT)

    def check_prid(self, serial_log_path):
        """
        This function checks for prid value.

        :param: serial_log_path: serial log file path
        :return: socket0_prid_values, socket1_prid_values - Socket 0 and socket 1 prid values
        """
        self._log.info("Checking Socket 0 & 1 Prid values in serial log")
        with open(serial_log_path, 'r') as log_file:
            logfile_data = log_file.read()
            socket0_prid_values = re.findall(self.REGEX_CMD_FOR_SOCKET0, logfile_data)
            self._log.info("Socket0 Prid values {}".format(socket0_prid_values))
            socket1_prid_values = re.findall(self.REGEX_CMD_FOR_SOCKET1, logfile_data)
            self._log.info("Socket1 Prid Values {}".format(socket1_prid_values))
        return socket0_prid_values, socket1_prid_values

    def compare_prid_values(self, before_prid_value, after_prid_value, socket):
        """
        Comparing the prid values before and after owner_epoch bios knob is set

        :param before_prid_value: Before bios knob enable prid value
        :param after_prid_value: After bios knob enabled value
        :param socket: Socket number
        :raise: content_exceptions.TestFail if prid values are different after owner_epoch bios is enabled
        """
        if len(set(before_prid_value)) == 1 and len(set(after_prid_value)) == 1:
            before_prid_value = before_prid_value[0]
            after_prid_value = after_prid_value[0]
        else:
            self._log.error("Prid values are different")

        if before_prid_value != after_prid_value:
            raise content_exceptions.TestFail(
                "Socket{} Prid values {} before enabling owner_epoch bios knob and after enabling Prid values {} are "
                "different".format(socket, before_prid_value, after_prid_value))
        self._log.info(
            "Socket{} Prid values {} before enabling owner_epoch bios knob and after enabling Prid values {} are same "
            "as expected".format(socket, before_prid_value, after_prid_value))

    def install_pnpwls_master(self) -> None:
        """Downloads and installs pnpwls-master on sut and runs associated setup scripts
        :raises content_exceptions.TestSetupError: If either install scripts fail"""
        setup_timeout: float = 2 * TimeConstants.ONE_MIN_IN_SEC

        self._log.info("Installing MLC tool")

        pnpwls_path: str = self._install_collateral.download_and_copy_zip_to_sut("pnpwls-master", "pnpwls-master.tar.gz")

        self.pnpwls_master_path: str = Path(os.path.join(pnpwls_path, "pnpwls-master")).as_posix()
        setup_dir: str = Path(os.path.join(self.pnpwls_master_path, "setup")).as_posix()

        self._log.info("Running basic setup")
        pnp_res: OsCommandResult = self._os.execute("./basic_pnp_setup.sh", timeout=setup_timeout, cwd=setup_dir)
        if pnp_res.cmd_failed():
            raise content_exceptions.TestSetupError(f"Base setup script failed with return code {pnp_res.return_code}.\nstderr:\n{pnp_res.stderr}")

        self._log.info("Installing docker")
        docker_res: OsCommandResult = self._os.execute("./install_docker.sh", timeout=setup_timeout, cwd=setup_dir)
        if docker_res.cmd_failed():
            raise content_exceptions.TestSetupError(f"Docker install script failed with return code {docker_res.return_code}.\nstderr:\n{docker_res.stderr}")

    def execute_mlc_tool(self, mode: str = "all", script_timeout: float = 20,
                        socket: Union[None, int]=None, run_async=False, cmd_timeout: float=30) -> Union[OsCommandResult, None]:
        """Executes run_mlc.sh with given parameters:
        ./run_mlc.sh -m <mode> -t <script_timeout> -s <socket>
        If self.pnpwls_master_path is unset, pnpwls will be installed first

        :param mode: Script mode parameter. Possible modes:
            local_latency, remote_latency, llc_latency, llc_bandwidth,
            local_read_bandwidth, peak_remote_bandwidth, peak_remote_bandwidth_reverse,
            peak_bandwidth, peak_bandwidth_NTW, latency_matrix, bandwidth_matrix,
            loaded_latency, default, all
        :param script_timeout: Script timeout parameter. Time is in seconds
        :param socket: Script socket parameter. Indicates which socket the test will run on
        :param run_async: False to execute synchronously
        :param cmd_timeout: Command timeout for synchronous execution
        :returns OsCommandResult: if run_async=False, None otherwise
        """
        if not self.pnpwls_master_path:
            self.install_pnpwls_master()
        mlc_path: str = Path(os.path.join(self.pnpwls_master_path, "mlc")).as_posix()

        mlc_cmd: str = f"./run_mlc.sh -m {mode} -t {script_timeout}"
        if socket:
            mlc_cmd += f" -s {socket}"

        self._log.info(f"Running {mlc_cmd} on sut")

        if not run_async:
            return self._os.execute(mlc_cmd, mlc_path, timeout=cmd_timeout)
        else:
            self._os.execute_async(mlc_cmd, mlc_path)

    def read_msr(self, msr_add: hex, squash: bool = True) -> hex:
        """
        Attempts to read MSR through OS and if it fails, revert to ITP
        :param msr_add: address of MSR to be read
        :param squash: If True, will check that all threads returned the same value, and return that single value.
                       Otherwise, a list of each thread's result will be returned.
        :return: Value of MSR.
        """
        if self._os.is_alive():
            self.install_rdmsr_cpuid()
            msr_value = self._common_content_lib.execute_sut_cmd(self.MSR_CMD.format(msr_add), "msr_cmd",
                                                                 self.EXECUTION_TIMEOUT)
            if not msr_value:
                msr_value = super(LinuxSGXDriver, self).read_msr(msr_add)
            else:
                msr_value = hex(int(msr_value, 16))
        else:
            msr_value = super(LinuxSGXDriver, self).read_msr(msr_add)
        return msr_value

    def read_cpuid(self, cpuid_leaf: hex, cpuid_registry: str) -> str:
        """
        Attempts to read Cpuid MSR through OS and if it fails, revert to ITP
        :param cpuid_leaf: address of MSR to be read.
        :param cpuid_registry: Registry type could be any one value eax, ebx, ecx and edx
        :return: Value of MSR
        """
        epuid_exp = self.CPUID_EXP.format(cpuid_registry)
        cmd = self.CPUID_CMD.format(cpuid_leaf)
        if self._os.is_alive():
            self.install_rdmsr_cpuid()
            cpuid_value = self._common_content_lib.execute_sut_cmd(cmd, "cpuid_cmd", self.EXECUTION_TIMEOUT)
            self._log.debug("Output of cpuid cmd {} is {}".format(cmd, cpuid_value))
            cpuid_value = re.findall(epuid_exp, cpuid_value)[0].strip()
            self._log.info("SGX EAX CPUID %s value is :%s", hex(cpuid_leaf), cpuid_value)
            if not cpuid_value:
                cpuid_value = super(LinuxSGXDriver, self).read_cpuid(cpuid_leaf, cpuid_registry)
        else:
            cpuid_value = super(LinuxSGXDriver, self).read_cpuid(cpuid_leaf, cpuid_registry)
        return cpuid_value

    def install_rdmsr_cpuid(self) -> None:
        """
        Install RDMSR and Cpuid rpm module if not already installed.
        :return: None
        """
        if not self._install_collateral.yum_verify_package(self.MSR_REPO):
            self._rdmsr_and_cpuid_obj.install_msr_tools()
        if not self._install_collateral.yum_verify_package(self.CPUID_REPO):
            self._rdmsr_and_cpuid_obj.install_cpuid()

    def execute_fvt_and_app_test(self) -> None:
        """
        This function install SGX PSW and SGX FVT tool installation, run sgx test app.

        :raise: content_exceptions.TestFail if Sgx Run App test has failures.
        :return: None
        """
        self._log.info("checking SGX data sealing")
        self.check_psw_installation()
        self.install_sdk()
        if not self.run_sgx_app_test():
            raise content_exceptions.TestFail("./sgx_app -auto have failures")
        self.copy_fvt_tool()
        self.execute_functional_validation_tool()
