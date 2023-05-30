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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import sys
from typing import List

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.cbnt_constants import LinuxOsTypes
from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.dsa_driver_lib import DsaDriverUtility
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class OutofBandDSAFuncProvisionAndReturnToBase4DSAInstance(ContentBaseTestCase):
    """
    Glasgow_ID: 70166
    Phoenix_ID: 18014074619
    Expectation is that DSA devices should works only after applying the DSA4 licenses(except default devices)
    """
    #constants
    DSA_PAYLOAD_NAME = 'DSA4'
    DSA_ROOT_TO_BASE_PAYLOAD_NAME="DSA1"
    SOCKET_0 = 0
    SOCKET_1 = 1
    ROOT_FOLDER = "/"
    UPDATE_GRUB_CMDLINE_CENT0S = "intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_local=1 modprobe.blacklist=idxd_uacce"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OutofBandDSAFuncProvisionAndReturnToBase4DSAInstance

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super().__init__(test_log, arguments, cfg_opts)

        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)

        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power,
                                       cfg_opts)

        self.bIsCentOS = False
        if(self._sdsi_obj._os.os_subtype.upper() == LinuxOsTypes.CENTOS):
            self.bIsCentOS = True


    def prepare(self):
        # type: () -> None
        """preparing the setup"""

        super().prepare()

        #create an object of  DSADriverUtitlity class
        self.DsaDriverUtilityInst = DsaDriverUtility(self._log, self.os, self._common_content_lib,
                                                     self._common_content_configuration, self._cfg)

        self._log.info("Verify the SPR_SDSi_Installer by initiating --help command.")
        self._sdsi_installer.verify_sdsi_installer()

        self._log.info("Verify the license key auth fail count and payload auth fail count is 0.")
        self._sdsi_obj.validate_default_registry_values()

        self._log.info("Clear any existing payloads from all sockets")
        self._sdsi_obj.erase_payloads_from_nvram()

        self._log.info("Starting a cold reset.")
        self.perform_graceful_g3()
        # set date time to SUT
        self._common_content_lib.set_datetime_on_linux_sut()



    def _update_bios_settings_dino(self, bios_name_list: List[str], new_bios_val: str ) -> bool:
        """
        This method is using to update bios knob settings

        :param bios_name_list: list of the bios names to be update
        :param new_bios_val: new bios values it can be  0x01 or 0x00
        :return: True or False
        """

        self._log.info("Updating bios knob settings Items.")
        for knobe_name in bios_name_list:
            self.bios_util.set_single_bios_knob(knobe_name, new_bios_val)

        return  True


    def _enable_initial_bios_settings(self) -> None:
        """
        This method is using to update all initial bios settings

        """
        enable_bios_list = ['PcieEnqCmdSupport', 'ProcessorVmxEnable','OsNativeAerSupport','VTdSupport','InterruptRemap' ]
        enable_dsa_list_1 = ['DsaEn_0', 'DsaEn_1', 'DsaEn_2', 'DsaEn_3']
        enable_dsa_list_2 = ['DsaEn_4', 'DsaEn_5', 'DsaEn_6', 'DsaEn_7']

        self._log.info("Update the current values of DSA settings under DINO X Items")
        self._update_bios_settings_dino(enable_bios_list,"0x1")
        self._update_bios_settings_dino(enable_dsa_list_1, "0x1")
        if(self._sdsi_obj.number_of_cpu > 1):
            self._update_bios_settings_dino(enable_dsa_list_2, "0x1")

        return


    def _query_pcie_device_status(self, deviceid: str, exp_device_presense: bool = False) -> bool:
        """
        This method is using to query the pcie device list, check the status and cross verify with expected values.

        :param deviceid: this id is passing to the lspci -s command so the command should be in bus:device.func format
        :param exp_device_presence: True means, the device should be enumerated.
        :return: raise exception if the expected values are not matching with the current status of the devices.
                 otherwise returns True
        """

        command = "lspci -s " + deviceid
        #get all coprocessor details
        dlb_pci_response = self._sdsi_obj._os.execute(command, self._sdsi_obj.cmd_timeout,self.ROOT_FOLDER)
        if dlb_pci_response.cmd_failed():
            self._log.error(dlb_pci_response.stderr)

        dlb_pci_information = dlb_pci_response.stdout.strip()
        self._log.debug(dlb_pci_information)
        if(exp_device_presense == False):
            assert dlb_pci_information == '', "{} device is present in the SUT. It is not expected in a clean SUT".format(deviceid)
        else:
            if deviceid in dlb_pci_information:
                self._log.info("{} is present in the SUT".format(deviceid))
            else:
                log_error ="{} is not present in the SUT".format(deviceid)
                self._log.error(log_error)
                raise RuntimeError(log_error)

        return True


    def apply_Payload(self, socket, payload_name):
        """
        This method is using to apply the HQM payload to a socket.

        :param socket: socket number
        :param payload_name: payload name to be apply for a given socket
        :return: True if payload is applied successfully.
        """

        payload_info = self._sdsi_obj.get_capability_activation_payload(socket, payload_name)
        self._log.debug(payload_info)
        self._sdsi_obj.apply_capability_activation_payload(payload_info, socket)

        return True



    def verify_device_list_status(self, device_list: List[str], status: bool = False) -> None:
        """
        This method is using to check the status of the pcie device status.

        :param device_list: the device list should be in bus:device.function mode.
        :param status: expected status  means device should be present or not
        """

        for device_id in device_list:
            self._query_pcie_device_status(device_id,status)

    def run_accel_config_test(self) -> None:
        """
        This method is using to test the accel-config test to
        """
        command = "accel-config test"
        dlb_pci_response = self._sdsi_obj._os.execute(command, self._sdsi_obj.cmd_timeout, self.ROOT_FOLDER)
        if dlb_pci_response.cmd_failed():
            self._log.error(dlb_pci_response.stderr)

        dlb_pci_information = dlb_pci_response.stdout.strip()
        self._log.debug(dlb_pci_information)


    def execute(self):
        """
            Test case steps.
            pre: apply license, clear NVRAM.
            - Enable bios settings
            - check SDSI Installer is working
            - verify default dsa device lists
            - Install all dependency packages for DSA utility package
            - Verify the presence of idxd devices
            - apply DSA4 payload.
            - Verify all 8 dsa devices enumerated
            - Verify  idxd driver loaded to all new dsa devices
            - build and run the DSA utility package
            - Bring down DSA payload to base by applying DSA1 payload
            - Reverify the only default dsa devices are working.
        """
        # set date time to SUT
        self._common_content_lib.set_datetime_on_linux_sut()

        # TC 4 Enable BIOS settings
        self._log.info("#4 - Enable new bios settings")
        self._enable_initial_bios_settings()
        self._log.info("Starting a cold reset - to apply the new BIOS settings.")
        self.perform_graceful_g3()
        # set date time to SUT - SUT may have very old date & time
        self._common_content_lib.set_datetime_on_linux_sut()

        #TC 6 verify the status of the default dsa device lists.
        self._log.info("#6 - Verify default dsa devices are enumerated without DSA4 capability payload")
        dsa1_cpu0_expected_dsa_periperal_list = ['6a:01.0']
        dsa1_cpu1_expected_dsa_periperal_list = ['e7:01.0']
        self.verify_device_list_status(dsa1_cpu0_expected_dsa_periperal_list, True)
        if (self._sdsi_obj.number_of_cpu > 1):
            self.verify_device_list_status(dsa1_cpu1_expected_dsa_periperal_list, True)

        self._log.info("Verify non expected dsa devices are enumerated without DSA4 capability payload")
        dsa1_cpu0_non_expected_dsa_periperal_list = ['6f:01.0', '74:01.0', '79:01.0']
        dsa1_cpu1_non_expected_dsa_periperal_list = ['ec:01.0', 'f1:01.0', 'f6:01.0']
        self.verify_device_list_status(dsa1_cpu0_non_expected_dsa_periperal_list, False)
        if (self._sdsi_obj.number_of_cpu > 1):
            self.verify_device_list_status(dsa1_cpu1_non_expected_dsa_periperal_list, False)

        #TC 7 install SW dependencies.
        self._log.info("#7 - Install DSA utility build dependency packages.")
        self.DsaDriverUtilityInst.install_dependency_packages()

        #TC 9 Verify the DSA driver directory
        # Check DSA devices
        expected_dsa_devices=1
        if (self._sdsi_obj.number_of_cpu > 1):
            expected_dsa_devices  = 2
        self.DsaDriverUtilityInst.verify_dsa_driver_directory(expected_dsa_devices)
        #confirm dsa driver module is installed and present
        self.DsaDriverUtilityInst.check_idxd_device()


        #TC 10 Install DSA 4 capability.
        self._log.info("#10 - Apply DSA4 payload on CPU 0 and start cold reboot")
        self.apply_Payload(self.SOCKET_0, self.DSA_PAYLOAD_NAME)
        if (self._sdsi_obj.number_of_cpu > 1):
            self.apply_Payload(self.SOCKET_1, self.DSA_PAYLOAD_NAME)
        self._log.info("Starting a cold reset - to check the CAP file updated properly.")
        self.perform_graceful_g3()
        # set date time to SUT
        self._common_content_lib.set_datetime_on_linux_sut()


        #TC 11 Verify DSA devices are numerated.
        self._log.info("#11 - Verify dsa devices are enumerated with the capability payload")
        dsa4_cpu0_expected_dsa_periperal_list = ['6a:01.0', '6f:01.0', '74:01.0', '79:01.0']
        dsa4_cpu1_expected_dsa_periperal_list = ['e7:01.0', 'ec:01.0', 'f1:01.0', 'f6:01.0']
        self.verify_device_list_status(dsa4_cpu0_expected_dsa_periperal_list, True)
        if (self._sdsi_obj.number_of_cpu > 1):
            self.verify_device_list_status(dsa4_cpu1_expected_dsa_periperal_list, True)

        # TC 12 install SW dependencies.
        self._log.info("#12 - Update grub commandlines in CentOS")
        if (self.bIsCentOS == True):
            retval, isRebootrequired = self.DsaDriverUtilityInst._update_grub_cmd_line_linux(self.bIsCentOS, self.UPDATE_GRUB_CMDLINE_CENT0S)
            if (isRebootrequired == 1):
                self._log.info("Starting a cold reset - to check new environment settings.")
                self.perform_graceful_g3()
                # set date time to SUT
                self._common_content_lib.set_datetime_on_linux_sut()

        #TC 13  determine the devices state.
        self._log.info("#13 - determine the devices state")
        self.DsaDriverUtilityInst.driver_basic_check()

        #TC 14  Install accel config tool
        self._log.info("#14 - build and install and test dsa driver utility package")
        retval = self.DsaDriverUtilityInst.build_and_run_accel_config_test()
        self.run_accel_config_test()

        #TC 15 Restore to DSA1 payload license
        self._log.info("#15 - Apply DSA1 payload on sockets and start cold reboot")
        payload_info = self._sdsi_obj.return_to_base(payload_name=self.DSA_ROOT_TO_BASE_PAYLOAD_NAME, socket=self.SOCKET_0)
        self._log.debug(payload_info)
        if (self._sdsi_obj.number_of_cpu > 1):
            payload_info = self._sdsi_obj.return_to_base(payload_name=self.DSA_ROOT_TO_BASE_PAYLOAD_NAME, socket=self.SOCKET_1)
            self._log.debug(payload_info)

        self._log.info("Starting a cold reset - to check the CAP file updated properly.")
        self.perform_graceful_g3()
        # set date time to SUT
        self._common_content_lib.set_datetime_on_linux_sut()


        #TC 16 Verify DSA1 default devices enumerated
        self._log.info("#16 - Verify default dsa devices are enumerated with default capability payload")
        dsa1_cpu0_expected_dsa_periperal_list = ['6a:01.0']
        dsa1_cpu1_expected_dsa_periperal_list = ['e7:01.0']
        self.verify_device_list_status(dsa1_cpu0_expected_dsa_periperal_list, True)
        if (self._sdsi_obj.number_of_cpu > 1):
            self.verify_device_list_status(dsa1_cpu1_expected_dsa_periperal_list, True)

        self._log.info("Verify non expected dsa devices are enumerated without DSA4 capability payload")
        dsa1_cpu0_non_expected_dsa_periperal_list = ['6f:01.0', '74:01.0', '79:01.0']
        dsa1_cpu1_non_expected_dsa_periperal_list = ['ec:01.0', 'f1:01.0', 'f6:01.0']
        self.verify_device_list_status(dsa1_cpu0_non_expected_dsa_periperal_list, False)
        if (self._sdsi_obj.number_of_cpu > 1):
            self.verify_device_list_status(dsa1_cpu1_non_expected_dsa_periperal_list, False)


        #TC 17 determine device state
        self._log.info("#17 - determine default device states")
        self.DsaDriverUtilityInst.driver_basic_check()

        return True


    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        # set date time to SUT
        self._common_content_lib.set_datetime_on_linux_sut()
        super().cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutofBandDSAFuncProvisionAndReturnToBase4DSAInstance.main()
             else Framework.TEST_RESULT_FAIL)