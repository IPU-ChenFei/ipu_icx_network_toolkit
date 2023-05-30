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

import re


class CpuDeviceInfo(object):
    """
    This Class is used to get the structure/information of the Lscpu for
    creating CpuDeviceInfo class
    """
    _CPU_FLAGS = "Flags"

    # regular expression to parse key value pair
    _CPU_REGEX_CMD = r"(.*)\:\s*(.*)"

    @classmethod
    def parse_cpu_output_data(cls, cpu_cmd_info):
        """
        This function is for populating the DataFrame object from the lscpu cmd output information as below
        Architecture:          x86_64
        CPU op-mode(s):        32-bit, 64-bit
        Byte Order:            Little Endian
        CPU(s):                96
        On-line CPU(s) list:   0-95
        Thread(s) per core:    2
        Core(s) per socket:    24
        Socket(s):             2
        NUMA node(s):          2
        Vendor ID:             GenuineIntel
        CPU family:            6
        Model:                 85
        Model name:            Genuine Intel(R) CPU 0000%@
        Stepping:              7
        CPU MHz:               2913.305
        CPU max MHz:           3900.0000
        CPU min MHz:           1200.0000
        BogoMIPS:              5600.00
        Virtualization:        VT-x
        L1d cache:             32K
        L1i cache:             32K
        L2 cache:              1024K
        L3 cache:              33792K
        NUMA node0 CPU(s):     0-23,48-71
        NUMA node1 CPU(s):     24-47,72-95
        Flags:                 fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts
         acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts
         rep_good nopl xtopology nonstop_tsc aperfmperf eagerfpu pni pclmulqdq dtes64 monitor ds_cpl vmx smx est
         tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave
         avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt ssbd mba ibrs ibpb stibp
         ibrs_enhanced tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms
         invpcid rtm cqm mpx rdt_a avx512f avx512dq rdseed adx smap clflushopt clwb avx512cd avx512bw avx512vl
         xsaveopt xsavec xgetbv1 cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts hwp
         hwp_act_window hwp_epp hwp_pkg_req pku ospke avx512_vnni spec_ctrl intel_stibp flush_l1d arch_capabilities

        :param cpu_cmd_info: This data is output from lscpu command
        :return: dictionary from output data from lscpu command
        :raise: if any exception occurs during parsing the lscpu data
        """

        cpu_cmd_info = [line for line in cpu_cmd_info.split('\n')]

        # Defining the cpu info data list
        cpu_cmd_column_list = []
        cpu_cmd_value_list = []
        cpu_values_list = []
        # Iterating through each cpu output data line and splitting the data using
        # the regex and appending in different lists
        for cpu_cmd_info_line in cpu_cmd_info:
            cpu_cmd_info_list = re.findall(
                CpuDeviceInfo._CPU_REGEX_CMD, cpu_cmd_info_line)
            if cpu_cmd_info_list:
                cpu_cmd_column_list.append(cpu_cmd_info_list[0][0])
                if "," in cpu_cmd_info_list[0][1]:
                    cpu_value_list = cpu_cmd_info_list[0][1].split(",")
                    cpu_cmd_value_list.append(cpu_value_list)
                else:
                    cpu_cmd_value_list.append(cpu_cmd_info_list[0][1])
        # Getting the CPU Flags details
        if CpuDeviceInfo._CPU_FLAGS in cpu_cmd_column_list:
            cpu_flags_index = cpu_cmd_column_list.index(CpuDeviceInfo._CPU_FLAGS)
            cpu_values_list = (
                cpu_cmd_value_list[cpu_flags_index]).split(" ")
        # Getting the CPU device info dictionary
        cpu_cmd_dict = dict(
            zip(cpu_cmd_column_list[:-1], cpu_cmd_value_list[:-1]))
        cpu_cmd_dict[CpuDeviceInfo._CPU_FLAGS] = cpu_values_list

        return cpu_cmd_dict

    @classmethod
    def get_cpu_data_diff(cls, cpu_info_src, cpu_info_dest):
        """
        This function will compare the cpu info data.

        :param cpu_info_first: cpu info src dictionary which you need to compare
        :param cpu_info_second: cpu info dest dictionary with you need to compare
        :return: TRUE if all the data is matching with each other and return FALSE if not matching
        """

        if sorted(cpu_info_src.items()) == sorted(cpu_info_dest.items()):
            cpu_data_compare_flag = True
        else:
            cpu_data_compare_flag = False

        return cpu_data_compare_flag
