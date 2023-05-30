#!/usr/bin/env python
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and propri-
# etary and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be ex-
# press and approved by Intel in writing.

import re
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.cpu_info_provider import CpuInfoProvider
import src.lib.content_exceptions as content_exception


class ProcessorUPIInfo(ContentBaseTestCase):
    """
    HPQC ID : H77963-PI_Processor_UPI_LinkSpeed_Status_W

    Test and verify if UPI link speed is normal or not.
    """
    STRESS_COMMAND_DICT = {"prime95": "prime95.exe -t", "mprime": "./mprime -t"}
    PORT_ROW_MATCH_REGEX = "Connected\sto"
    LINK_SPEED_ROW_MATCH_REGEX = "Link\sSpeed"
    REGEX_FOR_LINK_SPEED = "(\d+.)|(\d+.+) \s\S+"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ProcessorUPIInfo

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(ProcessorUPIInfo, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        call base class prepare function

        :return: None
        """
        super(ProcessorUPIInfo, self).prepare()

    def get_upi_linkspeed_details(self, filename):
        """
        This method returns a dictionary of UPI Link SPeed associated with each port.

        :param filename: Log file which  has UPI topology info.
        :return: Dictionary
        :raise : content_exception.TestFail() if failed
        """
        port_list = []
        link_speed_list = []
        self._log.info("Fetch UPI Link Speed Data from upi.topology()")
        with open(filename, "r") as log_file:
            upi_before_stress = log_file.readlines()
            self._log.debug("Processor UPI Status Details from UPI Topology : {}".format(upi_before_stress))
            for each_element in upi_before_stress:
                if re.search(self.PORT_ROW_MATCH_REGEX, each_element):
                    for each_port in each_element.strip().split("|"):
                        if not re.search(self.PORT_ROW_MATCH_REGEX, each_port):
                            port_list.append(each_port.strip())
                if re.search(self.LINK_SPEED_ROW_MATCH_REGEX, each_element):
                    for each_link in each_element.strip().split("|"):
                        if not re.search(self.LINK_SPEED_ROW_MATCH_REGEX, each_link):
                            if len(re.findall(self.REGEX_FOR_LINK_SPEED, each_link))>0:
                                link_speed_list.append(each_link.strip())

        link_speed_list = [non_empty_element for non_empty_element in link_speed_list if non_empty_element]
        port_list = [non_empty_element for non_empty_element in port_list if non_empty_element]

        if not link_speed_list or not port_list:
            raise content_exception.TestFail("Link Speed Data from upi.topology() output is not as expected, no data "
                                             "to compare")

        self._log.debug("Link Speed Details : {}".format(dict(zip(port_list, link_speed_list))))
        return dict(zip(port_list, link_speed_list))

    def log_upi_topology(self, log_file_name):
        """
        This method executes upi.topology() in cscripts and logs into a file.

        :param log_file_name: path to log file where the cscripts logs has to be saved.
        :raise: contentExceptions.TestFail() if failed.
        """
        try:
            with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
                sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
                self._upi = cscripts_obj.get_upi_obj()
                sdp_obj.halt()
                sdp_obj.start_log(log_file_name)
                self._upi.topology()
                sdp_obj.stop_log()
                sdp_obj.go()
        except Exception as ex:
            raise content_exception.TestFail("Failed to Log UPI Topology Due to Exception {}".format(ex))
