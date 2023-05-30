#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
INTEL CONFIDENTIAL
Copyright 2020-2021 Intel Corporation All Rights Reserved.

The source code contained or described herein and all documents related to the source code
("Material") are owned by Intel Corporation or its suppliers or licensors. Title to the Material remains
with Intel Corporation or its suppliers and licensors. The Material contains trade secrets and
proprietary and confidential information of Intel or its suppliers and licensors. The Material is
protected by worldwide copyright and trade secret laws and treaty provisions. No part of the
Material may be used, copied, reproduced, modified, published, uploaded, posted, transmitted,
distributed, or disclosed in any way without Intel's prior express written permission.

No license under any patent, copyright, trade secret or other intellectual property right is granted to
or conferred upon you by disclosure or delivery of the Materials, either expressly, by implication,
inducement, estoppel or otherwise. Any license under such intellectual property rights must be
express and approved by Intel in writing.
"""
import sys
import argparse
import subprocess

from input_parser import InputFilesParser
from output_parser import OutputCommandParser
from cc_client import CommandCenterAPIClient


class MainWrapper:
    def __init__(self):
        self.mpc_config = ''

    def prepare_command(self):
        """ Prepare command to run the provisioning script. """

        parser = argparse.ArgumentParser()
        parser.add_argument('-t', '--task', action='store', dest='task', help='Task to be performed')
        parser.add_argument('-c', action='store', dest='config_files', help='List of configuration files')
        parser.add_argument('-v', '--verbose', action='store_true', help='Verbose the parameters')
        parser.add_argument('-o', help='Output path defined in test case scenario (unused in provision wrapper)')
        args = parser.parse_args()

        task = args.task
        verbose = args.verbose
        config_files = args.config_files

        print("===== Running main wrapper for task: {} =====".format(task))

        if not task:
            print("ERROR: Missing task name: -t or --task")
            sys.exit(5)

        if verbose:
            print("Input command: {}".format(' '.join(sys.argv)))

        if config_files:
            input_parser = InputFilesParser(config_files)
            self.mpc_config = input_parser.mpc_config
        else:
            print("ERROR: Missing configuration files list parameter: -c")
            sys.exit(5)

        output_parser = OutputCommandParser(task, input_parser)
        return output_parser.provision_command, output_parser.product_versions

    def call_provision_process(self):
        """ Execute the provisioning script. """
        provision_command, product_versions = self.prepare_command()
        result = subprocess.run(provision_command, shell=True, check=False, cwd='..')
        provision_rc = result.returncode

        if self.mpc_config and provision_rc == 0:
            self.send_provision_summary(product_versions)
        return provision_rc

    @staticmethod
    def send_provision_summary(product_versions):
        print("===== Sending summary to CommandCenter =====")
        cc_client = CommandCenterAPIClient('https://api.commandcenter.iind.intel.com/api/ci/v1')
        cc_client.update_description(provisioned_versions=product_versions)

        # Uncomment in case of CommandCenter component version removal
        # cc_client.remove_component('CPLD')


if __name__ == '__main__':
    wrapper = MainWrapper()
    return_code = wrapper.call_provision_process()
    sys.exit(return_code)
