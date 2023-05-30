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

import re
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.storage.test.storage_common import StorageCommon
from src.provider.storage_provider import StorageProvider
from src.lib.test_content_logger import TestContentLogger
from src.environment.os_installation import OsInstallation
from src.lib.bios_util import PlatformConfigReader, ItpXmlCli
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import SutInventoryConstants


class StorageBootingToNvme(BaseTestCase):
    """
    PHOENIX ID : 16013540014 - PCieSSD-VMD enable - OS Install to PCie NvMe in VMD enable no raid Mode and NVME
    driver installation check (RHEL)
    """
    TEST_CASE_ID = ["16013540014",
                    "Storage_PCIe_SSD_VMD_E_OS_Installation_RHEL",
                    "PCieSSD-VMD enable - OS Install to PCie NvMe in VMD enable no raid Mode and NVME driver"
                    "installation check (RHEL)"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Check in boot manager menu if all the pcie nvme are getting detected',
            'expected_results': 'Check if all pcie nvme are detected at bios level.'},
        2: {'step_details': 'enable the VMD for respective ports',
            'expected_results': 'All the respective ports vmd should be enabled'},
        3: {'step_details': 'make any of the pcie nvme as the first  boot device',
            'expected_results': 'Make the first boot order as pcie nvme'},
        4: {'step_details': 'install os on pcie device',
            'expected_results': 'The rhel OS should get installed properly on the pcie nvme'}}

    NVME_SSD_NAME_RHEL = "nvme_ssd_name_rhel"
    MODEL_NUMBER_REGEX_PATTERN = r"Model Number[^A-Za-z0-9]*(\S+\s\S+)"
    SERIAL_NUMBER_REGEX_PATTERN = r"Serial Number[^A-Za-z0-9]*(\S+)"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToNvme object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        self._cc_log_path = arguments.outputpath

        super(StorageBootingToNvme, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.itp_xmlcli = ItpXmlCli(self._log, self._cfg)        
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self._storage_provider = StorageProvider.factory(self._log, os, self._cfg_opts, "os")
        self.storage_common_obj = StorageCommon(self._log, arguments, cfg_opts)
        self._common_content_lib = CommonContentLib(self._log, os, None)
        self.name_ssd = None
        self.log_dir = None

    @classmethod
    def add_arguments(cls, parser):
        super(StorageBootingToNvme, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        self._test_content_logger.start_step_logger(1)

        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        self.name_ssd = None
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if self.NVME_SSD_NAME_RHEL in line:
                    self.name_ssd = line
                    break

        if not self.name_ssd:
            raise content_exceptions.TestError("Unable to find ssd name, please check the file under "
                                               "{}".format(sut_inv_file_path))

        self.name_ssd = self.name_ssd.split("=")[1]

        self._log.info("NVME SSD Name from config file : {}".format(self.name_ssd))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.NVME, SutInventoryConstants.RHEL)

    def execute(self):

        itp_xmlcli = ItpXmlCli(self._log, self._cfg)
        self._sdp.halt()
        self.platform_config_read = PlatformConfigReader(itp_xmlcli.get_platform_config_file_path(),
                                                         test_log=self._log)
        self._sdp.go()
        #  Gets Platform Config file path
        platform_config_path = itp_xmlcli.get_platform_config_file_path()
        self._log.info("Platform Config file path:{}".format(platform_config_path))

        # Store commented line information from Platform Config file in a variable.
        platform_config_commented_info = self.platform_config_read.get_commented_info()
        self._log.debug("Commented information from platform config file:\n {}".format(platform_config_commented_info))
        # PCIe card interface details which is connected to PCIe slot's
        self._log.info("PCIe NVMe card information: {}".
                       format(self._common_content_configuration.get_nvme_cards_info()))
        verified_nvme_cards = set()

        # Checks for all PCIe card interface details in platform config file commented data.
        for each_slot in self._common_content_configuration.get_nvme_cards_info():
            for each_line in platform_config_commented_info.split("\n"):
                if each_slot in each_line:
                    verified_nvme_cards.add(each_slot)

        self._log.debug("successfully verified these bios knobs is: {}".format(verified_nvme_cards))

        # collect drive model numbers and serial numbers from scraping platform config xml
        model_number = re.findall(self.MODEL_NUMBER_REGEX_PATTERN, platform_config_commented_info)
        serial_number = re.findall(self.SERIAL_NUMBER_REGEX_PATTERN, platform_config_commented_info)

        serial_number = [num for num in serial_number if str(num) != 'N/A']

        self._log.debug("Model and Serial Numbers of NVMe cards:\nModel numbers:{}\n"
                        "Serial Numbers:{}".format(model_number, serial_number))
        # verify pcie ssd models and serial number detected in sut with content config file
        if len(model_number) != len(self._common_content_configuration.get_nvme_cards_info()) and \
                len(serial_number) != len(self._common_content_configuration.get_nvme_cards_info()):
            raise content_exceptions.TestFail("Few Model and Serial Numbers are incorrect\nModel numbers:{}\n"
                                              "Serial Numbers:{}".format(model_number, serial_number))

        self._log.info("successfully verified NVMe cards details")
        self._test_content_logger.end_step_logger(1, return_val=True)

        # setting boot order in bios is internally taken care by os installation method in step 3
        self._test_content_logger.start_step_logger(2)
        self._log.info("enable the VMD for respective ports")
        self.storage_common_obj.enable_vmd_bios_knobs()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        # os installation initiated
        ret_val = [self._os_installation_lib.rhel_os_installation()]
        self.log_dir = self._common_content_lib.get_log_file_dir()

        # confirm OS installation by getting booted device
        lsblk_res = self._storage_provider.get_booted_device()
        self._log.info("booted device is {}".format(str(lsblk_res)))

        if SutInventoryConstants.NVME not in lsblk_res:
            raise content_exceptions.TestFail("OS not installed on the NVME SSD, please try again..")

        self._log.info("Successfully verified that OS installed in NVME device..")
        self._test_content_logger.end_step_logger(3, return_val=True)
        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageBootingToNvme, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToNvme.main() else Framework.TEST_RESULT_FAIL)
