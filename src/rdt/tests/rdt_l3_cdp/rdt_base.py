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
import json
import os
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.lib.bios_util import BiosUtil
from src.lib.install_collateral import InstallCollateral


class RdtBase(ContentBaseTestCase):
    """
    This class contains RDT base functions which can be used across many test cases.
    """

    SET_UP_FILE = "./prepare_automation.sh"
    LOG_FILE = ["{}.zip"]

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of RdtBase

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(RdtBase, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path=bios_config_file)
        self.cfg_opts = cfg_opts
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.setup_file_path = self._common_content_configuration.get_rdt_script_path()
        self.test_content_bios_mapper = os.path.join(os.path.dirname(os.path.abspath(__file__)), "RTD_test_content_config.json")
        # self.test_content_bios_mapper = self._common_content_configuration.get_rtd_tc_bios_mapper_file()
        with open(self.test_content_bios_mapper, 'r') as json_conf_file:
            self.tc_bios_mapper = json.load(json_conf_file)

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(RdtBase, self).prepare()
        setup_file = Path(os.path.join(self.setup_file_path, self.SET_UP_FILE)).as_posix()
        if not self.os.check_if_path_exists(setup_file):
            raise content_exceptions.TestFail("{} file not present in SUT under {}".format(self.SET_UP_FILE ,self.setup_file_path))

    def execute(self, script="", args=""):  # type: () -> bool
        """
        This method would execute the RDT script on the SUT

        :param script: Script to be executed on SUT
        :param args: args to be passed for the script
        :return: True on success
        """
        if not self.tc_bios_mapper.get(script):
            raise content_exceptions.TestFail("Fail to get bios knob detail for the script - {}, please check the tc_bios_mapping_file".format(script))
        bios_knob_list = self.tc_bios_mapper[script].split(",")
        result = True
        for bios_knob_file in bios_knob_list:
            try:
                # Remove old script logs
                self._log.info("clear old {} logs".format(script))
                log_path = Path(os.path.join(self.setup_file_path, 'results')).as_posix()
                self.os.execute("rm -rf *{}*".format(script), self._command_timeout, cwd=log_path)

               # Configure the bios knobs
                bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), bios_knob_file.strip())
                if not os.path.exists(bios_config_file_path):
                    raise content_exceptions.TestFail("Bios knob file - {} doesn't exits".format("bios_config_file_path"))
                self.bios_util.load_bios_defaults()
                self.bios_util.set_bios_knob(bios_knob_file)
                self.perform_graceful_g3()
                self.bios_util.verify_bios_knob(bios_knob_file)

                #Execute the SUT prepartion script after reboot
                self._log.info("Executing the setup initialization script - {}".format(self.SET_UP_FILE))
                configure_setup_output = self._common_content_lib.execute_sut_cmd("{}".format(self.SET_UP_FILE),
                                                                                  "configure the setup",
                                                                                  self._common_content_configuration.get_command_timeout(),
                                                                                  cmd_path=self.setup_file_path)
                self._log.debug("Configure setup output - {}".format(configure_setup_output))
                self._log.info("Executed the SUT preparation script")
                scipt_path = Path(os.path.join(self.setup_file_path, (script + ".py"))).as_posix()
                if not scipt_path:
                    raise content_exceptions.TestFail("{} file is not present in SUT under {}".format(script, self.setup_file_path))
                self._log.info("Executing the script on SUT")
                script_output = self._common_content_lib.execute_sut_cmd("python {}".format(script + ".py " + args), "running the script" , self._common_content_configuration.get_command_timeout(),
                                                         cmd_path=self.setup_file_path)
                self._log.info("script output is \n{}".format(script_output))
            except Exception as err:
                self._log.error("Fail to execute script {} with bios knb setting {} due to {}".format(script, bios_knob_file, err))
                result = False
            finally:
                self.pull_rdt_logs(log_name=script, dest_folder="{}_{}".format(script, bios_knob_file.split(".")[0]))
        return result

    def pull_rdt_logs(self, log_name, dest_folder):
        """
        This method would pull the logs generated by the RDT script from SUT to host

        :param log_name: name of the files to pulled
        :param dest_folder: location where the files should be saved in host
        :return: None
        """
        sut_log_folder = Path(os.path.join(self.setup_file_path, "results")).as_posix()
        host_log_dir = self._common_content_lib.get_log_file_dir()
        if not os.path.exists(os.path.join(host_log_dir, dest_folder)):
            log_dir = os.path.join(host_log_dir, dest_folder)
            os.makedirs(log_dir)
        if self.os.os_type == OperatingSystems.LINUX:
            for log in self.LOG_FILE:
                sut_log_file = Path(os.path.join(sut_log_folder, log.format(log_name))).as_posix()
                if not self.os.check_if_path_exists(sut_log_file):
                    self._log.info("Log {} doesn't exist in the SUT".format(log.format(log_name)))
                else:
                    self.os.copy_file_from_sut_to_local(Path(os.path.join(sut_log_folder, log.format(log_name))).as_posix(),
                                                        os.path.join(log_dir, log.format(log_name)))
        else:
            self._log.info("Not Implemented : Copy logs from SUT to Host on {}".format(self.os.os_type))
