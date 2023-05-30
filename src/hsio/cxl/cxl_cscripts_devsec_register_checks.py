#!/usr/bin/env python
##########################################################################
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
##########################################################################
import sys
import re

from dtaf_core.providers.provider_factory import ProviderFactory

from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.cxl.cxl_ctg_base_test import CxlCtgCommon
from src.lib import content_exceptions


class CxlCscriptsDevsecRegisterChecks(CxlCtgCommon):
    """
    hsdes_id :  16015958532

    CXL specification defined configuration space registers are grouped into blocks and each block is enumerated
    as a PCI Express Designated Vendor-Specific Extended Capability (DVSEC) structure. DVSEC Vendor ID field is
    set to 1E98h to indicate these Capability structures are defined by the CXL specification.

    Read and decode DVSEC ID assignment

    Applicable for  - CXL 1.1 and CXL 2.0 devices.

    CXL spec reference -  Section 8.1.1 of CXL 2.0 spec

    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCscriptsDevsecRegisterChecks.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCscriptsDevsecRegisterChecks, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)
        self.socket_list = self._common_content_configuration.get_cxl_sockets()
        self.port_list = self._common_content_configuration.get_cxl_ports()
        self.current_link_speed = self._common_content_configuration.get_cxl_current_link_speed()
        self.cxl_link_width = self._common_content_configuration.get_cxl_link_width()
        self.cxl_cache_en = self._common_content_configuration.get_cxl_cache_en_list()
        self.cxl_io_en = self._common_content_configuration.get_cxl_io_en_list()
        self.cxl_mem_en = self._common_content_configuration.get_cxl_mem_en_list()

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCscriptsDevsecRegisterChecks, self).prepare()

    def execute(self):
        """
        This method is to perform Warm cycling and  validating linkspeed, width speed, bitrate, cxl version etc.
        """
        pcie = self.csp.get_cscripts_utils().get_pcie_obj()
        cxl = self.csp.get_cxl_obj()

        for socket, port, link_speed, cxl_width, cxl_cache, \
                cxl_io_en, cxl_mem_en in zip(
                self.socket_list, self.port_list, self.current_link_speed, self.cxl_link_width, self.cxl_cache_en,
                self.cxl_io_en, self.cxl_mem_en):

            actual_link_speed = pcie.get_current_link_speed(int(socket), port)

            if not self.is_cxl_card_enumerated(port=port, socket=socket, csp_obj=self.csp):
                raise content_exceptions.TestFail("CXL Card socket- {}, port- {} was not enumerated".format(
                    socket, port))
            self._log.info("CXL card socket- {} and port- {} is enumerated as expected".format(socket, port))
            if str(actual_link_speed) != link_speed:
                raise content_exceptions.TestFail("Link Speed was not found as Expected- {}".format(
                    str(actual_link_speed)))
            self._log.info("Link Speed was found as Expected- {} for socket- {} and port- {}".format(
                str(actual_link_speed), socket, port))

            actual_link_width = pcie.get_negotiated_link_width(int(socket), port)

            if str(int(actual_link_width)) != cxl_width:
                raise content_exceptions.TestFail("Link Width was not found as Expected for Socket-"
                                                  " {} and Port- {}".format(socket, port))

            self._log.info("Link Width was found as Expected for Socket- {} and Port- {}".format(socket, port))
            self._log.info("Displaying speed rate - {}".format(pcie.getBitrate(int(socket), port)))
            try:
                cxl_dp_dvsec_show = self.get_cxl_cscript_method_output("cxl_dp_dvsec_show", socket, port)
                self.validate_cxl_devsec_attribute(cxl_dp_dvsec_show, cxl_io_en, cxl_mem_en, cxl_cache,
                                                   self.cxl_vendor_id)

                cxl_up_dvsec_show = self.get_cxl_cscript_method_output("cxl_up_dvsec_show", socket, port)
                self.validate_cxl_devsec_attribute(cxl_up_dvsec_show, cxl_io_en, cxl_mem_en, cxl_cache,
                                                   self.cxl_vendor_id)

                cxl_iep_dvsec_show = self.get_cxl_cscript_method_output("cxl_iep_dvsec_show", socket, port)
                self.validate_cxl_devsec_attribute(cxl_iep_dvsec_show, cxl_io_en, cxl_mem_en, cxl_cache,
                                                   self.cxl_vendor_id)

                cxl_cmem_err_check = self.get_cxl_cscript_method_output("cxl_cmem_err_check", socket, port)
                output = re.findall(self.cxl_err_check_regex, cxl_cmem_err_check)
                if not output:
                    raise content_exceptions.TestFail("Couldn't get cxl mem error status ")
                self._log.info("List of Errors reported - {}".format(output))
                errors = [int(i) for i in output if int(i) > 0]
                if errors:
                    raise content_exceptions.TestFail("Error found in CXL Mem Error Check")
                self._log.info("No error found in CXL Mem Error Check")

                cxl_ieh_error_dump = self.get_cxl_cscript_method_output("cxl_ieh_error_dump", socket, port)
                output = re.findall(self.cxl_err_check_regex, cxl_ieh_error_dump)
                if not output:
                    raise content_exceptions.TestFail("Couldn't get cxl IEH error status ")
                self._log.info("List of Errors reported - {}".format(output))
                errors = [int(i) for i in output if int(i) > 0]
                if errors:
                    raise content_exceptions.TestFail("Error found in CXL IEH Error Check")
                self._log.info("No error found in CXL IEH Error Check")

            except Exception as ex:
                raise content_exceptions.TestFail("Failed due to - {} ".format(ex))
            finally:
                self.sdp.go()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCscriptsDevsecRegisterChecks.main() else
             Framework.TEST_RESULT_FAIL)
