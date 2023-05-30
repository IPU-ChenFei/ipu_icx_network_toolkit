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
import os
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib import content_exceptions
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from src.lib.dtaf_content_constants import TimeConstants


class PcieSurpriseLinkDownBaseTest(PcieCommon):
    """
    Phoenix ID:

    The purpose of this Test Case is to trigger an SLD (Surprise Link Down) event on a PCIe endpoint

    """

    _BIOS_CONFIG_FILE = "slde_testing.cfg"
    PCIBAR_OFFSET = {ProductFamilies.SPR: 0x3c48,
                     ProductFamilies.GNR: 0x3c48}
    WAIT_TIME_IN_SEC = 1
    OS_ERR_SIGNATURE = ["DPC: containment event", "DPC: unmasked uncorrectable error detected"]
    FORCE_DETECT_DICT = {
        ProductFamilies.SPR: "uncore.pi5.pxp{}.flexbus.port{}.expptmbar.ltssmstatejmp.forcedetect",
        ProductFamilies.EMR: "uncore.pi5.pxp{}.flexbus.port{}.expptmbar.ltssmstatejmp.forcedetect"
    }
    DPCTS_DICT = {
        ProductFamilies.SPR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.dpcsts.dpcts",
        ProductFamilies.EMR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.dpcsts.dpcts"
    }
    ERR_UNCMSK_DICT = {
        ProductFamilies.SPR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.erruncmsk.sldem",
        ProductFamilies.EMR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.erruncmsk.sldem"
    }
    DPCCTL_DICT = {
        ProductFamilies.SPR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.dpcctl",
        ProductFamilies.EMR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.dpcctl"
    }
    UNC_SLDE_DICT = {
        ProductFamilies.SPR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.erruncsts.slde",
        ProductFamilies.EMR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.erruncsts.slde",
        ProductFamilies.GNR: "uncore.pi5.pxp{}.pcieg5.port{}.rp0.cfg.erruncsts.slde"
    }
    DLLLA_DICT = {
        ProductFamilies.SPR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.linksts.dllla",
        ProductFamilies.EMR: "uncore.pi5.pxp{}.pcieg5.port{}.cfg.linksts.dllla"
    }

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Creates a PcieSurpriseLinkDownBaseTest object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        if bios_config_file is None:
            bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._BIOS_CONFIG_FILE)
        super(PcieSurpriseLinkDownBaseTest, self).__init__(test_log, arguments, cfg_opts,
                                                           bios_config_file)
        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration)
        self.PCIE_SOCKET = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        self.PCIE_PXP_PORT = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        self.sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        self.si_reg_obj = self.cscripts_obj
        self._pxp_port_list = self._common_content_configuration.get_pxp_port_list()

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        super(PcieSurpriseLinkDownBaseTest, self).prepare()

    def execute(self, os_err_signature=[]):
        """
        This method is to execute:
        1. Halt the system
        2. Write to direct media (expptmbar) register to trigger an SLD on PXP port
        3. Check SLD bit was set
        4. Check OS reporter errors
        5. Release the system

        :return: True or False
        """
        if not os_err_signature:
            os_err_signature = self.OS_ERR_SIGNATURE
        reg_expptmbar = {ProductFamilies.SPR: "pi5.%s.cfg.expptmbar" % self.PCIE_PXP_PORT,
                         ProductFamilies.GNR: "pi5.%s.rp0.cfg.expptmbar" % self.PCIE_PXP_PORT}
        reg_erruncsts_slde = {ProductFamilies.SPR: "pi5.%s.cfg.erruncsts.slde" % self.PCIE_PXP_PORT,
                              ProductFamilies.GNR: "pi5.%s.rp0.cfg.erruncsts.slde" % self.PCIE_PXP_PORT}

        reg_expptmbar_value = self.cscripts_obj.get_by_path(self.cscripts_obj.UNCORE,
                                                            reg_expptmbar[self.cscripts_obj.silicon_cpu_family],
                                                            socket_index=self.PCIE_SOCKET)
        reg_erruncsts_slde_value = self.cscripts_obj.get_by_path(self.cscripts_obj.UNCORE,
                                                                 reg_erruncsts_slde[self.cscripts_obj.silicon_cpu_family],
                                                                 socket_index=self.PCIE_SOCKET)

        self._log.info("Triggering SLD")
        self.sdp_obj.halt_and_check()
        self.trigger_sld(reg_expptmbar_value, self.PCIBAR_OFFSET[self.cscripts_obj.silicon_cpu_family])

        self._log.info("Checking SLDE bit")
        if reg_erruncsts_slde_value != 0x1:
            content_exceptions.TestFail("SLDE bit was not set after memory write")
            return False
        self._log.info("SLDE bit was set")
        self.sdp_obj.go()

        self._log.info("Checking OS log")

        errors_reported = self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                                        os_err_signature)

        if not errors_reported:
            log_err = "OS did not report expected errors after SLD event"
            self._log.error(log_err)
            raise content_exceptions.TestFail(log_err)

        self._log.info("OS did report expected errors after SLD event")

        return True

    def check_for_errors(self, sdp=None, pxp_port_list=[], clear_errors=0):
        """
        This method is to check the error.

        :param sdp - sdp object
        :param pxp_port_list - slot register path in list - ["s1.pxp2.port0", "s0.pxp0.port0"]
        :param clear_errors - Clear error
        :return False if error found else True.
        """
        status_list = []
        ltssm = self.si_reg_obj.get_ltssm_object()
        for each_register in pxp_port_list:
            socket_num, pxp_num, port_num = self.extract_pxp_and_port_number(each_register)

            pxp_dict = {
                ProductFamilies.SPR: "pxp%d.pcieg5.port%d" % (pxp_num, port_num),
                ProductFamilies.EMR: "pxp%d.pcieg5.port%d" % (pxp_num, port_num)
            }
            sdp.start_log("check_for_error.log", "w")
            err_op = ltssm.checkForErrors(socket_num, pxp_dict[self._common_content_lib.get_platform_family()],
                                          clear_errors)
            sdp.stop_log()

            with open("check_for_error.log", "r") as fp:
                error_log = fp.read()

            self._log.info("Check For Error Log output - {}".format(error_log))

            status_list.append(bool(err_op))

        return all(status_list)

    def extract_pxp_and_port_number(self, pxpport):
        """
        This method is to extract the Pxp Number and Port Number.

        :param pxpport - pxp port - "s1.pxp1.port0"
        :return - tupple (pxp_number, port_number)
        """
        pxpport_tmp = pxpport.replace("pxp", "")
        pxpport_tmp = pxpport_tmp.replace("port", "")
        pxpport_tmp = pxpport_tmp.replace("s", "")
        pxpport_list = pxpport_tmp.split(".")
        soc_num = int(pxpport_list[0])
        pxp_num = int(pxpport_list[1])
        port_num = int(pxpport_list[2])
        return soc_num, pxp_num, port_num

    def force_detect_check_sld_edpc(self, sdp, socketnum, pxpport):
        """
        This method is to check the SLD EDPC.

        :param sdp: sdp object
        :param socketnum: etc: 0, 1
        :param pxpport: "s1.pxp2.port0"
        :return:
        """
        self._log.info("Unlock the Machine")
        sdp.itp.unlock()

        soc_num, pxp_num, port_num = self.extract_pxp_and_port_number(pxpport=pxpport)
        self._log.info("pxpport: {}".format(pxpport))

        dpcts_reg = self.DPCTS_DICT[self._product_family].format(pxp_num, port_num)
        err_uncmask_reg = self.ERR_UNCMSK_DICT[self._product_family].format(pxp_num, port_num)
        dpcctl_reg = self.DPCCTL_DICT[self._product_family].format(pxp_num, port_num)

        unc_slde_reg = self.UNC_SLDE_DICT[self._product_family].format(pxp_num, port_num)

        self.clear_force_detect_reg(soc_num=socketnum, pxp_num=pxp_num, port_num=port_num)

        self.clear_edpc_event_reg(soc_num=socketnum, pxp_num=pxp_num, port_num=port_num)

        erruncmsk_output = self.si_reg_obj.get_by_path(scope=self.si_reg_obj.SOCKET,
                                                       reg_path=err_uncmask_reg, socket_index=socketnum).read()

        self._log.info("sv.socket{}.{}.read() - {}".format(socketnum, err_uncmask_reg, erruncmsk_output))

        if erruncmsk_output:
            self._log.error("Error: Surprise Link Down is masked!!!!")
            return False

        dpcctl_output = self.si_reg_obj.get_by_path(
           scope=self.si_reg_obj.SOCKET, reg_path=dpcctl_reg, socket_index=socketnum).read()

        if not dpcctl_output:
            self._log.error("Error: eDPC is not enabled!!")
            return False

        self.clear_sld_reg(soc_num=soc_num, pxp_num=pxp_num, port_num=port_num)

        # --> Start the test
        self._log.info("Start running")

        # --> Force Detect
        self._log.info("Forcing link to detect..")

        self.set_force_detect_reg(soc_num=soc_num, pxp_num=pxp_num, port_num=port_num)

        has_error = False
        # --> make sure Link is down, SLD and DPC triggered
        self.check_pcie_link_status(soc_num=socketnum, pxp_num=pxp_num, port_num=port_num, status="down")

        # --> Release force-detect
        self.clear_force_detect_reg(soc_num, pxp_num, port_num)

        time.sleep(self.WAIT_TIME_IN_SEC)
        sld_output = self.si_reg_obj.get_by_path(
            scope=self.si_reg_obj.SOCKET, reg_path=unc_slde_reg, socket_index=socketnum).read()

        self._log.info("sv.socket{}.{}.read() - {}".format(socketnum, unc_slde_reg, sld_output))
        if sld_output:
            self._log.info("PCIe Link Uncorrectable Surprise Link Down Status is successfully set...")
        else:
            self._log.error("Error: Surprise Link Down status bit is not set!!...")
            self._log.error("Error: Please check %s!!" % unc_slde_reg)
            has_error = True

        dpcts_output = self.si_reg_obj.get_by_path(
            scope=self.si_reg_obj.SOCKET, reg_path=dpcts_reg, socket_index=socketnum).read()
        self._log.info("sv.socket{}.{}.read() - {}".format(socketnum, dpcts_reg, dpcts_output))
        if dpcts_output:
            self._log.info("DPC has been triggered!!")
        else:
            self._log.error("Error: DPC event has not been triggered!!")
            self._log.error("Error: Dcfg.dpcsts.dpcts is not set to 1!!")
            return False

        if has_error:
            return False

        # --> All events are triggered successfuly, let clear ForceDown, DPC and bring back the link
        self.clear_force_detect_reg(soc_num, pxp_num, port_num)

        self.clear_edpc_event_reg(soc_num, pxp_num, port_num)

        time.sleep(2 * self.WAIT_TIME_IN_SEC)

        # --> Make sure Link is Active again
        self.check_pcie_link_status(soc_num=socketnum, pxp_num=pxp_num, port_num=port_num, status="up")

        self._log.info("force_det_chk_sld_dpc test is completed successfuly!!")
        return True

    def check_pcie_link_status(self, soc_num=0, pxp_num=0, port_num=0, status="down"):
        """
        This method is to check the pcie link status - down / up.

        :param soc_num - 0, 1
        :param pxp_num - 0, 1, 2
        :param port_num - 0, 1, 2
        :param status - down/up
        """
        dllla_reg = self.DLLLA_DICT[self._product_family].format(pxp_num, port_num)
        dllla_output = self.si_reg_obj.get_by_path(
            scope=self.si_reg_obj.SOCKET, reg_path=dllla_reg, socket_index=soc_num).read()

        self._log.info("sv.socket{}.{}.read() - {}".format(soc_num, dllla_reg, dllla_output))
        if status is "up":
            if dllla_output:
                self._log.info("PCIe Link is back")
            else:
                self._log.error("Error: Fail to bring Link back to Active!!")
                raise content_exceptions.TestFail("Error: Please check cfg.linksts.dllla!!")

        elif status is "down":
            # --> make sure Link is down, SLD and DPC triggered
            if not dllla_output:
                self._log.info("PCIe Link has been successfully forced down")
            else:
                self._log.error("Error: Fail to force link-down!!...")
                raise content_exceptions.TestFail("Error: Please check cfg.linksts.dllla!!")
        else:
            raise content_exceptions.TestFail("Not implemented for status- {}".format(status))

    def clear_force_detect_reg(self, soc_num=0, pxp_num=0, port_num=0):
        """
        This method is to clear force detect reg.

        :param soc_num - 0, 1, 2
        :param pxp_num - 0, 1, 2, 3
        :param port_num - 0, 1, 2
        """
        forcedetect_reg = self.FORCE_DETECT_DICT[self._product_family].format(pxp_num, port_num)
        force_detect_output = self.si_reg_obj.get_by_path(
            scope=self.si_reg_obj.SOCKET, reg_path=forcedetect_reg, socket_index=soc_num).read()

        self._log.info("sv.socket{}.{}.read() - {}".format(soc_num, forcedetect_reg, force_detect_output))

        if force_detect_output:
            self._log.info("Warning!! Force Detect is already set prior to the test!!")
            self._log.info("We will clear this and continue..")
            self.si_reg_obj.get_by_path(
                scope=self.si_reg_obj.SOCKET, reg_path=forcedetect_reg, socket_index=soc_num).write(0)
            self._log.info("sv.socket{}.{}.write(0)".format(soc_num, forcedetect_reg))

            force_det_val = self.si_reg_obj.get_by_path(
                scope=self.si_reg_obj.SOCKET, reg_path=forcedetect_reg, socket_index=soc_num).read()
            self._log.info("sv.socket{}.{}.read() - {}".format(soc_num, forcedetect_reg,
                                                               force_det_val))

    def clear_edpc_event_reg(self, soc_num=0, pxp_num=0, port_num=0):
        """
        This method is to clear the EDPC events reg.

        :param soc_num - 0, 1
        :param pxp_num - 0, 1, 2
        :param port_num - 0, 1, 2
        """
        dpcts_reg = self.DPCTS_DICT[self._product_family].format(pxp_num, port_num)
        dpcts_output = self.si_reg_obj.get_by_path(
            scope=self.si_reg_obj.SOCKET, reg_path=dpcts_reg, socket_index=soc_num).read()
        self._log.info("sv.socket{}.{}.read() - {}".format(soc_num, dpcts_reg, dpcts_output))

        if dpcts_output:
            self._log.info("Warning!! DPC event is already set !!")
            self._log.info("We will clear this and continue..")
            self._log.info("Writing to register- sv.socket{}.{}.write(1)".format(soc_num, dpcts_reg))
            self.si_reg_obj.get_by_path(
                scope=self.si_reg_obj.SOCKET, reg_path=dpcts_reg, socket_index=soc_num).write(1)
            dpcts_output = self.si_reg_obj.get_by_path(
                scope=self.si_reg_obj.SOCKET, reg_path=dpcts_reg, socket_index=soc_num).read()
            self._log.info("sv.socket{}.{}.read() - {}".format(soc_num, dpcts_reg, dpcts_output))

    def set_force_detect_reg(self, soc_num=0, pxp_num=0, port_num=0):
        """
        This method is Forcing link to detect..

        :param soc_num - 0, 1, 2
        :param pxp_num - 0, 1, 2
        :param port_num - 0, 1, 2
        """
        forcedetect_reg = self.FORCE_DETECT_DICT[self._product_family].format(pxp_num, port_num)

        self._log.info("Writing to register - sv.socket{}.{}.write(1)".format(soc_num,
                                                                              forcedetect_reg))
        self.si_reg_obj.get_by_path(
            scope=self.si_reg_obj.SOCKET, reg_path=forcedetect_reg, socket_index=soc_num).write(1)

        time.sleep(self.WAIT_TIME_IN_SEC)
        force_detect_output = self.si_reg_obj.get_by_path(
            scope=self.si_reg_obj.SOCKET, reg_path=forcedetect_reg, socket_index=soc_num).read()
        self._log.info("sv.socket{}.{}.read() - {}".format(soc_num, forcedetect_reg,
                                                           force_detect_output))
        if not force_detect_output:
            self._log.error("Error: Fail to write to %s" % forcedetect_reg)
            return False

    def clear_sld_reg(self, soc_num=0, pxp_num=0, port_num=0):
        """
        This Method is to clear the SLD reg.

        :param soc_num - 0, 1, 2
        :param pxp_num - 0, 1, 2
        :param port_num 0, 1, 2
        """
        unc_slde_reg = self.UNC_SLDE_DICT[self._product_family].format(pxp_num, port_num)
        uncorr_sld__output = self.si_reg_obj.get_by_path(
            scope=self.si_reg_obj.SOCKET, reg_path=unc_slde_reg, socket_index=soc_num).read()

        self._log.info("sv.socket{}.{}.read() - {}".format(soc_num, unc_slde_reg,
                                                           uncorr_sld__output))
        # --> Clear SLD before the test
        if uncorr_sld__output:
            self._log.info("Writing to register - sv.socket{}.{}.write(1) ".format(
                soc_num, unc_slde_reg))

            self.si_reg_obj.get_by_path(
                scope=self.si_reg_obj.SOCKET, reg_path=unc_slde_reg, socket_index=soc_num).write(1)

    def run_sld_edpc(self, sdp, socketnum_pxpport_list, loop=1, errorexit=1, edpc_enable=True):
        """
        This method is to run surprise link down edpc.

        :param sdp: - sdp object
        :param socketnum_pxpport_list: - ["s1.pxp0.port0", "s0.pxp2.port0"]
        :param loop: - number of loop
        :param errorexit: - exit on error
        :param edpc_enable - True if edpc is enable else False
        :return:
        """
        self._log.info("Unlock the Machine")
        sdp.itp.unlock()

        run_list = []
        result = {}
        for socketnum_pxpport in socketnum_pxpport_list:

            socket_num, pxp_num, port_num = self.extract_pxp_and_port_number(socketnum_pxpport)

            pxp_port = "uncore.pi5.pxp%d.pcieg5.port%d" % (pxp_num, port_num)

            run_list.append("%d,%s" % (socket_num, pxp_port))
            result[socketnum_pxpport] = {}
            result[socketnum_pxpport]['fail'] = 0
            result[socketnum_pxpport]['pass'] = 0
            result[socketnum_pxpport]['socket'] = socket_num
            result[socketnum_pxpport]['pxp'] = pxp_num
            result[socketnum_pxpport]['port'] = port_num
            result[socketnum_pxpport]['pxp_port'] = pxp_port

        current_loop = 0
        num_errs = 0
        failing_devices = []
        while current_loop < loop:
            self._log.info("\nStart running iterations:%d" % current_loop)
            for socketnum_pxpport in socketnum_pxpport_list:
                pxp_port = result[socketnum_pxpport]['pxp_port']
                socket = result[socketnum_pxpport]['socket']
                self._log.info("Validating PCIe %s ..." % socketnum_pxpport)
                if edpc_enable is True:
                    run_stat = self.force_detect_check_sld_edpc(sdp, socket, socketnum_pxpport)
                else:
                    run_stat = self.force_detect_poll_sld_only(sdp, socket, socketnum_pxpport)

                if run_stat is False:
                    self._log.error("Error:%s Surprise Link Down test has failed at iterations:%d!!" % (
                    socketnum_pxpport, current_loop))
                    self._log.error("Error:%s Scroll up for detail errors\n\n" % socketnum_pxpport)
                    result[socketnum_pxpport]['fail'] = result[socketnum_pxpport]['fail'] + 1
                    num_errs = num_errs + 1

                    if result[socketnum_pxpport]['fail'] == 1:
                        failing_devices.append(socketnum_pxpport)

                    if errorexit:
                        return False

                else:
                    self._log.info("%s:Surprise Link Down Test is completed successfully for iterations:%d\n\n" % (
                    socketnum_pxpport, current_loop))

                if edpc_enable is False:
                    if self.is_sut_rebooted_to_uefi(sdp):
                        self._log.info("Rebooted to Uefi Successful")

            current_loop = current_loop + 1

        if not num_errs:
            self._log.info("Tests are passing %d iterations!!" % loop)
        else:
            for fail_device in failing_devices:
                self._log.error(
                    "Error: %s is failing %d out of %d iterations\n" % (fail_device, result[fail_device]['fail'], loop))
            return False

        return True

    def force_detect_poll_sld_only(self, sdp, socket_num, pxp_port):
        """
        This method is to Apply Force Det and Polling SLD.

        :param sdp : silicon debug provider object
        :param socket_num : socket number
        :param pxp_port : pxp port
        """
        self._log.info("Unlock the Machine")
        sdp.itp.unlock()
        socket_num, pxp_num, port_num = self.extract_pxp_and_port_number(pxp_port)

        uncorr_sld_reg = self.UNC_SLDE_DICT[self._product_family].format(pxp_num, port_num)
        err_uncmsk_reg = self.ERR_UNCMSK_DICT[self._product_family].format(pxp_num, port_num)
        slde_reg = self.UNC_SLDE_DICT[self._product_family].format(pxp_num, port_num)
        dllla_reg = self.DLLLA_DICT[self._product_family].format(pxp_num, port_num)

        self.clear_force_detect_reg(soc_num=socket_num, pxp_num=pxp_num, port_num=port_num)

        self.clear_edpc_event_reg(socket_num, pxp_num, port_num)

        errunmsk_output = self.si_reg_obj.get_by_path(
                scope=self.si_reg_obj.SOCKET, reg_path=err_uncmsk_reg,
                socket_index=socket_num).read()

        self._log.info("sv.socket{}.{}.read() - {}".format(socket_num, err_uncmsk_reg, errunmsk_output))

        if errunmsk_output:
            self._log.info("Error: Surprise Link Down is masked!!!!")
            return False

        slde_output = self.si_reg_obj.get_by_path(
                scope=self.si_reg_obj.SOCKET, reg_path=slde_reg,
                socket_index=socket_num).read()

        self._log.info("sv.socket{}.{}.write(1) ".format(socket_num, slde_reg))
        if slde_output:
            self._log.info("sv.socket{}.{}.write(1)".format(socket_num, slde_reg))
            self.si_reg_obj.get_by_path(
                scope=self.si_reg_obj.SOCKET, reg_path=slde_reg,
                socket_index=socket_num).write(1)

        self._log.info("Start Running..")

        sleep_time_in_sec = 5

        poll_slde = poll_reg(self.si_reg_obj, socket_num, slde_reg, 1, sleep_time_in_sec, self._log)
        poll_slde.run()

        self._log.info("Forcing link to detect..")
        self.set_force_detect_reg(socket_num, pxp_num, port_num)

        time.sleep(sleep_time_in_sec)

        if poll_slde._return is False:
            self._log.info("Error: %s never set to 1 after %s" % (uncorr_sld_reg, sleep_time_in_sec))
            self._log.error("Error: after forced link down!!")
            return False

        # --> make sure Link is down, SLD and DPC triggered

        if self.si_reg_obj.get_by_path(
                scope=self.si_reg_obj.SOCKET, reg_path=dllla_reg, socket_index=socket_num).read() != 1:
            self._log.info("PCIe Link has been successfully forced down")
        else:
            self._log.error("Error: Fail to force link-down!!...")
            self._log.error("Error: Please check cfg.linksts.dllla!!")
            return False

        # --> Release force-detect
        self.clear_force_detect_reg(socket_num, pxp_num, port_num)

        time.sleep(self.WAIT_TIME_IN_SEC)

        self._log.info("force_det_chk_sld_dpc test is completed successfuly!!")
        return True

    def is_sut_rebooted_to_uefi(self, sdp):
        """
        This method is to boot the SUT to UEFI.

        :param sdp
        :return:
        """
        #  Create UEFI object
        from dtaf_core.providers.uefi_shell import UefiShellProvider

        uefi_cfg = self._cfg.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        uefi_obj = ProviderFactory.create(uefi_cfg, self._log)  # type: UefiShellProvider

        self._log.info("Checking if SUT is in UEFI..")
        time.sleep(10 * self.WAIT_TIME_IN_SEC)
        if uefi_obj.in_uefi():
            raise content_exceptions.TestFail("SUT did not rebooted and it is already in Uefi")
        self._log.info("Waiting SUT to reach UEFI")

        sdp.itp.resettarget()
        time.sleep(self.WAIT_TIME)
        uefi_obj.wait_for_uefi(self._common_content_config.bios_boot_menu_entry_wait_time())

        time.sleep(self.WAIT_TIME)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieSurpriseLinkDownBaseTest.main() else Framework.TEST_RESULT_FAIL)


class poll_reg(object):
    """
       The run() method will be started and it will run in the background
       until the application exits.
   """

    def __init__(self, si_reg_obj, socket_num, reg_name, expected_val, timeout=10, log=None):
        """ Constructor
          :timeout in second
        """
        self.si_reg_obj = si_reg_obj
        self.reg_name = reg_name
        self.expected_val = expected_val
        self.timeout = timeout
        self._return = False
        self._log = log
        self.socket = socket_num

    def run(self):
        thread = threading.Thread(target=self.poll, args=())
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution
        return self._return

    def poll(self):
        """ Method that runs forever """
        full_reg_name = "sv.socket{}.{}".format(self.socket, self.reg_name)
        self._log.info('Start background run for polling')
        self._log.info("Polling %s ..." % full_reg_name)
        reg_read_val = ""
        cur_time = time.time()
        # --> Poll for SDL
        stat = self.si_reg_obj.get_by_path(self.si_reg_obj.SOCKET,
                                                    self.reg_name, self.socket).read()
        self._log.info("sv.socket{}.{} initial value-{}".format(self.socket, self.reg_name, stat))
        while stat != self.expected_val:
            time2 = time.time()
            reg_read_val = self.si_reg_obj.get_by_path(self.si_reg_obj.SOCKET,
                                                    self.reg_name, self.socket).read()
            if (time2 - cur_time) > self.timeout:
                self._return = False
                return

            stat = self.si_reg_obj.get_by_path(self.si_reg_obj.SOCKET,
                                               self.reg_name, self.socket).read()
            self._log.info("sv.socket{}.{} -{}".format(self.socket, self.reg_name, stat))

        self._log.info("%s value is %s" % (full_reg_name, reg_read_val))
        self._log.info("Hit!!: %s is set to %d" % (full_reg_name, self.expected_val))
        self._return = True

        return True
