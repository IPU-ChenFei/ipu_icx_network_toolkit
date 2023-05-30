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
import os
import re
import time

from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.ras.lib.ras_upi_util import RasUpiUtil

from src.lib.common_content_lib import CommonContentLib
from src.lib.dtaf_content_constants import PassThroughAttribute
from src.lib.install_collateral import InstallCollateral

from src.provider.vm_provider import VMProvider
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon

from src.virtualization.virtualization_common import VirtualizationCommon

from src.lib import content_exceptions
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.dtaf_content_constants import VmTypeAttribute
from src.ras.tests.upi_dynamic_link_width_reduction_tests.upi_lane_failover_common import UpiLaneFailoverCommon


class VmUpiLaneFailOverBaseTest(IoVirtualizationCommon):
    """
    This Class is Used as Common Class For VmUpiLaneFailOverBaseTest
    """

    VM_OS = [VmTypeAttribute.RHEL.value]
    VM_NAME = []

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file=None
    ):
        """
        Create an instance of VmUpiLaneFailOverBaseTest

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), bios_config_file)
        super(
            VmUpiLaneFailOverBaseTest,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file=bios_config_file)
        self.cfg_opts = cfg_opts
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._upi_lane_failover_common_obj = UpiLaneFailoverCommon(self._log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        Execute prepare.
        """
        super(VmUpiLaneFailOverBaseTest, self).prepare()

    def execute(self, num_of_vms):  # type: () -> bool
        """
        This method is to
        1. Create VM
        2. Verify VM
        3. Run Crunch tool
        4. Run Upi Lane Fail Over Test
        5. Verify VM is alive or not

        :return True if Test pass
        """
        vm_os_obj_list = []
        for index in range(num_of_vms):

            vm_name = self.VM_OS[0] + "_" + str(index)
            vm_os_obj = self.create_and_verify_vm(vm_name, self.VM_OS[0], crunch_tool=True, enable_yum_repo=True)
            vm_os_obj_list.append(vm_os_obj)

        ret_val = self._upi_lane_failover_common_obj.inject_and_check_upi_link_width_change_failure(
                self._upi_lane_failover_common_obj.TRANSMIT,
            self._upi_lane_failover_common_obj.UPI_LANE_MASK_DISABLE_ALL_LOW_LANES)
        if not ret_val:
            raise content_exceptions.TestFail("Test Failed: UPI Lane Fail Over")

        #  Check VM is alive or not
        for index in range(num_of_vms):
            vm_name = self.VM_OS[0] + "_" + str(index)
            self._log.info("Check VM- {} is alive or not".format(vm_name))

            if not vm_os_obj_list[index].is_alive():
                raise content_exceptions.TestFail("VM- {} is not alive after UPI Lane Fail Over Test".format(vm_name))
            self._log.info("VM- {} is alive after UPI Lane Fail Over Test as expected".format(vm_name))

    def cleanup(self, return_status, num_of_vms=None):
        try:
            for index in range(num_of_vms):
                vm_name = self.VM_OS[0] + "_" + str(index)
                self._vm_provider_obj.destroy_vm(vm_name)
        except Exception as ex:
            raise RuntimeError("Unable to Destroy the VM")
        super(VmUpiLaneFailOverBaseTest, self).cleanup(return_status)
