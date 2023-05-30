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

from dmidecode import DMIParse

from src.lib.content_configuration import ContentConfiguration
from src.lib.common_content_lib import CommonContentLib


class DmiDecodeParser(object):
    """
    To convert the dmidecode output data to a dict.
    To fetch the domain based configurations accordingly to the test case from the xml file to be used on
    across memory, RAS and Security domains.
    """

    dmi_output = None

    def __init__(self, log, os_obj):
        self._log = log
        self._os = os_obj

        self._common_content_lib = CommonContentLib(self._log, self._os, None)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()

    def dmidecode_parser(self, log_path_to_parse):
        """
        Function to fetch the attribute values from the xml configuration file.

        :return: dmidecode output as dict.
        """
        dmi_path = os.path.join(log_path_to_parse, "dmi.txt")
        if os.path.isfile(dmi_path):
            with open(dmi_path, "r") as dmi_file:
                self.dmi_output = dmi_file.read()
            verify_dmi = ""

            instance_dmiparse = DMIParse(verify_dmi)
            dmi_decode_from_cmd_line = instance_dmiparse.dmidecode_parse((self.dmi_output.replace("<", ""))
                                                                         .replace(">", ""))
            self._log.info("OS provided SMBIOS dmidecode informaton.. \n {}".format(dmi_decode_from_cmd_line))

            return dmi_decode_from_cmd_line
        else:
            err_log = "Dmi decode file '{}' does not exists, please populate the file and " \
                      "run test again..".format(dmi_path)
            self._log.error(err_log)
            raise IOError(err_log)
