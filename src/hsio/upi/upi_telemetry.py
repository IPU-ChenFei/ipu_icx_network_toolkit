import re
import os
import pandas as pd
from imp import importlib
from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.pcie.lib.hsio_base_telemetry import HsioBaseTelemetry


class UpiTelemetry(HsioBaseTelemetry):

    """
    This class is used to capture upi related data for telemetry which would be captured before and after the test case
    execution without impacting the testcase
    """

    UPI_MOD_DEFS = {ProductFamilies.SPR: "platforms.SPR.sprupidefs",
                    ProductFamilies.GNR: "platforms.GNR.gnrupidefs",
                    ProductFamilies.ICX: "platforms.ICX.icxupidefs"
                    }

    def __init__(self, log, os, cfg_opts):
        """
        Creates a new UpiTelemetry object

        :param log: Used for debug and info messages
        :param os: system os
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiTelemetry, self).__init__(log, os, cfg_opts)

    def get_upi_info(self):
        """
        creates a upi telemetry log
        :return: upi telemetry dictionary of linkspeed, tx/rx lane status per port per socket
        """
        module = importlib.import_module(self.UPI_MOD_DEFS[self._common_content_lib.get_platform_family()])
        upi_defs_obj = eval("module.%supidefs()" % self._common_content_lib.get_platform_family().lower())
        self._sdp.start_log(self.pcie_sls_log_file)
        upi_defs_obj.topology()
        self._sdp.stop_log()

        with open(self.pcie_sls_log_file) as log_file:
            cmd_output = log_file.read()

            inventory_upi = {}
            upi_ports = {}
            upi_speed = {}
            upi_tx = {}
            upi_rx = {}
            socket = 0
            upi_ports_found = False

            lines = cmd_output.split("\n")
            for line in lines:
                match_socket = re.findall(r"\*\s*(Socket\s\d)", line)
                if len(match_socket) > 0:
                    socket = match_socket[0]
                    inventory_upi[socket] = ""
                match_upi_ports_header = re.findall(r"Port\s\d", line)
                if len(match_upi_ports_header) > 0:
                    upi_port_list = match_upi_ports_header
                    upi_ports_found = True
                if upi_ports_found:
                    port_num = 0
                    match_link_speed = re.findall(r"\|\s*Link Speed\s", line)
                    match_tx_lane_status = re.findall(r"\|\s*UPI Tx Lane Status\s", line)
                    match_rx_lane_status = re.findall(r"\|\s*UPI Rx Lane Status\s", line)
                    if len(match_tx_lane_status) > 0:
                        upi_ports = {}
                        ports = line.split("|")[2:][:-1]
                        for p in range(len(ports)):
                            upi_tx["TxLaneStatus"] = ports[port_num].strip()
                    if len(match_rx_lane_status) > 0:
                        upi_ports = {}
                        ports = line.split("|")[2:][:-1]
                        for p in range(len(ports)):
                            upi_rx["RxLaneStatus"] = ports[port_num].strip()
                    if len(match_link_speed) > 0:
                        upi_ports = {}
                        ports = line.split("|")[2:][:-1]
                        for p in range(len(ports)):
                            upi_speed["LinkSpeed"] = ports[port_num].strip()
                            upi_ports["Port%d" % port_num] = {"Link Speed": upi_speed["LinkSpeed"],
                                                              "UPI Tx Lane Status": upi_tx["TxLaneStatus"],
                                                              "UPI Rx Lane Status": upi_rx["RxLaneStatus"]}
                            port_num += 1
                            inventory_upi[socket] = upi_ports
            return inventory_upi

    def get_upi_linkspeed(self, socket, port):
        """
        :param socket: socket number input
        :param port: port number input
        :return:string of linkspeed of port and socket
        """
        get_upi_info_dict = self.get_upi_info()
        return get_upi_info_dict["Socket %d" % socket]["Port%d" % port]["Link Speed"]

    def get_upi_tx_lane_status(self, socket, port):
        """
        :param socket: socket number input
        :param port: port number input
        :return:string of tx lane status of port and socket
        """
        get_upi_info_dict = self.get_upi_info()
        return get_upi_info_dict["Socket %d" % socket]["Port%d" % port]["UPI Tx Lane Status"]

    def get_upi_rx_land_status(self, socket, port):
        """
        :param socket: socket number input
        :param port: port number input
        :return:string of rx lane status of port and socket
        """
        get_upi_info_dict = self.get_upi_info()
        return get_upi_info_dict["Socket %d" % socket]["Port%d" % port]["UPI Rx Lane Status"]

    def write_upi_telemetry_to_csv(self, upi_telemetry_dict, hostname, testcase):
        """
        This method  would either create  a csv  and  write the upi telemetry info into that csv or appends upi telemetry info
        :param testcase: name of testcase
        :param upi_telemetry_dict -upi device dictionary which has all the devices
        :param hostname - hostname would be used for naming the file
        :return:None
        """
        final_csv_file_path = os.path.join(self.TELEMETRY_UPI_OUTPUT_CSV_DEST_PATH, hostname + "_" + testcase + "_final_sheet.csv")
        csv_data = pd.DataFrame.from_dict(upi_telemetry_dict)
        if os.path.isfile(final_csv_file_path):
            csv_data.to_csv(final_csv_file_path)
        else:
            csv_data.to_csv(final_csv_file_path)

    def get_final_upi_telemetry(self, pre_test_exec_upi_dict, post_test_exec_upi_dict):
        """
        This method will take the pre and post upi dictionaries as input and return the final dictionary with upi telemetry
        which would be written into the csv
        :param pre_test_exec_upi_dict  -upi device dictionary before test case executes
        :param post_test_exec_upi_dict -upi device dictionary after test executes
        :return:final_upi_telemetry_dict -Return combined dictionary to save in csv
        """
        final_upi_telemetry_dict = {"upi_telemetry_pre_test": pre_test_exec_upi_dict,
                                    "upi_telemetry_post_test": post_test_exec_upi_dict}
        return final_upi_telemetry_dict

    def collect_upi_telemetry_to_csv(self, testcase_name, instance_num):
        """
        This method will save the telemetry data related to upi and would write into the csv if
        below flag is set
        <upi_telemetry>
        < collect_upi_telemetry_flag>True</ collect_upi_telemetry_flag>>
        </upi_telemetry>
        :param testcase_name -testcase name with id
        :param instance_num - 0 for before(during prepare) executing the testcase and 1 for after the testcase(during cleanup)
        :return:None
        """
        try:
            if self._common_content_configuration.collect_upi_telemetry_flag():
                self._log.info("Telemetry Started")
                hostname, test_date_time = self.get_dtaf_host(), self.get_dtaf_host_current_datetime()
                if instance_num == 0:
                    self.UPI_TELEMETRY_PRE_DICT = self.get_upi_info()
                    self.UPI_TELEMETRY_PRE_DICT["Hostname"] = hostname
                    self.UPI_TELEMETRY_PRE_DICT["Date/Time"] = test_date_time
                    self.UPI_TELEMETRY_PRE_DICT["Test Case Name"] = testcase_name
                elif instance_num == 1:
                    self.UPI_TELEMETRY_POST_DICT = self.get_upi_info()
                    self.UPI_TELEMETRY_POST_DICT["Hostname"] = hostname
                    self.UPI_TELEMETRY_POST_DICT["Date/Time"] = test_date_time
                    self.UPI_TELEMETRY_POST_DICT["Test Case Name"] = testcase_name
                    final_device_dict = self.get_final_upi_telemetry(self.UPI_TELEMETRY_PRE_DICT,
                                                                  self.UPI_TELEMETRY_POST_DICT)
                    self.write_upi_telemetry_to_csv(final_device_dict, hostname, testcase_name)
                    self._log.info("Telemetry Completed")
        except Exception as e:
            self._log.exception("Telemetry Failed '{}'".format(e))
