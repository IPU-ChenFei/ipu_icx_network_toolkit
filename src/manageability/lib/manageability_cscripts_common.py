#!/usr/bin/env python
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and propri-
# etary and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be ex-
# press and approved by Intel in writing.

from dtaf_core.providers.provider_factory import ProviderFactory

from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.lib.content_base_test_case import ContentBaseTestCase


class ManageabilityCscriptsCommon(ContentBaseTestCase):
    """
    Base class extension for ManageabilityCscriptsCommon which holds common functionality
    """
    _BASE_16 = 16
    _DIVIDER_VALUE_TO_CONVERT_POWER_TO_WATT = 8

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ManageabilityCscriptsCommon object

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(ManageabilityCscriptsCommon, self).__init__(test_log, arguments, cfg_opts)

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        self._sv = self._cscripts.get_cscripts_utils().getSVComponent()

    def convert_power_to_watt(self, power_in_hex):
        """
        This method converts Hexadecimal Power to Decimal Power in Watt.

        :return: Decimal Value
        """
        power = hex(power_in_hex)
        power_in_decimal = int(power, self._BASE_16)
        return power_in_decimal / self._DIVIDER_VALUE_TO_CONVERT_POWER_TO_WATT

    def get_cscripts_min_power_value(self):
        """
        This method will fetch Min Power Wattage using cscripts.

        :return:
        """
        try:
            min_power_socket0 = 0
            min_power_socket1 = 0
            self._sv.refresh()
            self._log.info("Get values of min_power per socket.")
            if not len(self._cscripts.get_sockets()) >= 2:
                log_error = "Requires minimum of 2 sockets "
                self._log.error(log_error)
                raise RuntimeError(log_error)

            if self._cscripts.silicon_cpu_family in [ProductFamilies.CLX, ProductFamilies.SKX,
                                                     ProductFamilies.CPX]:
                min_power_socket0 = self._cscripts.get_sockets()[0].uncore0.pcu_cr_package_power_sku_cfg.pkg_min_pwr
                min_power_socket1 = self._cscripts.get_sockets()[1].uncore0.pcu_cr_package_power_sku_cfg.pkg_min_pwr

            if self._cscripts.silicon_cpu_family in [ProductFamilies.ICX, ProductFamilies.SNR,
                                                     ProductFamilies.SPR]:
                min_power_socket0 = self._cscripts.get_sockets()[0].uncore.punit.package_power_sku.pkg_min_pwr
                min_power_socket1 = self._cscripts.get_sockets()[1].uncore.punit.package_power_sku.pkg_min_pwr

            min_power = self.convert_power_to_watt(min_power_socket0) + self.convert_power_to_watt(min_power_socket1)
            return min_power
        except Exception as ex:
            log_error = "Unable to get Min Power Value from cscripts due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise ex

    def get_cscripts_max_power_value(self):
        """
        This method will fetch max Power Wattage using cscripts.

        :return:
        """
        try:
            max_power_socket0 = 0
            max_power_socket1 = 0
            self._sv.refresh()
            self._log.info("Get values of max_power per socket.")
            if not len(self._cscripts.get_sockets()) >= 2:
                log_error = "Requires minimum of 2 sockets "
                self._log.error(log_error)
                raise RuntimeError(log_error)

            if self._cscripts.silicon_cpu_family in [ProductFamilies.CLX, ProductFamilies.SKX,
                                                     ProductFamilies.CPX]:
                max_power_socket0 = self._cscripts.get_sockets()[0].uncore0.pcu_cr_package_power_sku_cfg.pkg_max_pwr
                max_power_socket1 = self._cscripts.get_sockets()[1].uncore0.pcu_cr_package_power_sku_cfg.pkg_max_pwr

            if self._cscripts.silicon_cpu_family in [ProductFamilies.ICX, ProductFamilies.SNR,
                                                     ProductFamilies.SPR]:
                max_power_socket0 = self._cscripts.get_sockets()[0].uncore.punit.package_power_sku.pkg_max_pwr
                max_power_socket1 = self._cscripts.get_sockets()[1].uncore.punit.package_power_sku.pkg_max_pwr

            max_power = self.convert_power_to_watt(max_power_socket0) + self.convert_power_to_watt(max_power_socket1)
            return max_power
        except Exception as ex:
            log_error = "Unable to get max Power Value from cscripts due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise ex

    def get_cscripts_tdp_power_value(self):
        """
        This method will fetch tdp Power Wattage using cscripts.

        :return:
        """
        try:
            tdp_power_socket0 = 0
            tdp_power_socket1 = 0
            self._sv.refresh()
            self._log.info("Get values for tdp_power per socket.")
            if not len(self._cscripts.get_sockets()) >= 2:
                log_error = "Requires minimum of 2 sockets "
                self._log.error(log_error)
                raise RuntimeError(log_error)
            if self._cscripts.silicon_cpu_family in [ProductFamilies.CLX, ProductFamilies.SKX,
                                                     ProductFamilies.CPX]:
                tdp_power_socket0 = self._cscripts.get_sockets()[0].uncore0.pcu_cr_package_power_sku_cfg.pkg_tdp
                tdp_power_socket1 = self._cscripts.get_sockets()[1].uncore0.pcu_cr_package_power_sku_cfg.pkg_tdp

            if self._cscripts.silicon_cpu_family in [ProductFamilies.ICX, ProductFamilies.SNR,
                                                     ProductFamilies.SPR]:
                tdp_power_socket0 = self._cscripts.get_sockets()[0].uncore.punit.package_power_sku.pkg_tdp
                tdp_power_socket1 = self._cscripts.get_sockets()[1].uncore.punit.package_power_sku.pkg_tdp

            tdp_power = self.convert_power_to_watt(tdp_power_socket0) + self.convert_power_to_watt(tdp_power_socket1)
            return tdp_power
        except Exception as ex:
            log_error = "Unable to get tdp Power Value from cscripts due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise ex

    def get_cscripts_min_memory_power_value(self):
        """
        This method will fetch Min Memory Power Wattage using cscripts.

        :return:
        """
        try:
            min_power_socket0 = 0
            min_power_socket1 = 0
            self._sv.refresh()
            self._log.info("Get values of min_power per socket.")
            if not len(self._cscripts.get_sockets()) >= 2:
                log_error = "Requires minimum of 2 sockets "
                self._log.error(log_error)
                raise RuntimeError(log_error)

            if self._cscripts.silicon_cpu_family in [ProductFamilies.CLX, ProductFamilies.SKX,
                                                     ProductFamilies.CPX]:
                min_power_socket0 = self._cscripts.get_sockets()[0].uncore0.pcu_cr_dram_power_info_cfg.dram_min_pwr
                min_power_socket1 = self._cscripts.get_sockets()[1].uncore0.pcu_cr_dram_power_info_cfg.dram_min_pwr

            if self._cscripts.silicon_cpu_family in [ProductFamilies.ICX, ProductFamilies.SNR,
                                                     ProductFamilies.SPR]:
                min_power_socket0 = self._cscripts.get_sockets()[0].uncore.punit.dram_power_info.dram_min_pwr
                min_power_socket1 = self._cscripts.get_sockets()[1].uncore.punit.dram_power_info.dram_min_pwr

            min_power = self.convert_power_to_watt(min_power_socket0) + self.convert_power_to_watt(min_power_socket1)
            return min_power
        except Exception as ex:
            log_error = "Unable to get Min Memory Power Value from cscripts due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise ex

    def get_cscripts_tdp_memory_power_value(self):
        """
        This method will fetch tdp Memory Power Wattage using cscripts.

        :return:
        """
        try:
            tdp_power_socket0 = 0
            tdp_power_socket1 = 0
            self._sv.refresh()
            self._log.info("Get values for tdp memory power per socket.")
            if not len(self._cscripts.get_sockets()) >= 2:
                log_error = "Requires minimum of 2 sockets "
                self._log.error(log_error)
                raise RuntimeError(log_error)

            if self._cscripts.silicon_cpu_family in [ProductFamilies.CLX, ProductFamilies.SKX,
                                                     ProductFamilies.CPX]:
                tdp_power_socket0 = self._cscripts.get_sockets()[0].uncore0.pcu_cr_dram_power_info_cfg.dram_tdp
                tdp_power_socket1 = self._cscripts.get_sockets()[1].uncore0.pcu_cr_dram_power_info_cfg.dram_tdp

            if self._cscripts.silicon_cpu_family in [ProductFamilies.ICX, ProductFamilies.SNR,
                                                     ProductFamilies.SPR]:
                tdp_power_socket0 = self._cscripts.get_sockets()[0].uncore.punit.dram_power_info.dram_tdp
                tdp_power_socket1 = self._cscripts.get_sockets()[1].uncore.punit.dram_power_info.dram_tdp

            tdp_power = self.convert_power_to_watt(tdp_power_socket0) + self.convert_power_to_watt(tdp_power_socket1)
            return tdp_power
        except Exception as ex:
            log_error = "Unable to get tdp Memory Power Value from cscripts due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise ex

    def get_cscripts_max_memory_power_value(self):
        """
        This method will fetch max Memory Power Wattage using cscripts.

        :return:
        """
        try:
            max_power_socket0 = 0
            max_power_socket1 = 0
            self._sv.refresh()
            self._log.info("Get values of max memory power per socket.")
            if not len(self._cscripts.get_sockets()) >= 2:
                log_error = "Requires minimum of 2 sockets "
                self._log.error(log_error)
                raise RuntimeError(log_error)

            if self._cscripts.silicon_cpu_family in [ProductFamilies.CLX, ProductFamilies.SKX,
                                                     ProductFamilies.CPX]:
                max_power_socket0 = self._cscripts.get_sockets()[0].uncore0.pcu_cr_dram_power_info_cfg.dram_max_pwr
                max_power_socket1 = self._cscripts.get_sockets()[1].uncore0.pcu_cr_dram_power_info_cfg.dram_max_pwr

            if self._cscripts.silicon_cpu_family in [ProductFamilies.ICX, ProductFamilies.SNR,
                                                     ProductFamilies.SPR]:
                max_power_socket0 = self._cscripts.get_sockets()[0].uncore.punit.dram_power_info.dram_max_pwr
                max_power_socket1 = self._cscripts.get_sockets()[1].uncore.punit.dram_power_info.dram_max_pwr

            max_power = self.convert_power_to_watt(max_power_socket0) + self.convert_power_to_watt(max_power_socket1)
            return max_power
        except Exception as ex:
            log_error = "Unable to get max Power Value from cscripts due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise ex

