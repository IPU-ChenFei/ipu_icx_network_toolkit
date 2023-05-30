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

from pathlib import Path

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions


class FIOCommonLib(object):
    """
    Utility class to interface with class FIOCommonLib
    Provides functions to fio Sequential write, Sequential read, Mixed read write, random write, random read
    """

    ROOT = "/root"
    FIO_MOUNT_POINT = "/mnt/nvme"
    LOG_FILE = "/root/fio.log"
    FIO_LOG_FILE = "fio.log"
    TOOL_NAME = '/mnt/nvme/fiotest'
    FIO_COMMAND_RUN  = r"fio --name={} --rw={} --numjobs={} --bs={} --filename={} --size={} " \
                   r"--ioengine={} --runtime={} --time_based --iodepth={} --group_reporting --output={}"

    def __init__(self, log_obj, sut_os_obj):
        """
        :param log_obj: log object
        :param sut_os_obj: sut os object
        """
        self._log = log_obj
        self._os = sut_os_obj
        self._common_content_lib = CommonContentLib(self._log, self._os, None)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._fio_runtime = self._common_content_configuration.memory_fio_run_time()

    def fio_path_finder(self):
        """
        Function to find where the fio tool has been installed

        :return fio_executer_path: parent path of the .exe file.
        """
        fio_executer_path = self._common_content_lib.execute_sut_cmd("where fio.exe", "find installed path",
                                                                     self._command_timeout)
        fio_executer_path = Path(fio_executer_path).parent
        return fio_executer_path

    def fio_sequential_write(self, fio_test_points, cmd_run=None):
        """
        Function to run the Sequential write command of fio executer.

        :param fio_test_points: pmem device points
        :param cmd_run: command to run
        :return: None
        """
        # Sequential write
        if self._os.os_type == OperatingSystems.WINDOWS:
            fio_drive = fio_test_points

            cmd_run = "fio.exe --name=seqwrite --ioengine=psync --size=10G --rw=write --bs=64k-2M " \
                      "--numjobs=16 --direct=1 --time_based --runtime={} --output=win_fio_seq_write.log --filename={}" \
                .format(self._fio_runtime, fio_drive)

            self._log.info("FIO Sequential write has started on the pmem disk(s).")
            self._common_content_lib.execute_sut_cmd(cmd_run, "FIO Sequential write", self._command_timeout)
            self._log.info("FIO Sequential write has completed successfully!")
        elif self._os.os_type == OperatingSystems.LINUX:
            cmd_run = cmd_run.format(self._fio_runtime, fio_test_points)

            self._log.info("FIO Sequential write has started on the pmem disk(s).")
            self._common_content_lib.execute_sut_cmd(cmd_run, "FIO Sequential write", self._command_timeout,
                                                     self.ROOT)
            self._log.info("FIO Sequential write has completed successfully!")
        else:
            log_error = "Sequential write is not implemented for OS '{}'".format(self._os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def fio_sequential_read(self, fio_test_points, cmd_run=None):
        """
        Function to run the Sequential read command of fio executer.

        :param fio_test_points: pmem device points
        :param cmd_run: command to run
        :return: None
        """
        # Sequential read
        if self._os.os_type == OperatingSystems.WINDOWS:
            fio_drive = fio_test_points

            cmd_run = "fio.exe --name=seqread --ioengine=psync --size=10G --rw=read --bs=64k-2M " \
                      "--numjobs=16 --direct=1 --time_based --runtime={} --output=win_fio_seq_read.log " \
                      "--filename={}".format(self._fio_runtime, fio_drive)

            self._log.info("FIO Sequential read has started on the pmem disk(s).")
            self._common_content_lib.execute_sut_cmd(cmd_run, "FIO Sequential write", self._command_timeout)
            self._log.info("FIO Sequential read has completed successfully!")
        elif self._os.os_type == OperatingSystems.LINUX:
            cmd_run = cmd_run.format(self._fio_runtime, fio_test_points)

            self._log.info("FIO Sequential read has started on the pmem disk(s).")
            self._common_content_lib.execute_sut_cmd(cmd_run, "FIO Sequential read", self._command_timeout,
                                                     self.ROOT)
            self._log.info("FIO Sequential read has completed successfully!")
        else:
            log_error = "Sequential read is not implemented for OS '{}'".format(self._os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def fio_mixed_read_write(self, fio_test_drives):
        """
        Function to run the Mixed read write command of fio executer.

        :param fio_test_drives: pmem drives
        :return: None
        """
        # Mixed read write
        if self._os.os_type == OperatingSystems.WINDOWS:
            fio_drive = fio_test_drives

            cmd_run = "fio.exe --name=seqrw --ioengine=psync --size=10G --rw=rw --bs=64k-2M " \
                      "--numjobs=16 --direct=1 --time_based --runtime={} --output=win_fio_mixed_rw.log " \
                      "--filename='{}'".format(self._fio_runtime, fio_drive)

            self._log.info("FIO Mixed read and write has started on the pmem disk(s).")
            self._common_content_lib.execute_sut_cmd(cmd_run, "FIO Mixed read write", self._command_timeout)
            self._log.info("FIO mixed read and write has completed successfully!")
        else:
            log_error = "Mixed read write is not implemented for OS '{}'".format(self._os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def fio_execute_async(self, fio_drive):
        """
        Function to run the read write command of fio executer in async mode.

        :param fio_drive: pmem drives
        :return: None
        """
        if self._os.os_type == OperatingSystems.LINUX:
            linux_fio_cmd = r'fio --name=readwrite --ioengine=sync --rw=rw --rwmixread=70 --direct=1 --bs=256k ' \
                            '--iodepth=8 --numjobs=16  --runtime={} --time_based --size=10M --output={} ' \
                            '--filename={}'.format(self._fio_runtime, self.FIO_LOG_FILE, fio_drive)
            self._os.execute_async(linux_fio_cmd, cwd=self.ROOT)
            self._log.info("FIO async execution has started on the pmem disk(s).")
        else:
            log_error = "async execution is not implemented for OS '{}'".format(self._os)
            raise content_exceptions.TestNotImplementedError(log_error)

    def fio_random_write(self, fio_test_drives):
        """
        Function to run the random write command of fio executer.

        :param fio_test_drives: pmem drives
        :return: None
        """
        # random write
        if self._os.os_type == OperatingSystems.WINDOWS:
            fio_drive = fio_test_drives

            cmd_run = "fio.exe --name=ranwrite --ioengine=psync --size=10G --rw=randwrite --bs=64k-2M " \
                      "--numjobs=16 --direct=1 --time_based --runtime={} --output=win_fio_ran_write.log " \
                      "--filename='{}'".format(self._fio_runtime, fio_drive)

            self._log.info("FIO random write has started on the pmem disk(s).")
            self._common_content_lib.execute_sut_cmd(cmd_run, "FIO random write", self._command_timeout)
            self._log.info("FIO random write has completed successfully!")
        else:
            log_error = "Random write is not implemented for OS '{}'".format(self._os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def fio_random_read(self, fio_test_drives):
        """
        Function to run the random read command of fio executer.

        :param fio_test_drives: pmem drives
        :return: None
        """
        # random read
        if self._os.os_type == OperatingSystems.WINDOWS:
            fio_drive = fio_test_drives

            cmd_run = "fio.exe --name=ranread --ioengine=psync --size=10G --rw=randread --bs=64k-2M " \
                      "--numjobs=16 --direct=1 --time_based --runtime={} --output=win_fio_ran_read.log " \
                      "--filename='{}'".format(self._fio_runtime, fio_drive)

            self._log.info("FIO random read has started on the pmem disk(s).")
            self._common_content_lib.execute_sut_cmd(cmd_run, "FIO random read", self._command_timeout)
            self._log.info("FIO random read has completed successfully!")
        else:
            log_error = "Random read is not implemented for OS '{}'".format(self._os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def fio_log_parsing(self, log_path, pattern):
        """
        Function to check the bandwidth measurements reported by FIO appear normal for a storage target.

        :param log_path: where the log has generated.
        :param pattern: regex pattern to search the log files
        :return ret_val: false if error else true
        """
        ret_val = True
        with open(log_path, "r") as fp:
            if len(fp.readlines()) == 0:
                self._log.error("Fio log file %s was empty" % log_path)
                ret_val = False
                return ret_val
            for line in fp.readlines():
                if re.search("{}".format(pattern), line):
                    mylist = ' '.join(line.split(",")[0].split(":")[1].split(" ")).split()
                    no_string = list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])), mylist))
                    percent_calculate = (50 / 100) * no_string[1]

                    if no_string[0] < percent_calculate:
                        ret_val = False
        if ret_val:
            self._log.info("The '{}' has passed without any errors!".format(log_path))
        else:
            self._log.error("Found bandwidth issue while checking the '{}' during {} operation!".format(
                log_path, pattern))
        return ret_val

    def verify_fio_log_pattern(self, log_path, pattern):
        """
        Function to check the bandwidth measurements reported by FIO appear normal for a storage target.
        :param log_path: where the log has generated.
        :param pattern: regex pattern to search the log files
        :return ret_val: false if error else true
        """
        ret_val = True
        with open(log_path, "r") as fp:
            for line in fp.readlines():
                if re.search("{}".format(pattern), line):
                    self._log.info(line)
                    if "BW=" in line:
                        # to check if the output is in MiBs
                        try:
                            # get the total used bandwidth for fio
                            used_bandwidth = line.split(",")[1].split("=")[1].split(" ")[0].split("M")[0]
                            # get the total bandwidth
                            total_bandwidth = line.split(",")[1].split("=")[1]. \
                            split(" ")[1].split("(")[1].split("M")[0]
                            re_bw = (int(total_bandwidth) * 80) / 100
                            if int(re_bw) <= int(used_bandwidth): # comparing the difference with used and total bandwidth is 80%
                                self._log.info(
                                    "Total used bandwidth {} which is greater than equal to 80% of total Memory"
                                    .format(used_bandwidth))
                                return True
                            else:
                                self._log.error(
                                    "Found bandwidth issue while checking the '{}' during {} operation!".format(
                                        log_path, pattern))
                                raise content_exceptions.TestFail("Total used bandwidth: {} is less than 80%".format
                                                                  (used_bandwidth))
                        # to verify if the output is in GiB's
                        except Exception as e:
                            used_bandwidth = line.split(",")[1].split("=")[1].split("G")[0]
                            total_bandwidth = \
                                line.split(",")[1].split("=")[1].split(" ")[1].split("(")[1].split("G")[0]

                            re_bw = (float(total_bandwidth) * 80) / 100
                            if int(re_bw) <= float(used_bandwidth):
                                self._log.info("Total used bandwidth {} which is greater than equal to 80% "
                                               "of total Memory".format(used_bandwidth))
                                return True
                            else:
                                self._log.error(
                                    "Found bandwidth issue while checking the '{}' during {} operation!".format(
                                        log_path, pattern))
                                raise content_exceptions.TestFail("Total used bandwidth: {} is less than 80%".format
                                                                  (used_bandwidth))

    def run_fio_cmd(self, name, rw, numjobs, bs, filename, size, ioengine, runtime, iodepth, output):
        """
        This Method is used to run generic fio commands
        """
        if name == "write":
            self._common_content_lib.execute_sut_cmd("umount {}".format(filename), "delete mount point",
                                                     self._command_timeout)
            self._common_content_lib.execute_sut_cmd(self.FIO_COMMAND_RUN.format(name, rw, numjobs, bs, filename,
                                                                                 size, ioengine, runtime, iodepth,
                                                                                 output),
                                                     "executing FIO for {}".format(name), self._command_timeout+int(runtime))
        else:
            self._common_content_lib.execute_sut_cmd(self.FIO_COMMAND_RUN.format(name, rw, numjobs, bs, filename,
                                                                             size, ioengine, runtime, iodepth, output),
                                                 "executing FIO for {}".format(name), self._command_timeout+int(runtime))

    def numactl_run_fio(self, cpunodebind, membind, name, rw, filename,
                      iodepth, bs, size, numjobs, runtime, output):
        """
        Function to run the read write command of fio executer in numactl mode.

        :return: None
        """
        self._log.info("Starting FIO execution")
        linux_fio_cmd = r"numactl --cpunodebind={} --membind={} fio --name={} --rw={} " \
                        r"--filename={} --iodepth={} --bs={} --size={} --numjobs={} --group_reporting --time_based " \
                        r"--runtime={} --output={}".format(cpunodebind, membind, name, rw, filename,
                          iodepth, bs, size, numjobs, runtime, output)
        self._common_content_lib.execute_sut_cmd(linux_fio_cmd.format(cpunodebind, membind, name, rw, filename, iodepth,bs,size,numjobs,
                                                      runtime, output), "Executing FIO Command- for {}".format(name),
                                                 self._command_timeout)
