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

import zipfile

from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.driver_provider import DriverProvider, NetworkDrivers
from src.provider.network_provider import NetworkProvider
from src.power_management.lib.reset_base_test import ResetBaseTest
from src.lib.install_collateral import InstallCollateral
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.provider.host_usb_drive_provider import HostUsbDriveProvider


class NetworkingCommon(ContentBaseTestCase):
    """
    Base class extension for NetworkingCommon which holds common functionality
    """
    WAITING_TIME_IN_SEC = 30

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of NetworkingCommon.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(NetworkingCommon, self).__init__(test_log, arguments, cfg_opts)
        self.network_provider = NetworkProvider.factory(test_log, cfg_opts, self.os)
        self.driver_provider = DriverProvider.factory(self._log, cfg_opts, self.os)  # type: DriverProvider
        self.sut_ip = self.network_provider.get_sut_ip()
        self._command_timeout = 30
        self.reset_base_test = ResetBaseTest(self._log, arguments, cfg_opts)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.driver_provider.copy_driver_files(self.phy)
        self.foxville_inf_file = self._common_content_configuration.get_driver_inf_file_name(
            NetworkDrivers.FOXVILLE_DRIVER_NAME)
        self.foxville_device_id = self._common_content_configuration.get_driver_device_id(
            NetworkDrivers.FOXVILLE_DRIVER_NAME)
        self.sut1_ip = self._common_content_configuration.get_sut1_ip()
        self.sut2_ip = self._common_content_configuration.get_sut2_ip()
        self.cfg_opts = cfg_opts
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, cfg_opts)
        self._host_usb_provider = HostUsbDriveProvider.factory(test_log, cfg_opts,self.os)
        self.usb_set_time = self._common_content_configuration.get_usb_set_time_delay()

    def assign_static_ip(self, device_name):
        """
        This Method is used to assign Static IP's for the Card's which uses SFP LOOP Back Cable.

        :param device_name: Device Name
        :return interface,ip_address: Adapter Interface and static ip address.
        """
        if device_name in NetworkDrivers.SFP_LOOPBACK:
            self._log.info("Assigning Static Ip's to {} Network Driver Interfaces"
                           .format(device_name))
            network_interface_dict = self.network_provider.get_network_adapter_interfaces(assign_static_ip=True)
            interface = list(network_interface_dict.keys())[0]
            ip_address = network_interface_dict[interface]
            self._log.debug("Assigned {} Ip Address to {} Network Driver Interface {}"
                            .format(ip_address, device_name, interface))
            return interface, ip_address

    def copy_columbiaville_files(self, phy):
        """
        Copy the  zip files from Artifctory  to USB drive.
        :param phy: physical control provider object
        :param file_name: File name to copy
        :param host_usb_provider: Host usb provider object
        """
        self._log.info("Copying network driver file to sut")
        artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.INTEL_LAN_V26_4]
        driver_source_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        usb_drive = self._host_usb_provider.get_hotplugged_usb_drive(phy)
        self._log.debug("Hot-plugged USB drive='{}'".format(usb_drive))
        self._host_usb_provider.format_drive(usb_drive)
        self._log.debug("USB disconnecting")
        phy.disconnect_usb(self.usb_set_time)
        self._log.debug("USB connecting to HOST")
        phy.connect_usb_to_host(self.usb_set_time)
        self._log.debug("Copying Network Driver zip file to sut")
        with zipfile.ZipFile(driver_source_path.strip(), 'r') as zip:
            zip.extractall(usb_drive, )
        self._log.debug("USB disconnecting")
        phy.disconnect_usb(self.usb_set_time)
        self._log.debug("USB connecting to SUT")
        phy.connect_usb_to_sut(self.usb_set_time)
        self._log.info("Network files copied successfully")

