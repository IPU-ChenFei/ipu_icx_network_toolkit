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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import os

import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

class DLBDriverLib(object):
    FIND_CMD = "find $(pwd) -type f -name {} | sort -r"
    DLB_PARENT_PATH = "/root/dtaf_sdsi_driver_source_code"
    INSTALLER_NAME = "release_ver_*.zip"
    DLB_UNZIP_LOCATION = "/root/dtaf_sdsi_driver_source_code/dlb"
    REMOVE_OLD_DLB_SRC = "rm -rf /root/dtaf_sdsi_driver_source_code/dlb"

    DLB_LIB_SOURCE_CODE_LOC = "/root/dtaf_sdsi_driver_source_code/dlb/libdlb"
    DLB2_DRIVER_SOURCE_CODE_LOC = "/root/dtaf_sdsi_driver_source_code/dlb/driver/dlb2"

    DLB_SAMPLES = "/root/dtaf_sdsi_driver_source_code/dlb/libdlb/examples"
    COMMENT_DLB_BUILD_FAILURE = "sed -e '/CONFIG_INTEL_DLB2_SIOV/ s/^#*/#/g' -i Makefile"
    ROOT_FOLDER = "/"
    DLB2_DRIVER_NAME="dlb2"
    DLB2_DRIVER_MODULE_FILE_NAME="dlb2.ko"
    LBD_TRAFFIC_COMMAND = "export LD_LIBRARY_PATH=" + DLB_LIB_SOURCE_CODE_LOC +":/usr/local/lib:${LD_LIBRARY_PATH};./ldb_traffic -n 1024"
    LBD_TRAFFIC_VERIFY_TX = "[tx_traffic()] Sent 1024 events"
    LBD_TRAFFIC_VERIFY_RX = "[rx_traffic()] Received 1024 events"


    def __init__(self, log, sut_os, common_content_lib, common_content_config_lib):
        """
        Initiating the DLB source code extraction and build.

        """
        self._log = log
        self._os = sut_os
        self._common_content_lib = common_content_lib
        self._common_content_config_lib = common_content_config_lib
        self.cmd_timeout = self._common_content_config_lib.get_command_timeout()

        self.installer_dest_path = self.unzip_dlb_driver_source_package()



    def unzip_dlb_driver_source_package(self):
        """
        This method searches for the compressed DLB2 package in "/root/dtaf_sdsi_driver_source_code", and extract it.

        :raise: content_exception.TestFail if unable to un-tar properly.

        :return: The extracted folder path in SUT
        """
        self._log.info("[IMPORTANT PRE-REQUEST] - Please make sure dlb driver source code *.zip are located in {}".format(self.DLB_PARENT_PATH))
        self._log.info("Searching for DLB driver source code file in zip format")
        cmd = self.FIND_CMD.format(self.INSTALLER_NAME)
        self._log.debug("command to search driver zip file cmd {}".format(cmd))
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.cmd_timeout, self.DLB_PARENT_PATH)
        if not output.strip():
            log_error = "No DLB driver package(compressed) is found in the SUT path {}".format(self.DLB_PARENT_PATH)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.debug("find cmd output {}".format(output))
        zip_path = os.path.split(output.strip())[-1]
        source_path = os.path.split(output.strip())[0]
        directory_name = os.path.dirname(output.strip())
        self._log.debug("directory name {}, zip path {} , source path {} ".format(directory_name, zip_path, source_path))
        return self.extract_compressed_file(source_path, zip_path, directory_name)


    def extract_compressed_file(self, sut_folder_path, zip_file, folder_name):
        """
        This function Extract the compressed file.

        :param sut_folder_path : sut folder path
        :param folder_name : name of the folder in SUT
        :param zip_file : name of the zip file.
        :return: The extracted folder path in SUT.
        """
        self._log.info("Removing old dlb driver source code folder and files")
        output = self._common_content_lib.execute_sut_cmd(self.REMOVE_OLD_DLB_SRC, "remove old folder",
                                                 self.cmd_timeout, sut_folder_path)
        self._log.debug(output)

        self._log.info("extracts the compressed file")
        unzip_command = "unzip  {} -d {}".format(zip_file, self.DLB_UNZIP_LOCATION)

        self._common_content_lib.execute_sut_cmd(unzip_command, "unzip the folder",
                             self.cmd_timeout, sut_folder_path)

        tool_path_sut = Path(os.path.join("/root", folder_name)).as_posix()

        self._log.debug("The file '{}' has been unzipped successfully "
                       "..".format(zip_file))
        self._log.debug("Set execution permission for the contents in extracted package.")
        self._os.execute("chmod -R 777 %s" % tool_path_sut, self.cmd_timeout)
        self._log.debug(tool_path_sut)
        return tool_path_sut


    def build_dlb_driver_source_code(self):
        """
        This method is using to build the dlb driver source code.

        :return : Pass or Fail.
        """
        export_library_path = "export LD_LIBRARY_PATH=" + self.DLB_LIB_SOURCE_CODE_LOC + ":$LD_LIBRARY_PATH"
        build_command = export_library_path + "; make"
        output = self._common_content_lib.execute_sut_cmd(build_command, "build dlb driver",
                                                 self.cmd_timeout, self.DLB2_DRIVER_SOURCE_CODE_LOC)
        self._log.debug(output)
        return True

    def build_dlb_library_source_code(self):
        """
        This method is using to build the dlb library source code located at
        '/root/dtaf_sdsi_driver_source_code/dlb/libdlb'

        """
        build_command = "make"
        output = self._common_content_lib.execute_sut_cmd(build_command, "building libdlb files",
                                                          self.cmd_timeout, self.DLB_LIB_SOURCE_CODE_LOC)
        self._log.debug(output)
        changemod=" chmod 777 *.so"
        self._os.execute("chmod 777 {}/*.so".format(self.DLB_LIB_SOURCE_CODE_LOC), self.cmd_timeout)
        return True

    def build_dlb_examples(self):
        """
        This method is using to build the dlb sample codes located at '/root/dtaf_sdsi_driver_source_code/dlb/libdlb/examples'
        """
        dlb_sample_build_command = "make"
        output = self._common_content_lib.execute_sut_cmd(dlb_sample_build_command, "building DLB samples",
                                                 self.cmd_timeout, self.DLB_SAMPLES)
        self._log.debug(output)
        self._os.execute("chmod -R 777 %s" % self.DLB_SAMPLES, self.cmd_timeout)
        return True


    def run_ldlb_traffic_from_sample(self):
        """
        This method is using to run the lbd_traffic and verify the results are good.

        """
        command = self.LBD_TRAFFIC_COMMAND
        output = self._common_content_lib.execute_sut_cmd(command, "running ldb dlb traffic",
                                                          self.cmd_timeout, self.DLB_SAMPLES)
        self._log.debug(output)
        #verify the traffic is successful by checking the tx/rx status
        if((self.LBD_TRAFFIC_VERIFY_TX in output) and (self.LBD_TRAFFIC_VERIFY_RX in output)):
            return True

        return False

    def comment_SIOV_flag_for_non_Intel_Next_Kernel(self ):
        """
        This method is using to comment out a compiler options for non Intel Next Kernels.

        """

        comment_siov_build_flag = self.COMMENT_DLB_BUILD_FAILURE
        self._common_content_lib.execute_sut_cmd(comment_siov_build_flag, "commenting SIOV flag from make file",
                                                 self.cmd_timeout,self.DLB2_DRIVER_SOURCE_CODE_LOC)

        return True

    def execute_sut_cmd(self, sut_cmd, execute_timeout, cmd_path=None):
        """
        This method is using to execute a command in SUT and returns the output.
        :param sut_cmd : the command to be execute
        :param execute_timeout: The timeout for the above command
        :param cmd_path: Location of the command

        : return: The output of the command executed in the SUT
        """

        sut_cmd_result = self._os.execute(sut_cmd, execute_timeout, cmd_path)
        return sut_cmd_result.stdout

    def install_dlb_driver(self):
        """
        This method is using to install the DLB2 driver located '/root/dtaf_sdsi_driver_source_code/dlb/driver/dlb2'
        then it checks whether the driver is loaded.

        :return: Whether the driver is loaded or not.
        """

        install_dlb = 'insmod ' + self.DLB2_DRIVER_SOURCE_CODE_LOC + '/' + self.DLB2_DRIVER_MODULE_FILE_NAME
        output = self.execute_sut_cmd(install_dlb, self.cmd_timeout, self.DLB2_DRIVER_SOURCE_CODE_LOC)
        self._log.debug(output)

        return self.is_dlb_driver_loaded()

    def get_modinfo_of_a_module(self, modulename):
        """
        This method is using to get the modinfo of a module to verify the real hardware is up and running

        :param modulename: name of the module to be check
        :return: False if module is not running otherwise True
        """

        query_mod_info = "modinfo " + modulename
        output = self.execute_sut_cmd(query_mod_info, self.cmd_timeout, self.ROOT_FOLDER)

        self._log.debug(output)
        output = output.strip()
        if (output == '' or ("ERROR:" in output) ):
            self._log.info("{} modinfo is not available".format(modulename))
            return False
        else:
            #TBD
            return True

    def verfify_any_device_is_running_using_a_module(self, modulename):
        """

        """
        query_mod_info = "lspci -v | grep  " + modulename
        output = self.execute_sut_cmd(query_mod_info, self.cmd_timeout, self.ROOT_FOLDER)

        self._log.debug(output)
        output = output.strip()
        if (output == '' or ("ERROR:" in output)):
            self._log.info("{} not using by any hardware".format(modulename))
            return False
        else:
            return True

    def is_dlb_driver_loaded(self):
        """
        This method is using to check whether dlb2 driver module is loaded

        """
        query_dlb = "lsmod"
        output = self.execute_sut_cmd(query_dlb, self.cmd_timeout, self.ROOT_FOLDER)
        self._log.debug(output)
        output = output.strip()
        if (output == ''):
            self._log.info("dlb2 driver is not running")
            return False
        if(self.DLB2_DRIVER_NAME in output):
            self._log.info("dlb2 driver is running")
            return  True

        return False


    def remove_dlb_driver(self):
        """
        This method is using to remove the dlb driver

        :return: True if  dlb driver is removed successfully, otherwise False
        """

        if(self.is_dlb_driver_loaded() == False):
            self._log.info("{} driver is not running".format(self.DLB2_DRIVER_NAME))
            return True

        remove_dlb2 = "rmmod " + self.DLB2_DRIVER_NAME
        output = self.execute_sut_cmd(remove_dlb2, self.cmd_timeout, self.ROOT_FOLDER)
        self._log.debug(output)

        #returns False if driver still exist otherwise returns True
        return False if self.is_dlb_driver_loaded() else True


    def analyze_dmesg_for_a_string(self, searchString, dmesg_tail_count=None):
        """
        This method is using to search a particular string in the dmesg by pulling the tail

        :param searchString : string to be search in the dmesg output.
        :param dmesg_tail_count: using to get the last n number of lines in the dmesg log
        :return: True if search string find in the dmesg log.
        """

        if (searchString == ''):
            return False

        if(dmesg_tail_count != None):
            command = "dmesg | tail -n {}".format(dmesg_tail_count)
        else:
            command = "dmesg | tail "

        output = self.execute_sut_cmd(command, self.cmd_timeout, self.ROOT_FOLDER)
        self._log.debug(output)

        if(searchString in output):
            return True

        return False


    def single_command_to_build_all_dlb_components(self, is_sut_non_intel_next_kernel=True):
        """
        This method is using to extract the dlb source code, build the libraries, samples and drivers.

        :param is_sut_non_intel_next_kernel: True for non Intel next kernel modules.
        """

        #source code is already extracted by initialization

        #build the libary -- libdlb
        self.build_dlb_library_source_code()

        #build the examples
        self.build_dlb_examples()

        #comment out the SIOV in non intel next kernel versions
        if(is_sut_non_intel_next_kernel == True):
            self.comment_SIOV_flag_for_non_Intel_Next_Kernel()

        #build the dlb driver source code
        self.build_dlb_driver_source_code()
