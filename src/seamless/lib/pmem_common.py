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
import os
import time
import ntpath
import random
from src.seamless.lib.seamless_common import SeamlessBaseTest
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.tests.bmc.constants.pmem_constants import PmemLinux, PmemWindows
from src.seamless.tests.bmc.constants.ssd_constants import TimeDelay
from src.seamless.tests.bmc.constants.pm_constants import CoreCStates
from src.seamless.lib.pm_common import PmCommon, SocwatchCommon


class PmemCommon(SeamlessBaseTest):
    """
    This Class is Used as Common Class For all the PMEM FW Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PmemCommon

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super().__init__(test_log, arguments, cfg_opts)
        self.nvdimmutil_path = None
        self.file_sut_path = None
        self.pm_soc = SocwatchCommon(test_log, arguments, cfg_opts)

    def show_dimm(self):
        """
        This function will run the ipmctl show dimm
        """
        output = self.run_ssh_command(PmemLinux.SHOW_DIMM)
        if output.stderr:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
        if "Invalid or unexpected" in output.stdout:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")
        return output.stdout

    def show_topology(self):
        """
        This function will run the ipmctl show topology
        """
        output = self.run_ssh_command(PmemLinux.SHOW_TOPOLOGY)
        if output.stderr:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
        if "Invalid or unexpected" in output.stdout:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")
        return output.stdout

    def memoryresources(self):
        """
        This function will run the ipmctl show memoryresources
        """
        output = self.run_ssh_command(PmemLinux.SHOW_MEMORYRESOURCES)
        if output.stderr:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
        if "Invalid or unexpected" in output.stdout:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")
        return output.stdout

    def create_appdirect(self):
        """
            This function will create appdirect mode
        """
        output = self.run_ssh_command(PmemLinux.APPDIRECT_CMD)
        if output.stderr:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
        if "Invalid or unexpected" in output.stdout:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")
        self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
        return output.stdout

    def update_fw(self, fw_file_path):
        """
        This function will Update the firmware using ndctl
        fw_file_path: PMEM firmware file path
        """
        if self._os_type == OperatingSystems.LINUX:
            output = self.run_ssh_command(PmemLinux.UPDATE_FW_CMD.format(fw_file_path))
            # if output.stderr:
            #     lines = output.stderr.split("\n")
            #     for line in lines:
            #         if not ("uploading firmware" in line or "updated" in line):
            #             raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
            if "Invalid or unexpected" in output.stdout:
                raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")
            return output.stdout
        else:
            dimms = self.dimm_ids
            if len(dimms) <= 0:
                raise RuntimeError("Dimms are not detected")
            for dimm_id in range(len(self.dimm_ids)):
                index = random.randrange(0, len(dimms))
                dimm = dimms.pop(index)
                output = self.run_ssh_command(PmemWindows.CMD.format(self.nvdimmutil_path, dimm, fw_file_path))
                if output.stderr:
                    lines = output.stderr.split("\n")
                    for line in lines:
                        if not ("updating firmware" in line or "Downloaded Successfully" in line):
                            self._log.info(f"Unable to run the command with the below error \n {output.stderr}")
                if "Invalid or unexpected" in output.stdout:
                    raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")
                if "The firmware was downloaded successfully. The new firmware revision for slot 1 is" not in output.stdout:
                    raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")

    def activate_fw(self):
        """
        This function will activate the run time activation
        """
        if self._os_type == OperatingSystems.LINUX:
            output = self.run_ssh_command(PmemLinux.ACTIVATE_CMD)
        else:
            output = self.run_ssh_command(PmemWindows.CMD2.format(self.nvdimmutil_path))
            if "Activate runtime firmware using firmware managed IO Quiesce method ... done" not in output.stdout:
                raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
        if output.stderr:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
        return output.stdout

    def get_pmem_fw_debug_log(self, folder_path, prefix, version):
        """
        This function will get the fw debug log form the dimm
        folder_path: folder path where nlog_dict is present
        prefix: output file name
        version:  fw version
        return: out put of nlog command
        """
        output = self.run_ssh_command(PmemLinux.NLOG_CMD.format(folder_path, prefix, version))
        if output.stderr:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
        if "Invalid or unexpected" in output.stdout or "The passed dictionary file doesn't exist" in output.stdout:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")
        return output.stdout

    def get_pmem_memory_configuration(self):
        """
            This function will get the pmem_memory configuration
        """
        output = self.show_topology()
        if output:
            count_ddr5 = 0
            count_pmem = 0
            for i in output.split(" "):
                if "DDR5" in i:
                    count_ddr5 = count_ddr5 + 1
                if "Non-Volatile" in i:
                    count_pmem = count_pmem + 1
        if count_ddr5 or count_pmem:
            self._log.info(f"Number of DDR5:{count_ddr5}")
            self._log.info(f"Number of PMEM:{count_pmem}")
        else:
            self._log.info("No Dimm is connected or unable to detect DIMM")

    def health_status(self, show_dimm_out):
        """
            This function check the health status of the PMEM
            show_dimm_out: output of ipmctl show -dimm
        """
        result = show_dimm_out.strip().split("\n")
        for i in result:
            regex1 = re.findall(r"\dx\d\d\d\d", i)
            if len(regex1) == 1:
                result3 = i.split("|")
                if len(result3) > 3:
                    if "Healthy" != result3[3].strip():
                        raise RuntimeError("Dimm {} is not Healthy".format(regex1))
        self._log.info("All Dimms are Healthy")
        return True

    def get_index(self, output, split_str, string):
        """
        The Function will split the line of string into list with split string and returns
        the index of the required string
        output: sting line
        split_str: srt=ring to be split the line
        string: string used to get the index

        return: index
        """
        index = 0
        if string in output:
            result = output.split(split_str)
            for i in result:
                if string == i.strip():
                    return index
                index += 1
        return False

    def total_memory_show_dimm(self, output_show_dimm):
        """
        This function is to calculate the total memory from show -dimm
        output_memoryresources: output of ipmctl show -dimm

        return: sum of memory capacity of dimms
        """
        regex = re.findall(r"\d+\.?\d* GiB", output_show_dimm)
        if len(regex) > 0:
            sum = 0
            for i in regex:
                regex2 = re.findall(r"\d+\.?\d*", i)
                if regex2[0]:
                    sum += float(regex2[0])
                else:
                    raise RuntimeError("Unable to read the dimm Capacity")
        else:
            raise RuntimeError("Unable to read the output")
        return sum

    def check_near_value(self, percentage, value, comp_value):
        """
        This function will return true if +/-a percentage of the value
        percentage: percentage to be allowed
        value: Number or value
        comp_value: Comparison  value/number

        return: true if comparison  value is +/- percentage of the value
        """
        result = float(float(percentage) / 100) * value
        min = value - result
        max = value + result
        if comp_value >= min and comp_value <= max:
            return True
        return False

    def check_appdirect(self, output_memoryresources, output_show_dimm):
        """
        The function will check the pmem is appdirect or not
        output_memoryresources: output of ipmctl show -memoryresources
        output_show_dimm: output of ipmctl show -dimm

        return: True if sut is in appdirect
        """
        pmemmodule = {}
        ddr = {}
        total = {}
        index = None
        result = output_memoryresources.split("\n")
        for i in result:
            if "PMemModule" in i:
                index = self.get_index(output_memoryresources, "|", "PMemModule")
                break
        if not index:
            raise RuntimeError("Unable to get PmemModule index")
        # The below lambda function converts string digits into float
        conv_int = lambda a: float((re.findall(r"\d+\.?\d*", a))[0]) if (re.findall(r"\d+\.?\d*", a)) else a
        for i in result:
            if "Volatile" in  i or "AppDirect" in i or "Cache" in i or "Inaccessible" in i or "Physical" in i:
                list = i.split("|")
                pmemmodule[list[0].strip()] = conv_int(list[index].strip())
                ddr[list[0].strip()] = conv_int(list[1].strip())
                total[list[0].strip()] = conv_int(list[3].strip())
        result = self.total_memory_show_dimm(output_show_dimm)
        if self.check_near_value(.5, float(result), float(pmemmodule["AppDirect"])) and pmemmodule["Volatile"] == 0:
            self._log.info("Pmem is in Appdirect mode")
            return True
        return False

    def check_pmem_fw(self, version, filename):
        """
            Function to check pmem firmware is in the sut if not it will install
            version: pmem version
            filename: file_name

            return: firmware path
        """
        foldername = "crfw_{}".format(version)
        fw_zip_file = "crfw_{}.zip".format(version)
        if self._os_type == OperatingSystems.LINUX:
            root_path = "/root"
            cmd = r"cd {} && ls".format(root_path)
        else:
            root_path = self.windows_sut_root_path
            cmd = r"cd {} && dir".format(root_path)
        if self._os_type == OperatingSystems.WINDOWS:
            folderpath = f"{root_path}\\{foldername}"
        else:
            folderpath = f"{root_path}/{foldername}"
        result = self.run_ssh_command(cmd, log_output=False)
        if result.stderr:
            raise RuntimeError("Unable to get the {} folder list with the error \n{}".format(root_path, result.stderr))
        list = result.stdout.split("\n")
        found = False
        for i in range(len(list)):
            if foldername == list[i]:
                found = True
        if not found:
            if self._os_type == OperatingSystems.WINDOWS:
                cmd4 = "cd {} && mkdir {}".format(root_path, foldername)
                self.run_ssh_command(cmd4)
            else:
                cmd4 = "mkdir {}".format(foldername)
                result5 = self.run_ssh_command(cmd4)
                if result5.stderr:
                    raise RuntimeError("Unable to make directory {} with the error \n{}".format(foldername, result5.stderr))
        result2 = self.check_filepath_sut(folderpath, filename)
        if result2:
            return result2
        else:
            if fw_zip_file not in result.stdout:
                host_path = self.find_cap_path(fw_zip_file)
                if not host_path:
                    raise RuntimeError(r"Unable to find the file {} in C:\Artifactory".format(filename))
                self.sut_ssh.copy_local_file_to_sut(host_path, root_path)
            if self._os_type == OperatingSystems.WINDOWS:
                cmd3 = r"cd {} && tar xvzf {} -C {}".format(root_path, fw_zip_file, foldername)
            else:
                cmd3 = r"cd {} && unzip {} -d {}".format(root_path, fw_zip_file, foldername)
            result3 = self.run_ssh_command(cmd3)
            if self._os_type == OperatingSystems.LINUX:
                if result3.stderr:
                    raise RuntimeError("Unable to extract the {} file  with the error \n".format(fw_zip_file, result3.stderr))
            result4 = self.check_filepath_sut(folderpath, filename)
            if not result4:
                raise RuntimeError(r"Unable to find the file {} or copy the file in sut".format(filename))
            return result4

    def get_total_pmem_dimms(self, show_dimm):
        """
            This function will read the number of pmem dimm from show dimm
            show_dimm: output od ipmctl show dimm

            return: total number of pmem dimms
        """
        dimms = len(re.findall(r"\dx\d\d\d\d", show_dimm))
        if dimms == 0:
            raise RuntimeError("Unable to detect Pmem modules")
        return dimms

    def check_armed_state(self, output):
        """
            This function will return number of pmem dimms activated
            output: output of activation

            return: number of activated pmem dimms
        """
        return len(re.findall('"activate_state":"armed"', output))

    def check_activate_output(self, output, version):
        """
            This function will check the version in the activation output
            output: output of activation command
            version: Firmware version

            return: number of verified dimm version
        """
        version_without_zero = version.replace("0", "")
        version_without_zero = version_without_zero.replace(".", "")
        ver = re.findall('"current_version":"0x\d+"', output)
        res = re.findall('"can_update":true', output)
        for i in range(len(ver)):
            ver[i] = ver[i].replace('"current_version":"0x', '')
            ver[i] = ver[i].replace('"', '')
            ver[i] = ver[i].replace('0', '')
            if  int(ver[i]) != int(version_without_zero):
                return False
        if len(ver) == len(res):
            return len(ver)
        self._log.error("count is mismatching")
        return False

    def get_pmem_version(self, show_dimm, dimm_id):
        """
            This Function read the pmem version from show dimm
            show_dimm: output of ipmctl show -dimm
            dimm_id: dimm is
            return: pmem version
        """
        lines = show_dimm.split("\n")
        for i in lines:
            regex1 = re.findall(r"\dx\d\d\d\d", i)
            version = re.findall(r"\d?\d\.\d?\d\.\d?\d\.\d\d\d\d", i)
            if len(regex1) == 1 and regex1[0] == dimm_id and len(version)>0:
                return version[0]
        raise  RuntimeError("Unable to read the version")

    def comp_version(self, current_version, exp_version):
        """
            This Function will compare the actual version to expected_version
            current_version: Current version
            exp_version: expected_ver

            return: True if both the current and expected version are matched
        """
        c_version = current_version
        current_version = current_version.replace("0", "")
        current_version = current_version.replace(".", "")
        if not self.expected_ver:
            raise RuntimeError("Expected_ver is not there in command")
        exp_version = exp_version.replace("0", "")
        exp_version = exp_version.replace(".", "")
        if int(current_version) != int(exp_version):
            raise RuntimeError("Expected_version {} is not matching with current version {}".format(self.expected_ver, c_version))
        return True

    def run_nlog(self, tool_path, dst_file, version):
        """
            This function will run nlog command and return output
            tool_path: nlog dct path
            version: fw version

            return: output nlog command
        """
        output = self.run_ssh_command(PmemLinux.NLOG_CMD.format(tool_path, dst_file, version))
        if output.stderr:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
        if "Invalid or unexpected" in output.stdout:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")
        return output.stdout

    def ipmctl_interface_ver_match(self, tool_ver_out):
        """
            This function will check the ipmitool version
            tool_ver_out: output of ipmctl version

            return: version without . and 0
        """
        version = re.findall(r"\d?\d\.\d?\d\.\d?\d\.\d?\d\d\d", tool_ver_out)
        if len(version) > 0:
            ver = version[0].replace("0", "")
            ver = ver.replace(".", "")
            return ver
        raise RuntimeError("Unable to find the ipmctl version")

    def install_ipmctl_tool(self):
        """
            This function will install ipmctl tool
        """
        if self._os_type == OperatingSystems.LINUX:
            cmd = "ipmctl version"
            result = self.run_ssh_command(cmd)
            if "Interface Version" in result.stdout:
                current_version = self.ipmctl_interface_ver_match(result.stdout)
                self._log.info("Current Version of ipmctl is {}".format(current_version))
                version = self.ipmctl_interface_ver_match(self.ipmctl_centos_zip)
                if int(current_version) == int(version):
                    return True
            path = self.ipmctl_centos_zip.split("\\")
            if not len(path) > 0:
                raise RuntimeError("un able to read the file name")
            folder_name = "ipmctl_tool"
            self.run_ssh_command("rm -rf {}".format(folder_name))
            self.run_ssh_command("yum remove ipmctl -y")
            self.copy_extract_file(self.ipmctl_centos_zip, "/root", folder_name)
            cmd4 = 'cd /root/{} && dnf -y --disablerepo="*" install *.rpm'.format(folder_name)
            res4 = self.run_ssh_command(cmd4)
            if res4.stderr:
                raise RuntimeError("Unable to install ipmitool with the error {}".format(res4.stderr))
            result = self.run_ssh_command(cmd)
            if "Interface Version" in result.stdout:
                current_version = self.ipmctl_interface_ver_match(result.stdout)
                self._log.info("Current Version of ipmctl is {}".format(current_version))
                version = self.ipmctl_interface_ver_match(self.ipmctl_centos_zip)
                if int(current_version) == int(version):
                    return True
                else:
                    raise RuntimeError("Unable to install ipmitool")
        else:
            cmd = "ipmctl version"
            result = self.run_ssh_command(cmd)
            if "Interface Version" in result.stdout:
                current_version = self.ipmctl_interface_ver_match(result.stdout)
                self._log.info("Current Version of ipmctl is {}".format(current_version))
                version = self.ipmctl_interface_ver_match(self.ipmctl_windows_zip)
                if int(current_version) == int(version):
                    return True
            path = self.ipmctl_windows_zip.split("\\")
            if not len(path) > 0:
                raise RuntimeError("unable to read the file name")
            folder_name = "ipmctl_tool"
            self.run_ssh_command("rm -r -d {}".format(folder_name))
            self.copy_extract_file(self.ipmctl_windows_zip, self.windows_sut_root_path, folder_name)
            cmd1 = "cd {}/{} && dir".format(self.windows_sut_root_path, folder_name)
            output = self.run_ssh_command(cmd1)
            version = list(re.findall(r"\d?\d\.\d?\d\.\d?\d\.\d?\d\d\d", output.stdout))
            for i in version:
                if len(version) > 0:
                    ver = i.replace("0", "")
                    ver = ver.replace(".", "")
            file = self.ipmctl_windows_zip
            version2 = re.findall(r"\d?\d\.\d?\d\.\d?\d\.\d?\d\d\d", file)
            for i in version2:
                if len(version2) > 0:
                    ver1 = i.replace("0", "")
                    ver1 = ver1.replace(".", "")
            if current_version != ver1:
                self._log.info("version is not matching")
                version3 = re.findall(r"\d?\d\.\d?\d\.\d?\d\.\d\d\d\d", file)
                ver = version3[:len(version3) - 4]
                for i in version3:
                    if len(version3) > 0:
                        ver3 = i
                ver = ver3[:len(ver3) - 4]
                version4 = re.findall(r"\d\d\d\d", str(version3))
                ver4 = version4[0]
                regex = "^0+(?!$)"
                ver4 = re.sub(regex, "", ver4)
                ver5 = ver + ver4
                cmd1 = "where /R {} {}".format(self.windows_sut_root_path, folder_name)
                res1 = self.run_ssh_command(cmd1)
                cmd4 = f'cd {self.windows_sut_root_path}/{folder_name} && {self.ipmctl_tool_file}{ver5}.exe /S'
                res2 = self.run_ssh_command(cmd4)
                if res2.stderr:
                    raise RuntimeError("Unable to install ipmitool with the error {}".format(res2.stderr))
                result = self.run_ssh_command(cmd)
                if "Interface Version" in result.stdout:
                    current_version = self.ipmctl_interface_ver_match(result.stdout)
                    self._log.info("Current Version of ipmctl is {}".format(current_version))
                    version = self.ipmctl_interface_ver_match(self.ipmctl_windows_zip)
                    if int(current_version) == int(version):
                        return True
            else:
                raise RuntimeError("Unable to find the file")

    def set_armstate(self):
        """
            This function will Update the firmware version with armstate
        """
        output = self.run_ssh_command(PmemWindows.CMD1.format(self.nvdimmutil_path))
        if output.stderr:
            lines = output.stderr.split("\n")
            for line in lines:
                if not ("Set to Arm State" in line):
                    raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
                if "Invalid or unexpected" in output.stdout:
                    raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")

    def install_nvdimmutil(self):
        """
            This function willinstall nvdimmutill in sut

            return: folder path of nvdimmutill
        """
        if self._os_type == OperatingSystems.WINDOWS:
            for file in PmemWindows.FW_TOOL_FILES:
                res = self.check_filepath_sut(self.windows_sut_root_path, file)
                if not res:
                    self.copy_extract_file(self.nvdimmutil_windows_zip, self.windows_sut_root_path, PmemWindows.ACTIVATION_TOOLS)
                    res = self.check_filepath_sut(self.windows_sut_root_path, file)
                    if not res:
                        raise RuntimeError("Unable to copy {} file to SUT".format(file))
            folder_path = "\\".join(res.split('\\')[0:-1])
            return folder_path

    def all_dimm_id(self, show_dimm):
        """
            This function will return the dimm ids
            show_dimm: output of show dimm command
            return: dimm ids
        """
        dimms = re.findall(r"\dx\d\d\d\d", show_dimm)
        if not len(dimms) > 0:
            raise RuntimeError("Unable to detect Pmem Dimm id")
        return dimms

    def pmem_prepare(self):
        """
                This function will check for ipmitool, total number of dimms, check for appdirect
                capsule path, fio and vm
        """
        self.after_path = os.path.join(self.log_dir, "after")
        self.before_path = os.path.join(self.log_dir, "before")
        os.makedirs(self.after_path)
        os.makedirs(self.before_path)
        self.run_ssh_command("mkdir {}".format(self.windows_sut_root_path), log_output=False)
        self.install_ipmctl_tool()
        self.nvdimmutil_path = self.install_nvdimmutil()
        show_memoryresources = self.memoryresources()
        show_dimm = self.show_dimm()
        self.total_dimms = self.get_total_pmem_dimms(show_dimm)
        self.check_appdirect(show_memoryresources, show_dimm)
        if self.capsule_name:
            self.file_sut_path = self.check_pmem_fw(self.expected_ver, self.capsule_name)
        if self.capsule_name2:
            self.file_sut_path2 = self.check_pmem_fw(self.expected_ver2, self.capsule_name2)
        if self.fio:
            self.install_fio()
            self.begin_workloads_lin()
            self.check_ezfio_tool()
            self.del_namespace()
            self.create_namespace()
            self.create_namespace()

        if self.vm:
            # self.copy_vm_file(destination="/mnt/{}".format(device_name), artifactory_link=self.vm_artifactory_link)
            self.vm_installation_linux(destination="/root", server_name=self.vm)
            time.sleep(PmemLinux.VM_WAIT_TIME)
            self.run_vm_linux(self.vm)
            time.sleep(TimeDelay.VM_STABLE_TIMEOUT)
            if not self.verify_vm(self.vm):
                raise RuntimeError("VM is not running")
        if self.hyperv:
            if not self.verify_vm(self.win_vm_name):
                self.start_hyperv_vm(self.win_vm_name)
                if not self.verify_vm(self.win_vm_name):
                    self.create_hyper_v_windows(self.win_vm_name, "C:\\VHD\\VMPHU.vhdx")
                    self.start_hyperv_vm(self.win_vm_name)

        if self.dsaworkload:
            self.dsa_worload()
            
        if self.ptu:
            PmCommon.ptu_prepare(self)
        if self.socwatch:
            self.pm_soc.socwatch_prepare()

    def pmem_execute(self, file_sut_path, exp_version):
        """

        """
        activation_time = []
        show_dimm = self.show_dimm()
        self.health_status(show_dimm)
        self.dimm_ids = self.all_dimm_id(show_dimm)
        if self.vm:
            if not self.verify_vm(self.vm):
                raise RuntimeError("VM is not running")
        if self.hyperv:
            if not self.verify_vm(self.win_vm_name):
                raise RuntimeError("VM is not running")
        self.nlog(file_sut_path, self.before_path, exp_version)
        result = self.update_fw(file_sut_path)
        if self._os_type == OperatingSystems.WINDOWS:
            self.set_armstate()
        else:
            armed_state = self.check_armed_state(result)
            if not armed_state == self.total_dimms:
                raise RuntimeError("Unable to update all {} dimms. Only {} dimms are updated".format(self.total_dimms, armed_state))
        activate_result = self.activate_fw()
        if self._os_type == OperatingSystems.LINUX:
            activated_dimms = self.check_activate_output(activate_result, exp_version)
            if not activated_dimms == self.total_dimms:
                raise RuntimeError("Unable to activate all {} dimms. Only {} dimms are activated".format(self.total_dimms, activated_dimms))
        show_dimm = self.show_dimm()
        regex1 = re.findall(r"\dx\d\d\d\d", show_dimm)
        for i in regex1:
            current_version = self.get_pmem_version(show_dimm, i)
            res = self.comp_version(current_version, exp_version)
        file_list = self.nlog(file_sut_path, self.after_path, exp_version)
        for file in file_list:
            before_file = r"{}\{}".format(self.before_path, file)
            after_file = r"{}\{}".format(self.after_path, file)
            activation_time = self.read_time(before_file,after_file)
            dimm = re.findall(r"\dx\d\d\d\d", file)
            if not dimm[0]:
                raise RuntimeError("unable to read the dimm id")
            self._log.info("Activation time of dimm {} is {}".format(dimm[0], activation_time))
            if activation_time > PmemLinux.KPI_VALUE:
                self._log.warning("Activation time is exceeding {} us".format(PmemLinux.KPI_VALUE))
        if self.warm_reset:
            self.reboot()
        if self.dc_reset:
            self.dc_cycle()
        if self.ac_reset:
            self.ac_cycle()
        return True

    def list_meadia_file(self, folderpath):
        """
            This Function will return the list of media.txt file
            folderpath: SUT folder path
            return: list of media files
        """
        if self._os_type == OperatingSystems.LINUX:
            cmd = "cd {} && ls"
        else:
            cmd = "cd {} && dir"
        result = self.run_ssh_command(cmd.format(folderpath))
        if result.stdout:
            media_file_list = re.findall(r"{}.+media.txt".format(PmemLinux.FILE_PREFIX), result.stdout)
            return media_file_list

    def nlog(self, file_sut_path, host_path, version):
        """
            This Function will run log command and copy media file to host
            file_sut_path: sut file path
            host_path: destination path in host
            version: fw version
        """
        if self._os_type == OperatingSystems.LINUX:
            folder = "/".join(file_sut_path.split('/')[0:-1])
            folder_path = r"{}/".format(folder)
        else:
            folder = "\\".join(file_sut_path.split('\\')[0:-1])
            folder_path = r"{}\\".format(folder)
        self.get_pmem_fw_debug_log(folder, PmemLinux.FILE_PREFIX, version)
        file_list = self.list_meadia_file(folder)
        if len(file_list) != self.total_dimms:
            raise RuntimeError("Number of dimms is not matching with generated  media.txt files")
        for file in file_list:
            self.os.copy_file_from_sut_to_local(folder_path+file, r"{}\{}".format(host_path,file))
        return file_list

    def read_time(self, file1, file2):
        """
            This Function will read the activation time
            file1: file path of before update (media.txt) in Host
            file2: file path of after update (media.txt) in Host
            return: activation time
        """
        file_1 = open(file1)
        file_2 = open(file2)
        file_1_line = file_1.readline()
        file_2_line = file_2.readline()
        # Use as a Counter
        line_no = 1
        with open(file1) as file1:
            with open(file2) as file2:
                same = set(file1).intersection(file2)
        while file_1_line != '' or file_2_line != '':
            # Removing whitespaces
            file_1_line = file_1_line.rstrip()
            file_2_line = file_2_line.rstrip()
            # Compare the lines from both file
            if file_1_line != file_2_line:
                while "taking a total of" not in file_2_line:
                    # Read the next line from the file
                    file_1_line = file_1.readline()
                    file_2_line = file_2.readline()
                    line_no += 1
                break
            # Read the next line from the file
            file_1_line = file_1.readline()
            file_2_line = file_2.readline()
            line_no += 1
        file_1.close()
        file_2.close()
        regex1 = re.findall(r"taking a total of \d+ us", file_2_line)
        if len(regex1) == 1:
            time = re.findall(r"\d+", regex1[0])
            return int(time[0])

    def pmem_pre_update(self):
        """
            This function will start workload and vm before to fw update
            :return: NA
        """
        if self.vm:
            self.run_vm_linux(self.vm)
            time.sleep(TimeDelay.VM_STABLE_TIMEOUT)
            if not self.verify_vm(self.vm):
                raise RuntimeError("VM is not running")

        if self.hyperv:
            if not self.verify_vm(self.win_vm_name):

                self.start_hyperv_vm(self.win_vm_name)

                self.start_hyperv_vm(self.win_vm_name)
                
        if self.fio:
            self.start_fio()

        if self.ptu:
            PmCommon.deleting_file(self)
            PmCommon.execute_ptu_tool(self)

        if self.socwatch:
            self.pm_soc.execute_socwatch_tool()

    def pmem_post_update(self):
        if self.ptu:
            PmCommon.kill_ptu_tool(self)
            PmCommon.deleting_csv_files_in_host(self)
            PmCommon.copy_csv_file_from_sut_to_host(self)
            PmCommon.read_csv_file(self)
        if self.socwatch:
            self.pm_soc.copy_socwatch_csv_file_from_sut_to_host()
            CC6_CONDITION = "%s > " + str(self.cc6_value)
            self.pm_soc.verify_core_c_state_residency_frequency(CoreCStates.CORE_C_STATE_CC6,
                                                                CC6_CONDITION %
                                                                CoreCStates.CORE_C_STATE_CC6)

