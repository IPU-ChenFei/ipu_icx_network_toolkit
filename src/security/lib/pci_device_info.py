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

import pandas as pd
import re


class PciDeviceInfo(object):
    """
    This Class is used to get the structure/information of the PCI for
    creating PciDeviceInfo class
    """
    # panda dataframe column names
    _BDF_BUS_NUMBER = "BDFBusNumber"
    _BDF_DEVICE_NUMBER = "BDFDeviceNumber"
    _BDF_FUNCTION_NUMBER = "BDFFunctionNumber"
    _BDF_DEVICE_CLASS = "BDFDeviceClass"
    _BDF_DEVICE_NAME = "BDFDeviceName"
    # regular expression to parse BDF data
    _BDF_REGEX_CMD = r"([0-9]*)\:([0-9]*)\.([0-9]*)\s(.*)\:(.*)"

    @classmethod
    def parse_pci_output_data(cls, pci_cmd_info):
        """
        This function is for populating the DataFrame object from the lspci cmd output information as below
        00:00.0 Host bridge: Intel Corporation Sky Lake-E DMI3 Registers (rev 07)
        00:04.0 System peripheral: Intel Corporation Sky Lake-E CBDMA Registers (rev 07)
        00:04.1 System peripheral: Intel Corporation Sky Lake-E CBDMA Registers (rev 07)
        00:04.2 System peripheral: Intel Corporation Sky Lake-E CBDMA Registers (rev 07)
        00:04.3 System peripheral: Intel Corporation Sky Lake-E CBDMA Registers (rev 07)
        00:04.4 System peripheral: Intel Corporation Sky Lake-E CBDMA Registers (rev 07)
        00:04.5 System peripheral: Intel Corporation Sky Lake-E CBDMA Registers (rev 07)
        00:04.6 System peripheral: Intel Corporation Sky Lake-E CBDMA Registers (rev 07)
        00:04.7 System peripheral: Intel Corporation Sky Lake-E CBDMA Registers (rev 07)
        00:05.0 System peripheral: Intel Corporation Sky Lake-E MM/Vt-d Configuration Registers (rev 07)
        00:05.2 System peripheral: Intel Corporation Device 2025 (rev 07)

        :param pci_cmd_info: This data is output from lspci command
        :return: data panda object from output data from lspci command
        :raise: if any exception occurs during parsing the lspci data
        """
        pci_cmd_info = [line for line in pci_cmd_info.split('\n')]

        # Defining the pci info data list
        bdf_bus_num_list = []
        bdf_device_num_list = []
        bdf_function_num_list = []
        bdf_device_class_list = []
        bdf_device_name_list = []

        # Iterating through each pci output data line and splitting the data using
        # the regex and appending in different lists
        for pci_cmd_info_line in pci_cmd_info:
            pci_cmd_info_list = re.findall(
                PciDeviceInfo._BDF_REGEX_CMD, pci_cmd_info_line)
            if pci_cmd_info_list:
                bdf_bus_num_list.append(pci_cmd_info_list[0][0])
                bdf_device_num_list.append(pci_cmd_info_list[0][1])
                bdf_function_num_list.append(pci_cmd_info_list[0][2])
                bdf_device_class_list.append(pci_cmd_info_list[0][3])
                bdf_device_name_list.append(pci_cmd_info_list[0][4])

        df_pci_cmd_info = pd.DataFrame(
            list(
                zip(
                    bdf_bus_num_list,
                    bdf_device_num_list,
                    bdf_function_num_list,
                    bdf_device_class_list,
                    bdf_device_name_list)),
            columns=[
                PciDeviceInfo._BDF_BUS_NUMBER,
                PciDeviceInfo._BDF_DEVICE_NUMBER,
                PciDeviceInfo._BDF_FUNCTION_NUMBER,
                PciDeviceInfo._BDF_DEVICE_CLASS,
                PciDeviceInfo._BDF_DEVICE_NAME])  # Converting the list to dataframe

        return df_pci_cmd_info

    @classmethod
    def get_pci_data_diff(cls, df_pci_info_src, df_pci_info_dest):
        """
        This function will compare the pci info data and return TRUE if all the data is matching with each other and
        return FALSE if not matching

        :param df_pci_info_src: pci data dataframe which you need to compare
        :param df_pci_info_dest: pci data dataframe with you need to compare
        :return: TRUE if two data frame is matched else FALSE
        """
        # Comparing the pci device info dataframes and returning the Boolean
        pci_data_compare_val = df_pci_info_src.equals(df_pci_info_dest)
        return pci_data_compare_val
