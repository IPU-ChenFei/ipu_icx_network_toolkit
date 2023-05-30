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

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from dtaf_core.lib.dtaf_constants import ProductFamilies, Framework
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.dtaf_content_constants import TimeConstants
from src.lib.install_collateral import InstallCollateral
from src.provider.memory_provider import MemoryProvider
from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.pcie_provider import PcieProvider
from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon, PxpInventory
from src.provider.pcie_provider import PcieProvider


class CxlCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the CXL Test Cases
    """

    REGEX_TO_CHECK_CTG_BW = "total bandwidth is 0"
    NO_OF_ADDRESSES = 2048
    NUM_OF_SOCKETS_CMD = "grep 'physical id' /proc/cpuinfo | ""sort -u | wc -l"
    ERROR_DMESG_SIGNATURES = ["Memory failure", "recoverable", "unrecoverable"]
    MPRIME_TORTURE_TEST_ARGUMENT_IN_DICT = {"cmd": "sudo numactl --cpunodebind=1  --membind={} ./mprime -m", "Join Gimps?": "N", "Your choice": "15",
                        "Number of torture test threads to run": "224", "Type of torture test to run": "4",
                        "Customize settings": "Y", "Min FFT size": "4", "Max FFT size": "4096",
                        "Memory to use": "16834", "Time to run each FFT size": "60",
                        "Run a weaker torture test": "N", "Accept the answers above?": "Y"}
    CXL_TYPE_IN_OS = {"Type 1": "Cache+ IO+ Mem-", "Type 2": "Cache+ IO+ Mem+", "Type 3": "Cache- IO+ Mem+"}
    CXL_TYPE_IN_CSCRIPTS = {"Type 1": {"Cache": "0x1", "IO": "0x1", "Mem": "0x0"},
                            "Type 2": {"Cache": "0x1", "IO": "0x1", "Mem": "0x1"},
                            "Type 3": {"Cache": "0x0", "IO": "0x1", "Mem": "0x1"}
                            }

    CXL_ERROR_STATISTICS_DICT = {
                      "Poisoned TLP Egress Blocked": ["erruncmsk.ptlpebm", "erruncsev.ptlpebs", "erruncsts.ptlpeb"],
                      "TLP Prefix Blocked Error": ["erruncmsk.tpbem", "erruncsev.tpbes", "erruncsts.tpbe"],
                      "AtomicOp Egress Blocked": ["erruncmsk.aebem", "erruncsev.aebes", "erruncsts.aebe"],
                      "MC Blocked TLP": ["erruncmsk.mcem", "erruncsev.mces", "erruncsts.mce"],
                      "Uncorrectable Internal Error": ["erruncmsk.uiem", "erruncsev.uies", "erruncsts.uie"],
                      "ACS Violation": ["erruncmsk.acsem", "erruncsev.acses", "erruncsts.acse"],
                      "Unsupported Request Error": ["erruncmsk.urem", "erruncsev.ures", "erruncsts.ure"],
                      "ECRC Error": ["erruncmsk.ecrcem", "erruncsev.ecrces", "erruncsts.ecrce"],
                      "Malformed TLP": ["erruncmsk.mtlpem", "erruncsev.mtlpes", "erruncsts.mtlpe"],
                      "Receiver Overflow Error": ["erruncmsk.roem", "erruncsev.roes", "erruncsts.roe"],
                      "Unexpected Completion Error": ["erruncmsk.ucem", "erruncsev.uces", "erruncsts.uce"],
                      "Completer Abort Error": ["erruncmsk.caem", "erruncsev.caes", "erruncsts.cae"],
                      "Completion Timeout Error": ["erruncmsk.ctem", "erruncsev.ctes", "erruncsts.cte"],
                      "Flow Control Protocol Error": ["erruncmsk.fcem", "erruncsev.fces", "erruncsts.fce"],
                      "Poisoned TLP Received": ["erruncmsk.ptlpem", "erruncsev.ptlpes", "erruncsts.ptlpe"],
                      "Data Link Protocol Error": ["erruncmsk.dlpem", "erruncsev.dlpes", "erruncsts.dlpe"],
                      "Header Log Overflow Error": ["errcormsk.hloem", "errcorsts.hloe"],
                      "Correctable Internal Error": ["errcormsk.ciem", "errcorsts.cie"],
                      "Advisory NonFatal Error": ["errcormsk.anfem", "errcorsts.anfe"],
                      "Replay timer timeout occurs": ["errcormsk.rttem", "errcorsts.rtte"],
                      "Replay number rolls over from 11 to 00": ["errcormsk.rnrem", "errcorsts.rnre"],
                      "CRC errors on DLLP": ["errcormsk.bdllpem", "errcorsts.bdllpe"],
                      "CRC errors on TLP": ["errcormsk.btlpem", "errcorsts.btlpe"],
                      "receiver error": ["errcormsk.rem", "errcorsts.re"],
                      "Enables the interrupt generation when a Fatal error is reported": ["rooterrcmd.fere"],
                      "Enables the interrupt generation when a NonFatal error is reported": ["rooterrcmd.nfere"],
                      "Enables the interrupt generation when a Correctable error is reported": ["rooterrcmd.cere"],
                      "MSI/MSIX vector used for the interrupt message": ["rooterrsts.aemn"],
                      "Fatal Error Message Received": ["rooterrsts.femr"],
                      "NonFatal Error message Received": ["rooterrsts.nfemr"],
                      "First Uncorrectable Fatal": ["rooterrsts.fuf"],
                      "Multiple Error Fatal/NonFatal Received": ["rooterrsts.mefr"],
                      "Error Fatal/NonFatal Received": ["rooterrsts.efr"],
                      "Multiple Error Correctable Error Received": ["rooterrsts.mcer"],
                      "Correctable Error Received": ["rooterrsts.cer"]
    }

    CXL_UNC_CMD_DICT = {
        ProductFamilies.SPR: "uncore.pi5.{}.cfg.{}",
        ProductFamilies.EMR: "uncore.pi5.{}.cfg.{}",
        ProductFamilies.GNR: "io{}.uncore.pi5.{}.cfg.{}"}

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._args = arguments
        self._cfg = cfg_opts
        self._pcie_provider = PcieProvider.factory(test_log, self.os, cfg_opts, "os", uefi_obj=None)
        self._product_family = self._common_content_lib.get_platform_family()
        self.sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)
        self.cxl = self.csp.get_cxl_obj()
        self.socket_list = self._common_content_configuration.get_cxl_sockets()
        self.port_list = self._common_content_configuration.get_cxl_ports()
        self.dax_device = self._common_content_configuration.get_cxl_dax_device()
        self.dax_socket_list = self._common_content_configuration.get_socket_for_cxl_dax_device()
        self.dax_port_list = self._common_content_configuration.get_port_for_cxl_dax_device()
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._hsio_upi_common = HsioUpiCommon(test_log, arguments, cfg_opts)
        self._check_os_log = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                               self._common_content_lib)
        self.pcie_common = PcieCommon(self._log, self._args, self._cfg)
        self.pcie_obj = self.csp.get_cscripts_utils().get_pcie_obj()
        self.memory_provider = MemoryProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)
        self.pxp_inventory = PxpInventory(self.sdp, self.pcie_obj, self.pcie_common.PCIE_SLS_OUTPUT_LOG)
        self.cxl = self.csp.get_cxl_obj()
        self.cxl_get_dax_devs_cmd = "cat /proc/iomem | grep dax"
        self.cxl_device_config_cmd = "sudo daxctl reconfigure-device --mode=system-ram --no-online {}"
        self.cxl_mlc_run_cmd = "./mlc_internal -j{} -c0 -b2g --idle_latency"
        self.cxl_mlc_idle_run_cmd = "./mlc_internal -j{} --idle_latency"
        self.cxl_mlc_mem_bw_scan_run_cmd = "./mlc_internal --memory_bandwidth_scan -j{}"
        self.cxl_mlc_write_bw_check_cmd = "./mlc_internal --bandwidth_matrix -b4g -W6"
        self.cxl_mlc_read_bw_check_cmd = "./mlc_internal --bandwidth_matrix -R -b4g"
        self.expected_cxl_write_bw_value = self._common_content_configuration.get_cxl_write_bw_value()
        self.expected_cxl_read_bw_value = self._common_content_configuration.get_cxl_read_bw_value()
        self.cxl_mlc_internal_permission_cmd = "chmod 777 ./mlc_internal"
        self.cxl_vendor_id = "0x1e98"
        self.cxl_err_check_regex = r"Found (\d+) error\(s\)"
        self.cxl_addr_value_pair_grep_regex = r"\(addr = (.*), val = (.*)\)"
        self.busybox_devmem_cmd = "busybox devmem {}"
        self.cmd_to_grep_node_details = "node (.*) free: (.*)"
        self.cmd_to_grep_cores = "node {} cpus: (.*)"
        self.cxl_rcrb_addr_regex = "rcrb address = (.*)"
        self.cxl_exppt_addr_regex = "exppt address = (.*)"

    def calculate_dimm_address_range(self, start_index, end_index, size_of_dimm):
        """
        This method is to calculate the Address range for dimm.

        :param start_index - eg if target dimm is CPU0_DIMM_B1 then start_index should be 1 and end_index 2-
        ["CPU0_DIMM_A1", "CPU0_DIMM_A2", "CPU0_DIMM_B1", "CPU0_DIMM_B2", "CPU0_DIMM_C1"]
        :param end_index - eg if target dimm is CPU0_DIMM_B1 then start_index should be 1 and end_index 2-
        ["CPU0_DIMM_A1", "CPU0_DIMM_A2", "CPU0_DIMM_B1", "CPU0_DIMM_B2", "CPU0_DIMM_C1"]
        :param size_of_dimm - DIMM size
        """
        each_gb_assumed_addr = 0x100000000 / 4
        start_addr = start_index * int(size_of_dimm) * each_gb_assumed_addr
        end_addr = end_index * int(size_of_dimm) * each_gb_assumed_addr
        return int(start_addr), int(end_addr)

    def create_and_copy_hdm_vm_on_sut(self, peer_name="dax0.0", addr_range="start", ctg_tool_path=None,
                                       stride_addr=0x4):
        """
        This method is to create the Vector Machine for peer device (HDM).

        :param peer_name - peer name for eg:- dax0.0, dax0.1, dax1.0
        :param addr_range - start - to pick the address from starting range.
                            end - to pick the address from last range.
        :param ctg_tool_path - ctg tool path on sut
        :param stride_addr - skipping address
        """
        peer_addr_range_str = self._common_content_lib.execute_sut_cmd("cat /proc/iomem | grep '{}'".format(peer_name), "cmd", 200)
        peer_addr_range = re.search(r"\s+([\S]+)-([\S+]+)", peer_addr_range_str)
        start_addr = peer_addr_range.group(1)
        end_addr = peer_addr_range.group(2)

        if addr_range == "start":
            start = int(start_addr, 16) + 0x100000
        elif addr_range == "end":
            start = int(end_addr, 16) - 0x1000000 - stride_addr * self.NO_OF_ADDRESSES
        else:
            raise content_exceptions.TestFail("Not implemented for selected Address range")

        file_name = peer_name.split('.')[0] + "_" + peer_name.split('.')[1] + addr_range + ".txt"

        host_file_name = os.path.join(self.log_dir, file_name)
        with open(host_file_name, "w+") as fp:

            for index in range(start, start + stride_addr * self.NO_OF_ADDRESSES, stride_addr):
                fp.writelines(str(hex(index)) + "\n")

        self.os.copy_local_file_to_sut(source_path=host_file_name, destination_path=ctg_tool_path)
        self._log.info(Path(os.path.join(ctg_tool_path, file_name)).as_posix())
        return Path(os.path.join(ctg_tool_path, file_name)).as_posix()

    def get_dimm_size_and_location(self, csp=None, dimm_name="CPU0_DIMM_D1"):
        """
        This method is used to get the dimm size and location.

        :param csp - cscripts object
        :param dimm_name - dimm name
        :return tupple - size, dimm location
        """
        #  sorted dimm name a/c to Address
        sorted_dimm_list = ["CPU0_DIMM_A1", "CPU0_DIMM_A2", "CPU0_DIMM_B1", "CPU0_DIMM_B2", "CPU0_DIMM_C1",
                            "CPU0_DIMM_C2", "CPU0_DIMM_D1", "CPU0_DIMM_D2", "CPU0_DIMM_E1", "CPU0_DIMM_E2",
                            "CPU0_DIMM_F1", "CPU0_DIMM_F2", "CPU0_DIMM_G1", "CPU0_DIMM_G2", "CPU0_DIMM_H1",
                            "CPU0_DIMM_H2", "CPU1_DIMM_A1", "CPU1_DIMM_A2", "CPU1_DIMM_B1", "CPU1_DIMM_B2",
                            "CPU1_DIMM_C1", "CPU1_DIMM_C2", "CPU1_DIMM_D1", "CPU1_DIMM_D2", "CPU1_DIMM_E1",
                            "CPU1_DIMM_E2", "CPU1_DIMM_F1", "CPU1_DIMM_F2", "CPU1_DIMM_G1", "CPU1_DIMM_G2",
                            "CPU1_DIMM_H1", "CPU1_DIMM_H2"]

        if csp.get_socket_count() > 2:
            raise content_exceptions.TestFail("Still not implemented for grater than 2 sockets")

        #  Getting the dimm location and size from OS command.
        dimm_dict = self.memory_provider.get_dict_off_loc_size_mem_type()

        self._log.info("mem details on SUT - {}".format(dimm_dict))

        size = 0
        dimm_installed_list = []
        size_in_list = []
        for each_key, value in dimm_dict.items():
            if "No Module Installed-Unknown" not in value:
                dimm_installed_list.append(each_key)
                if re.findall(r"([0-9]+)\sGB", value):
                    size_in_list.append(re.findall(r"([0-9]+)\sGB", value)[0])
        self._log.debug(size_in_list)

        size = size_in_list[0]
        installed_dimm_sorted = []
        self._log.info(dimm_installed_list)
        for each_dimm in sorted_dimm_list:
            if each_dimm in dimm_installed_list:
                installed_dimm_sorted.append(each_dimm)
        self._log.info(installed_dimm_sorted)
        self._log.debug("Installed RAM on SUT - {}".format(installed_dimm_sorted))
        self._log.debug("The size of each dimm are- {}".format(size))

        index_number = installed_dimm_sorted.index(dimm_name)

        return size, index_number

    def is_all_dimm_equal_size(self):
        """
        This method to check if all dimm is of equal size.

        :return boolean
        """
        dimm_dict = self.memory_provider.get_dict_off_loc_size_mem_type()

        self._log.info("mem details on SUT - {}".format(dimm_dict))

        size_in_list = []
        for each_key, value in dimm_dict.items():
            if "No Module Installed-Unknown" not in value:
                if re.findall(r"([0-9]+)\sGB", value):
                    size_in_list.append(re.findall(r"([0-9]+)\sGB", value)[0])
        self._log.debug(size_in_list)
        if len(set(size_in_list)) != 1:
            return False
        return True

    def create_and_copy_dimm_vm_on_sut(self, dimm_name="CPU0_DIMM_D1", ctg_tool_path=None, csp=None,
                                       stride_addr=0x40, no_of_files=1):
        """
        This method is to create Vector Machine for (Cache- Dimm).

        :param dimm_name - dimm which needs to target.
        :param sut_dir - sut directory where vm file needs to create.
        :param ctg_tool_path - ctg tool path on sut.
        :param csp - cscripts object
        :param stride_addr - address to skip
        :param no_of_files - number of file
        """
        if not self.is_all_dimm_equal_size():
            raise content_exceptions.TestFail("All dimms are not equal")

        size, index_number = self.get_dimm_size_and_location(csp=csp, dimm_name=dimm_name)

        start, end = self.calculate_dimm_address_range(index_number, index_number + 1, size)
        if no_of_files == 1:

            file_name = dimm_name + ".txt"

            host_file_name = os.path.join(self.log_dir, file_name)
            with open(host_file_name, "w+") as fp:
                for index in range(start, start + stride_addr * self.NO_OF_ADDRESSES, stride_addr):
                    fp.writelines(str(hex(index)) + "\n")

            self.os.copy_local_file_to_sut(source_path=host_file_name, destination_path=ctg_tool_path)
            self._log.info(Path(os.path.join(ctg_tool_path, file_name)).as_posix())

            return Path(os.path.join(ctg_tool_path, file_name)).as_posix()

        else:
            file_path_dict = {}
            for each_file in range(no_of_files):
                file_name = dimm_name + "_{}.txt".format(str(each_file))

                host_file_name = os.path.join(self.log_dir, file_name)

                with open(host_file_name, "w+") as fp:
                    for index in range(start, start + stride_addr * self.NO_OF_ADDRESSES, stride_addr):
                        fp.writelines(str(hex(index)) + "\n")

                start = start + stride_addr * self.NO_OF_ADDRESSES + 102400
                self.os.copy_local_file_to_sut(source_path=host_file_name, destination_path=ctg_tool_path)
                self._log.info(Path(os.path.join(ctg_tool_path, file_name)).as_posix())
                file_path_dict[each_file] = Path(os.path.join(ctg_tool_path, file_name)).as_posix()

            return file_path_dict

    def execute_cxl_ctg_pre_condition(self, sdp_obj=None):
        """
        This method is to execute CXL CTG pre-condition.

        :param sdp_obj
        """
        register_addr_dict = {ProductFamilies.SPR: 0x620
                              }
        value_dict = {ProductFamilies.SPR: 0x1717}
        try:
            register = register_addr_dict[self._common_content_lib.get_platform_family()]
            value = value_dict[self._common_content_lib.get_platform_family()]
            self._log.info("Halt the Machine")
            sdp_obj.halt()
            self._log.info("Read the register - {} ({})".format(register, hex(register)))
            req_output = sdp_obj.msr_read(register)
            self._log.info("Register output is - {}".format(req_output))
            self._log.info("Write value- {} ({}) to register- {} ({})".format(value, hex(value), register,
                                                                              hex(register)))
            sdp_obj.msr_write(register, value)
            output = sdp_obj.msr_read(register)
            self._log.info("Register output is - {}".format(output))
            for each_thread in output:
                if value != each_thread:
                    raise content_exceptions.TestFail("Found unexpected value in register output- {} ".format(output))
            sdp_obj.go()
        except:
            raise content_exceptions.TestFail("Failed during executing pre condition")

    def is_bus_enumerated(self, bus):
        """
        This method is to check bus is enumerated.

        :param bus
        """
        try:
            out_put = self._common_content_lib.execute_sut_cmd("lspci | grep '{}:00.0'".format(bus),
                                                               "lspci", self._command_timeout)
            self._log.info(out_put)
            return True
        except:
            return False

    def is_ctg_tool_running(self, api_to_check=[]):
        """
        This method is to check the status of the CTG tool

        :param api_to_check - running tool command which needs to check.
        eg : ["./ctg -v -p 56 --sc 0 --vm /root/ctg_tool/ctg-master/dax1_0start.txt --s1 0 --sc 1
        --vm /root/ctg_tool/ctg-master/dax1_0end.txt --s3 25 -t 2000 > peer0_to_peer1.txt"]
        """
        stress_provider = StressAppTestProvider.factory(self._log, self._cfg, self.os)

        for each_api in api_to_check:

            if stress_provider.check_app_running(app_name="./ctg", stress_test_command=each_api):
                self._log.info("{} is running".format(each_api))
            else:
                return False
        return True

    def poll_the_ctg_tool(self, execution_time_seconds, api_to_check=[]):
        """
        This method is to poll the tool.

        :param execution_time_seconds - times to poll
        :param api_to_check - running tool command which needs to check.
        eg : ["./ctg -v -p 56 --sc 0 --vm /root/ctg_tool/ctg-master/dax1_0start.txt --s1 0 --sc 1
        --vm /root/ctg_tool/ctg-master/dax1_0end.txt --s3 25 -t 2000 > peer0_to_peer1.txt"]
        """
        start_time = time.time()
        self._log.info("Stress is in progress")
        while time.time() - start_time < execution_time_seconds:
            self._log.info("Remaining time in second- {}".format(execution_time_seconds - (time.time() - start_time)))
            time.sleep(TimeConstants.TEN_MIN_IN_SEC)
            if not (execution_time_seconds - (time.time() - start_time) < TimeConstants.TEN_MIN_IN_SEC):
                if not self.is_ctg_tool_running(api_to_check):
                    raise content_exceptions.TestFail("CTG tool execution stopped before expected time")
            else:
                start_time_to_poll = time.time()
                while time.time() - start_time_to_poll < TimeConstants.FIFTEEN_IN_SEC * 2:
                    ret_val = []
                    for each_api in api_to_check:
                        if not self.is_ctg_tool_running(api_to_check=[each_api]):
                            ret_val.append(True)
                        else:
                            ret_val.append(False)
                    time.sleep(TimeConstants.ONE_MIN_IN_SEC)
                    if all(ret_val):
                        return True
                log_err = "Stress execution did not completed in time"
                self._log.error(log_err)
                raise log_err

    def verify_bw_in_ctg_tool_output(self, file_name=None, ctg_tool_path=None):
        """
        This method is to verify the bw from ctg tool path.

        :param file_name - logged file name
        :param ctg_tool_path - ctg tool path on sut
        """
        ctg_tool_output = self._common_content_lib.execute_sut_cmd("cat {}".format(file_name), "cat {}".format(
            file_name), self._command_timeout, ctg_tool_path)

        if re.findall(self.REGEX_TO_CHECK_CTG_BW, ctg_tool_output):
            raise content_exceptions.TestFail("Unexpected bandwidth captured in OS")

    def get_the_core_list(self, cpu=0):
        """
        This method is to get the all cores in list.

        :param cpu - socket number
        :return cores in list
        """
        numact_output = self._common_content_lib.execute_sut_cmd("numactl -H", "numactl -H", self._command_timeout)
        cpu_cores_dict = {}
        for each_line in numact_output.split('\n'):
            import re
            status = re.findall("node [0-9] cpus: (.*)", each_line)
            if status:
                self._log.debug("CPU cores:- {}".format(status))
                if "node 0 cpus" in each_line:
                    cpu_cores_dict[0] = status[0].split(' ')
                elif "node 1 cpus" in each_line:
                    cpu_cores_dict[1] = status[0].split(' ')
                elif "node 2 cpus" in each_line:
                    cpu_cores_dict[2] = status[0].split(' ')
                elif "node 3 cpus" in each_line:
                    cpu_cores_dict[3] = status[0].split(' ')
                else:
                    raise content_exceptions.TestFail("Still Not implemented for more than 4 CPU.")

        return cpu_cores_dict[cpu]

    def create_mem_traffic_cmd(self, bus=52, ct_list=[], addr_start=0x0, addr_stop=0x4000000, stride_addr=0x4000000,
                               iteration_addr=1048578, opcode="s1", opcode_value= 9, t=7200):
        """
        This method is to create command to put mem traffic.

        :param bus - cxl pcie bus
        :param ct_list - core numbers in list
        :param addr_start - starting address
        :param addr_stop - stop address
        :param stride_addr - skipping address
        :param iteration_addr
        :param opcode - opcode - eg:- s1, s2, s3
        :param opcode_value - eg:- 9, 11, 30 etc
        :param t - stress execution time

        :return command
        """
        cmd = "./ctg -v -p {}".format(bus)
        opcode_cmd = " --ct {} --addr-start {} --addr-stop {} --addr-stride {} --addr-iteration {} --{} {}"

        start_addr = addr_start
        for each_core in ct_list:

            cmd = cmd + opcode_cmd.format(each_core, hex(start_addr), hex(addr_stop), hex(stride_addr),
                                          iteration_addr, opcode, opcode_value)
            start_addr = start_addr + stride_addr
            addr_stop = addr_stop + stride_addr

        cmd += " -t {}".format(t)
        return cmd

    def is_cxl_card_enumerated(self, port=None, socket=None, csp_obj=None):
        """
        This method is to check if Cxl Card is enumerated or not.

        :param port - port
        :param socket - Socket
        :param csp_obj - Cscripts provider object
        :return True if enumerated else False
        """
        sec_bus_reg_path_dict = {ProductFamilies.SPR: "pi5.{}.cfg.secbus".format(port),
                                 ProductFamilies.EMR: "pi5.{}.cfg.secbus".format(port)}
        product_family = self._common_content_lib.get_platform_family()

        sec_bus_output = csp_obj.get_by_path(csp_obj.UNCORE, socket_index=socket,
                                             reg_path=sec_bus_reg_path_dict[product_family])
        self._log.info("CXL Card Bus: {} is : {}".format(sec_bus_reg_path_dict[product_family], sec_bus_output))
        if sec_bus_output:
            return True
        return False

    def get_cxl_bus(self, port=None, socket=None, csp_obj=None):
        """
        This method is to get the cxl device bus.

        :param port - port name- pxp3.pcieg5.port0
        :param socket - socket number
        :param csp_obj - cscripts obj
        """

        sec_bus_reg_path_dict = {ProductFamilies.SPR: "pi5.{}.cfg.secbus".format(port),
                                 ProductFamilies.EMR: "pi5.{}.cfg.secbus".format(port)}
        product_family = self._common_content_lib.get_platform_family()

        sec_bus_output = csp_obj.get_by_path(csp_obj.UNCORE, socket_index=socket,
                                             reg_path=sec_bus_reg_path_dict[product_family])
        self._log.info("Socket Number- {} PXP Port- {} is mapped to the Bus Number- {}".format(
            socket, sec_bus_reg_path_dict[product_family], sec_bus_output))

        return str(sec_bus_output)

    def initialize_os_cyling_script(self):
        """
        This method is to execute the CXL Cycling(OS).

        return True/False
        """
        pcie_health_check_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pcie_health_check")
        pcie_base_line = os.path.join(pcie_health_check_dir, "get_baseline.sh")

        pcie_check = os.path.join(pcie_health_check_dir, "pci_check_cycle.sh")

        self.os.copy_local_file_to_sut(pcie_base_line, "/root")
        self.os.copy_local_file_to_sut(pcie_check, "/root")
        self.os.execute("chmod +777 get_baseline.sh", 20, "/root")
        self.os.execute("chmod +777 pci_check_cycle.sh", 20, "/root")
        self.os.execute(r"sed -i -e 's/\r$//' get_baseline.sh", 20, "/root")
        self.os.execute(r"sed -i -e 's/\r$//' pci_check_cycle.sh", 20, "/root")
        self._common_content_lib.execute_sut_cmd("./get_baseline.sh", "gather initial pcie baseline data",
                                                 self._command_timeout, "/root")

        return True

    def check_cap_err_cnt(self):
        """
        This method is to check the CXL Capability Err Cnt.
        """
        cxl_cap_err_cnt_output = self._common_content_lib.execute_sut_cmd("cat CxlCapErrorCount", "CxlCapErrorCount",
                                                                          self._command_timeout, "/var/log/cycling")
        if int(cxl_cap_err_cnt_output) != 0:
            raise content_exceptions.TestFail("Unexpected CXL Capability Error count was captured- {}".format(
                cxl_cap_err_cnt_output))

        self._log.info("No CXL Capability was Captured")
        link_err_cnt_output = self._common_content_lib.execute_sut_cmd("cat LinkErrorCount", "LinkErrorCount",
                                                                       self._command_timeout, "/var/log/cycling")
        if int(link_err_cnt_output) != 0:
            raise content_exceptions.TestFail("Unexpected Link Error Count was Captured -{}".format(
                link_err_cnt_output))
        self._log.info("No Link Error was Capture")

    def get_sockets_expected_bandwidth(self, bw_value, sockets):
        """
        Sum up the bandwidth between sockets and cxl node, if they are connected directly.

        :param bw_value: expected bandwidth value
        :param sockets: number of sockets
        :return: A dictionary that map a pair of socket numbers to the expected bandwidth
        between them. Note that the first socket number in the pair will always be
        the smaller one.
        """
        bandwidth_dict = {}

        for skt in range(sockets):
            if (skt, sockets) not in bandwidth_dict.keys():
                bandwidth_dict[(skt, sockets)] = 0
            bandwidth_dict[(skt, sockets)] = bw_value
        for socket_pair in bandwidth_dict.keys():
            self._log.info("The bandwidth between sockets {} is expected to be {} GB/s".format(socket_pair,
                                                                                               bandwidth_dict[socket_pair]))
        return bandwidth_dict

    def check_bandwidth_with_mlc(self, bandwidth_expected_dict, bw_cmd, mlc_tool_path):
        """
        Check if mlc bandwidth matrix meets the expectation.

        :param bandwidth_expected_dict: A dictionary that map a pair of socket numbers to the bandwidth
        between them. Note that the first socket number in the pair will always be
        the smaller one.
        :param bw_cmd: command for BW calculation
        :param mlc_tool_path: mlc tool path
        :return: True if expectations are met. False otherwise.
        """
        self._log.info("Starting MLC bandwidth with cmd={}".format(bw_cmd))
        mlc_bandwidth_results = self._common_content_lib.execute_sut_cmd(bw_cmd, bw_cmd, self._command_timeout,
                                                                         mlc_tool_path)
        if not mlc_bandwidth_results:
            self._log.error("mlc bandwidth test not executed properly!")
            return False
        self._log.info(mlc_bandwidth_results.strip())
        raw_data = mlc_bandwidth_results.partition('Numa node\t')[2].strip().replace('-', "").split('\t\n')[1:]
        mlc_matrix = [list(map(float, row.strip().split('\t')))[1:] for row in raw_data]

        verification_succeed = True
        for skt_pair in bandwidth_expected_dict.keys():
            try:
                mlc_result = mlc_matrix[skt_pair[0]][skt_pair[1]] / 1000
                expected_value = bandwidth_expected_dict[skt_pair]
                if not mlc_result >= expected_value:
                    verification_succeed = False
                    self._log.info("The actual bandwidth between {} and {} is {} GB/s, but expected {} GB/s"\
                                   .format(skt_pair[0], skt_pair[1], mlc_result, expected_value))
            except IndexError as ex:
                self._log.error("One or more data point(s) missing in bandwidth matrix from mlc...")
                raise ex

        if verification_succeed:
            self._log.info("Verification succeed, all bandwidths meets expectation.")
        else:
            self._log.info("Bandwidth failed to meet expectation, details listed above.")

        return verification_succeed

    def get_cxl_device_type_cscripts(self, socket, port):
        """
        Get CXL device type from cscripts.

        :param socket: socket
        :param port: port
        :return device_type: string containing cxl device type
        """
        self._log.info("Configuration check from cscripts......................")
        self.sdp.halt()
        self.sdp.start_log("csripts_output.txt", "w")
        self.cxl.get_device_type(int(socket), port)
        self.sdp.stop_log()

        with open("csripts_output.txt", "r") as fp:
            device_type_output = fp.read()
        self.sdp.go()
        self._log.info(f"CXL device type actually present {device_type_output}")
        return str(device_type_output)

    def get_cxl_device_inventory(self, detailed_inventory=False):
        """
        This method will get you a dict having all the cxl devices connected to the system.

        :param detailed_inventory: if True - will get all specs for each cxl device, otherwise only cxl device ports.
        :return cxl_inventory_dict: cxl devices inventory dictionary, where key - the socket number,
        value - list of port numbers of cxl devices connected to that socket
        """
        if detailed_inventory:
            cxl_inventory_dict = self.pxp_inventory.get_slot_inventory(self._common_content_lib.get_platform_family(),
                                                                       self.csp)[self.pxp_inventory.IOProtocol.CXL]
        else:
            cxl_inventory_dict = self.pxp_inventory.get_pxp_inventory()[self.pxp_inventory.IOProtocol.CXL]
        if not cxl_inventory_dict:
            raise content_exceptions.TestFail("No CXL cards is been placed on platform")
        cxl_dev_present = False
        for key, value in cxl_inventory_dict.items():
            if value:
                cxl_dev_present = True
        if not cxl_dev_present:
            raise content_exceptions.TestFail("Inventory dictionary has no cxl device.")
        self._log.info("Listing all cxl devices - {}".format(cxl_inventory_dict))
        return cxl_inventory_dict

    def cxl_cmem_err_check(self, cxl_inventory_dict):
        """
        Method covers
        Running cxl method "cmem_err_check" from cscripts. Also check for any error

        :param cxl_inventory_dict: cxl_devices_inventory_dict
        :return True/False
        """
        for key, value in cxl_inventory_dict.items():
            for port in value:
                if port:
                    cxl_mem_output = self.get_cxl_cscript_method_output("cxl_cmem_err_check", key, port)
                    output = re.findall(self.cxl_err_check_regex, cxl_mem_output)
                    if not output:
                        raise content_exceptions.TestFail("Couldn't get cxl mem error status ")
                    self._log.info("List of Errors reported - {}".format(output))
                    errors = [int(i) for i in output if int(i) > 0]
                    if errors:
                        self._log.info("Errors reported for cxl device at socket-{} port-{}".format(key, port))
                        return False
                    self._log.info("Test passed for cxl device at socket-{} port-{}".format(key, port))
            self.sdp.go()
        self._log.info("Test cxl_cmem_err_check passed for cxl devices")
        return True

    def get_dvsec_address_value_pair(self, cxl_func, socket, port):
        """
        Method covers
        Running given cxl method from cscripts.

        :param cxl_func: cscript method name for cxl
        :param socket: cxl device socket
        :param port: cxl device port
        :return cxl_iep_dvsec_output_dict: dictionary for the registers and it's values.
        """
        cxl_dvsec_output = self.get_cxl_cscript_method_output(cxl_func, socket, port)
        regex_output = re.findall(self.cxl_addr_value_pair_grep_regex, cxl_dvsec_output)
        if not regex_output:
            raise content_exceptions.TestFail(f"No addr values found on running {cxl_func}..")
        cxl_dvsec_output_dict = {}
        for value in regex_output:
            cxl_dvsec_output_dict[value[0]] = value[1]
        self._log.info("Cxl {} output for cxl device at socket-{}, port-{}\n Address-Value - {}".
                       format(cxl_func, socket, port, cxl_dvsec_output_dict))
        return cxl_dvsec_output_dict

    def configure_cxl_device_with_dax(self, socket, port, dax_device):
        """
        Method prepares the device to run mprime load.

        :param socket: socket number
        :param port: port number
        :param dax_device: dax number
        :return node_num: configures node number for cxl
        :return node_mem: available memory on the cxl node
        """
        self._log.info("Verifying device is TYPE 3.............")
        if not "Type 3" in self.get_cxl_device_type_cscripts(int(socket), port):
            raise content_exceptions.TestFail(f"Type 3 device not present at socket- {socket} {port}")
        self._log.info("Verifying the availability of given dax device")
        if dax_device in self._common_content_lib.execute_sut_cmd(self.cxl_get_dax_devs_cmd,
                                                                  "cmd to get all dax devices present",
                                                                  self._command_timeout).split():
            self._log.info("{} is available, Configuring it....".format(dax_device))
        else:
            raise content_exceptions.TestFail("{} dax device not present".format(dax_device))
        self._common_content_lib.execute_sut_cmd(self.cxl_device_config_cmd.format(dax_device),
                                                 "CXL device configuration command", self._command_timeout)

        numactl_output = self._common_content_lib.execute_sut_cmd("numactl -H", "numactl -H", self._command_timeout)
        status = re.findall(self.cmd_to_grep_node_details, numactl_output)
        if status:
            node_num = status[-1][0]
            node_mem = status[-1][1]
        else:
            raise content_exceptions.TestFail("couldn't get cxl configured node details")
        self._log.info("Finding cpu cores available")
        status = re.findall(self.cmd_to_grep_cores.format(int(self.csp.get_socket_count())-1), numactl_output)
        core_count = int(status[0].split()[-1]) + 1
        self._log.info("cxl configured node - {}, with free memory - {}, and core_count - {}".format(node_num, node_mem, core_count))
        self._common_content_lib.clear_dmesg_log()

        return node_num, node_mem, core_count

    def get_cxl_cscript_method_output(self, cxl_method, socket, port):
        """
        This method will return the output from the given cscript cxl method.

        :param cxl_method: cscript cxl method
        :param socket: socket number
        :param port: cxl port number
        :return cscript_output: output of cscript method
        """
        self.sdp.halt()
        time.sleep(TimeConstants.TEN_SEC)
        self.sdp.start_log("csripts_output.txt", "w")
        eval("self.cxl.{}(int(socket), port)".format(cxl_method))
        self.sdp.stop_log()
        self.sdp.go()
        with open("csripts_output.txt", "r") as fp:
            cscript_output = fp.read()
        self._log.info("{} output for socket- {}, and slot - {} \nOutput - {}".
                       format(cxl_method, socket, port, cscript_output))
        return cscript_output

    def verify_addr_value_from_busybox(self, cxl_addr_value_dict):
        """
        Method to compare and verify address values from cxl_method with busybox devmem.

        :param cxl_addr_value_dict: dictionary of cxl function where addr as key and addr value as value.
        :return True/False
        """
        self._log.info("Checking the address values with busybox")
        status = True
        for key, value in cxl_addr_value_dict.items():
            busybox_value = self._common_content_lib.execute_sut_cmd(self.busybox_devmem_cmd.format(key),
                                                                     self.busybox_devmem_cmd.format(key),
                                                                     self._command_timeout)
            if not busybox_value:
                raise content_exceptions.TestFail(f"No output from busybox for address-{key}")
            if not int(value, 16) == int(busybox_value.split()[0], 16):
                self._log.info("Cscript value-{} did not match with busybox value-{} for address-{}".
                               format(value, busybox_value.split()[0], key))
                status = False
            else:
                self._log.info("Cscript value-{} matched with busybox value-{} for address-{}".
                           format(value, busybox_value.split()[0], key))
        return status

    def verify_cxl_addr_from_cxl_function(self, addr_name, regex, cxl_output, socket, port):
        """
        This method verifies the given address from the cxl methods of cscripts

        :param addr_name: name/type of cxl address
        :param regex: regex to grep the given address name from cxl method output
        :param cxl_output: output cxl function form cscript
        :param socket: socket number
        :param port: cxl port number
        :returns True/False
        """
        regex_output = re.findall(regex, cxl_output)
        if not regex_output:
            raise content_exceptions.TestFail("Couldn't grep {} address from cxl output"
                                              "for cxl device at socket-{} port-{}".format(addr_name, socket, port))
        self.sdp.halt()
        addr = eval(f"self.cxl.get_cxl_{addr_name}_bar(int(socket), port)")
        self.sdp.go()
        if not int(regex_output[0], 16) == addr:
            self._log.info(f"{addr_name} address {regex_output[0]} did not match with 'get_cxl_{addr_name}_bar' value "
                           f"{addr}")
            return False
        self._log.info(f"{addr_name} is verified for socket - {socket} and port - {port}")
        return True

    def extract_data_from_cxl_cap_list(self, cap_list_cscript_output, process="pci"):
        """
        Method will return back the given cap list data in the required format.

        :param cap_list_cscript_output: cscrpit output of the executed cap list
        :param process: (pci/rcrb) is the kind of format we need to process the data for further verification.
        return data: Dict/list, if pci-list, if rcrb-dict
        """
        cap_name_list_output = cap_list_cscript_output.partition('Next CAP Offset')[2].strip().split('\n')[2:-1]
        if process == "pci":
            data = []
            self._log.info("Processing data for cxl ext pci cap list...............")
        else:
            data = {}
            regex_output = re.findall("RCRB Base = (.*)", cap_list_cscript_output)
            if not regex_output:
                raise content_exceptions.TestFail("Couldn't grep any rcrb base address from the cscript output")
            rcrb_base_addr = regex_output[0]
            self._log.info("Processing data for cxl ext rcrb cap list...............")
            self._log.info(f"cxl RCRB base address - {rcrb_base_addr}")
        for string in cap_name_list_output:
            cap_name_output = string.replace(" ", "").strip().split("|")[1:-1]
            self._log.info(f"Formating CXL CAP - {cap_name_output}")
            if process == "pci":
                data.append(f"[{cap_name_output[2][2:]} v{cap_name_output[3][2:]}]")
            if process == "rcrb":
                data[hex(int(rcrb_base_addr, 16) + int(cap_name_output[2], 16))] = cap_name_output[4] + \
                                                                                   cap_name_output[3][2:] + \
                                                                                   cap_name_output[1][2:]
        self._log.info(f"Returning the cxl ext {process} cap list data - {data}")
        return data

    def get_cxl_ieh_error_dump(self, socket, port):
        """
        This method runs cxl ieh error dump and returns the dict of all error registers and there values.

        :param socket: socket number
        :param port: port number
        """
        cxl_error_dump_output = self.get_cxl_cscript_method_output("cxl_ieh_error_dump", socket, port)
        cxl_error_dump_output_list = cxl_error_dump_output.replace('*', "").replace('-', "").split('\n')
        cxl_error_dump_output_dict = {}
        for value in cxl_error_dump_output_list:
            if value.startswith('|') and not "Bit#" in value:
                error_status_list = value.replace("  ", "").split('|')[1:-1]
                error_status_list = [item.strip() for item in error_status_list]
                cxl_error_dump_output_dict[error_status_list[0]] = error_status_list[2:]
        self._log.info(f"cxl_ieh_error_dump dict for socket {socket} port '{port}' is - \n{cxl_error_dump_output_dict}")
        return cxl_error_dump_output_dict

    def verify_cxl_error_dump_for_all_error_registers(self, cxl_error_dump_dict, socket, port):
        """
        This method verifies the error register values got from cxl_error_dump with the individual error registers.

        :param cxl_error_dump_dict: cxl_error_dump dictionary
        :param socket: socket number
        :param port: port number
        """
        status = True
        io_die = self.pcie_common.get_pxp_io_die(port)
        for key, value in cxl_error_dump_dict.items():
            if not len(value) == len(self.CXL_ERROR_STATISTICS_DICT[key]):
                raise content_exceptions.TestFail("error values grepped from cxl_error_dump does not match the actual "
                                                  f"number of error registers - {self.CXL_ERROR_STATISTICS_DICT[key]}")
            for num in range(len(value)):
                if self._product_family == ProductFamilies.GNR:
                    output = self.csp.get_by_path(
                        scope=self.csp.SOCKET, reg_path=self.CXL_UNC_CMD_DICT[self._product_family].
                        format(io_die, port, self.CXL_ERROR_STATISTICS_DICT[key][num]), socket_index=socket).read()
                else:
                    output = self.csp.get_by_path(
                        scope=self.csp.SOCKET, reg_path=self.CXL_UNC_CMD_DICT[self._product_family].
                        format(port, self.CXL_ERROR_STATISTICS_DICT[key][num]), socket_index=socket).read()
                if not int(str(value[num]), 16) == int(str(output), 16):
                    self._log.info(f"Socket - {socket}, Port - {port}\nRegister {key}- "
                                   f"{self.CXL_ERROR_STATISTICS_DICT[key][num]}"
                                   f"\t cxl error dump value - {value[num]} did not match register value - {output}")
                    status = False
                self._log.info(f"Register {key}- {self.CXL_ERROR_STATISTICS_DICT[key][num]}\t"
                               f" cxl error dump value - {value[num]}  matches the register value - {output}")
        return status

    def cxl_pci_ext_cap_list_show(self, bus, socket, port):
        """
        This method runs cscript cxl method show_pci_ext_cap_list(bus, device, function, segment) .

        :param bus: bus id of cxl device
        :param socket: socket number
        :param port: port number
        """
        self.sdp.halt()
        self.sdp.start_log("csripts_output.txt", "w")
        self.cxl.show_pci_ext_cap_list(int(bus, 16), 0, 0, 0)
        self.sdp.stop_log()
        self.sdp.go()
        with open("csripts_output.txt", "r") as fp:
            cscript_output = fp.read()
        self._log.info("pci_ext_cap_list output for cxl device - {} at socket-{}, and slot-{} \nOutput- {}".
                       format(bus, socket, port, cscript_output))
        data = self.extract_data_from_cxl_cap_list(cscript_output, "pci")
        if not data:
            raise content_exceptions.TestFail(f"no data extracted for pci_ext_cap_list")
        lspci_output = self._common_content_lib.execute_sut_cmd(
            "lspci -s {}:00.0 -vvv".format(str(bus[2:])),
            "bus details command execution", self._command_timeout)

        for val in data:
            if val not in lspci_output:
                self._log.info(f"{val} is not present in lspci output for bdf - {bus} at socket-{socket}"
                               f" and port-{port}")
                return False
        return True

    def validate_device_type(self, socket, port, cxl, cxl_device_type):
        """
        This method is to verify the CXL device type.

        :param socket
        :param port
        :param cxl
        :param cxl_device_type
        """
        self.sdp.start_log("csripts_output.txt", "w")
        cxl.get_device_type(int(socket), port)
        self.sdp.stop_log()

        with open("csripts_output.txt", "r") as fp:
            device_type_output = fp.read()

        if cxl_device_type not in str(device_type_output):
            raise content_exceptions.TestFail("Cxl Device Type was not found as expected for socket- {}"
                                              "and port- {}".format(socket, port))
        self._log.info("cxl device type output- {} for socket- {} and port- {}".format(device_type_output,
                                                                                       socket, port))

    def validate_cxl_version(self, socket, port, cxl, cxl_version):
        """
        This method is to validate the CXL version.

        :param socket
        :param port
        :param cxl
        :param cxl_version
        """
        self.sdp.start_log("csripts_output.txt", "w")
        cxl.get_cxl_version(int(socket), port)
        self.sdp.stop_log()

        with open("csripts_output.txt", "r") as fp:
            cxl_version_output = fp.read()

        if cxl_version not in str(cxl_version_output):
            raise content_exceptions.TestFail("Cxl Device Version was not found as expected for socket- {} "
                                              "and port- {}".format(socket, port))
        self._log.info("cxl version output- {} for socket- {} and port- {}".format(cxl_version_output,
                                                                                   socket, port))

    def check_devsec_equal_to_initial_value(self, cycle_num=0, file_1=None, file_2=None, devsec_type="dp_dvsec"):
        """
        This method is to check the devsec out put from Initial Cycle.

        :param cycle_num
        :param file_1
        :param file_2
        :param devsec_type
        """
        if cycle_num != 0:
            import filecmp
            result = filecmp.cmp(file_1, file_2)
            if not result:
                raise content_exceptions.TestFail("{} was not equal to initial value in Cycle Number- {}".format(
                    devsec_type, cycle_num))
        else:
            self._log.info("Cycle Number - {} is in progress. So, skipping comparision as it is not required".format(
                cycle_num))
