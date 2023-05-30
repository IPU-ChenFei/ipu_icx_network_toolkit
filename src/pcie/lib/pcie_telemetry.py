from src.pcie.lib.hsio_base_telemetry import HsioBaseTelemetry
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
import pandas as pd
import os
import sys
import re
import struct


class PcieTelemetry(HsioBaseTelemetry):

    def __init__(self, log, os, cfg_opts):
        """
        This class inherits HsioBaseTelemetry  for pythonsv/cscripts objects and also to retrieve datetime and dtaf host name.
        This class is used to capture pcie related data for telemetry like width, speed, memory allocated
        which would be captured before and after the test case execution without impacting the testcase
        """
        try:
            super(PcieTelemetry, self).__init__(
                log, os, cfg_opts)
        except Exception as e:
            self._log.error("Telemetry Initialization Failed '{}'".format(e))

    def get_ltssm_state_all_ports(self):
        """
        This method executes sls command and then parse it results  to return a dictionary which contains pxp_path as key and LTSSM state as the value .
        :return: dict - It returns a dictionary with key:value as pxp_path:LTSSM State
        """
        ltssm_states_of_all_ports = {}
        try:
            # To get the sockets count
            sockets_count = len(self._sv.sockets)
            self._log.info("Sockets Count : {}".format(sockets_count))
            self._sdp.start_log(self.pcie_sls_log_file, "w")
            self.pcie_ltssm_obj.sls()
            self._sdp.stop_log()
            with open(self.pcie_sls_log_file, "r") as log_file:
                log_file_list = log_file.readlines()
            # To verify the connected slots in pcie.sls command output
            for each in range(len(log_file_list)):
                pxp_string = re.findall(self.REGEX_CMD_FOR_PYTHONSV_PORT, log_file_list[each])
                if pxp_string:
                    pythonsv_port_address = pxp_string[0].split(" ")[1]
                    ltssm_state = pxp_string[0].split("=")[-1]
                    log_file = list(map(str.rstrip, log_file_list))
                    index = log_file.index(pxp_string[0])
                    for socket_index in reversed(range(sockets_count)):
                        if re.findall(self.REGEX_CMD_FOR_SOCKET.format(socket_index), "".join(log_file[index::-1])):
                            socket = self.SOCKET.format(socket_index)
                            endpoint_path = {
                                ProductFamilies.SPR: socket.lower() + ".uncore.pi5." + pythonsv_port_address}
                            pythonsv_port_address = endpoint_path[self._reg_provider.silicon_cpu_family]
                            ltssm_states_of_all_ports[pythonsv_port_address] = {}
                            ltssm_states_of_all_ports[pythonsv_port_address]["Link-State"] = ltssm_state.lstrip()
                            break
            return ltssm_states_of_all_ports
        except Exception as e:
            self._log.error("Failed to get sls results '{}'".format(e))

    def get_active_port_ltssm_state(self, pxp_path):
        """
        This method returns the ltssm state corresponding to the input pxp path
        :param: pxp_path  -Complete pxp path of the desired endpoint
        :return: str - LTSSM state of the input pxp port.
        """
        try:
            return self.PCIE_ENDPOINT_LTSSM_STATES_DICT[pxp_path]["Link-State"]
        except Exception as e:
            self._log.error("Failed to get PCIE Endpoint LTSSM State '{}'".format(e))
            return "NA"

    def get_endpoints_pxp_paths(self):
        """
        This method returns the pcie endpoint pxp paths in a list
        :returns: pcie endpoint list with complete pxpx paths .
        """
        try:
            self._log.info("Getting the pcie data ")
            self._sdp.halt_and_check()
            endpoint_pxp_path = []
            endpoint_bus_did_vid_dict = {}
            reg = {ProductFamilies.SPR: self._sv.sockets.uncore.pi5.pxps.pciegs.ports.path}
            all_available_paths = eval(str(reg[self._reg_provider.silicon_cpu_family]))
            for i in all_available_paths:
                try:
                    pcie_cfg_reg_path = self._sv.get_by_path(i)
                    if (
                            pcie_cfg_reg_path.cfg.did != 0xFFFF and pcie_cfg_reg_path.cfg.linksts.dllla == 1 and pcie_cfg_reg_path.cfg.secbus != 0x0):  # if sec bus is not 0 it's an endpoint
                        endpoint_pxp_path.append(i)
                except Exception as e:
                    if 'RSP 10 - Powered down' in str(e):
                        pass
                    else:
                        self._log.error("Failed to check secbus  '{}'".format(e))
            return endpoint_pxp_path
        except Exception as e:
            self._log.error("Failed to get pxp paths for endpoints  '{}'".format(e))
        finally:
            self._sdp.go()

    def get_pcie_endpoint_bus_vid_did(self):
        """
        This method gets the pcie endpoint bus,vid and did
        :return: pcie device dictionary with bus,vid and did.
        """
        try:
            endpoint_bus_did_vid_dict = {}
            endpoint_pxp_path = []
            endpoint_pxp_path = self.get_endpoints_pxp_paths()
            self._sdp.halt_and_check()
            for count in range(len(endpoint_pxp_path)):
                endpoint_bus_did_vid_dict[count] = {}
                pcie_cfg_reg_path = self._sv.get_by_path(endpoint_pxp_path[count])
                endpoint_bus_did_vid_dict[count]["Bus"] = pcie_cfg_reg_path.cfg.secbus.read()
                register_read00 = struct.pack(">I", self.pcicfg(endpoint_bus_did_vid_dict[count]["Bus"], 0, 0,
                                                           0x00)).hex()  # read register and output in big endian mode
                endpoint_bus_did_vid_dict[count]["Device-Id"] = register_read00[:4]
                endpoint_bus_did_vid_dict[count]["Vendor-Id"] = register_read00[4:]
                endpoint_bus_did_vid_dict[count]["PXP-PATH"] = endpoint_pxp_path[count]
            return endpoint_bus_did_vid_dict
        except Exception as e:
            self._log.error("Failed to get PCIE related data due to the exception '{}'".format(e))
        finally:
            self._sdp.go()

    def append_all_pcie_data_into_dict(self, pcie_devices, lspci_info, testcase_name, hostname, test_date_time,
                                       cmd_output_bios_version):
        """
        This method  appends the lspci data,testname,hostname,bios version to the pcie_devices  dictionary
        :param pcie_devices  -list of endpoint pcie_devices
        :param lspci_info -lspci results  from linux
        :param testcase_name - str testcase name and hsdes id ex- testcase_hsdesid
        :param hostname -str hostname  where dtaf is running
        :param test_date_time -str datetime info when test is triggered
        :param cmd_output_bios_version - (str )bios version in sut.
        :return:complete_dev_dict-device dictionary contains Bus,LinkState,Vid,Did,Testid,hostname,Bios_version,memory allocated
        Link Speed and width
         """
        device_dict = {}
        found_device_set = False
        for key in pcie_devices:
            device_dict[key] = {}
            device_dict[key]["Bus"] = pcie_devices[key]["Bus"]
            device_dict[key]["Link-State"] = self.get_active_port_ltssm_state(pcie_devices[key]["PXP-PATH"])
            device_dict[key]["Vendor-id"] = pcie_devices[key]["Vendor-Id"]
            device_dict[key]["device-id"] = pcie_devices[key]["Device-Id"]
            device_dict[key]["Test-id"] = testcase_name
            device_dict[key]["System"] = hostname
            device_dict[key]["Datetime"] = test_date_time
            device_dict[key]["Bios"] = cmd_output_bios_version
            search_string = (str(device_dict[key]["Bus"])[2:]) + ':00.0'
            for line in lspci_info:
                line = line.rstrip()
                if search_string in line:
                    found_device_set = True
                    mem_list = []
                    device_dict[key]["Name"] = line
                    vendor_name = re.search(":\s(\w+)", line)
                    device_dict[key]["Vendor-Name"] = vendor_name.group(1)
                    device_dict[key]["Mem_Size"] = "na"
                    device_dict[key]["Link-Capacity-Speed"] = 0
                    device_dict[key]["Link-Capacity-Width"] = 0
                    device_dict[key]["Link-Status-Speed"] = 0
                    device_dict[key]["Link-Status-Width"] = 0
                if found_device_set:
                    if 'Region' in line:
                        try:
                            mem = re.findall(r"[^[]*\[([^]]*)\]", line)
                            mem_size = mem[0].split("=")
                            mem_list.append(mem_size[1])
                            total_mem = '+'.join(mem_list)
                            device_dict[key]["Mem_Size"] = total_mem
                        except  Exception as e:
                            self._log.error("Failed to get mem  data from lspci due to the exception '{}'".format(e))
                            device_dict[key]["Mem_Size"] = "na"
                    if 'LnkCap:' in line:
                        try:
                            device_dict[key]["Link-Capacity"] = line[17:]
                            speed_and_width_numbers = re.findall('[0-9]+', str(device_dict[key]["Link-Capacity"]))
                            speed_and_width_numbers = [speed_and_width_numbers[0] + "." + speed_and_width_numbers[1],
                                                       speed_and_width_numbers[2]] if len(
                                speed_and_width_numbers) == 3 else speed_and_width_numbers
                            device_dict[key]["Link-Capacity-Speed"] = speed_and_width_numbers[0]
                            device_dict[key]["Link-Capacity-Width"] = speed_and_width_numbers[1]
                        except  Exception as e:
                            device_dict[key]["Link-Capacity-Speed"] = 0
                            device_dict[key]["Link-Capacity-Width"] = 0
                    if 'LnkSta:' in line:
                        try:
                            device_dict[key]["Link-Status"] = line[16:]
                            speed_and_width_numbers = re.findall('[0-9]+', str(device_dict[key]["Link-Status"]))
                            speed_and_width_numbers = [speed_and_width_numbers[0] + "." + speed_and_width_numbers[1],
                                                       speed_and_width_numbers[2]] if len(
                                speed_and_width_numbers) == 3 else speed_and_width_numbers
                            device_dict[key]["Link-Status-Speed"] = speed_and_width_numbers[0]
                            device_dict[key]["Link-Status-Width"] = speed_and_width_numbers[1]
                            found_device_set = False
                        except Exception as e:
                            device_dict[key]["Link-Status-Speed"] = 0
                            device_dict[key]["Link-Status-Width"] = 0
        return device_dict

    def get_pcie_device_info(self, pre_test_exec_device_dict, post_test_exec_device_dict):
        """
        This method will take the pre and post pcie device dictionaries as input and return the final dictionary with the speed and width
        which would be written into the csv
        :param pre_test_exec_device_dict  -pcie device dictionary before test case executes
        :param post_test_exec_device_dict -pcie device dictionary after test executes
        :return:final_dev_dict -Return final dictionary to save in csv
        """
        final_dev_dict = {}
        for key in post_test_exec_device_dict:
            final_dev_dict[key] = {}
            final_dev_dict[key]["Name"] = pre_test_exec_device_dict[key]["Name"]
            final_dev_dict[key]["Bus"] = pre_test_exec_device_dict[key]["Bus"]
            final_dev_dict[key]["Vendor-Name"] = pre_test_exec_device_dict[key]["Vendor-Name"]
            final_dev_dict[key]["Vendor-id"] = pre_test_exec_device_dict[key]["Vendor-id"]
            final_dev_dict[key]["Device-id"] = pre_test_exec_device_dict[key]["device-id"]
            final_dev_dict[key]["Ltssm-State-Pre"] = pre_test_exec_device_dict[key]["Link-State"]
            final_dev_dict[key]["Ltssm-State-Post"] = post_test_exec_device_dict[key]["Link-State"]
            final_dev_dict[key]["Test-id"] = pre_test_exec_device_dict[key]["Test-id"]
            final_dev_dict[key]["System"] = pre_test_exec_device_dict[key]["System"]
            final_dev_dict[key]["Datetime"] = pre_test_exec_device_dict[key]["Datetime"]
            final_dev_dict[key]["Bios"] = pre_test_exec_device_dict[key]["Bios"]
            final_dev_dict[key]["Link-Capacity"] = pre_test_exec_device_dict[key]["Link-Capacity"]
            final_dev_dict[key]["Link-Status-Pre"] = pre_test_exec_device_dict[key]["Link-Status"]
            final_dev_dict[key]["Link-Status-Post"] = post_test_exec_device_dict[key]["Link-Status"]
            final_dev_dict[key]["Link-Capacity-Speed"] = pre_test_exec_device_dict[key]["Link-Capacity-Speed"]
            final_dev_dict[key]["Link-Capacity-Width"] = pre_test_exec_device_dict[key]["Link-Capacity-Width"]
            final_dev_dict[key]["Link-Status-Speed-Pre"] = post_test_exec_device_dict[key]["Link-Status-Speed"]
            final_dev_dict[key]["Link-Status-Width-Pre"] = pre_test_exec_device_dict[key]["Link-Status-Width"]
            final_dev_dict[key]["Link-Status-Speed-Post"] = post_test_exec_device_dict[key]["Link-Status-Speed"]
            final_dev_dict[key]["Link-Status-Width-Post"] = post_test_exec_device_dict[key]["Link-Status-Width"]
            final_dev_dict[key]["SpeedDiff"] = float(post_test_exec_device_dict[key]["Link-Status-Speed"]) - float(
                post_test_exec_device_dict[key]["Link-Status-Speed"])
            final_dev_dict[key]["WidthDiff"] = int(post_test_exec_device_dict[key]["Link-Status-Width"]) - int(
                pre_test_exec_device_dict[key]["Link-Status-Width"])
            final_dev_dict[key]["SpeedDiffCap"] = float(pre_test_exec_device_dict[key]["Link-Capacity-Speed"]) - float(
                post_test_exec_device_dict[key]["Link-Status-Speed"])
            final_dev_dict[key]["WidthDiffCap"] = int(pre_test_exec_device_dict[key]["Link-Capacity-Width"]) - int(
                post_test_exec_device_dict[key]["Link-Status-Width"])
            final_dev_dict[key]["Link-Capacity-Gen"] = self._DEVICE_SPEED_IN_GT_SEC_TO_PCIE_GEN_DICT[
                str(final_dev_dict[key]["Link-Capacity-Speed"])]
            final_dev_dict[key]["Link-Status-Gen-Pre"] = self._DEVICE_SPEED_IN_GT_SEC_TO_PCIE_GEN_DICT[
                str(final_dev_dict[key]["Link-Status-Speed-Pre"])]
            final_dev_dict[key]["Link-Status-Gen-Post"] = self._DEVICE_SPEED_IN_GT_SEC_TO_PCIE_GEN_DICT[
                str(final_dev_dict[key]["Link-Status-Speed-Post"])]
            final_dev_dict[key]["GenDiff"] = final_dev_dict[key]["Link-Status-Gen-Post"] + "-" + final_dev_dict[key][
                "Link-Status-Gen-Pre"]
            final_dev_dict[key]["GenDiffCap"] = final_dev_dict[key]["Link-Capacity-Gen"] + "-" + final_dev_dict[key][
                "Link-Status-Gen-Post"]
            final_dev_dict[key]["Device_Mem"] = pre_test_exec_device_dict[key]["Mem_Size"]
        return final_dev_dict

    def write_pcie_devices_to_csv(self, device_dict, hostname):
        """
        This method  would either create  a csv  and  write the pcie devices  into that csv or appends the pcie devices
        data on to the csv if its already present..
        :param device_dict -pcie device dictionary which has all the devices
        :param hostname - hostname would be used for naming the file
        :return:None
        """
        final_csv_file_path = os.path.join(self.TELEMETRY_OUTPUT_CSV_DEST_PATH, hostname + "_final_sheet.csv")
        csv_data = pd.DataFrame(list(device_dict.values()))
        if (os.path.isfile(final_csv_file_path)):
            csv_data.to_csv(final_csv_file_path, mode='a', header=False, index=False)
        else:
            csv_data.to_csv(final_csv_file_path, mode='a', index=False)

    def collect_io_telemetry_to_csv(self, testcase_name, instance_num):
        """
        This method will save the telemetry data related to pcie endpoints((Bus no,speed,width and memory allocated to the device)) and would write into the csv if
        below flag is set
        <io_telemetry>
        < collect_io_telemetry_flag>True</ collect_io_telemetry_flag>>
        </io_telemetry>
        :param testcase_name -testcase name with id
        :param instance_num - 0 for before(during prepare) executing the testcase and 1 for after the testcase(during cleanup)
        :return:None
        """
        try:
            if self._common_content_configuration.collect_io_telemetry_flag():
                self._log.info("Telemetry Started")
                final_device_dict = {}
                device_dict = {}
                device_parameters = []
                if self._os.os_type == OperatingSystems.LINUX:
                    pcie_devices = self.get_pcie_endpoint_bus_vid_did()
                    self.PCIE_ENDPOINT_LTSSM_STATES_DICT = self.get_ltssm_state_all_ports()
                    hostname, test_date_time = self.get_dtaf_host(), self.get_dtaf_host_current_datetime()
                    cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd="lspci -vv ",
                                                                          cmd_str="Running LSPCI on SUT",
                                                                          execute_timeout=self._cmd_time_out)
                    cmd_output_bios_version = self._common_content_lib.execute_sut_cmd(
                        sut_cmd="dmidecode | grep -i -m 1 Version ",
                        cmd_str="Running dmidecode for bios version on SUT", execute_timeout=self._cmd_time_out)
                    cmd_output_bios_version = re.search('E\S+', cmd_output_bios_version).group(0)
                    lspci_info = list(cmd_output.split("\n"))
                    device_dict = self.append_all_pcie_data_into_dict(pcie_devices, lspci_info, testcase_name, hostname,
                                                                      test_date_time,
                                                                      cmd_output_bios_version)
                    if (instance_num == 0):
                        self.PCIE_DEVICES_PRE_DICT = device_dict
                        for key in self.PCIE_DEVICES_PRE_DICT:
                            self._log.info(
                                "IOTELEM->" + "Bus:" + str(self.PCIE_DEVICES_PRE_DICT[key]["Bus"]) + ";" + "Vendorid:" +
                                str(self.PCIE_DEVICES_PRE_DICT[key][
                                        "Vendor-id"]) + ";" + "Deviceid:" + str(self.PCIE_DEVICES_PRE_DICT[key][
                                                                                    "device-id"]) + ";" + "Host:" + str(
                                    self.PCIE_DEVICES_PRE_DICT[key]["System"]) + ";")
                    elif (instance_num == 1):
                        self.PCIE_DEVICES_POST_DICT = device_dict
                        final_device_dict = self.get_pcie_device_info(self.PCIE_DEVICES_PRE_DICT,
                                                                      self.PCIE_DEVICES_POST_DICT)
                        self.write_pcie_devices_to_csv(final_device_dict, hostname)
                        self._log.info("Telemetry Completed")
                elif self._os.os_type == OperatingSystems.WINDOWS:
                    self._log.exception("Not supported for Windows")
            else:
                self._log.info("Telemetry Not Configured")
        except Exception as e:
            self._log.exception("Telemetry Failed '{}'".format(e))
