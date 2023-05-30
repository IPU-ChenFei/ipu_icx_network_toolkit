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
import sys
import time

import six
from dtaf_core.providers.provider_factory import ProviderFactory

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from src.lib import content_exceptions
from src.hsio.cxl.cxl_common import CxlCommon
from src.provider.pcie_provider import PcieProvider

from dtaf_core.lib.dtaf_constants import ProductFamilies


class CxlCtgCommon(CxlCommon):
    """
    This Class is Used as Common Class For all the CXL CTG Test Cases
    """
    BW_0_SIG = ["total WR bandwidth (Core Loops) is 0"]
    CXL_BIOS_KNOBS = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), "cxl_common_bios_file.cfg")

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCtgCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCtgCommon, self).__init__(test_log, arguments, cfg_opts, self.CXL_BIOS_KNOBS)
        self._pcie_provider = PcieProvider.factory(test_log, self.os, cfg_opts, "os", uefi_obj=None)
        self.ctg_tool_sut_path = self.install_collateral.install_ctg_tool()
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.execution_time_in_sec = self._common_content_configuration.get_cxl_stress_execution_runtime(tool="ctg")
        self.socket_list = self._common_content_configuration.get_cxl_sockets()
        self.port_list = self._common_content_configuration.get_cxl_ports()
        self.current_link_speed = self._common_content_configuration.get_cxl_current_link_speed()
        self.cxl_version_list = self._common_content_configuration.get_cxl_version()
        self.cxl_device_type = self._common_content_configuration.get_cxl_device_type()
        self.cxl_link_width = self._common_content_configuration.get_cxl_link_width()
        self.cxl_cache_en = self._common_content_configuration.get_cxl_cache_en_list()
        self.cxl_io_en = self._common_content_configuration.get_cxl_io_en_list()
        self.cxl_mem_en = self._common_content_configuration.get_cxl_mem_en_list()
        self.cxl_bus = self._common_content_configuration.get_cxl_target_bus_list()
        self.cxl = self.csp.get_cxl_obj()

    def prepare(self, sdp=None):  # type: () -> None
        """
        This is to execute prepare.
        """
        self.install_collateral.screen_package_installation()
        if sdp is not None:
            self.execute_cxl_ctg_pre_condition(sdp_obj=sdp)
        super(CxlCtgCommon, self).prepare()

    def get_cxl_device_bus(self, sockets=[0, 1]):
        """
        This method is to get the bus of cxl device.

        :param sockets - list
        :return bus - tuple
        """
        bus_list = []
        for each_socket in sockets:
            bus = self._common_content_configuration.get_cxl_target_bus_list(tool="ctg")[each_socket]
            bus_list.append(bus)
            if not self.is_bus_enumerated(bus):
                raise content_exceptions.TestFail("Socket {} Card bus({}) is not enumerated in OS".format(each_socket,
                                                                                                          bus))
            self._log.info("Socket {} Card with bus - {} is enumerated as expected".format(each_socket, bus))

        return tuple(bus_number for bus_number in bus_list)

    def execute_and_poll_ctg_stress(self, command_list=[], timeout=None):
        """
        This method is to execute the Ctg Stress.

        :param command_list
        :param timeout
        """
        for each_instance_cmd in command_list:
            self.os.execute_async(each_instance_cmd, self.ctg_tool_sut_path)
        if not self.poll_the_ctg_tool(execution_time_seconds=self.execution_time_in_sec if timeout is None else timeout,
                                      api_to_check=command_list):
            raise content_exceptions.TestFail("CTG tool fail to run")

        self._log.info("Stress execution completed Successfully")

    def verify_bw_in_ctg_output_files(self, file_names=[], signatures=[]):
        """
        This method is to validate the bandwidth.

        :param file_names
        :param signatures
        """
        for (each_file, signature_list) in zip(file_names, signatures):
            ctg_tool_output = self._common_content_lib.execute_sut_cmd("cat {}".format(each_file), "cat {}".format(
                each_file), self._command_timeout, self.ctg_tool_sut_path)

            for each_signature in signature_list:
                self._log.info("Checking Signature - {}".format(each_signature))
                if re.findall(each_signature, ctg_tool_output):
                    self._log.error("Found Unexpected Signature - {}".format(each_signature))
                    raise content_exceptions.TestFail("Unexpected bandwidth captured in OS")
                else:
                    self._log.info("Signature - {} not found as Expected".format(each_signature))

    def verify_bw_number_in_ctg_output(self, file_name=None, tolerance_percent=10, expected_bw=39.5):
        """
        This method is to verify the bandwidth number tolerance.

        :param file_name
        :param tolerance_percent
        :param expected_bw - in gb
        """
        ctg_tool_output = self._common_content_lib.execute_sut_cmd("cat {}".format(file_name), "cat {}".format(
            file_name), self._command_timeout, self.ctg_tool_sut_path)
        regex_output = re.findall(r"0 the total.*bandwidth.*is ([\S]+)", ctg_tool_output)[0]
        initial_val = int(expected_bw * 1024 - expected_bw * 1024 * tolerance_percent / 100)
        self._log.info("initial val- {}".format(initial_val))
        self._log.info("Actual - {}".format(regex_output))
        if not (initial_val <= int(float(regex_output))):
            raise content_exceptions.TestFail("Unexpected Bandwidth Captured by CTG :- {}".format(regex_output))
        self._log.info("Expected Bandwidth got Captured by CTG- {}".format(regex_output))

    def get_hdm_vm_sut_path(self, stride_addr=0x4, socket=0):
        """
        This method is to get the HDM VM file path on SUT.

        :param stride_addr - skipping address
        :param socket - Socket number
        :return path - hdm address containing file path (start, end).
        """
        hdm = self._common_content_configuration.get_cxl_target_peer_point_device_list(tool="ctg")[socket]
        self._log.info("Creating the HDM-{} VM addresses range file".format(socket))
        hdm1_start_txt = self.create_and_copy_hdm_vm_on_sut(peer_name=hdm, addr_range="start",
                                                            ctg_tool_path=self.ctg_tool_sut_path,
                                                            stride_addr=stride_addr)
        hdm1_end_txt = self.create_and_copy_hdm_vm_on_sut(peer_name=hdm, addr_range="end",
                                                          ctg_tool_path=self.ctg_tool_sut_path, stride_addr=stride_addr)
        self._log.info("HDM-{} VM addresses file got created- {} and {}".format(socket, hdm1_start_txt, hdm1_end_txt))
        return hdm1_start_txt, hdm1_end_txt

    def validate_cxl_devsec_attribute(self, devsec_output=None, cxl_io_en="0x1", cxl_mem_en="0x1", cxl_cache_en="0x1",
                                      devsec_ven_id=0x1e98):
        """
        This method is to cxl dev sec attr. (io en, mem en, cache en, devsec_ven_id)

        :param devsec_output
        :param cxl_io_en
        :param cxl_mem_en
        :param cxl_cache_en
        :param devsec_ven_id
        """
        io_en_regex = r"IO_CAP.*(0[xX][0-9a-fA-F]+)"
        if re.findall(io_en_regex, devsec_output)[0] != str(cxl_io_en):
            raise content_exceptions.TestFail("CXL io enable value was not captured as required")
        self._log.info("CXL io enable was found as expected")

        mem_en_regex = r"MEM_CAP.*(0[xX][0-9a-fA-F]+)"
        if re.findall(mem_en_regex, devsec_output)[0] != str(cxl_mem_en):
            raise content_exceptions.TestFail("CXL mem enable value was not captured as required")
        self._log.info("CXl mem enable value was found as expected")

        cache_en_regex = "CACHE_CAP.*(0[xX][0-9a-fA-F]+)"

        if re.findall(cache_en_regex, devsec_output)[0] != str(cxl_cache_en):
            raise content_exceptions.TestFail("CXL cache enable value was not captured as required")
        self._log.info("CXL cache enable was found as expected")

        devsec_ven_id_regex = r"DVSEC Vendor ID.*(0[xX][0-9a-fA-F]+)"

        if re.findall(devsec_ven_id_regex, devsec_output)[0] != str(devsec_ven_id):
            raise content_exceptions.TestFail("CXL devsec vendor id value was not captured as required")
        self._log.info("CXl devsec vendor id was found as expected")

    def cxl_enumerate_and_discover(self, reboot="no_reboot", auto_inventory_input=False):
        """
        Find out CXL spces from lspci and verify them

        :param reboot: warm_reboot/ac_cycle/no_reboot
        :param auto_inventory_input: True if cxl specs to be auto picked, False if user inputs to be picked
        :retrun True/False
        """
        if reboot == "warm_reboot":
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            self._log.info("Verifying after Warm Reboot")
        elif reboot == "ac_cycle":
            self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
            self._common_content_lib.wait_for_os(self.reboot_timeout)
            self._log.info("Verifying after Cold Reboot")
        else:
            pass

        # Checking cxl devices in sls
        self._log.info("Checking cxl devices in sls...........")
        pcie_obj = self.csp.get_cscripts_utils().get_pcie_obj()
        self.sdp.start_log("csripts_output.txt", "w")
        pcie_obj.sls()
        self.sdp.stop_log()
        with open("csripts_output.txt", "r") as log_file:
            log_file_list = log_file.readlines()
        self._log.info("pcie.sls Log file data : {}".format(log_file_list))
        if not "CXL" in str(log_file_list):
            self._log.info("CXL device not present in sls")
            return False
        self._log.info("CXL device  present in sls")

        if auto_inventory_input:
            cxl_inventory_dict = self.get_cxl_device_inventory(detailed_inventory=True)
            for key, value in cxl_inventory_dict.items():
                if value:
                    for key_1, value_1 in value.items():
                        bus = self.get_cxl_bus(key_1, int(key), self.csp)
                        device_details = self._pcie_provider.get_device_details_with_bus(bus=str(bus[2:]))
                        self._log.info("bus_id - '{}' device details - \n{}".format(bus, device_details))
                        if not device_details:
                            raise content_exceptions.TestFail("Bus ID - {} did not match....".format(bus))
                        bdf = list(device_details.keys())[0]
                        self.check_root_complex_for_cxl(value_1["cxl_version"],
                                                        device_details[str(bdf)]["root_complex"])
                        self._log.info("starting verification for {}".format(bdf))
                        self.verify_cxl_devsec_config("Vendor_ID", self.cxl_vendor_id[2:],
                                                      device_details[str(bdf)]["vendor_id"])
                        self._log.info("Verify device type from os")
                        self.verify_cxl_devsec_config("CXL device type", value_1["cxl_type"],
                                                      device_details[str(bdf)]["cxl_device_type"])

        else:
            for socket, port, link_speed, cxl_version, cxl_device_type, cxl_width \
                 in zip(self.socket_list, self.port_list, self.current_link_speed, self.cxl_version_list,
                        self.cxl_device_type, self.cxl_link_width):
                self._log.info("Configuration check from OS(LSPCI)......................")
                bus = self.get_cxl_bus(port, socket, self.csp)[2:]
                device_details = self._pcie_provider.get_device_details_with_bus(bus=str(bus))
                self._log.info("bus_id - '{}' device details - \n{}".format(bus, device_details))
                if not device_details:
                    raise content_exceptions.TestFail("No device details from os found for Bus ID - {}....".format(bus))
                bdf = list(device_details.keys())[0]
                self._log.info("starting verification for {}".format(bdf))
                self.verify_cxl_devsec_config("Vendor_ID", self.cxl_vendor_id[2:], device_details[str(bdf)]["vendor_id"])
                self._log.info("Verify device type from os")
                self.verify_cxl_devsec_config("CXL device type", cxl_device_type, device_details[str(bdf)]["cxl_device_type"])
                self.check_root_complex_for_cxl(cxl_version, device_details[str(bdf)]["root_complex"])

                # Get CXL device type from cscripts
                device_type_output = self.get_cxl_device_type_cscripts(socket, port)

                if cxl_device_type not in str(device_type_output):
                    raise content_exceptions.TestFail(f"For socket- {socket} and port- {port}, Cxl Device Type was "
                                                      f"expected to be- \n{device_type_output}")
                self._log.info("cxl device type output- {} for socket- {} and port- {}".format(device_type_output,
                                                                                               socket, port))
                self.sdp.halt()
                self.sdp.start_log("csripts_output.txt", "w")
                self.cxl.get_cxl_version(int(socket), port)
                self.sdp.stop_log()
                self.sdp.go()

                with open("csripts_output.txt", "r") as fp:
                    cxl_version_output = fp.read()

                if cxl_version not in str(cxl_version_output):
                    raise content_exceptions.TestFail("Cxl Device Version was not found as expected for socket- {} "
                                                      "and port- {}".format(socket, port))
                self._log.info("cxl version output- {} for socket- {} and port- {}".format(cxl_version_output,
                                                                                           socket, port))

        return True

    def verify_cxl_devsec_config(self, spec_name, expected_value, current_value):
        """
        Method to verify specifications of a pci device by comparing them with the expected.

        :param spec_name: name of the specification
        :param expected_value: expected value of the spec
        :param current_value: current value of the spec
        :return True/False
        """
        self._log.info("Verifying {}...................".format(spec_name))
        self._log.info("Expected value - {}".format(expected_value))
        self._log.info("Current value - {}".format(current_value))
        if expected_value == current_value:
            self._log.info("{} matches".format(spec_name))
            return True
        else:
            raise content_exceptions.TestFail("{} did not match....".format(spec_name))

    def check_root_complex_for_cxl(self, cxl_version, rcie_in_os):
        """
        This method verifies cxl version via RCIE string from os lspci.
        :param cxl_version: version from cscript
        :param rcie_in_os: version from os as per Root complex integrated endpoint string
        """
        self._log.info("check for root complex string for cxl version verification")
        if cxl_version == "CXL 1.1":
            if not rcie_in_os:
                raise content_exceptions.TestFail("'Root complex' string (RCIE) in os(lspci) should be present for "
                                                  "CXL 1.1 ")
        else:
            self._log.info("For 'SPR' and 'EMR', Root complex string will still be there in the OS")
            if not self._common_content_lib.get_platform_family() in [ProductFamilies.SPR, ProductFamilies.EMR]:
                if rcie_in_os:
                    raise content_exceptions.TestFail("'Root complex' string (RCIE) in os(lspci) should not be present "
                                                      "for CXL 2.x ")
