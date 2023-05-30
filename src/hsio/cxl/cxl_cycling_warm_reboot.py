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
import time

from dtaf_core.providers.provider_factory import ProviderFactory

from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.cxl.cxl_ctg_base_test import CxlCtgCommon
from src.pcie.tests.pi_pcie.pcie_common import PxpInventory
from src.hsio.cxl.cxl_common import CxlCommon
from src.lib import content_exceptions


class CxlCyclingWarmReboot(CxlCtgCommon):
    """
    hsdes_id :  16016160286

    The purpose of this test is to verify the below register values through  cscripts during Warm reset cycling.
    This is additional check in cycling content .

    pcie.get_data_link_layer_link_active(socket,port) : Returns True if the given port/link has an active Link Layer.

    pcie.get_current_link_speed(socket, port): Get the current speed of the given port/link (i.e., 5.0 as in Gen5)

    pcie.getBitrate(socket,port): Gets the speed rate of the link in GT/s

    cxl.in_cxl_mode(socket,port): Validates if  device is in CXL mode.

    cxl.get_device_type(socket, port): Gets device type in which the CXL device is operating with.

    cxl.get_cxl_version(socket, port): Gets CXL version in which the device was developed with.
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlCscriptsRegisterChecksWarmResetCycling.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlCyclingWarmReboot, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)
        self.no_of_cycle = self._common_content_configuration.get_num_of_cxl_cycling()

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlCyclingWarmReboot, self).prepare()

    def execute(self, reboot_type="warm_reboot"):
        """
        This method is to perform Warm cycling and  validating linkspeed, width speed, bitrate, cxl version etc.
        """
        pcie = self.csp.get_cscripts_utils().get_pcie_obj()
        cxl = self.csp.get_cxl_obj()
        self.initialize_os_cyling_script()

        cxl_slots_dict = self.pxp_inventory.get_slot_inventory(
            platform=self._common_content_lib.get_platform_family(),
            silicon_reg_provider_obj=self.csp)[PxpInventory.IOProtocol.CXL]

        for index in range(0, self.no_of_cycle):

            self._common_content_lib.execute_sut_cmd("./pci_check_cycle.sh", "health check", self._command_timeout,
                                                     "/root")

            self._log.info("Cycle Number- {} is in progress..".format(index + 1))
            count = 0

            for socket, pxp_port_dict in cxl_slots_dict.items():
                for port, port_dict in pxp_port_dict.items():
                    socket = socket
                    port = port
                    link_speed = PxpInventory.PCIeLinkSpeed.GEN_DICT[port_dict["speed"]]
                    cxl_width = port_dict["width"]
                    cxl_device_type = port_dict["cxl_type"]
                    cxl_version = port_dict["cxl_version"]
                    cxl_cache = CxlCommon.CXL_TYPE_IN_CSCRIPTS[cxl_device_type]["Cache"]
                    cxl_io_en = CxlCommon.CXL_TYPE_IN_CSCRIPTS[cxl_device_type]["IO"]
                    cxl_mem_en = CxlCommon.CXL_TYPE_IN_CSCRIPTS[cxl_device_type]["Mem"]
                    bit_rate = port_dict["bit_rate"]

                    actual_link_speed = pcie.get_current_link_speed(int(socket), port)

                    if not self.is_cxl_card_enumerated(port=port, socket=socket, csp_obj=self.csp):
                        raise content_exceptions.TestFail("CXL Card (socket- {}, port- {}) was not enumerated".format(
                            socket, port))
                    self._log.info("CXL card (socket- {} and port- {} is enumerated as expected".format(socket, port))

                    if str(actual_link_speed) != link_speed:
                        raise content_exceptions.TestFail("Link Speed was not found as Expected- {}".format(
                            str(actual_link_speed)))
                    self._log.info("Link Speed was found as Expected- {} for socket- {} and port- {}".format(
                        str(actual_link_speed), socket, port))

                    actual_link_width = pcie.get_negotiated_link_width(int(socket), port)

                    if str(int(actual_link_width)) != str(cxl_width)[1:]:
                        raise content_exceptions.TestFail("Link Width was not found as Expected for Socket-"
                                                          " {} and Port- {}".format(socket, port))

                    self._log.info("Link Width was found as Expected for Socket- {} and Port- {}".format(socket, port))
                    if not cxl.in_cxl_mode(int(socket), port):
                        raise content_exceptions.TestFail("CXL mode was not found as Expected for"
                                                          " socket- {} and port- {}".format(socket, port))
                    self._log.info("CXL mode was found as Expected for  socket- {} and port- {}".format(socket, port))

                    if bit_rate not in str(pcie.getBitrate(int(socket), port)):
                        raise content_exceptions.TestFail("Bit-rate for socket- {} and port- {} was "
                                                          "not found as expected".format(socket, port))

                    self._log.info("Bit-rate for socket - {} and port- {} was found as expected".format(socket, port))

                    if not pcie.getCrcErrCnt(int(socket), port):
                        raise content_exceptions.TestFail(
                            "Unexpected Crc Error Count was captured for socket- {} and port- {}".format(socket, port))
                    self._log.info("Crc Error Cnt for Socket- {} and port was found as expected".format(socket, port))

                    self.sdp.halt()

                    self.validate_device_type(socket=socket, port=port, cxl=cxl, cxl_device_type=cxl_device_type)

                    self.validate_cxl_version(socket=socket, port=port, cxl=cxl, cxl_version=cxl_version)

                    self.sdp.start_log("{}_cxl_dp_dvsec_show_output_{}.txt".format(count, 0 if index == 0 else 1), "w")
                    cxl.cxl_dp_dvsec_show(int(socket), port)
                    self.sdp.stop_log()

                    with open("{}_cxl_dp_dvsec_show_output_{}.txt".format(count, 0 if index == 0 else 1), "r") as fp:
                        cxl_dp_dvsec_show = fp.read()
                    self._log.info(cxl_dp_dvsec_show)

                    self.validate_cxl_devsec_attribute(cxl_dp_dvsec_show, devsec_ven_id=self.cxl_vendor_id)

                    self.check_devsec_equal_to_initial_value(cycle_num=index,
                                                             file_1="{}_cxl_dp_dvsec_show_output_0.txt".format(count),
                                                             file_2="{}_cxl_dp_dvsec_show_output_1.txt".format(count),
                                                             devsec_type="dp_devsec")

                    self.sdp.start_log("{}_cxl_up_dvsec_show_output_{}.txt".format(count, 0 if index == 0 else 1), "w")
                    cxl.cxl_up_dvsec_show(int(socket), port)
                    self.sdp.stop_log()

                    with open("{}_cxl_up_dvsec_show_output_{}.txt".format(count, 0 if index == 0 else 1), "r") as fp:
                        cxl_up_dvsec_show = fp.read()
                    self._log.info(cxl_up_dvsec_show)

                    self.validate_cxl_devsec_attribute(cxl_up_dvsec_show, cxl_io_en, cxl_mem_en, cxl_cache,
                                                       self.cxl_vendor_id)

                    self.check_devsec_equal_to_initial_value(cycle_num=index,
                                                             file_1="{}_cxl_up_dvsec_show_output_0.txt".format(count),
                                                             file_2="{}_cxl_up_dvsec_show_output_1.txt".format(count),
                                                             devsec_type="up_devsec")

                    self.sdp.start_log("{}_cxl_iep_dvsec_show_output_{}.txt".format(count, 0 if index == 0 else 1), "w")
                    cxl.cxl_iep_dvsec_show(int(socket), port)
                    self.sdp.stop_log()

                    with open("{}_cxl_iep_dvsec_show_output_{}.txt".format(count, 0 if index == 0 else 1), "r") as fp:
                        cxl_iep_dvsec_show = fp.read()
                    self._log.info(cxl_iep_dvsec_show)

                    self.check_devsec_equal_to_initial_value(cycle_num=index,
                                                             file_1="{}_cxl_iep_dvsec_show_output_0.txt".format(count),
                                                             file_2="{}_cxl_iep_dvsec_show_output_1.txt".format(count),
                                                             devsec_type="up_devsec")

                    self.sdp.start_log("{}_cxl_cmem_err_check_output_{}.txt".format(count, 0 if index == 0 else 1), "w")
                    cxl.cxl_cmem_err_check(int(socket), port)
                    self.sdp.stop_log()

                    with open("{}_cxl_cmem_err_check_output_{}.txt".format(count, 0 if index == 0 else 1), "r") as fp:
                        cxl_cmem_err_check = fp.read()
                    self._log.info(cxl_cmem_err_check)

                    self.check_devsec_equal_to_initial_value(cycle_num=index,
                                                             file_1="{}_cxl_cmem_err_check_output_0.txt".format(count),
                                                             file_2="{}_cxl_cmem_err_check_output_1.txt".format(count),
                                                             devsec_type="cmem_err")

                    self.sdp.start_log("{}_cxl_ieh_error_dump_output_{}.txt".format(count, 0 if index == 0 else 1), "w")
                    cxl.cxl_ieh_error_dump(int(socket), port)
                    self.sdp.stop_log()

                    with open("{}_cxl_ieh_error_dump_output_{}.txt".format(count, 0 if index == 0 else 1), "r") as fp:
                        cxl_ieh_error_dump = fp.read()
                    self._log.info(cxl_ieh_error_dump)

                    self.check_devsec_equal_to_initial_value(cycle_num=index,
                                                             file_1="{}_cxl_ieh_error_dump_output_0.txt".format(count),
                                                             file_2="{}_cxl_ieh_error_dump_output_1.txt".format(count),
                                                             devsec_type="ieh_error")

                    count += 1

                    self.sdp.go()

            if reboot_type == "warm_reboot":
                self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            elif reboot_type == "ac_cycle":
                self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
                self._common_content_lib.wait_for_os(self.reboot_timeout)
            elif reboot_type == "dc_cycle":
                try:
                    self.os.execute("rtcwake -m off -s {}".format(
                        self._common_content_configuration.get_sut_wakeup_time_in_sec()), self._command_timeout)
                except:
                    pass
                self._common_content_lib.wait_for_os(self.reboot_timeout)
            else:
                raise content_exceptions.TestFail("Still Not Implemented for cycling - {}".format(reboot_type))
            time.sleep(self.WAIT_TIME)
            self._log.info("Cycle Number- {} has Completed Successfully..".format(index + 1))

        self.check_cap_err_cnt()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlCyclingWarmReboot.main() else
             Framework.TEST_RESULT_FAIL)
