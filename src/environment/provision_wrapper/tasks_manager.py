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
import os
import sys

from utils import get_config_params, prepare_win_oneliner, prepare_fw_oneliner, \
    prepare_os_oneliner_with_sft_pkg, prepare_cpld_fw_oneliner, prepare_os_iso_oneliner


class Task:
    """
    Class with tasks definitions: OS/FW installation.
    """
    def __init__(self, task, config):
        self.task = task
        self.config = config
        self.provision_command = {}

        try:
            # Match task name to the method
            method = getattr(self, task)
            oneliner, product_versions = method()
        except AttributeError:
            print("ERROR: Unsupported task: {}".format(task))
            sys.exit(5)

        config_params = get_config_params(self.task, config.input_parameters)
        self.provision_command = 'python {oneliner} {config_params}'.format(oneliner=oneliner,
                                                                            config_params=config_params)
        self.product_versions = product_versions

    def windows_installation(self):
        provision_script = os.path.join('windows', 'paiv_win_os_online_installation.py')
        return prepare_win_oneliner(self.config, provision_script)

    def linux_rhel_installation(self):
        provision_script = os.path.join('linux_rhel', 'paiv_rhel_os_installation_bmc.py')
        return prepare_os_iso_oneliner(self.config, provision_script, 'RHEL')

    def linux_centos_installation(self):
        provision_script = os.path.join('linux_centos', 'paiv_cent_os_installation_bmc.py')
        return prepare_os_iso_oneliner(self.config, provision_script, 'CentOS')

    def esxi_installation(self):
        provision_script = os.path.join('esxi', 'paiv_esxi_os_online_installation.py')
        return prepare_os_oneliner_with_sft_pkg(self.config, provision_script, 'ESXiBaseOS', 'ESXiSoftware')

    def ifwi_flashing(self):
        provision_script = os.path.join('ifwi_flashing', 'paiv_ifwi_flashing_online.py')
        return prepare_fw_oneliner(self.config, provision_script, 'IFWI', 'IFWI', 'atf_path_ifwi_pkg')

    def bmc_banino_flashing(self):
        provision_script = os.path.join('bmc_flashing', 'paiv_bmc_flashing_banino_online.py')
        return prepare_fw_oneliner(self.config, provision_script, 'BMCBanino', 'BMC', 'atf_path_bmc_pkg')

    def bmc_redfish_flashing(self):
        provision_script = os.path.join('bmc_flashing', 'paiv_bmc_flashing_redfish_online.py')
        return prepare_fw_oneliner(self.config, provision_script, 'BMCRedfish', 'BMC', 'atf_path_bmc_red_pkg')

    def cpld_flashing(self):
        provision_script = os.path.join('cpld_flashing', 'paiv_cpld_flashing_online.py')
        return prepare_cpld_fw_oneliner(self.config, provision_script)
