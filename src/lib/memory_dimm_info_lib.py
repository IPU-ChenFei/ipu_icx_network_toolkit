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
import pandas as pd


class MemoryDimmInfo:
    """
    This Class is used to get the structure/information of the DIMM's for creating the memory dimm info class
    """
    # panda dataframe column names
    DIMM_ID = "DimmID"
    HEALTH_STATE = "HealthState"
    MANAGEABLE_STATUS = "ManageabilityState"
    NON_VOLATILE_DIMM = "Non-Volatile"
    FIRMWARE_VERSION = "FWVersion"

    def __init__(self, dimm_topology, show_dimm=None, manageability=None, performance=False):
        """
        Create a new Memory_Dimm_Info object by parsing dimm_topology data from ipmctl command

        :param dimm_topology: This data is output from ipmctl -show topology command
        :param show_dimm: This data is output from ipmctl -show -dimm command
        :param manageability: whether to add an manageability state to the data frame
        """

        # create the dataframe panda object from initial topology data
        if performance:
            self.df_dimm_performance_data = self.create_stress_performance_dataframe(dimm_topology)
        else:

            self._df_dimm_data = self._parse_ipmctl_output_data(dimm_topology)

            # removing DDR from data frame
            for (rowName, rowData) in self._df_dimm_data.iterrows():
                if '0x' not in rowData['DimmID']:
                    self._df_dimm_data.drop(rowName, inplace=True)

            # create the dataframe panda object from initial dimm data
            if show_dimm is not None:
                self._df_show_dimm_data = self._parse_ipmctl_output_data(show_dimm)

                # Adding one more column "HealthState" to our data frame obtained from executing
                # the ipmctl show topology command
                list_health_status = ["Not Healthy" for index in range(len(self._df_dimm_data))]
                self._df_dimm_data[self.HEALTH_STATE] = list_health_status

                # Adding one more column "Firmware version" to our data frame obtained from executing
                # the ipmctl show topology command
                list_firmware_version = ["0000000" for index in range(len(self._df_dimm_data))]
                self._df_dimm_data[self.FIRMWARE_VERSION] = list_firmware_version

                self.df_dimm_health_state = self._update_dimm_health_state_info()

                self.df_dimm_fw_version = self._update_dimm_firmware_version_info()

            # Adding one more column "ManageabilityState" to our data frame obtained from executing
            # the ipmctl show topology command
            if manageability is not None:
                list_manageability_state = ["Not Manageable" for index in range(len(self._df_dimm_data))]
                self._df_dimm_data[self.MANAGEABLE_STATUS] = list_manageability_state

                self.df_dimm_manageability_state = self._update_dimm_manageability_state_info(manageability)

            # Create list which contains only non volatile dimm information
            self.list_dcpmm_info = self.get_dimm_info_by_memory_type(self._df_dimm_data, self.NON_VOLATILE_DIMM)

    def _parse_ipmctl_output_data(self, dimm_output):
        """
        This function is for populating the DataFrame object from the dimm topology output information as below
        DimmID | MemoryType                  | Capacity    | PhysicalID| DeviceLocator
        ==============================================================================
        0x0001 | Logical Non-Volatile Device | 253.688 GiB | 0x0016    | CPU0_DIMM_A2
        N/A    | DDR4                        | 8.000 GiB   | 0x0015    | CPU0_DIMM_A1

        :param dimm_output: This data is output from ipmctl command
        :return: data panda object from output data from ipmctl command
        :raise: RuntimeError if any exception occurs during parsing the topology data
        """
        try:
            show_topology_command_result = [str(line).split("|") for line in
                                            [line for line in dimm_output.split('\n') if "=" not in line]]
            if len(show_topology_command_result) == 0:
                show_topology_command_result = [str(line).split("|") for line in
                                                [line for line in dimm_output.split('\r') if "=" not in line and
                                                 "|" in line]]
            show_topology_command_result = [element for element in show_topology_command_result if element != ['']]
            if show_topology_command_result:  # If the dimm_info list is not empty then will create the dataframe
                list_of_show_topology_cmd_output = []
                for info in show_topology_command_result:
                    show_topology_cmd_output_list = []
                    for x in info:
                        show_topology_cmd_output_list.append(x.strip())

                    list_of_show_topology_cmd_output.append(show_topology_cmd_output_list)

                df_dimm = pd.DataFrame(list_of_show_topology_cmd_output)  # Converting the list to dataframe
                df_dimm.columns = df_dimm.iloc[0]  # Modifying Dataframe as First Row of Data as Dataframe Column's
                df_dimm = df_dimm.drop(df_dimm.index[0])  # After Assigning Column Names as Fist Row Data Dropping
                # 0th Index data

                return df_dimm
        except Exception as ex:
            raise RuntimeError("Encountered an error during populating the dataframe using dimm topology output with "
                               "exception '{}'".format(ex))

    def _update_dimm_health_state_info(self):
        """
        This Method is used for Updating the Health Status of Dimm Dataframe Created through ipmctl show topology
         command by getting the health status from ipmctl show dimm command by comparing dimm_id.

        :param: show_dimm_data - passing the output of ipmctl show dimm command.
        :return Update DIMM memory info with Healthy status
        """
        try:
            self._df_dimm_data[self.HEALTH_STATE] = self._df_dimm_data[self.HEALTH_STATE].replace(
                "Not Healthy", self._df_show_dimm_data[self.HEALTH_STATE].iloc[1], inplace=False)
            return self._df_dimm_data
        except Exception:
            raise RuntimeError("Encountered an error during updating dimm_health_state_info : "
                               "update_dimm_health_state_info")

    def _update_dimm_firmware_version_info(self):
        """
        This Method is used for Updating the Firmware version of Dimm Dataframe created through ipmctl show topology
         command by getting the firmware version from ipmctl show dimm command by comparing dimm_id.

        :param: show_dimm_data - passing the output of ipmctl show dimm command.
        :return Update DIMM memory info with Firmware version
        """
        try:
            self._df_dimm_data[self.FIRMWARE_VERSION] = self._df_dimm_data[self.FIRMWARE_VERSION].replace(
                "0000000", self._df_show_dimm_data[self.FIRMWARE_VERSION][1], inplace=False)
            return self._df_dimm_data
        except Exception:
            raise RuntimeError("Encountered an error during updating update_dimm_firmware_version_info : "
                               "update_dimm_firmware_version_info")

    def _update_dimm_manageability_state_info(self, show_dimm_data):
        """
        This Method is used for Updating the Manageability State of Dimm Dataframe Created through ipmctl show
         topology command by getting the Manageability State from ipmctl show Manageability command by
         comparing dimm_id.

        :param: show_dimm_data - passing the output of ipmctl show manageability command.
        :return Update DIMM memory info with Manageability status
        """
        try:
            regex_cmd = r"-*DimmID=([0-9a-z]*)-*\s*[A-Za-z]*\=(Manageable)"  # Regular expression is used to
            # parse the output of ipmctl show manageability and check whether dimm is in Manageable state or not
            show_dimm_data_list = re.findall(regex_cmd, show_dimm_data)

            show_dimm_data_list = [item for items in show_dimm_data_list for item in items]
            _df_dimm_data_dimm_id_list = self._df_dimm_data[self.DIMM_ID].values.tolist()

            index = 0
            for dimm_id in _df_dimm_data_dimm_id_list:
                if dimm_id in show_dimm_data_list:
                    show_dimm_id_index = show_dimm_data_list.index(dimm_id)
                    if show_dimm_data_list[show_dimm_id_index] == dimm_id:
                        self._df_dimm_data[self.MANAGEABLE_STATUS].values[index] = \
                            show_dimm_data_list[show_dimm_id_index + 1]
                    index += 1
            return self._df_dimm_data

        except Exception:
            raise RuntimeError("Encountered an error during updating dimm_manageability_state_info : "
                               "update_dimm_manageability_state_info")

    def get_show_dimm_data_frame(self):
        """
        Function to return the created data frame from show dimm output

        :return data frame
        """
        return self._df_show_dimm_data

    def get_complete_dimm_memory_info(self):
        """
        This Method is used to get Complete Dataframe Created by Ipmctl show topology command with extra
        added two columns HEALTH_STATUS and MANAGEABLE_STATUS

        :return DIMM memory info
        """
        try:
            dimm_req_info = [dimm_dataframe_value for dimm_dataframe_value in
                             self._df_dimm_data.values.tolist()]  # Converting the dataframe values to list
            return dimm_req_info  # returning the DIMM memory info list
        except Exception:
            raise RuntimeError("Encountered an error during getting the complete dimm memory information : "
                               "get_complete_dimm_memory_info")

    def get_dimm_info_healthy(self):
        """
        This function is for filter DIMM_ID info which are "Healthy" under Health state.

        :return DIMM ID list
        """
        try:
            df_healthy_dimm = self._df_dimm_data[(self._df_dimm_data[self.HEALTH_STATE] == "Healthy")]

            return df_healthy_dimm[self.DIMM_ID].values.tolist()
        except Exception:
            raise RuntimeError("Encountered an error during filtering DIMM_ID info which are Healthy Heath "
                               "state and Manageable manageability state: "
                               "get_dimm_info_healthy_manageable")

    def get_dimm_info_healthy_manageable(self):
        """
        This function is for filter DIMM_ID info which are "Healthy" Health state and "Manageable" manageability state

        :return DIMM ID list
        """
        try:
            df_healthy_manageable_dimm = self._df_dimm_data[(self._df_dimm_data[self.HEALTH_STATE] == "Healthy") &
                                                            (self._df_dimm_data[
                                                                 self.MANAGEABLE_STATUS] == "Manageable")]

            return df_healthy_manageable_dimm[self.DIMM_ID].values.tolist()
        except Exception:
            raise RuntimeError("Encountered an error during filtering DIMM_ID info which are Healthy Heath "
                               "state and Manageable manageability state: "
                               "get_dimm_info_healthy_manageable")

    def get_dimm_info_by_index(self, dimm_id_list_index):
        """
        This Method is used for Fetching the Complete data from a dimm data dataframe of a particular dimm by
        passing dimm index

        :param dimm_id_list_index: DIMM_ID index
        :return DIMM memory info
        """
        try:
            dimm_id_list_index = int(dimm_id_list_index)
            df_req_dimm = self._df_dimm_data.iloc[
                          dimm_id_list_index: dimm_id_list_index + 1]  # slicing the DIMM info list
            dimm_req_info = [dimm_data for dimm_data in df_req_dimm.values.tolist()]
            return dimm_req_info  # returning the DIMM memory info list
        except Exception:
            raise RuntimeError("Encountered an error during getting the dimm memory information by index: "
                               "get_dimm_info_by_index")

    def get_dimm_info_by_dimm_id(self, dimm_id):
        """
        This Method is used for Fetching the Complete data from a dimm data dataframe of a particular dimm by
        passing dimm Id

        :param dimm_id: DIMM_ID
        :return DIMM memory info
        """
        try:
            df_req_dimm = self._df_dimm_data.loc[self._df_dimm_data.DimmID == dimm_id]
            dimm_req_info = df_req_dimm.values.tolist()
            return dimm_req_info  # returning the DIMM memory info list
        except Exception:
            raise RuntimeError("Encountered an error during getting the dimm memory information by dimm_id: "
                               "get_dimm_info_by_dimm_id")

    def get_dimm_info_by_memory_type(self, df_dimm, memory_type_info):
        """
        This Method is used to fetch the data from a dataframe based on the Memory_type we are passing. if we
        pass DDR4 then only the data of DDR4 Memory type will be fetched.

        :param df_dimm: Data frame of DIMM
        :param memory_type_info: Memory Type info. example:- "DDR4"
        :return DIMM memory info
        """
        try:
            df_req_dimm = df_dimm[df_dimm['MemoryType'].str.contains(memory_type_info)]
            dimm_req_info = df_req_dimm.values.tolist()
            return dimm_req_info  # returning the DIMM memory info list
        except Exception:
            raise RuntimeError("Encountered an error during getting the dimm memory information by memory type: "
                               "get_dimm_info_by_memory_type")

    def get_dimm_health_state_info_by_dimm_id(self, dimm_id):
        """
        This Method is used to Fetch the Health Status of a Particular Dimm by Passing that Dimm ID

        :param dimm_id: DIMM_ID
        :return Boolean
        """
        try:
            dimm_state_healthy = False
            df_req_dimm = self._df_dimm_data.loc[self._df_dimm_data.DimmID == dimm_id]
            if "Healthy" in df_req_dimm.values:  # Checking the health state
                dimm_state_healthy = True
            return dimm_state_healthy
        except Exception:
            raise RuntimeError(
                "Encountered an error during getting the dimm memory health state information by dimm id: "
                "get_dimm_health_state_info_by_dimm_id")

    def get_dimm_manageability_state_by_dimm_id(self, dimm_id, dimm_output):
        """
        This Method is used to fetch the Manageability State of a Particular Dimm by Passing that Dimm ID
        :param dimm_id: DIMM_ID
        :param dimm_output: Dimm Dataframe
        :return Boolean
        """
        manageability_status_flag = False
        regex_cmd = r"-*DimmID={}-*\s*[A-Za-z]*\=(Manageable)".format(dimm_id)  # Regular expression is used to check
        # whether dimm id is in manageable state or not
        output_list = re.findall(regex_cmd, dimm_output)
        if output_list:
            if output_list[0] == "Manageable":  # Checking the state is Manageable or not
                manageability_status_flag = True
        else:
            raise Exception("Manageable state of dimm_id: {} is not found".format(dimm_id))
        return manageability_status_flag

    def create_stress_performance_dataframe(self, performance_data):
        """
        This function is used to create a data frame for performance data of DCPMM.

        :return: param performance_data : performance data frame
        """
        param_data_list = []
        value_data_list = []
        for data in performance_data.split('\n'):
            performance_data = data.strip().split("=")
            if '' not in performance_data:
                if "--" in performance_data[0]:
                    param_data_list.append(performance_data[0].strip("-"))
                    value_data_list.append(performance_data[1].strip("-"))
                else:
                    param_data_list.append(performance_data[0].strip())
                    value_data_list.append(performance_data[1].strip())
        performance_data_frame = pd.DataFrame(value_data_list, param_data_list)
        return performance_data_frame
