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

import os
from decimal import Decimal

from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.cpu_info_provider import CpuInfoProvider
import src.lib.content_exceptions as content_exception


class ProcessorCPUInfoBase(ContentBaseTestCase):
    """
    TestCase Id : H80052
    This case is used to verify the CPU info reported by OS match the PHY processor

    """
    _MULTIPLE_TO_CONVERT_GHZ_TO_MHZ = 1000

    # Below is Core Po1m value from QDF spec
    _MAX_TURBO_CPU_FREQUENCY = 'core_max_turbo_frequency'
    # Below is Core P1n value from QDF spec
    _MAX_BASE_CPU_FREQUENCY = 'core_max_base_frequency'

    _MAX_CPU_FREQUENCY = 'max_cpu_frequency'
    _MINIMUM_CPU_FREQUENCY = 'minimum_cpu_frequency'
    _CURRENT_CPU_FREQUENCY = 'current_cpu_frequency'
    _LOGICAL_PROCESSORS = 'logical_processors'
    _NUMBER_OF_SOCKETS = 'no_of_sockets'
    _NUMBER_OF_CORES = 'no_of_cores'
    _L2_CACHE_SIZE = 'l2_cache_size'
    _L3_CACHE_SIZE = 'l3_cache_size'
    _VIRTUALIZATION = 'virtualization'

    def __init__(self, test_log, arguments, cfg_opts, eist_enable_bios_config_file,
                 eist_disable_bios_config_file):
        """
        Create an instance of sut os provider, BiosProvider and
         BIOS util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param eist_enable_bios_config_file: Bios Configuration file name
        :param eist_disable_bios_config_file: Bios Configuration file name
        """
        super(ProcessorCPUInfoBase, self).__init__(test_log, arguments, cfg_opts)
        self._cfg = cfg_opts
        self.disable_cores_bios_config_file_path = eist_disable_bios_config_file

        cur_path = os.path.dirname(os.path.realpath(__file__))
        self._enable_eist_bios_config_file_path = self._common_content_lib.get_config_file_path(
                                                                cur_path,
                                                                eist_enable_bios_config_file)

        self._disable_eist_bios_config_file_path = self._common_content_lib.get_config_file_path(
                                                            cur_path,
                                                            eist_disable_bios_config_file)

        self._cpu_provider = CpuInfoProvider.factory(test_log, cfg_opts, self.os)

    def prepare(self):
        # type: () -> None
        """
        call base class prepare function

        :return: None
        """
        super(ProcessorCPUInfoBase, self).prepare()

    def enable_disable_eist(self, bios_config_file):
        self.bios_util.load_bios_defaults()
        self.bios_util.set_bios_knob(bios_config_file)  # To set the bios knob setting.
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        self.bios_util.verify_bios_knob(bios_config_file)  # To verify the bios knob settings.

    def get_cpu_info(self):
        """
        This method fetches minimum freqcency, the max frequency, socket number, core number,logical processor,
        virtualization,L1,L2,L3 cache size using cpu provider and returns a dictionary.

        :return: Dictionary of cpu related data
        """
        try:
            self._cpu_provider.populate_cpu_info()

            cpu_info_dict = {self._MAX_CPU_FREQUENCY: self._cpu_provider.get_max_cpu_frequency(),
                             self._MINIMUM_CPU_FREQUENCY: self._cpu_provider.get_min_cpu_frequency(),
                             self._CURRENT_CPU_FREQUENCY: self._cpu_provider.get_current_cpu_frequency(),
                             self._LOGICAL_PROCESSORS: self._cpu_provider.get_logical_processors(),
                             self._NUMBER_OF_SOCKETS: self._cpu_provider.get_number_of_sockets(),
                             self._NUMBER_OF_CORES: self._cpu_provider.get_number_of_cores(),
                             self._L2_CACHE_SIZE: self._cpu_provider.get_l2_cache_size(),
                             self._L3_CACHE_SIZE: self._cpu_provider.get_l3_cache_size(),
                             self._cpu_provider.VIRTUALIZATION: self._cpu_provider.get_virtualization_data()}
            return cpu_info_dict

        except Exception as ex:
            log_error = "Unable to get CPU info from OS provider due to exception '{}'".format(ex)
            self._log.error(log_error)
            raise ex

    def get_qdf_info_from_config(self, qdf_tag_value):

        try:
            cpu_family = self._common_content_lib.get_platform_family()
            cpu_info_config_dict = self._common_content_configuration.get_cpu_qdf_info(cpu_family, qdf_tag_value)

            return cpu_info_config_dict

        except Exception as ex:
            log_error = "Unable to get CPU info from config file due to exception '{}'".format(ex)
            self._log.error(log_error)
            raise ex

    def get_cpu_info_from_config(self):

        try:
            cpu_family = self._common_content_lib.get_platform_family()
            cpu_info_config_dict = self._common_content_configuration.get_cpu_info(cpu_family)

            return cpu_info_config_dict

        except Exception as ex:
            log_error = "Unable to get CPU info from config file due to exception '{}'".format(ex)
            self._log.error(log_error)
            raise ex

    def __verify_cpu_info_with_config(self, dict_cpu_info_qdf_spec, dict_cpu_info_os):
        variance_value = 0.02
        ret_val = True

        self._log.info("'{}' from QDF Specification: {}".format(self._MAX_TURBO_CPU_FREQUENCY,
                                                                dict_cpu_info_qdf_spec[self._MAX_TURBO_CPU_FREQUENCY]))
        self._log.info("'{}' from QDF Specification: {}".format(self._MAX_BASE_CPU_FREQUENCY,
                                                                dict_cpu_info_qdf_spec[self._MAX_BASE_CPU_FREQUENCY]))

        self._log.info("'{}' from OS: {}".format(self._MAX_CPU_FREQUENCY,
                                                 dict_cpu_info_os[self._MAX_CPU_FREQUENCY]))

        logical_processors_config = dict_cpu_info_qdf_spec[self._LOGICAL_PROCESSORS]
        logical_processors_os = dict_cpu_info_os[self._LOGICAL_PROCESSORS]
        self._log.info("'{}' from QDF Specification: {}".format(self._LOGICAL_PROCESSORS,
                                                          logical_processors_config))
        self._log.info("'{}' from OS: {}".format(self._LOGICAL_PROCESSORS,
                                                 logical_processors_os))
        if logical_processors_config  != logical_processors_os:
            ret_val = False
            self._log.error("The '{}' value is not matching with QDF Specification..".format(self._LOGICAL_PROCESSORS))

        no_sockets_config = dict_cpu_info_qdf_spec[self._NUMBER_OF_SOCKETS]
        no_sockets_os = dict_cpu_info_os[self._NUMBER_OF_SOCKETS]
        self._log.info("'{}' from QDF Specification: {}".format(self._NUMBER_OF_SOCKETS, no_sockets_config))
        self._log.info("'{}' from OS: {}".format(self._NUMBER_OF_SOCKETS, no_sockets_os))
        if int(no_sockets_config) != int(no_sockets_os):
            ret_val = False
            self._log.error("The '{}' info is not matching with value from "
                            "QDF Specification..".format(self._NUMBER_OF_SOCKETS))

        no_cores_config = dict_cpu_info_qdf_spec[self._NUMBER_OF_CORES]
        no_cores_os = dict_cpu_info_os[self._NUMBER_OF_CORES]
        self._log.info("'{}' from QDF Specification: {}".format(self._NUMBER_OF_CORES, no_cores_config))
        self._log.info("'{}' from OS: {}".format(self._NUMBER_OF_CORES, no_cores_os))
        if no_cores_config != no_cores_os:
            ret_val = False
            self._log.error("The '{}' info is not matching with value from QDF "
                            "Specification..".format(self._NUMBER_OF_CORES))

        l2_cache_config = dict_cpu_info_qdf_spec[self._L2_CACHE_SIZE]
        l2_cache_os = dict_cpu_info_os[self._L2_CACHE_SIZE]
        self._log.info("'{}' from QDF Specification: {}".format(self._L2_CACHE_SIZE, l2_cache_config))
        self._log.info("'{}' from OS: {}".format(self._L2_CACHE_SIZE, l2_cache_os))
        if float(l2_cache_config) != float(Decimal(l2_cache_os)):
            ret_val = False
            self._log.error("The '{}' info is not matching with value from "
                            "QDF Specification..".format(self._L2_CACHE_SIZE))

        l3_cache_config = dict_cpu_info_qdf_spec[self._L3_CACHE_SIZE]
        l3_cache_os = dict_cpu_info_os[self._L3_CACHE_SIZE]
        self._log.info("'{}' from QDF Specification: {}".format(self._L3_CACHE_SIZE, l3_cache_config))
        self._log.info("'{}' from OS: {}".format(self._L3_CACHE_SIZE, l3_cache_os))
        if float(l3_cache_config) != float(Decimal(l3_cache_os)):
            ret_val = False
            self._log.error("The '{}' info is not matching with value from "
                            "QDF Specification..".format(self._L3_CACHE_SIZE))

        virtualization_config = dict_cpu_info_qdf_spec[self._cpu_provider.VIRTUALIZATION]
        virtualization_os = dict_cpu_info_os[self._cpu_provider.VIRTUALIZATION]
        self._log.info("'{}' from QDF Specification: {}".format(self._cpu_provider.VIRTUALIZATION, virtualization_config))
        self._log.info("'{}' from OS: {}".format(self._cpu_provider.VIRTUALIZATION, virtualization_os))
        if virtualization_config != virtualization_os:
            ret_val = False
            self._log.error("The '{}' info is not matching with value from "
                            "QDF Specification..".format(self._cpu_provider.VIRTUALIZATION))

        return ret_val

    def verify_processor_cpu_info(self):
        """
        1. Enable Processor EIST
        2. Verify CPU Info values from OS are matching with QDF specifications
        3. Disable Processor EIST
        4. Verify CPU Info values from OS are matching with QDF specifications

        :return:  True if pass, False if not
        """
        try:
            qdf_tag_name = self._common_content_lib.get_processor_qdf()
            dict_cpu_info_qdf_spec = self.get_qdf_info_from_config(qdf_tag_name)
            self._log.info("CPU Info from QDF Specification: {}".format(dict_cpu_info_qdf_spec))

            qdf_cpu_turbo_max_freq = int(dict_cpu_info_qdf_spec[self._MAX_TURBO_CPU_FREQUENCY])
            qdf_cpu_max_base_freq = int(dict_cpu_info_qdf_spec[self._MAX_BASE_CPU_FREQUENCY])

            # enable PIST and then get CPU info
            self._log.info("Enable Processor EIST bios knob...")
            self.enable_disable_eist(self._enable_eist_bios_config_file_path)

            self._log.info("CPU EIST is enabled...")
            dict_cpu_info_os = self.get_cpu_info()
            self._log.info("CPU Info from OS with EIST Enabled: {}".format(dict_cpu_info_os))

            ret_val_eist_enable = self.__verify_cpu_info_with_config(dict_cpu_info_qdf_spec, dict_cpu_info_os)
            if not ret_val_eist_enable:
                log_error = "EIST Enabled: CPU Info values from OS are not matching with QDF Specification..."
                self._log.error(log_error)

            os_cpu_max_speed_eist_enabled = int(Decimal(dict_cpu_info_os[self._MAX_CPU_FREQUENCY]))
            self._log.info("EIST Enabled: Max frequency reported by OS should be same as QDF Max Turbo Frequency..")
            self._log.info("EIST Enabled: OS Maximum Frequency='{}' and QDF Max Turbo "
                           "Frequency='{}'...".format(os_cpu_max_speed_eist_enabled,qdf_cpu_turbo_max_freq))
            if os_cpu_max_speed_eist_enabled != qdf_cpu_turbo_max_freq:
                log_error = "EIST Enabled: MAX Frequency reported by OS should be equal to QDF MAX Turbo Frquency." \
                            "The OS MAX CPU frequency and  QDF Max Turbo frequency are not same.."
                self._log.error(log_error)
                ret_val_eist_enable = False

            # disable EIST and then get CPU info
            self._log.info("Disable Processor EIST bios knob...")
            self.enable_disable_eist(self._disable_eist_bios_config_file_path)
            self._log.info("CPU EIST is disabled...")
            dict_cpu_info_os = self.get_cpu_info()
            self._log.info("CPU Info from OS with EIST Disabled: {}".format(dict_cpu_info_os))
            ret_val_eist_disable = self.__verify_cpu_info_with_config(dict_cpu_info_qdf_spec, dict_cpu_info_os)
            if not ret_val_eist_disable:
                log_error = "EIST Disabled: CPU Info values from OS are not matching with QDF Specification..."
                self._log.error(log_error)

            os_cpu_max_speed_eist_disabled = int(Decimal(dict_cpu_info_os[self._MAX_CPU_FREQUENCY]))
            self._log.info("EIST Disabled: Max frequency reported by OS should be same as QDF Max Base Frequency..")
            self._log.info("EIST Disabled: OS Max Frequency='{}' and QDF Max Base "
                           "frequency='{}'...".format(os_cpu_max_speed_eist_disabled, qdf_cpu_max_base_freq))

            if os_cpu_max_speed_eist_disabled != qdf_cpu_max_base_freq:
                log_error = "EIST Disabled: The Max frequency reported by OS and QDF Base Max frquency are not same.."
                self._log.error(log_error)
                ret_val_eist_disable = False

            if not ret_val_eist_enable or not ret_val_eist_disable:
                raise content_exception.TestFail("EIST Enabled/Disabled:CPU Info verification with QDF Specification "
                                                 "is not Successful...")

            self._log.info("CPU Info verification with EIST enabled and disabled is Successful...")

            return True
        except Exception as ex:
            log_error = "Verification of CPU Info failed due to exception '{}'..." .format(ex)
            self._log.error(log_error)
            raise content_exception.TestFail(log_error)
