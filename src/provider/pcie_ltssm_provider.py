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
import time

from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass
from collections import OrderedDict
from numpy import random

from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.provider.base_provider import BaseProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import ProductFamilies
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


class SiliconRegLtssmProviderName:
    LtssmProviderCscripts = "cscripts"
    LtssmProviderPythonsv = "pythonsv"


@add_metaclass(ABCMeta)
class PcieLtssmToolProvider(BaseProvider):
    """ Class to provide Pcie Ltssm Tool execution """

    PCIE_TRANSFER_RATE_TO_GEN_DICT = {"5GT/s": 2, "8GT/s": 3, "16GT/s": 4, "32GT/s": 5}

    def __init__(self, log, cfg_opts, os_obj, pcie_provider_obj):
        """
        Create a new PcieLtssmToolProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param pcie_provider_obj
        """
        super(PcieLtssmToolProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._sut_os = self._os.os_type

        #  common_content_obj and config object
        self.common_content_lib_obj = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

    @staticmethod
    def factory(log, cfg_opts, os_obj, pcie_provider_obj=None, silicon_reg_ltssm_provider=None):
        """
        To create a factory object based on the configuration xml file.
        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        :param pcie_provider_obj
        :param silicon_reg_ltssm_provider - indicate the debug tool provider to use to run LTSSM testing instead of ltssmtool

        :return: object
        """

        package = r"src.provider.pcie_ltssm_provider"
        if silicon_reg_ltssm_provider == SiliconRegLtssmProviderName.LtssmProviderCscripts:
            mod_name = "CscriptsLtssmProvider"
        elif silicon_reg_ltssm_provider.lower() == SiliconRegLtssmProviderName.LtssmProviderPythonsv:
            mod_name = "PythonsvLtssmProvider"
        elif OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsLtssmProvider"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxLtssmProvider"
        else:
            raise NotImplementedError("Test is not implemented for %s or %s" % (os_obj.os_type, silicon_reg_ltssm_provider))
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log=log, cfg_opts=cfg_opts, os_obj=os_obj, pcie_provider_obj=pcie_provider_obj)

    @abstractmethod
    def install_ltssm_tool(self):
        """
        This method is to install ltssm tool on SUT.

        :return sut folder path
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def run_ltssm_tool(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None,
                       disable_kernel_driver=True):
        """
        This method is to run the ltssm tool.

        :param test_name
        :param device_id
        :param cmd_path
        :param skip_errors_on_failures
        :param bdf
        :param disable_kernel_driver
        :raise NotImplementedError

        return speed, width
        """
        raise NotImplementedError

    @abstractmethod
    def run_ltssm_tool_var_speed_grades(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None,
                                        disable_kernel_driver=True):
        """
        This method is to run the ltssm tool for varies speed grades.

        :param test_name -contain which Test to execute like sbr.
        :param device_id -device id of pcie device
        :param cmd_path - tool dir.
        :param skip_errors_on_failures- This will not raise if TestCase is failed. Proceed for other remaining test.
        :param bdf - Pcie device bus device function
        :param disable_kernel_driver - It will disable kernel driver
        :raise content_exception
        :return grades, width
        """
        raise NotImplementedError


class WindowsLtssmProvider(PcieLtssmToolProvider):
    """ Class to provide ltssm Tool functionality for windows platform """
    LTSSM_TOOL_CMD = "LTSSMtool.exe {} {} [{},{},{}] -w 500"
    LTSSM_ERROR_SUMMARY_REGEX = r"Error\sSummary.*PASSED"
    LTSSM_ERROR_RETRY = "Retry.*\((\d+)\%\)"

    def __init__(self, log, cfg_opts, os_obj, pcie_provider_obj):
        """
        Create a new WindowsLtssmProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(WindowsLtssmProvider, self).__init__(log, cfg_opts, os_obj, pcie_provider_obj)
        self._log = log
        self._os = os_obj
        self._pcie_provider_obj = pcie_provider_obj
        self._number_of_cycle_to_test_ltssm = self._common_content_configuration.get_number_of_cycle_to_test_ltssm()

    def factory(self, log, cfg_opts, os_obj, pcie_provider_obj=None):
        pass

    def install_ltssm_tool(self):
        """
        This method is to install ltssm tool on SUT.

        :return sut_path
        """
        return self._install_collateral.install_ltssm_tool()

    def run_ltssm_tool(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None):
        """
        This method is to run the ltssm tool.

        :param test_name -contain which Test to execute like sbr.
        :param device_id -device id of pcie device
        :param cmd_path - tool dir.
        :param skip_errors_on_failures
        :param bdf
        :raise content_exception
        return speed, width
        """
        lapsed_retry_ltssm = False
        cnt = 0
        if not bdf:
            speed = self._pcie_provider_obj.get_linkcap_speed(device_id)
            width = self._pcie_provider_obj.get_linkstatus_width(device_id)
            bus_id = hex(int(self._pcie_provider_obj.get_device_bus(device_id=device_id)))
        else:
            speed = self._pcie_provider_obj.get_linkcap_speed(device_id)
            width = self._pcie_provider_obj.get_linkstatus_width(device_id)
            bus_id = hex(int(self._pcie_provider_obj.get_device_bus(bdf=bdf)))
        self._log.debug("Negotiable Link Width for device id: {} is {}".format(device_id, width))
        self._pcie_provider_obj.disable_kernel_driver(device_id)
        speed = self.PCIE_TRANSFER_RATE_TO_GEN_DICT[speed]
        self._log.debug("Negotiable Link Speed for device id: {} is {}".format(device_id, speed))
        sut_cmd = self.LTSSM_TOOL_CMD.format(
            test_name, self._number_of_cycle_to_test_ltssm, bus_id, width[1:], speed)
        self._log.debug("command to execute: '{}'".format(sut_cmd))
        while True:
            cmd_output = self.common_content_lib_obj.execute_sut_cmd(sut_cmd=sut_cmd, cmd_str=test_name,
                                                                     execute_timeout=self._command_timeout * 5,
                                                                     cmd_path=cmd_path.strip())
            self._log.info("Output of LTSSM tool testing '{}' are: '{}'".format(test_name, cmd_output))
            reg_output = re.findall(self.LTSSM_ERROR_SUMMARY_REGEX, cmd_output)
            self._log.debug("regex output: {}".format(reg_output))
            cnt += 1
            if not reg_output:
                reg_retry = re.findall(self.LTSSM_ERROR_RETRY, cmd_output)
                if int(reg_retry[0]) != 0:
                    self._log.error("Found Retry error. re-running the ltssm test")
                    if cnt > 1:
                        lapsed_retry_ltssm = True
                        self._log.debug("Re-ran the the ltssm test {} times. returning".format(cnt))
                        break
                    else:
                        continue
                if skip_errors_on_failures:
                    self._log.error("LTSSM Output reported errors, skipping...")
                    return False
                raise content_exceptions.TestFail("LTSSM Output reported errors")
            else:
                break
        if lapsed_retry_ltssm:
            self._log.error("lapsed number of LTSSM retry runs")
            return False
        self._log.debug("LTSSM test passed for '{}' ".format(test_name))

        return speed, width

    def run_ltssm_tool_var_speed_grades(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None,
                                        disable_kernel_driver=True):
        """
        This method is to run the ltssm tool for varies speed grades.

        :param test_name -contain which Test to execute like sbr.
        :param device_id -device id of pcie device
        :param cmd_path - tool dir.
        :param skip_errors_on_failures- This will not raise if TestCase is failed. Proceed for other remaining test.
        :param bdf - Pcie device bus device function
        :param disable_kernel_driver - It will disable kernel driver
        :raise content_exception
        return grades, width
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Windows")


class LinuxLtssmProvider(PcieLtssmToolProvider):
    """ Class to provide Ltssm Tool Test execution for linux platform """

    LTSSM_TOOL_CMD = "./LTSSMtool {} {} [{},{},{}] -w 500"
    LTSSM_ERROR_SUMMARY_REGEX = r"Error\sSummary.*PASSED"
    LTSSM_ERROR_RETRY = "Retry.*\((\d+)\%\)"

    def __init__(self, log, cfg_opts, os_obj, pcie_provider_obj):
        """
        Create a new LinuxLtssmProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(LinuxLtssmProvider, self).__init__(log, cfg_opts, os_obj, pcie_provider_obj)
        self._log = log
        self._os = os_obj
        self._pcie_provider_obj = pcie_provider_obj
        self._number_of_cycle_to_test_ltssm = self._common_content_configuration.get_number_of_cycle_to_test_ltssm()

    def factory(self, log, cfg_opts, os_obj, pcie_provider_obj=None):
        pass

    def install_ltssm_tool(self):
        """
        This method is to install ltssm tool on SUT.

        :return sut folder path
        """
        return self._install_collateral.install_ltssm_tool()

    def run_ltssm_tool(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None,
                       disable_kernel_driver=True):
        """
        This method is to run the ltssm tool.

        :param test_name -contain which Test to execute like sbr.
        :param device_id -device id of pcie device
        :param cmd_path - tool dir.
        :param skip_errors_on_failures- This will not raise if TestCase is failed. Proceed for other remaining test.
        :param bdf - Pcie device bus device function
        :param disable_kernel_driver - It will disable kernel driver
        :raise content_exception
        :return speed, width
        """
        lapsed_retry_ltssm = False
        cnt = 0
        if not bdf:
            speed = self._pcie_provider_obj.get_linkcap_speed(device_id)
            width = self._pcie_provider_obj.get_linkstatus_width(device_id)
            bus_id = self._pcie_provider_obj.get_device_bus(device_id=device_id)
        else:
            speed = self._pcie_provider_obj.get_link_status_speed_by_bdf(bdf)
            width = self._pcie_provider_obj.get_link_status_width_by_bdf(bdf)
            bus_id = self._pcie_provider_obj.get_device_bus(bdf=bdf)
        self._log.debug("Negotiable Link Width for device id: {} is {}".format(device_id, width))
        if disable_kernel_driver:
            self._pcie_provider_obj.disable_kernel_driver(device_id)
        speed = self.PCIE_TRANSFER_RATE_TO_GEN_DICT[speed]
        self._log.debug("Negotiable Link Speed for device id: {} is {}".format(device_id, speed))

        sut_cmd = self.LTSSM_TOOL_CMD.format(
            test_name, self._number_of_cycle_to_test_ltssm, "0x" + bus_id, width[1:], speed)
        self._log.debug("command to execute: '{}'".format(sut_cmd))

        while True:
            cmd_output = self.common_content_lib_obj.execute_sut_cmd(sut_cmd=sut_cmd, cmd_str=test_name,
                                                                     execute_timeout=self._command_timeout*5,
                                                                     cmd_path=cmd_path.strip())
            self._log.info("Output of LTSSM tool testing '{}' are: '{}'".format(test_name, cmd_output))
            reg_output = re.findall(self.LTSSM_ERROR_SUMMARY_REGEX, cmd_output)
            self._log.debug("regex output: {}".format(reg_output))
            cnt += 1
            if not reg_output:
                reg_retry = re.findall(self.LTSSM_ERROR_RETRY,cmd_output)
                if int(reg_retry[0]) != 0:
                    self._log.error("Found Retry error. re-running the ltssm test")
                    if cnt > 1:
                        lapsed_retry_ltssm = True
                        self._log.debug("Re-ran the the ltssm test {} times. returning".format(cnt))
                        break
                    else:
                        continue
                if skip_errors_on_failures:
                    self._log.error("LTSSM Output reported errors, skipping...")
                    return False
                raise content_exceptions.TestFail("LTSSM Output reported errors")
            else:
                break
        if lapsed_retry_ltssm:
            self._log.error("lapsed number of LTSSM retry runs")
            return False
        self._log.debug("LTSSM test passed for '{}' ".format(test_name))

        return speed, width

    def run_ltssm_tool_var_speed_grades(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None,
                                        disable_kernel_driver=True):
        """
        This method is to run the ltssm tool for varies speed grades.

        :param test_name -contain which Test to execute like sbr.
        :param device_id -device id of pcie device
        :param cmd_path - tool dir.
        :param skip_errors_on_failures- This will not raise if TestCase is failed. Proceed for other remaining test.
        :param bdf - Pcie device bus device function
        :param disable_kernel_driver - It will disable kernel driver
        :raise content_exception
        :return grades, width
        """
        if not bdf:
            speed = self._pcie_provider_obj.get_inkcap_speed(device_id)
            width = self._pcie_provider_obj.get_linkstatus_width(device_id)
            bus_id = self._pcie_provider_obj.get_device_bus(device_id=device_id)
        else:
            speed = self._pcie_provider_obj.get_link_status_speed_by_bdf(bdf)
            width = self._pcie_provider_obj.get_link_status_width_by_bdf(bdf)
            bus_id = self._pcie_provider_obj.get_device_bus(bdf=bdf)
        self._log.debug("Negotiable Link Width for device id: {} is {}".format(device_id, width))
        if disable_kernel_driver:
            self._pcie_provider_obj.disable_kernel_driver(device_id)
        speed = self.PCIE_TRANSFER_RATE_TO_GEN_DICT[speed]
        self._log.debug("Negotiable Link Speed for device id: {} is {}".format(device_id, speed))

        grades = OrderedDict()
        grades['up_grade'] = range(1, speed + 1)
        grades['down_grade'] = range(speed, 0, -1)
        grades['random_grade'] = random.permutation(range(1, speed + 1))

        for grade, speed_range in grades.items():
            for speed in speed_range:
                sut_cmd = self.LTSSM_TOOL_CMD.format(
                    test_name, self._number_of_cycle_to_test_ltssm, "0x" + bus_id, width[1:], speed)
                self._log.debug("command to execute: '{}'".format(sut_cmd))
                cmd_output = self.common_content_lib_obj.execute_sut_cmd(sut_cmd=sut_cmd, cmd_str=test_name,
                                                                         execute_timeout=self._command_timeout * 5,
                                                                         cmd_path=cmd_path.strip())
                self._log.info("Output of LTSSM tool testing '{}' {} {} are: '{}'".format(test_name, grade, speed, cmd_output))
                reg_output = re.findall(self.LTSSM_ERROR_SUMMARY_REGEX, cmd_output)
                self._log.debug("regex output for {} and {} speed : {}".format(grade, speed, reg_output))
                if not reg_output:
                    if skip_errors_on_failures:
                        self._log.error("LTSSM Output reported errors, skipping...")
                        return False
                    raise content_exceptions.TestFail("LTSSM Output reported errors")
        self._log.debug("LTSSM test passed for '{}' ".format(test_name))

        return grades, width


class CscriptsLtssmProvider(PcieLtssmToolProvider):
    """ Class to provide Ltssm Tool Test execution for cscripts """

    LTSSM_ERROR_SUMMARY_REGEX = r"No\serrors\sdetected"

    LT_LOOP_TEST_MAPPING = {"sbr": 0, "linkRetrain": 1, "linkDisable": 2, "pml1": 3, "txEqRedo": 4, "SpeedChangeAll": 5,
                            "SpeedChange": 6, "aspml1": 7}
    LT_LOOP_LOG_FILE = "pcie_lt_loop.txt"
    LT_LOOP_NOT_IMPLEMENTED_TEST_LIST = ["flr"]  # some tests like flr are only supported by ltssmtool
    INTEROP_SBR_TEST_CYCLES_LIST = [1, 50, 100]
    INTEROP_SBR_TEST_CYCLES_WAIT_TIME_SEC = 10
    LINK_CHECK_WAIT_TIME_SEC = 0.5  # seconds to wait after link recovery before checking for errors

    def __init__(self, log, cfg_opts, os_obj, pcie_provider_obj):
        """
        Create a new CscriptsLtssmProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(CscriptsLtssmProvider, self).__init__(log, cfg_opts, os_obj, pcie_provider_obj)
        self._log = log
        self._os = os_obj
        self._pcie_provider_obj = pcie_provider_obj
        self._number_of_cycle_to_test_ltssm = self._common_content_configuration.get_number_of_cycle_to_test_ltssm()
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        self._si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(self._si_dbg_cfg, self._log)  # type: SiliconDebugProvider

    def factory(self, log, cfg_opts, os_obj, pcie_provider_obj=None, ltssm_tool=None):
        pass

    def install_ltssm_tool(self):
        """
        Method stub required by the abstract class class, no implementation for CscriptsLtssmProvider
        """
        pass

    def run_ltssm_tool_var_speed_grades(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None,
                                        disable_kernel_driver=True):
        """
        Method stub required by the abstract class class, no implementation for CscriptsLtssmProvider
        """
        pass

    def run_ltssm_tool(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None,
                       disable_kernel_driver=True, interop_sbr_test_cycles_list=[1, 50, 100], pxp_port=None,
                       pxp_socket=None):
        """
        This method is to run the ltssm tool.

        :param test_name
        :param device_id
        :param cmd_path
        :param skip_errors_on_failures
        :param bdf
        :param disable_kernel_driver
        :param interop_sbr_test_cycles_list
        :param pxp_port
        :param pxp_socket
        :raise NotImplementedError

        return speed, width
        """

        if not self._common_content_configuration.get_pcie_ltssm_auto_discovery():
            pxp_port = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()
            pxp_socket = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()

        pciedefs_module_name_dict = {ProductFamilies.SPR: "sprpciedefs",
                                     ProductFamilies.GNR: "gnrpciedefs",
                                     ProductFamilies.EMR: "emrpciedefs"}

        pciedefs_module_path_dict = {ProductFamilies.SPR: "platforms.SPR." + pciedefs_module_name_dict[ProductFamilies.SPR],
                                     ProductFamilies.GNR: "platforms.GNR." + pciedefs_module_name_dict[ProductFamilies.GNR],
                                     ProductFamilies.EMR: "platforms.EMR." + pciedefs_module_name_dict[ProductFamilies.EMR]}

        silicon_cpu_family = self._cscripts_obj.silicon_cpu_family
        if silicon_cpu_family not in pciedefs_module_path_dict.keys():
            raise NotImplementedError

        mod_path = pciedefs_module_path_dict[silicon_cpu_family]
        mod_name = pciedefs_module_name_dict[silicon_cpu_family]

        pcie_functions_module = getattr(import_module(mod_path), mod_name)
        pcie_functions = pcie_functions_module()

        if not bdf:
            speed = self._pcie_provider_obj.get_linkcap_speed(device_id)
            width = self._pcie_provider_obj.get_linkstatus_width(device_id)
        else:
            speed = self._pcie_provider_obj.get_link_status_speed_by_bdf(bdf)
            width = self._pcie_provider_obj.get_link_status_width_by_bdf(bdf)
        self._log.debug("Negotiable Link Width for device id: {} is {}".format(device_id, width))
        if disable_kernel_driver:
            self._pcie_provider_obj.disable_kernel_driver(device_id)
        speed = self.PCIE_TRANSFER_RATE_TO_GEN_DICT[speed]
        self._log.debug("Negotiable Link Speed for device id: {} is {}".format(device_id, speed))

        self._sdp.start_log(self.LT_LOOP_LOG_FILE)
        self._sdp.halt_and_check()
        if test_name in self.LT_LOOP_NOT_IMPLEMENTED_TEST_LIST:
            raise NotImplementedError("Test %s is not implemented by ltssm provider" % test_name)
        if test_name == "sbr":
            for num_of_cycles in interop_sbr_test_cycles_list:
                if num_of_cycles == interop_sbr_test_cycles_list[-1]:
                    time.sleep(self.INTEROP_SBR_TEST_CYCLES_WAIT_TIME_SEC)
                self.run_ltssm_cmd(pcie_functions, test_name, num_of_cycles, pxp_port, pxp_socket)
            self._sdp.stop_log()
            if not self.check_ltssm_test_passed(skip_errors_on_failures):
                return False

            # 1 more cycle for SBR Test
            self.run_ltssm_cmd(pcie_functions, test_name, self._number_of_cycle_to_test_ltssm, pxp_port, pxp_socket)
            time.sleep(self.INTEROP_SBR_TEST_CYCLES_WAIT_TIME_SEC)
        else:
            self.run_ltssm_cmd(pcie_functions, test_name, self._number_of_cycle_to_test_ltssm, pxp_port, pxp_socket)
            self._sdp.stop_log()
            if not self.check_ltssm_test_passed(skip_errors_on_failures):
                return False
        self._log.debug("LTSSM test passed for '{}' ".format(test_name))
        self._sdp.go()

        return speed, width

    def run_ltssm_cmd(self, pcie_functions, test_name, num_of_cycles, pxp_port, pxp_socket):
        """
        This method triggers the ltssm command for the given cycles.

        :param pcie_functions: pcie function object
        :param test_name: test name
        :param num_of_cycles: number of iterations
        :param pxp_port
        :param pxp_socket
        :return None
        """
        self._log.debug(
            "Running %s iteration(s) of lt_loop %s test on socket %s, %s" % (num_of_cycles, test_name, pxp_socket,
                                                                             pxp_port))
        pcie_functions.lt_loop(int(pxp_socket), pxp_port, int(self._number_of_cycle_to_test_ltssm),
                               self.LT_LOOP_TEST_MAPPING[test_name], delayErrorCheck=self.LINK_CHECK_WAIT_TIME_SEC)

    def check_ltssm_test_passed(self, skip_errors_on_failures=False):
        """
        This method verify the ltssm test from the lt_loop_log_file.

        :param skip_errors_on_failures: flag to skip or not skip the errors
        :return True/False
        """
        with open(self.LT_LOOP_LOG_FILE) as log_file:
            cmd_output = log_file.read()
            reg_output = re.findall(self.LTSSM_ERROR_SUMMARY_REGEX, cmd_output, re.I)

            if not reg_output:
                if skip_errors_on_failures:
                    self._log.error("LTSSM Output reported errors, skipping...")
                    return False
                self._sdp.go()
                raise content_exceptions.TestFail("LTSSM Output reported errors")
        return True


class PythonsvLtssmProvider(PcieLtssmToolProvider):
    """ Class to provide Ltssm Tool Test execution for Pythonsv """


    LT_LOOP_TEST_MAPPING = {"sbr": 0, "linkRetrain": 1, "linkDisable": 2, "pml1": 3, "txEqRedo": 4, "SpeedChangeAll": 5,
                            "SpeedChange": 6, "aspml1": 7, "dlw": 8}
    LT_LOOP_LOG_FILE = "pcie_lt_loop.txt"
    LT_LOOP_NOT_IMPLEMENTED_TEST_LIST = ["flr"]  # some tests like flr are only supported by ltssmtool
    INTEROP_SBR_TEST_CYCLES_WAIT_TIME_SEC = 10
    LINK_CHECK_WAIT_TIME_SEC = 0.5

    def __init__(self, log, cfg_opts, os_obj, pcie_provider_obj):
        """
        Create a new PythonsvLtssmProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(PythonsvLtssmProvider, self).__init__(log, cfg_opts, os_obj, pcie_provider_obj)
        self._log = log
        self._os = os_obj
        self._pcie_provider_obj = pcie_provider_obj
        self._number_of_cycle_to_test_ltssm = self._common_content_configuration.get_number_of_cycle_to_test_ltssm()
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._pythonsv_obj = ProviderFactory.create(self.sil_cfg, self._log)
        self._si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(self._si_dbg_cfg, self._log)  # type: SiliconDebugProvider

        from pysvtools.pciedebug.ltssm import runSBR, runRecovery, runLinkDisable, runPML1, runTxEqRedo, \
             runSpeedChangeAll, runSpeedChange, runASPML1, runDLW

        self.test_type_dict = {
            self.LT_LOOP_TEST_MAPPING["sbr"]: runSBR,
            self.LT_LOOP_TEST_MAPPING["linkRetrain"]: runRecovery,
            self.LT_LOOP_TEST_MAPPING["linkDisable"]: runLinkDisable,
            self.LT_LOOP_TEST_MAPPING["pml1"]: runPML1,
            self.LT_LOOP_TEST_MAPPING["txEqRedo"]: runTxEqRedo,
            self.LT_LOOP_TEST_MAPPING["SpeedChangeAll"]: runSpeedChangeAll,
            self.LT_LOOP_TEST_MAPPING["SpeedChange"]: runSpeedChange,
            self.LT_LOOP_TEST_MAPPING["aspml1"]: runASPML1,
            self.LT_LOOP_TEST_MAPPING["dlw"]: runDLW
        }

    def factory(self, log, cfg_opts, os_obj, pcie_provider_obj=None, ltssm_tool=None):
        pass

    def install_ltssm_tool(self):
        """
        Method stub required by the abstract class class, no implementation for PythonsvLtssmProvider
        """
        pass

    def run_ltssm_tool_var_speed_grades(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None,
                                        disable_kernel_driver=True):
        """
        Method stub required by the abstract class class, no implementation for PythonsvLtssmProvider
        """
        pass

    def lt_loop_wrapper(self, socket, ports, loop_count, test_type_index):
        """
        Custom wrapper for running lt loop tests for pythonsv.

        :param socket: Socket number.
        :param ports: the port(s) to run test on.
        :param loop_count: Number of loops to run.
        :param testTypeIndex: Specify which test to run.
                              0 - runSBR
                              1 - runRecovery
                              2 - runLinkDisable
                              3 - runPML1
                              4 - runTxEqRedo
                              5 - runSpeedChangeAll
                              6 - runSpeedChange
                              7 - runASPML1
                              8 - runDLW
        :return: A list of Device() objects containing details about any errors found.
        """
        port_list = [ports]
        if isinstance(ports, list):
            port_list = ports

        import pysvtools.pciedebug.ltssm as ltssm
        dev_list = []
        for port in port_list:
            (width, speed) = ltssm.ltssm(socket, port)
            dev_list.append([socket, port, width, speed])

        results = self.test_type_dict[test_type_index](int(loop_count), *dev_list)
        return results

    def run_ltssm_tool(self, test_name, device_id, cmd_path, skip_errors_on_failures=False, bdf=None,
                       disable_kernel_driver=True, interop_sbr_test_cycles_list=[1, 50, 100], pxp_port=None,
                       pxp_socket=None):
        """
        This method is to run the ltssm tool.

        :param test_name
        :param device_id
        :param cmd_path
        :param skip_errors_on_failures
        :param bdf
        :param disable_kernel_driver
        :param interop_sbr_test_cycles_list
        :param pxp_port
        :param pxp_socket
        :raise NotImplementedError

        return speed, width
        """

        if not self._common_content_configuration.get_pcie_ltssm_auto_discovery():
            pxp_port = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()
            pxp_socket = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()

        if not bdf:
            speed = self._pcie_provider_obj.get_linkcap_speed(device_id)
            width = self._pcie_provider_obj.get_linkstatus_width(device_id)
        else:
            speed = self._pcie_provider_obj.get_link_status_speed_by_bdf(bdf)
            width = self._pcie_provider_obj.get_link_status_width_by_bdf(bdf)
        self._log.debug("Negotiable Link Width for device id: {} is {}".format(device_id, width))
        if disable_kernel_driver:
            self._pcie_provider_obj.disable_kernel_driver(device_id)
        speed = self.PCIE_TRANSFER_RATE_TO_GEN_DICT[speed]
        self._log.debug("Negotiable Link Speed for device id: {} is {}".format(device_id, speed))

        self._sdp.start_log(self.LT_LOOP_LOG_FILE)
        self._sdp.halt_and_check()
        if test_name in self.LT_LOOP_NOT_IMPLEMENTED_TEST_LIST:
            raise NotImplementedError("Test %s is not implemented by ltssm provider" % test_name)
        results = []
        if test_name == "sbr":
            for num_of_cycles in interop_sbr_test_cycles_list:
                if num_of_cycles == interop_sbr_test_cycles_list[-1]:
                    time.sleep(self.INTEROP_SBR_TEST_CYCLES_WAIT_TIME_SEC)
                results = self.run_ltssm_cmd(results, test_name, num_of_cycles, pxp_port, pxp_socket)
            self._sdp.stop_log()
            if not self.check_ltssm_test_passed(results, skip_errors_on_failures):
                return False

            # 1 more cycle for SBR Test
            self.run_ltssm_cmd(results, test_name, self._number_of_cycle_to_test_ltssm, pxp_port, pxp_socket)
            time.sleep(self.INTEROP_SBR_TEST_CYCLES_WAIT_TIME_SEC)
        else:
            results = self.run_ltssm_cmd(results, test_name, self._number_of_cycle_to_test_ltssm, pxp_port, pxp_socket)
            self._sdp.stop_log()
            if not self.check_ltssm_test_passed(results, skip_errors_on_failures):
                return False
        self._log.debug("LTSSM test passed for '{}' ".format(test_name))
        self._sdp.go()

        return speed, width

    def run_ltssm_cmd(self, results, test_name, num_of_cycles, pxp_port, pxp_socket):
        """
        This method triggers the ltssm command for the given cycles.

        :param results: result list
        :param test_name: test name
        :param num_of_cycles: number of iterations
        :param pxp_port
        :param pxp_socket
        :return results: result list
        """
        self._log.debug(
            "Running %s iteration(s) of lt_loop %s test on socket %s, %s" % (num_of_cycles, test_name,
                                                                             pxp_socket,
                                                                             pxp_port))
        results.extend(self.lt_loop_wrapper(int(pxp_socket), pxp_port, num_of_cycles,
                                            self.LT_LOOP_TEST_MAPPING[test_name]))
        return results

    def check_ltssm_test_passed(self, results, skip_errors_on_failures=False):
        """
        This method verify the ltssm test from the result list.

        :param results: result list
        :param skip_errors_on_failures: flag to skip or not skip the errors
        :return True/False
        """
        for result in results:
            if result.has_errors:
                if skip_errors_on_failures:
                    self._log.error("LTSSM Output reported errors, skipping...")
                    return False
                self._sdp.go()
                raise content_exceptions.TestFail("LTSSM Output reported errors")
        return True
