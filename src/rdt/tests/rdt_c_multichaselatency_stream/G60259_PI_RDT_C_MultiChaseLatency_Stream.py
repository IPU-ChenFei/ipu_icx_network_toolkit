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

import sys
import time
import os

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class RdtMultiChaseLatencyStream(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G60259.1-PI_RDT_C_MultiChaseLatency_Stream

    Pre-Requisite :- Install Intel C++ Compiler by following below steps and run this test case
                        1. Get Intel System Studio  Free License
                        https://software.intel.com/en-us/system-studio/choose-download
                        2. Go to "configure installation" button then choose Intel C++ Compiler from list (add button)
                        3. Download for Linux* Host and Target
                        4. Follow Download and Install instructions

    This test case/class perform below tasks.
    1. Perform setup for this test case by installing multichase-master, STREAM-master
    2. Run taskset multichase and stream for core 0 and 1 e.g taskset -c 0 ./multichase , taskset -c 0 ./stream
    3. Associate core 0 to 1-23 e.g pqos -a 'llc:0=0' , pqos -a 'llc:1=1-23'
    4. Configure CLOS[0] to have access to a single sequence of LLC CBM bit (MSB) e.g pqos -e 'llc@0:0= 0x800'
    5. Configure CLOS[1] to have access to all other sequence of single LLC e.g pqos -e 'llc@0:1= 0x7ff'
    6. Run multichase on core 0 associated to COS0 e.g taskset -c 0 ./multichase
    7. Increment COS0 (multichase) and decrement COS1 CBM (stream) e.g taskset -c 0 ./stream, taskset -c 1 ./multichase
    8. There should not be significant increase in multichase latencies

    """
    MULTICHASE_BEFORE_WORKLOAD = []
    MULTICHASE_AFTER_WORKLOAD = []
    TEST_CASE_ID = ["G60259.1", "PI_RDT_C_MultiChaseLatency_Stream"]
    CORES = None
    MIN_INCREASE_VALUE = 50
    STREAM_WAIT_TIME = 5
    SETUP_COMMANDS = '''
    unzip multichase-master.zip -d ./ ;
    cd multichase-master/ ;
    sed 's/LDFLAGS=-g -O3 -static -pthread/LDFLAGS=-g -O3 -pthread/g' Makefile > Makefile.org ; mv -f Makefile.org Makefile ;
    echo "Building multichase-master" ;
    make > ../install.log ; 
    sleep 10 ;
    unzip ../STREAM-master.zip -d ../ ;
    cd ../STREAM-master ;
    sed 's/CC = gcc-4.9/CC = gcc/g' Makefile > Makefile.org ; mv -f Makefile.org Makefile ;
    sed 's/FC = gfortran-4.9/FC = gfortran/g' Makefile > Makefile.org ; mv -f Makefile.org Makefile ;
    sed 's/-DNTIMES=20/-DNTIMES=300/g' Makefile > Makefile.org ; mv -f Makefile.org Makefile ;
    make >> ../install.log ;
    sleep 10 ;
    '''
    STEP_DATA_DICT = {
        1: {'step_details': 'Perform setup for this test case by installing multichase-master, STREAM-master',
            'expected_results': 'Setup completed successfully'},
        2: {'step_details': 'Run taskset multichase and stream for core 0 and 1 and associate cores',
            'expected_results': 'Executed taskset and stream ad associated cores successfully'},
        3: {'step_details': 'Configure CLOS[0] & CLOS[1] to have access to a single sequence of LLC CBM bit (MSB) and '
                            'run multichase command, Repeat step 2 &3 by incrementing COS0 (multichase) and decrement '
                            'COS1 CBM (stream) ',
            'expected_results': 'Configured bits successfully and executed multichase successfully'},
        4: {'step_details': 'Compare the values returned by multichase latencies',
            'expected_results': 'There should not be significant increase in multichase latencies'}
    }

    def __init__(self, test_log, arguments, cfg_opts):

        """
        Create an instance of RdtMultiChaseLatencyStream
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtMultiChaseLatencyStream, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, cfg_opts)

        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("multichase & Stream installation is not implemented "
                                                 "for the os: {}".format(self.os.os_type))

    def prepare(self):
        # type: () -> None
        """
        Test preparation/setup
        """
        super(RdtMultiChaseLatencyStream, self).prepare()

    def run_stream_on_cores(self, stream_cmd, zip_file_path, current_core):
        """
        This function run stream command on associated cores using stream for specified amount of time

        :param stream_cmd : Contains stream command,
        :param current_core : Current core
        """
        stream_dir_path = self._rdt.find_package(zip_file_path, "STREAM*")
        stream_cmd_per_core = stream_cmd.format(current_core)
        self.os.execute_async(cmd="cd " + stream_dir_path + '; ' + stream_cmd_per_core)
        time.sleep(self.STREAM_WAIT_TIME)
        if not self._rdt.check_cmd_running(stream_cmd_per_core):
            log_error = "{} Failed to run on given core in the system".format(stream_cmd_per_core)
            self._log.error(log_error)
            raise content_exceptions.TestError(log_error)
        self._log.info("The stress instance is running on given core successfully")

    def compare_multichase_latency(self, multichase_res_list):
        """
        This function compare multichase values before and after aggregators are started

        :param multichase_res_list: List containing multichase values
        :raise: Exception if there is significant increase in multichase values after aggregators are started

        """
        # check if the value is increasing or decreasing in the multichase result list
        for iterator in range(len(multichase_res_list)):
            if multichase_res_list[iterator] < multichase_res_list[iterator]:
                raise content_exceptions.TestFail("There is significant increase in multichase "
                                                  "latencies when aggressors are started when workloads "
                                                  "are associated to isolated COS ")
        self._log.info("There should be no significant increase in multichase latencies when aggressors "
                       "are started when workloads are associated to isolated COS as expected")

    def execute(self):
        """
        This method executes the below: 1. Perform setup for this test case by installing multichase-master,
        STREAM-master 2. Run taskset multichase and stream for core 0 and 1 e.g taskset -c 0 ./multichase ,
        taskset -c 0 ./stream 3. Associate core 0 to 1-23 e.g pqos -a 'llc:0=0' , pqos -a 'llc:1=1-23' 4. Configure
        CLOS[0] to have access to a single sequence of LLC CBM bit (MSB) e.g pqos -e 'llc@0:0= 0x800' 5. Configure
        CLOS[1] to have access to all other sequence of single LLC e.g pqos -e 'llc@0:1= 0x7ff' 6. Run multichase on
        core 0 associated to COS0 e.g taskset -c 0 ./multichase 7. Increment COS0 (multichase) and decrement COS1 CBM
        (stream) e.g taskset -c 0 ./stream, taskset -c 1 ./multichase 8. There should not be significant increase in
        multichase latencies

        :return: True if test case pass
        """
        # Verify if RDT is installed, If not it will install
        self._rdt.install_rdt()
        # Restore default monitoring: pqos -R
        self._rdt.restore_default_rdt_monitor()

        multichase_result_list = []
        self._common_content_lib.set_datetime_on_linux_sut()

        # copying the zip multichase-master.zip from host to sut
        artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.MULTICHASE_TOOL_FILE]
        zip_file_path_in_host = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        self.zip_file_path = self._common_content_lib.copy_zip_file_to_linux_sut(
            "multichase-master",zip_file_path_in_host)
        self._log.debug("Zip file copied to sut location {}".format(self.zip_file_path))
        self._test_content_logger.start_step_logger(1)
        # Install and configure packages for setup
        self._rdt.install_dep_packages(self.zip_file_path, self.SETUP_COMMANDS)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self.CORES = self._common_content_lib.execute_sut_cmd(self._rdt.CORES_PER_SOCKET,
                                                              " Get core per socket value", self._command_timeout)

        multichase_result_list.append(self._rdt.run_multichase_on_core(self._rdt.TASKSET_MULTICHASE,
                                                                 self.zip_file_path,0))
        self._test_content_logger.start_step_logger(2)
        # Run stream on cores 1-N
        for core in range(1,int(self.CORES)):
           self.run_stream_on_cores(self._rdt.TASKSET_STREAM, self.zip_file_path, core)
        self._test_content_logger.end_step_logger(2, return_val=True)
        multichase_result_list.append(self._rdt.run_multichase_on_core(self._rdt.TASKSET_MULTICHASE,
                                                            self.zip_file_path, 0))

        self._test_content_logger.start_step_logger(3)
        # Associate and assign cores
        multichase_result_list.extend(self._rdt.associate_assign_cores(self.CORES, self.zip_file_path))
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self.compare_multichase_latency(multichase_result_list)
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMultiChaseLatencyStream.main() else Framework.TEST_RESULT_FAIL)
