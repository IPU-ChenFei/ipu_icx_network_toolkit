#!/usr/bin/env python
###############################################################################
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
###############################################################################
import os
import re

from montana.nativemodules import getdeviceid

from src.lib.common_content_lib import CommonContentLib


class GetDeviceId(object):
    """
    This Class is Used to Get the Details of the Device and verify if the device is in Operational Mode.
    """
    _MIV_LOG_FILE = "MEpythonlog.csv"
    _REGEX_FOR_DEVICE_ID = r".*montana.base.utilities.{3}Device\sID.*"
    _REGEX_FOR_REGION_NAME = r".*montana.base.utilities.{3}Region\sName.*"
    _REGEX_FOR_FIRMWARE_VERSION = r".*montana.base.utilities.{3}Firmware\sVersion.*"
    _REGEX_FOR_DEVICE_REVISION = r".*montana.base.utilities.{3}Device\sRevision.*"
    _REGEX_FOR_IPMI_VERSION = r".*montana.base.utilities.{3}IPMI\sVersion.*"
    _REGEX_FOR_ADDITIONAL_DEVICE_SUPPORT = r".*montana.base.utilities.{3}Additional\sDevice\sSupport.*"
    _REGEX_FOR_PLATFORM = r".*montana.base.utilities.{3}Platform.*"
    _KEY_DEVICE_ID = "device_id"
    _KEY_REGION_NAME = "region_name"
    _KEY_FIRMWARE_VERSION = "firmware_version"
    _KEY_IPMI_VERSION = "ipmi_version"
    _KEY_PLATFORM = "platform"
    _KEY_DEVICE_REVISION = "device_revision"
    _KEY_ADDITIONAL_DEVICE_SUPPORT = "additional_device_support"
    OPERATIONAL_MODE = "Operational Mode"
    RECOVERY_MODE = "Recovery Mode"
    MAINTENANCE_MODE = "Maintenance Mode"

    def __init__(self, log, montana_log_path, os_obj):
        """
        Creates an Instance of GetDeviceId

        :param log: log_object
        :param montana_log_path: montana_log_file path available in log_dir of TC.
        :param os_obj: Os object for all OS related Operations.
        """
        self._log = log
        self.dtaf_montana_log_path = montana_log_path
        self._os = os_obj
        self.get_dev_id_obj = getdeviceid.getdeviceid()
        self._common_content_lib = CommonContentLib(self._log, self._os, None)
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.miv_log_file = os.path.join(self.cwd, self._MIV_LOG_FILE)
        self.device_details_dict = {}
        self._populate_device_data()

    def _populate_device_data(self):
        """
        This Method is Used to get the Device Details from Montana.
        """
        if os.path.isfile(self.miv_log_file):
            os.remove(self.miv_log_file)
        self._common_content_lib.execute_cmd_on_host("python {}".format(getdeviceid.__file__), cwd=self.cwd)
        with open(self.miv_log_file, "r") as log_file:
            log_file_list = log_file.readlines()
            with open(self.dtaf_montana_log_path, "a") as montana_log:
                montana_log.write("".join(log_file_list))
            device_id_string = re.compile(self._REGEX_FOR_DEVICE_ID)
            device_id_value = device_id_string.search("".join(log_file_list)).group().split("|")[2].strip()
            self.device_details_dict[self._KEY_DEVICE_ID] = device_id_value
            region_name_string = re.compile(self._REGEX_FOR_REGION_NAME)
            region_name_value = region_name_string.search("".join(log_file_list)).group().split("|")[2].strip()
            self.device_details_dict[self._KEY_REGION_NAME] = region_name_value
            firmware_version_string = re.compile(self._REGEX_FOR_FIRMWARE_VERSION)
            firmware_version_value = \
                firmware_version_string.search("".join(log_file_list)).group().split("|")[2].strip()
            self.device_details_dict[self._KEY_FIRMWARE_VERSION] = firmware_version_value
            device_revision_string = re.compile(self._REGEX_FOR_DEVICE_REVISION)
            device_revision_value = device_revision_string.search("".join(log_file_list)).group().split("|")[
                2].strip()
            self.device_details_dict[self._KEY_DEVICE_REVISION] = device_revision_value
            ipmi_version_string = re.compile(self._REGEX_FOR_IPMI_VERSION)
            ipmi_version_value = ipmi_version_string.search("".join(log_file_list)).group().split("|")[2].strip()
            self.device_details_dict[self._KEY_IPMI_VERSION] = ipmi_version_value
            addl_device_supp_string = re.compile(self._REGEX_FOR_ADDITIONAL_DEVICE_SUPPORT)
            addl_device_supp_value = \
                addl_device_supp_string.search("".join(log_file_list)).group().split("|")[2].strip()
            self.device_details_dict[self._KEY_ADDITIONAL_DEVICE_SUPPORT] = addl_device_supp_value
            platform_string = re.compile(self._REGEX_FOR_PLATFORM)
            platform_value = platform_string.search("".join(log_file_list)).group().split("|")[2].strip()
            self.device_details_dict[self._KEY_PLATFORM] = platform_value

    def repopulate_device_data(self):
        """
        This Method is Used to Repopulate the Device Data
        """
        self._log.info("Populate Device Data")
        self._populate_device_data()

    def get_device_id(self):
        """
        This Method is used to Get the Device Id from device details.
        """
        self._log.info("Device Id is '{}'".format(self.device_details_dict[self._KEY_DEVICE_ID]))
        return self.device_details_dict[self._KEY_DEVICE_ID]

    def get_region_name(self):
        """
        This Method is Used to Get the Region Name of the Device.
        """
        self._log.info("Region Name is '{}'".format(self.device_details_dict[self._KEY_REGION_NAME]))
        if self.device_details_dict[self._KEY_REGION_NAME] == BmcMode.OPERATIONAL_MODE_IMAGE1 or \
                self.device_details_dict[self._KEY_REGION_NAME] == BmcMode.OPERATIONAL_MODE_IMAGE2:
            return self.OPERATIONAL_MODE
        elif self.device_details_dict[self._KEY_REGION_NAME] == BmcMode.RECOVERY_MODE:
            return self.RECOVERY_MODE
        elif self.device_details_dict[self._KEY_REGION_NAME] == BmcMode.MAINTENANCE_MODE:
            return self.MAINTENANCE_MODE
        else:
            return self.device_details_dict[self._KEY_REGION_NAME]

    def get_ipmi_version(self):
        """
        This Method is Used to Get the Ipmi Version of the Device.
        """
        self._log.info("Ipmi Version is '{}'".format(self.device_details_dict[self._KEY_IPMI_VERSION]))
        return self.device_details_dict[self._KEY_IPMI_VERSION]

    def get_firmware_version(self):
        """
        This Method is Used to Get the Firmware Version of the Device.
        """
        self._log.info("Firmware Version is '{}'".format(self.device_details_dict[self._KEY_FIRMWARE_VERSION]))
        return self.device_details_dict[self._KEY_FIRMWARE_VERSION]

    def get_device_revision(self):
        """
        This Method is Used to Get the Device Revision Value of the Device.
        """
        self._log.info("Device Revision Value is '{}'".format(self.device_details_dict[self._KEY_DEVICE_REVISION]))
        return self.device_details_dict[self._KEY_DEVICE_REVISION]

    def get_additional_device_support(self):
        """
        This Method is Used to Get the Additional Device Support Value of the Device.
        """
        self._log.info("Additional Device Support Value is '{}'".
                       format(self.device_details_dict[self._KEY_ADDITIONAL_DEVICE_SUPPORT]))
        return self.device_details_dict[self._KEY_ADDITIONAL_DEVICE_SUPPORT]

    def get_platform(self):
        """
        This Method is Used to Get the Platform of the Device.
        """
        self._log.info("Platform is '{}'".format(self.device_details_dict[self._KEY_PLATFORM]))
        return self.device_details_dict[self._KEY_PLATFORM]


class BmcMode(object):
    """
    This Class is used to define BMC Constants
    """
    OPERATIONAL_MODE_IMAGE1 = r"NM Operational Mode [image1]"
    OPERATIONAL_MODE_IMAGE2 = r"NM Operational Mode [image2]"
    RECOVERY_MODE = r"NM recovery Mode"
    MAINTENANCE_MODE = r"NM Maintenance Mode"
