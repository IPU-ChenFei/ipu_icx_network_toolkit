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


from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.dlb_driver_lib import DLBDriverLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class SDSI_DLB_Base_Class(ContentBaseTestCase):
    """
    Expectation is that DLB/HQM devices should works only after applying the HQM licenses.
    """
    #constants
    ROOT_FOLDER = "/"
    ENABLE = "0x1"
    EXPECTING_DLB_PCIE_DEVICE = True
    NOT_EXPECTING_DLB_PCIE_DEVICE = False
    DEF_HQM_PAYLOAD_NAME_TO_DISABLE = 'HQM0'

    hqm_payload_name_to_enable=""
    hqm_bios_name_list =[]
    dlb_pcie_device_ids_list = []


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OutOfBandDLBProvisionAndReturnToBaseFourDlbInst

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SDSI_DLB_Base_Class, self).__init__(test_log, arguments, cfg_opts)

        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)


    def Initialize(self, sdsicommonlibobj, hqm_payload_name, expected_dlb_pcie_devicelist, hqmbiosnamelist):
        """
        This method is using to initializing the basic components. It suppose to be called before the prepare

        :param sdsicommonlibobj: SDSI common lib function.
        :param hqm_payload_name:  HQM payload name to be apply
        :param expected_dlb_pcie_devicelist: expected dlb pci device list
        :param hqmbiosnamelist: you have to supply the Hqm bios names to be enable or disable.

        """

        self._sdsi_obj = sdsicommonlibobj
        self._dlb2_drv = DLBDriverLib(self._log, self.os, self._common_content_lib, self._common_content_configuration)
        self.hqm_payload_name_to_enable = hqm_payload_name
        self.hqm_bios_name_list = hqmbiosnamelist
        self.dlb_pcie_device_ids_list = expected_dlb_pcie_devicelist



    def prepare(self):
        # type: () -> None
        """preparing the setup"""

        self._log.debug("SDSI_DLB_Base_Class::prepare")
        super(SDSI_DLB_Base_Class, self).prepare()

        self._log.info("Verify the SPR_SDSi_Installer by initiating --help command.")
        self._sdsi_installer.verify_sdsi_installer()

        self._log.info("Verify the license key auth fail count and payload auth fail count is 0.")
        self._sdsi_obj.validate_default_registry_values()

        self._log.info("Clear any existing payloads from all sockets")
        self._sdsi_obj.erase_payloads_from_nvram()

        self._log.info("Make sure that DLB2 driver is ready for deployment")
        self._dlb2_drv.single_command_to_build_all_dlb_components()


    def _update_bios_settings_dino(self, new_bios_val ):
        """
        This method is using to update the HQM settings in the bios for each sockets

        """

        self._log.info("Updating HQM settings under DINO X Items.")
        for knobe_name in self.hqm_bios_name_list:
            self.bios_util.set_single_bios_knob(knobe_name, new_bios_val)


        return  True

    def _update_bios_settings_vtd(self, new_bios_val):
        """
        This method is using to updated VTD settings in the BIOS

        """

        self._log.info("Enabling 'VT-D' and 'InterruptRemap' in BIOS knobs")
        knobe_name = "VTdSupport"
        self.bios_util.set_single_bios_knob(knobe_name, new_bios_val)
        knobe_name = "InterruptRemap"
        self.bios_util.set_single_bios_knob(knobe_name, new_bios_val)

        return  True


    def _read_bios_settings_dino(self):
        """
        This method is using to read the  HQM Bios settings.

        """

        self._log.info("Read the current values of HQM settings under DINO X Items")
        for knobe_name in self.hqm_bios_name_list:
            val = self.bios_util.get_bios_knob_current_value(knobe_name)
            self._log.info("{} Status {}".format(knobe_name, val))

        return True


    def _verfiy_bios_settings_dino(self, expected_value):
        """
        This method is using to verify the HQM settings under DINO 0 & DINO 1 Items
        :param self:
        :param expected_value: passing the expected value as 0x01 or 0x0
        :return: True if the current bios knob values are matching with expected values
        """

        self._log.info("Verify the values of DINO X Item's -> HQM is set to {}".format(expected_value))
        for knobe_name in self.hqm_bios_name_list:
            val = self.bios_util.get_bios_knob_current_value(knobe_name)
            self._log.info("{} Status {}".format(knobe_name, val))
            assert val == expected_value, "{} BIOS settings are not updated in BIOS".format(knobe_name)

        return True


    def _query_dlb_pcie_device_status(self, exp_device_presense=False):
        """
        This method is using to query the pcie device list, check the status and cross verify with expected values.

        :param exp_device_presence: True means, the SUT should have dlb devices enumerated.
        :return: raise exception if the expected values are not matching with the current status of the devices.
                 otherwise returns True
        """

        for deviceid in  self.dlb_pcie_device_ids_list:
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


    def apply_HQM_Payload(self, socket, payload_name):
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



    def execute(self):
        """
            Test case steps.
            pre: apply license, clear NVRAM.
            #3  Update HqM bios settings
            #4 check SDsI installer is working(covered by initialization)
            #5 verifying any dlb devices enumerated without HQM licence
            #6  Removing the default dlb2 driver
            #7 Apply HQM payload licence
            #8 Enable VTD and Interrupt Mapping bios settings.
            #9 verifying all

        """
        self._log.info("Starting a cold reset - to check the CAP file updated properly.")
        self.perform_graceful_g3()

        #TC Step 4
        #NVRAM is cleared at the beginnig of the execution.
        self._log.info("#4 - Verify DLB PCIe peripheral devices are not present without DLB HQM License")
        self._query_dlb_pcie_device_status(self.NOT_EXPECTING_DLB_PCIE_DEVICE)

        #TC Step 5
        #dlb2 modules already build at initialization. Now need to remove the default dlb2 module.
        self._log.info("#5 - Unload previously loaded dlb2 driver")
        self._dlb2_drv.remove_dlb_driver()

        # TC Step 6
        self._log.info("#6 - Apply HQM payload to all sockets")
        for cpu_counter_index in range(self._sdsi_obj.number_of_cpu):
            self.apply_HQM_Payload(cpu_counter_index, self.hqm_payload_name_to_enable)

        self._log.info("Starting a cold reset - to check the CAP file updated properly.")
        self.perform_graceful_g3()


        #TC Step 7
        self._log.info("#7 - Read and update DINO X settings for each CPUs")
        self._log.info("Read current DINO X settings")
        self._read_bios_settings_dino()
        self._log.info("Update DIN X settings")
        self._update_bios_settings_dino(self.ENABLE)

        self._log.info("#Update VT-D settings")
        self._update_bios_settings_vtd(self.ENABLE)

        self._log.info("Starting a cold reset - to check the BIOS settings are updated properly.")
        self.perform_graceful_g3()

        #TC Step 8
        self._log.info("#8 - Verify DLB PCIe devices enumerated.")
        self._query_dlb_pcie_device_status(self.EXPECTING_DLB_PCIE_DEVICE)

        #TC 10
        self._log.info("#10 - Verify DLB driver loaded properly")
        if (self._dlb2_drv.is_dlb_driver_loaded() == True):
            self._log.info("dlb2 module is loaded, so unloading the dlb2 driver")
            self._dlb2_drv.remove_dlb_driver()

        self._dlb2_drv.install_dlb_driver()

        assert self._dlb2_drv.is_dlb_driver_loaded() == True, "DLB2 driver module is not loaded"
        assert self._dlb2_drv.verfify_any_device_is_running_using_a_module("dlb2") == True, "dlb2 is not using by any hardware"

        #TC 11
        self._log.info("#11 - run the ldb traffic")
        assert  self._dlb2_drv.run_ldlb_traffic_from_sample() == True, "lbd traffic failed"

        #TC 12
        self._log.info("#12 - Disable DLB by setting the HQM license 0")
        self._log.info(" - Apply HQM0 driver")
        for cpu_counter_index in range(self._sdsi_obj.number_of_cpu):
            payload_info = self._sdsi_obj.return_to_base(payload_name=self.DEF_HQM_PAYLOAD_NAME_TO_DISABLE, socket=cpu_counter_index)
            self._log.debug(payload_info)

        self._log.info("Starting a Cold reset - to check the CAP file updated properly.")
        self.perform_graceful_g3()

        #TC 13
        self._log.info("#13 - Verify DLB PCIe peripheral devices are not present without DLB HQM License")
        self._query_dlb_pcie_device_status(self.NOT_EXPECTING_DLB_PCIE_DEVICE)


        return True