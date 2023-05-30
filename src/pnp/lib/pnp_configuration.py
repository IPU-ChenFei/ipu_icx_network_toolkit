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
import os
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path
from xml.etree import ElementTree

class PnPConfiguration(object):
    def __init__(self, log):
        self._log = log
        self.config_path_from_pnp = Path("config\pnp_configuration.xml")

    def get_config(self, attrib):
        pnp_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
        pnp_config_path = os.path.join(pnp_path, self.config_path_from_pnp)

        tree = ElementTree.ElementTree()
        tree.parse(pnp_config_path)

        if os.path.isfile(pnp_config_path):
            tree.parse(pnp_config_path)
        else:
            err_log = "Configuration file does not exists, please check.."
            self._log.error(err_log)
            raise IOError(err_log)

        root = tree.getroot()
        return root.find(r".//{}".format(attrib)).text.strip()

    def get_mlc_command(self):
        return self.get_config(attrib="pnp/mlc_command")

    def get_media_command(self):
        return self.get_config(attrib="pnp/media_command")

    def get_iax_command(self):
        return self.get_config(attrib="pnp/iax_command")

    def get_linpack_command(self):
        return self.get_config(attrib="pnp/linpack_command")

    def get_sgx_command(self):
        return self.get_config(attrib="pnp/sgx_command")

    def get_stream_command(self):
        return self.get_config(attrib="pnp/stream_command")

    def get_system_location(self):
        return self.get_config(attrib="pnp/system_location")

    def get_basic_setup_script(self):
        return self.get_config(attrib="pnp/basic_setup_script")

    def get_docker_script(self):
        return self.get_config(attrib="pnp/docker_script")

    def get_pnp_commit_id(self):
        return self.get_config(attrib="pnp/pnp_commit")

    def get_pnp_git_username(self):
        return self.get_config(attrib="pnp/git_username")

    def get_pnp_deploy_token(self):
        return self.get_config(attrib="pnp/deploy_token")



