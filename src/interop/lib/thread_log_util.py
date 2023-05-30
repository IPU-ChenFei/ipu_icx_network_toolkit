import os
import re
import sys
import logging
import datetime
import threading

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.content_configuration import ContentConfiguration

from src.lib.os_lib import WindowsCommonLib
from src.collaterals.collateral_constants import CollateralConstants
from src.lib.dtaf_content_constants import PTUToolConstants
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.lib.grub_util import GrubUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.content_base_test_case import ContentBaseTestCase


class ThreadLogFilter(logging.Filter):
    """
    This filter only show log entries for specified thread name
    """

    def __init__(self, thread_name, *args, **kwargs):
        logging.Filter.__init__(self, *args, **kwargs)
        self.thread_name = thread_name

    def filter(self, record):
        return record.threadName == self.thread_name


class ThreadLogUtil(object):

    def __init__(self, log, os_obj, cfg_opts):

        self._log = log
        self._os = os_obj
        self.sut_os = self._os.os_type
        self._cfg = cfg_opts
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._common_content_configuration = ContentConfiguration(self._log)

        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._log_file_dir = self._common_content_lib.get_log_file_dir()

    def thread_logger(self, thread):

        thread_name = threading.Thread.getName(thread)
        self.thread_log_dir = os.path.join(self._log_file_dir, "thread_logs")
        if not os.path.exists(self.thread_log_dir):
            os.makedirs(self.thread_log_dir)
        log_file_name = os.path.join(self.thread_log_dir, "{0}.log".format(thread_name))
        piv_log_fmt = logging.Formatter(
            fmt=u'%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] [{0}] %(message)s'.format(
                thread_name),
            datefmt=u'%m/%d/%Y %I:%M:%S %p')
        th_log_handler = logging.FileHandler(log_file_name)
        th_log_handler.setLevel(logging.DEBUG)
        th_log_handler.setFormatter(piv_log_fmt)
        log_filter = ThreadLogFilter(thread_name)
        th_log_handler.addFilter(log_filter)

        # Add handlers to logger
        self._log.addHandler(th_log_handler)
        return th_log_handler

    def stop_thread_logging(self, log_handler):
        self._log.removeHandler(log_handler)
        log_handler.close()

    def verify_workload_logs(self, error_str_list=[]):
        """
        Verifying the workloads on each thread

        :raise: Testfail exeception if any error found in the workload thread logs
        """
        self._log.info("Verifying workload logs")
        regex_thread_log = r"Thread.\d+.log"
        regex_for_workload = r"Running (.*) workload"
        error_list = []
        workload_status_dict = {}
        thread_log_dir = os.path.join(self._log_file_dir, "thread_logs")
        output = self._common_content_lib.execute_cmd_on_host("dir", cwd=thread_log_dir)
        modified_output = str(output.decode('utf-8')).strip("\r\n")
        thread_log_list = re.findall(regex_thread_log, modified_output)
        thread_list = [thread.split(".")[0] for thread in thread_log_list]
        self._log.info("Workloads are running on threads {}".format(thread_list))
        for each_log in thread_log_list:
            log_file = os.path.join(thread_log_dir, each_log)
            workload_error_list = []
            workload = ''
            key = ''
            thread = each_log.split(".")[0]
            with open(log_file, 'r+') as f:
                for line in f.readlines():
                    workload_list = re.findall(regex_for_workload, line)

                    if workload_list:
                        workload = workload_list[0]
                        self._log.info("Checking error in thread {} for workload {}".format(thread, workload))
                        key = thread + "_" + workload
                    if ['True' for error in error_str_list if re.search(error, line)]:
                        self._log.error("Error {}".format(line))
                        workload_error_list.append(line)
            if workload_error_list:
                self._log.error("{} workload failed to execute on thread {}".format(workload, thread))
                error_list.extend(workload_error_list)
                self._log.debug("Error list {} for workload {}".format(workload_error_list, workload))
                workload_status_dict[key] = "FAIL"
            else:
                self._log.info("Workload {} execute successfully on thread {}".format(workload, thread))
                workload_status_dict[key] = "PASS"

        if error_list:
            raise content_exceptions.TestFail("Workload failed to execute {}".format(workload_status_dict))
        self._log.info("All the accelerator workload ran successfully {}".format(workload_status_dict))
