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
import sys
import os
import re


from src.lib import content_exceptions
from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from src.hsio.cxl.cxl_common import CxlCommon


class CxlCscriptsCmdsStatisticsGroup(CxlCommon):
    """
    hsdes_id :  22014767248 CXL Cscripts cxl. commands "Statistics" group
    This test exercises the new "cxl." command set in Cscripts, specifically the commands related to information
    gathering  and register dumps. The log and error injection commands are covered in a separate TCD

    """
    CXL_BIOS_KNOBS = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), "cxl_common_bios_file.cfg")

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=CXL_BIOS_KNOBS):
        """
        Create an instance of CxlCscriptsCmdsStatisticsGroup.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCscriptsCmdsStatisticsGroup, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCscriptsCmdsStatisticsGroup, self).prepare()

    def execute(self):
        """
        Method covers
        Running and verifying cxl methods from cscripts-
        1. cxl_cmem_err_check
        2. cxl_dp_dvsec_show
        3. cxl_up_dvsec_show
        4. show_cxl_membar0_cap_list
        5. get_cxl_rcrb_bar
        6. get_cxl_exppt_bar
        7. show_pci_ext_cap_list
        8. cxl_ieh_error_dump
        9. show_rcrb_ext_cap_list
        10. get_cxl_version
        11. in_cxl_mode
        12. cxl_iep_dvsec_show
        13. get_device_type
        
        """
        lspci_output_all = self._common_content_lib.execute_sut_cmd("lspci", "output of lspci", self._command_timeout)
        self._log.info("Checking whether busybox installed or not...")
        if not self._common_content_lib.execute_sut_cmd("rpm -qa busybox",
                                                        "Command to check busybox installation status",
                                                        self._command_timeout):
            raise content_exceptions.TestFail("Busybox tool not installed, please install and run again")
        cxl_inventory_dict = self.get_cxl_device_inventory()
        result_status = True

        for key, value in cxl_inventory_dict.items():
            for port in value:
                if port:
                    self._log.info(f"RUNNING CSCRIPT CXL METHODS FOR CXL DEVICE AT SOCKET-{key} AND PORT-{port}")
                    bdf = self.get_cxl_bus(port, key, self.csp)
                    device_details = self._pcie_provider.get_device_details_with_bus(bus=str(bdf[2:]))

                    # Running CXL_cmem_error_check
                    self._log.info("Running CXL_cmem_error_check...............")
                    cxl_mem_output = self.get_cxl_cscript_method_output("cxl_cmem_err_check", key, port)
                    output = re.findall(self.cxl_err_check_regex, cxl_mem_output)
                    if not output:
                        raise content_exceptions.TestFail("Couldn't get cxl mem error status ")
                    self._log.info("List of Errors reported - {}".format(output))
                    errors = [int(i) for i in output if int(i) > 0]
                    if errors:
                        self._log.info("CXL_cmem_error_check - Errors reported for cxl device at socket-{} port-{}".
                                       format(key, port))
                        result_status = False
                    else:
                        self._log.info("CXL_cmem_error_check passed for cxl device at socket-{} port-{}".
                                       format(key, port))

                    # Running CXL cxl_dp_dvsec_show and cxl_up_dvsec_show
                    self._log.info("Running CXL cxl_dp_dvsec_show and cxl_up_dvsec_show...............")
                    cxl_dp_addr_value_dict = self.get_dvsec_address_value_pair("cxl_dp_dvsec_show", key, port)
                    if not self.verify_addr_value_from_busybox(cxl_dp_addr_value_dict):
                        self._log.info(
                            "Test cxl_dp_dvsec_show FAILED for cxl device at socket-{} port-{}".format(key, port))
                        result_status = False
                    else:
                        self._log.info(
                            "Test cxl_dp_dvsec_show passed for cxl device at socket-{} port-{}".format(key, port))
                    cxl_up_addr_value_dict = self.get_dvsec_address_value_pair("cxl_up_dvsec_show", key, port)
                    if not self.verify_addr_value_from_busybox(cxl_up_addr_value_dict):
                        result_status = False
                        self._log.info(
                            "Test cxl_up_dvsec_show FAILED for cxl device at socket-{} port-{}".format(key, port))
                    else:
                        self._log.info(
                            "Test cxl_up_dvsec_show passed for cxl device at socket-{} port-{}".format(key, port))

                    # Running show_cxl_membar0_cap_list and verify 'rcrb'/'exppt' addr via cxl_rcrb_bar & cxl_exppt_bar
                    if device_details[f"{bdf[2:]}:00.0"]["root_complex"]:
                        self._log.info(
                            "Running show_cxl_membar0_cap_list and verify rcrb & exppt addresses from get_cxl_rcrb_bar"
                            "and get_cxl_exppt_bar......")
                        cxl_show_cxl_membar0_cap_list_output = self.get_cxl_cscript_method_output(
                            "show_cxl_membar0_cap_list", key, port)
                        if not self.verify_cxl_addr_from_cxl_function("rcrb", self.cxl_rcrb_addr_regex,
                                                                      cxl_show_cxl_membar0_cap_list_output, key, port):
                            result_status = False
                            self._log.info(
                                "Test cxl_rcrb_bar FAILED for cxl device at socket-{} port-{}".format(key, port))
                        if not self.verify_cxl_addr_from_cxl_function("exppt", self.cxl_exppt_addr_regex,
                                                                      cxl_show_cxl_membar0_cap_list_output, key, port):
                            result_status = False
                            self._log.info(
                                "Test cxl_exppt_bar FAILED for cxl device at socket-{} port-{}".format(key, port))
                    else:
                        self._log.info(
                            "Could not run show_cxl_membar0_cap_list and verify rcrb & exppt addresses from "
                            "get_cxl_rcrb_bar and get_cxl_exppt_bar as Root Complex Integrated Endpoint string is not "
                            f"present in os for cxl device {bdf} at socket {key} {port}")

                    # Running show_pci_ext_cap_list
                    self._log.info("Running show_pci_ext_cap_list............")
                    if not f"{bdf[2:]}:00.0" in lspci_output_all:
                        raise content_exceptions.TestFail(
                            "Target cxl device - {} not present in lspci listing".format(bdf))
                    if not self.cxl_pci_ext_cap_list_show(bdf, key, port):
                        self._log.info(
                            f"show_pci_ext_cap_list FAILED to verify from os (lspci) for cxl device- {bdf} at socket-"
                            f"{key} and port-{port}")
                        result_status = False
                    else:
                        self._log.info(f"show_pci_ext_cap_list is verified from os (lspci) for cxl device- {bdf} at socket-"
                                       f"{key} and port-{port}")

                    # Running cxl_ieh_error_dump and verifying
                    self._log.info("Running cxl_ieh_error_dump and verifying")
                    cxl_error_dump_dict = self.get_cxl_ieh_error_dump(key, port)
                    cxl_verification_status = self.verify_cxl_error_dump_for_all_error_registers(cxl_error_dump_dict,
                                                                                                 key, port)
                    if not cxl_verification_status:
                        self._log.info(
                            "cxl_ieh_error_dump verification FAILED for cxl device - {} at socket-{}, slot-{}".
                            format(bdf, key, port))
                        result_status = False
                    else:
                        self._log.info(
                            "cxl_ieh_error_dump verification PASSED for cxl device - {} at socket-{}, slot-{}".
                            format(bdf, key, port))

                    # Running show_rcrb_ext_cap_list
                    if device_details[f"{bdf[2:]}:00.0"]["root_complex"]:
                        self._log.info("Running show_rcrb_ext_cap_list")
                        cxl_rcrb_ext_cap_list_output = self.get_cxl_cscript_method_output(
                            "show_rcrb_ext_cap_list", key, port)
                        data = self.extract_data_from_cxl_cap_list(cxl_rcrb_ext_cap_list_output, "rcrb")
                        if not data:
                            raise content_exceptions.TestFail(f"no data extracted for rcrb_ext_cap_list")
                        if not self.verify_addr_value_from_busybox(data):
                            result_status = False
                            self._log.info(
                                "Test show_rcrb_ext_cap_list FAILED for cxl dev at socket-{} port-{}".format(key, port))
                        else:
                            self._log.info(
                                "Test rcrb_ext_cap_list passed for cxl device at socket-{} port-{}".format(key, port))
                    else:
                        self._log.info("Could not run show_rcrb_ext_cap_list as Root Complex Integrated Endpoint string"
                                       f" is not present in os for cxl device {bdf} at socket {key} {port}")

                    # Running get_cxl_version
                    self._log.info("Running get_cxl_version")
                    cxl_version_cscript_output = self.get_cxl_cscript_method_output("get_cxl_version", key, port)
                    cxl_version = re.findall(r"INFO: Device version.*(CXL \S+)", cxl_version_cscript_output)[0]
                    if cxl_version == "CXL 1.1":
                        if not device_details[f"{bdf[2:]}:00.0"]["root_complex"]:
                            raise content_exceptions.TestFail("Root complex string not present for CXL 1.1 ")
                    else:
                        if not self._common_content_lib.get_platform_family() in [ProductFamilies.SPR,
                                                                                  ProductFamilies.EMR]:
                            if device_details[str(bdf)]["root_complex"]:
                                raise content_exceptions.TestFail("Root complex string present for CXL 2.x ")

                    # Running in_cxl_mode to check cxl mode
                    self._log.info("Running in_cxl_mode to check cxl mode")
                    cxl_mode_status = self.cxl.in_cxl_mode(int(key), port)
                    if not cxl_mode_status:
                        self._log.info(f" Socket {key} '{port}' is not operating in CXL mode! ")
                        result_status = False
                    else:
                        self._log.info(f" Socket {key} '{port}' is operating in CXL mode! ")

                    # Running cxl_iep_dvsec_show
                    self._log.info("Running cxl_iep_dvsec_show")
                    cxl_iep_addr_value_dict = self.get_dvsec_address_value_pair("cxl_iep_dvsec_show", key, port)
                    if not self.verify_addr_value_from_busybox(cxl_iep_addr_value_dict):
                        result_status = False
                        self._log.info(
                            "cxl_iep_dvsec_show FAILED for cxl device at socket-{} port-{}".format(key, port))
                    else:
                        self._log.info("cxl_iep_dvsec_show verified for cxl device at socket-{} port-{}".format(key, port))

                    # Running device type - get_device_type
                    self._log.info("Running device type - get_device_type")
                    device_type_output = self.get_cxl_device_type_cscripts(key, port)
                    if device_details[f"{bdf[2:]}:00.0"]["cxl_device_type"] not in str(device_type_output):
                        raise content_exceptions.TestFail("Cxl Device Type was not found as expected for socket- {}"
                                                          "and port- {}".format(key, port))
                    self._log.info("cxl device type output- {} for socket- {} and port- {}".format(device_type_output,
                                                                                                   key, port))

                    if not result_status:
                        self._log.info("Please check the logs as one or more cxl methods have failed"
                                       f"for Socket {key} '{port}'")
                        return False
                    self._log.info("All cxl methods listed under statistics have passed for cxl device at"
                                   f"Socket {key} '{port}'")
                self.sdp.go()
        self._log.info("All test passed for all cxl devices")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCscriptsCmdsStatisticsGroup.main() else
             Framework.TEST_RESULT_FAIL)
