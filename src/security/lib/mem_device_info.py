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


class MemDeviceInfo(object):
    """
    This Class is used to get the structure/information of the MEM for
    creating MemDeviceInfo class
    """
    # regular expression for parsing total online memory data
    _MEM_REGEX_CMD_TOTAL_DATA = r"(Memory\sblock.*)"

    @classmethod
    def parse_mem_output_data(cls, mem_cmd_info):
        """
        This function is for populating the DataFrame object from the lsmem cmd output information as below
        RANGE                                 SIZE  STATE REMOVABLE BLOCK
        0x0000000000000000-0x000000007fffffff   2G online        no     0
        0x0000000100000000-0x000000017fffffff   2G online        no     2
        0x0000000180000000-0x00000007ffffffff  26G online       yes  3-15
        0x0000000800000000-0x00000008ffffffff   4G online        no 16-17
        0x0000000900000000-0x0000000fffffffff  28G online       yes 18-31
        0x0000001000000000-0x000000107fffffff   2G online        no    32

        Memory block size:         2G
        Total online memory:      64G
        Total offline memory:      0B

        :param mem_cmd_info: This data is output from lsmem command
        :return: data panda object from output data from lsmem command
        :raise: RuntimeError if any exception occurs during parsing the lsmem data
        """

        mem_cmd_complete_info_data = re.search(MemDeviceInfo._MEM_REGEX_CMD_TOTAL_DATA, mem_cmd_info, re.DOTALL)
        mem_cmd_complete_info_data = (mem_cmd_complete_info_data.groups()[0])

        mem_data_list = [line for line in mem_cmd_complete_info_data.split('\n')]
        mem_data_dic = {}
        for mem_data in mem_data_list:
            if len(mem_data) > 1:
                mem_data_dic[mem_data.split(":")[0].strip()] = mem_data.split(":")[1].strip()

        df_mem_info = pd.DataFrame(list(mem_data_dic.items()))

        return df_mem_info

    @classmethod
    def get_mem_data_diff(
            cls,
            df_mem_info_src,
            df_mem_info_dest):
        """
        This function will compare the mem info data.

        :param df_mem_info_src: mem data dataframe which you need to compare
        :param df_mem_info_dest: mem data dataframe with you need to compare
        :param mem_cmd_complete_info_src: mem device total memory data which you need to compare
        :param mem_cmd_complete_info_dest: mem device total memory data with you need to compare
        :return: TRUE if all the data is matching with each other and return FALSE if not matching
        """

        mem_data_compare_val = False
        mem_data_compare_val_state = df_mem_info_src.equals(
            df_mem_info_dest)  # Comparing the dataframes
        if mem_data_compare_val_state:
            mem_data_compare_val = True
        return mem_data_compare_val
