#!/usr/bin/env python
###############################################################################
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
###############################################################################
import time
import sys
import re
from collections import OrderedDict
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.private.cl_utils.adapter import data_types

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.dtaf_content_constants import ProviderXmlConfigs
from src.lib.bios_util import SerialBiosUtil
from src.lib.dtaf_content_constants import NumberFormats
from src.lib.bios_constants import IntelSSTTable as ist
from src.lib.bios_constants import BiosSerialPathConstants


class IntelSSTConfig:
    BASE = "Base"
    Config1 = "Config 1"
    Config2 = "Config 2"


class IntelSSTCommon(ContentBaseTestCase):
    """IntelSSTCommon class for intel speed select technology"""

    REGEX_SST_PP = r"Intel.*SST-PP.*is\ssupported"
    __CORE_COUNT_MSR = 0x35
    TDP_VALUE_MSR = 0x649
    __TDP_CONFIG_MSR = 0x64B
    RATIO_MSR = 0x198
    TDP_P1_RATIO_NORMAL_CONFIG_MSR = 0x648
    TDP_VALUE_CONFIG2 = 0x64A
    __THREAD_COUNT_INDICES = [0, 15]
    __CORE_COUNT_INDICES = [16, 31]
    __TDP_VALUE_INDECES = [0, 14]
    __TDP_CONFIG_INDICES = [0, 1]
    __IO_WP_IA_CV_PS_INDICES = [19, 27]
    TDP_RATIO_INDICES = [16, 23]
    RATIO_MSR_INDICES = [8, 14]
    TDP_RATIO_NORMAL_CONFIG_INDICES = [0, 7]

    MSR_x35 = 0x35
    MSR_648 = 0x648
    MSR_649 = 0x649
    MSR_64A = 0x64A
    MSR_64B = 0x64B
    MSR_198 = 0x198
    INDICES_0_1 = [0, 1]
    INDICES_0_7 = [0, 7]
    INDICES_0_14 = [0, 14]
    INDICES_0_15 = [0, 15]
    INDICES_8_14 = [8, 14]
    INDICES_16_23 = [16, 23]
    INDICES_16_31 = [16, 31]
    INDICES_19_27 = [19, 27]

    TDP_CONFIG_DICT = {
        IntelSSTConfig.BASE: [0],
        IntelSSTConfig.Config1: [1, 3],
        IntelSSTConfig.Config2: [2, 4]
    }
    P1_RATIO_PREFIX = "pcudata.resolved_ia_config_tdp_ratios"
    P1_RATIO_LIST = [
        "%s_0" % P1_RATIO_PREFIX,
        "%s_1" % P1_RATIO_PREFIX,
        "%s_2" % P1_RATIO_PREFIX,
        "%s_3" % P1_RATIO_PREFIX,
        "%s_4" % P1_RATIO_PREFIX,
    ]
    ISS_MAX_KNOB = "IssMaxLevel"
    MAX_SUPPORT_LEVEL = 4
    NO_SQUASH_MSR = [408]  # 0x198 = 408
    SST_BF_KNOB = 'Activate SST-BF'
    _REQUIRED_VALUES_FROM_BIOS_PAGE = []
    DEFAULT_ERROR_MESSAGE = "Check and close RAPL, EET and other power capping features, to make sure CPU and turbo " \
                            "to TDP"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of IntelSSTCommon

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(IntelSSTCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path=bios_config_file_path)
        self._cfg = cfg_opts
        self.platform = self._common_content_lib.get_platform_family()
        self._log.debug("Platform name is %s", self.platform)
        try:
            self.IntelSSTTable = eval("ist.%s" % (self.platform.upper()))
        except AttributeError:
            raise content_exceptions.TestError("Intel SST Table info is not defined for %s family, please define it for"
                                               " %s in bios_constants.py" % (self.platform, self.platform))
        self.load_required_bios_values()
        sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(sdp_cfg, test_log)
        self.serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)

    def load_required_bios_values(self):
        """Loads the required bios values"""
        self._REQUIRED_VALUES_FROM_BIOS_PAGE = [self.IntelSSTTable.INTEL_SST, self.IntelSSTTable.CORE_COUNT,
                                                self.IntelSSTTable.P1_RATIO, self.IntelSSTTable.PACKAGE_TDP,
                                                self.IntelSSTTable.TJMAX]

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(IntelSSTCommon, self).prepare()

    def get_msr_values(self, msrs, convert_to="hex"):
        """This function gets the msr values in the python dict format
        :param convert_to: Converts to hex
        :param msrs: msr addrs
        :return: returns the Python dictionary format
        """
        msr_values = {}
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.halt()
            for msr in msrs:
                if msr in self.NO_SQUASH_MSR:
                    msr_values[hex(msr)] = hex(self.sdp.msr_read(msr, squash=False)).strip("L").strip("H")
                else:
                    msr_values[hex(msr)] = hex(self.sdp.msr_read(msr, squash=True)).strip("L").strip("H")
        except Exception as e:
            self._log.error("Unknown exception while getting msr value")
        finally:
            self.sdp.go()
        self._log.debug("MSR values in default format:%s", msr_values)
        converted_numbers = self._common_content_lib.convert_hexadecimal(msr_values.values(), to=convert_to)
        for msr in msr_values:
            msr_values[msr] = converted_numbers[msr_values[msr]]
        self._log.debug("MSR values in %s format:%s", convert_to, msr_values)
        return msr_values

    def get_core_count(self):
        """Gets the core count from the intel sst python sv command"""
        msr_values = self.get_msr_values([self.__CORE_COUNT_MSR], convert_to=NumberFormats.BINARY)
        if not len(msr_values):
            raise content_exceptions.TestError("Failed to get core count from %s (intel sst)" % self.__CORE_COUNT_MSR)
        core_count_binary = self._common_content_lib.get_binary_bit_range(msr_values[hex(self.__CORE_COUNT_MSR)],
                                                                          self.__CORE_COUNT_INDICES)
        self._log.debug("Core count in binary format %s", core_count_binary)
        return self._common_content_lib.convert_binary_to_decimal(core_count_binary)

    def get_p1_ratio(self, sst_config, TDP_LEVEL='0'):
        """Gets the core count from the intel sst python sv command"""
        if sst_config == IntelSSTConfig.BASE:
            msr_values = self.get_msr_values([self.TDP_P1_RATIO_NORMAL_CONFIG_MSR], convert_to=NumberFormats.BINARY)
            if not len(msr_values):
                raise content_exceptions.TestError(
                    "Failed to get p1 ratio from %s (intel sst)" % self.TDP_P1_RATIO_NORMAL_CONFIG_MSR)
            p1_ratio_binary = self._common_content_lib.get_binary_bit_range(msr_values
                                                                            [hex(self.TDP_P1_RATIO_NORMAL_CONFIG_MSR)],
                                                                            self.TDP_RATIO_NORMAL_CONFIG_INDICES)
            self._log.debug("Current P1 ratio in binary format %s", p1_ratio_binary)
            return self._common_content_lib.convert_binary_to_decimal(p1_ratio_binary)
        else:
            tdp_config_value = TDP_LEVEL

            p1_ratios = self._common_content_lib.execute_pythonsv_function(IntelSSTCommon.get_config_tdp_ratio_pythonsv)
            self._log.info("P1 ratios: %s", p1_ratios)
            p1_ratio = hex(p1_ratios[self.P1_RATIO_PREFIX + "_" + str(tdp_config_value)]).strip("L").strip('H')
            return self._common_content_lib.convert_hexadecimal([p1_ratio], to=NumberFormats.DECIMAL)[p1_ratio]

    def get_package_tdp_value(self):
        """Gets the TDP config value"""
        msr_values = self.get_msr_values([self.TDP_VALUE_MSR], convert_to=NumberFormats.BINARY)
        if not len(msr_values):
            raise content_exceptions.TestError("Failed to get TDP value from %s (intel sst)" % self.TDP_VALUE_MSR)
        tdp_in_binary = self._common_content_lib.get_binary_bit_range(msr_values[hex(self.TDP_VALUE_MSR)],
                                                                      self.__TDP_VALUE_INDECES)
        self._log.debug("TDP value in binary format %s", tdp_in_binary)
        return self._common_content_lib.convert_binary_to_decimal(tdp_in_binary)

    def get_tdp_config_value(self):
        """Gets the TDP config value"""
        msr_values = self.get_msr_values([self.__TDP_CONFIG_MSR], convert_to=NumberFormats.BINARY)
        if not len(msr_values):
            raise content_exceptions.TestError("Failed to get TDP Config value from %s (intel sst)"
                                               % self.__TDP_CONFIG_MSR)
        tdp_in_binary = self._common_content_lib.get_binary_bit_range(msr_values[hex(self.__TDP_CONFIG_MSR)],
                                                                      self.__TDP_CONFIG_INDICES)
        self._log.debug("TDP config value in binary format %s", tdp_in_binary)
        return self._common_content_lib.convert_binary_to_decimal(tdp_in_binary)

    def navigate_intel_sst_config_path(self):
        """Navigate to Intel Speed Select table info"""

        success, msg = self.serial_bios_util.navigate_bios_menu()
        if not success:
            raise content_exceptions.TestFail(msg)
        try:
            serial_path = BiosSerialPathConstants.INTEL_SST_BIOS_PATH[self.platform.upper()]
        except KeyError:
            raise content_exceptions.TestError("Bios serial path of %s family is not defined for Intel SST" %
                                               self.platform)
        self.serial_bios_util.select_enter_knob(serial_path)

    def check_is_iss_supported(self):
        """
        This method is to check whether ISS support on SUT
        raise : raise exception if does not supports
        """
        intel_speed_select_info_cmd = "intel-speed-select -info"
        intel_speed_select_info_res_temp = self.os.execute(intel_speed_select_info_cmd, self._command_timeout)
        intel_speed_select_info_res = intel_speed_select_info_res_temp.stdout + "\n" + intel_speed_select_info_res_temp.stderr
        regex_res = re.findall(self.REGEX_SST_PP, intel_speed_select_info_res)
        if len(regex_res) == 0:
            raise content_exceptions.TestFail("SST PP does not supported in the SKU")

    def get_intel_sst_info_bios(self, sst_config="Base"):
        """Navigate and gets the Intel Speed Select table info"""
        self.navigate_intel_sst_config_path()
        time.sleep(10)
        bios_info = self.serial_bios_util.get_current_screen_info()
        self._log.info("Bios screen info: %s", bios_info)
        bios_info = bios_info[0]
        info_dict = {}
        count = 0
        found = 0
        for item in bios_info:
            if item.strip() in 'Level  Capable  Count   Ratio   TDP (W)  DTS_Max':
                found = 1
                continue
            if found and count < 3:
                count += 1
                temp = {}
                value_list = item.split()
                if len(value_list) != 6:
                    raise content_exceptions.TestFail("Not found expected number of INTEL SST Details. "
                                                      "Please verify the BIOS details")
                temp[self.IntelSSTTable.CORE_COUNT] = value_list[2]
                temp[self.IntelSSTTable.P1_RATIO] = value_list[3]
                temp[self.IntelSSTTable.PACKAGE_TDP] = value_list[4]
                temp[self.IntelSSTTable.TJMAX] = value_list[5]
                info_dict[value_list[0]] = temp

        if len(info_dict) == 0:
            raise content_exceptions.TestFail("Failed to get the intel SST details from the bios page")
        self._log.info("Intel SST table info from Bios is %s", info_dict)
        return info_dict

    def get_intel_sst_info_pythonsv(self, sst_config):
        """Gets the sst info from the PythonSV"""
        required_info = {}
        required_info[self.IntelSSTTable.CORE_COUNT] = self.get_core_count()
        required_info[self.IntelSSTTable.PACKAGE_TDP] = self.get_package_tdp_value()
        required_info[self.IntelSSTTable.P1_RATIO] = self.get_p1_ratio(sst_config)
        return required_info

    def get_uncore_pcodeio_map_show_search_io_wp_ia_cv_ps(self):
        final_dict_raw = self._common_content_lib.execute_pythonsv_function\
            (IntelSSTCommon.uncore_pcodeio_map_show_search_io_wp_ia_cv_ps)
        self._log.debug("all registers and its values: %s", final_dict_raw)
        final_dict = {}
        converted_dict = self._common_content_lib.convert_hexadecimal(final_dict_raw.values(), to=NumberFormats.BINARY)
        for key, value in final_dict_raw.items():
            final_dict[key] = int(
                self._common_content_lib.get_binary_bit_range(converted_dict[value], self.__IO_WP_IA_CV_PS_INDICES), 2)
        self._log.debug("all registers and its values after slice with the specific range: %s", final_dict)
        return final_dict

    def check_fuses_pcode_show_search_config_tdp(self):
        final_dict_raw = self._common_content_lib.execute_pythonsv_function(
            IntelSSTCommon.fuses_pcode_show_search_config_tdp)
        self._log.debug("all registers and its values: %s", final_dict_raw)
        if not len(final_dict_raw):
            raise content_exceptions.TestFail('sv.sockets.showsearch("pcode_config_tdp") did not show '
                                              'expected result')

    @staticmethod
    def get_config_tdp_ratio_pythonsv(pythonsv, log):
        si_cfg = ElementTree.fromstring(ProviderXmlConfigs.SDP_XML_CONFIG)
        sdp = ProviderFactory.create(si_cfg, log)  # type: SiliconDebugProvider
        sdp.itp.unlock()  # TODO: Waiting for better implementation
        pythonsv.refresh()
        ratio_dict = {}
        for ratio in IntelSSTCommon.P1_RATIO_LIST:
            ratio_dict[ratio] = pythonsv.get_by_path(scope=SiliconRegProvider.SOCKET, reg_path=ratio)
        print(ratio_dict)
        return ratio_dict

    @staticmethod
    def uncore_pcodeio_map_show_search_io_wp_ia_cv_ps(pythonsv, log):
        si_cfg = ElementTree.fromstring(ProviderXmlConfigs.SDP_XML_CONFIG)
        sdp = ProviderFactory.create(si_cfg, log)  # type: SiliconDebugProvider
        search_keyword = "io_wp_ia_cv_ps"
        log_file_name = "%s.log" % (search_keyword)
        sdp.itp.unlock()  # TODO: Waiting for better implementation
        pythonsv.refresh()
        final_dict = {}
        try:
            sdp.halt()
            sdp.start_log(log_file_name)
            pythonsv.show_search(scope=SiliconRegProvider.UNCORE, keyword=search_keyword)
            sdp.stop_log()
            with open(log_file_name) as f:
                for line in f:
                    if "pcodeio_map.%s_" % search_keyword in line.strip():
                        if line.strip().split("=")[0].strip() not in final_dict.keys():
                            final_dict[line.strip().split("=")[0].strip()] = line.strip().split("=")[-1].strip()
        except Exception as e:
            raise e
        finally:
            sdp.go()
        print(final_dict)
        return final_dict

    @staticmethod
    def fuses_pcode_show_search_config_tdp(pythonsv, log):
        si_cfg = ElementTree.fromstring(ProviderXmlConfigs.SDP_XML_CONFIG)
        sdp = ProviderFactory.create(si_cfg, log)  # type: SiliconDebugProvider
        search_keyword = "pcode_config_tdp"
        log_file_name = "%s.log" % (search_keyword)
        sdp.itp.unlock()  # TODO: Waiting for better implementation
        pythonsv.refresh()
        final_dict = {}
        try:
            sdp.halt()
            sdp.start_log(log_file_name)
            pythonsv.show_search(scope=SiliconRegProvider.SOCKET, keyword=search_keyword)
            sdp.stop_log()
            with open(log_file_name) as f:
                for line in f:
                    if "punit.%s_" % search_keyword in line.strip():
                        if line.strip().split("=")[0].strip() not in final_dict.keys():
                            final_dict[line.strip().split("=")[0].strip()] = line.strip().split("=")[-1].strip()
        except Exception as e:
            raise e
        finally:
            sdp.go()
        print(final_dict)
        return final_dict

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        super(IntelSSTCommon, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if IntelSSTCommon.main() else Framework.TEST_RESULT_FAIL)
