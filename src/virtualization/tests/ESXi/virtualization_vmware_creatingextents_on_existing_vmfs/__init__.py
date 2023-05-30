import os
import sys
import time
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from pathlib import Path
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.provider.mlc_provider import MlcProvider
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class virtualizationvmwarecreatingextentsonexistingvmfs(VirtualizationCommon):
    """
       Phoenix ID: 18014072666

        1. Create new datastore using any disk given in the config file
        2. Get the partition,sector and usable disk information from the disks
        3. Use parted resize command and resize the disk partition and extend the datastore
        4. Check if extend datastore is successfull.
       """

    VM = [VMs.RHEL]
    VM_TYPE = "RHEL"
    DATASTORE_NAME = "data-pdp"
    DEFAULT_DIRECTORY_ESXI = "/vmfs/volumes/datastore1"

    TEST_CASE_ID = ["P18014072666", "virtualizationvmwarecreatingextentsonexistingvmfs"]
    STEP_DATA_DICT = {
        1: {'step_details':  "Create new datastore using any disk given in the config file",
            'expected_results': "Creation of datastore should be successful"},
        2: {'step_details': " Get the partition,sector and usable disk information from the disks",
            'expected_results': "Should be successfull"},
        3: {'step_details': "Use parted resize command and resize the disk partition and extend the datastore.",
            'expected_results': "Get details should be successfull"},
        4: {'step_details': "Extend the datastore and validate",
            'expected_results': "Should be successfull"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new virtualizationvmwarecreatingextentsonexistingvmfs object.
        """
        super(virtualizationstoragemigration, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)


    def prepare(self):
        # Need to implement bios configuration for ESXi SUT
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type != OperatingSystems.ESXI:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._log.info("VMWare ESXi SUT detected for the testcase")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Create new datastore using any disk given in the config file
        2. Get the partition,sector and usable disk information from the disks
        3. Use parted resize command and resize the disk partition and extend the datastore
        4. Check if extend datastore is successfull.
        """
        self._test_content_logger.start_step_logger(1)

      #  disk_name_esxi = self._common_content_configuration.get_disk_esxi()
      #  self.create_datastore(self.DATASTORE_NAME, disk_name_esxi)
        cmd = "vmkfstools -P /vmfs/volumes/{} | grep 't10'"
        output = self._common_content_lib.execute_sut_cmd(cmd.format(self.DATASTORE_NAME), "get the disk of datastore",
                                                          self._command_timeout,self.DEFAULT_DIRECTORY_ESXI)
        disk_name = output.split(':')[0].replace(' ','').strip()
        self._log.info("disk_name of datastore is {} ".format(disk_name))

        parted_cmd = "partedUtil get /vmfs/devices/disks/{} | cut -d' ' -f1"
        print(parted_cmd.format(disk_name))
        output = self._common_content_lib.execute_sut_cmd(parted_cmd.format(disk_name), "get parted details of disk",
                                                          self._command_timeout, self.DEFAULT_DIRECTORY_ESXI)

        partition_number = output.replace("\n", ",")[-2]
        self._log.info("partition number is {} ".format(partition_number))

        starting_sector_cmd = "partedUtil get /vmfs/devices/disks/{} | cut -d' ' -f2"
        output = self._common_content_lib.execute_sut_cmd(starting_sector_cmd.format(disk_name), "get starting sector of disk",
                                                          self._command_timeout, self.DEFAULT_DIRECTORY_ESXI)

        starting_sector = output.replace("\n", " ").replace(" ",',') .split(",")[-2]
        self._log.info("starting_sector number is {} ".format(starting_sector))

        get_usable_disk_cmd = "partedUtil  getUsableSectors /vmfs/devices/disks/{}"
        output = self._common_content_lib.execute_sut_cmd(get_usable_disk_cmd.format(disk_name),
                                                          "get the usable disk of datastore",
                                                          self._command_timeout, self.DEFAULT_DIRECTORY_ESXI)

        end = output.split(" ")[1]
        self._log.info("end sector is {} ".format(end))
        resize_cmd = "partedUtil  resize /vmfs/devices/disks/{} {} {} {}"
        output = self._common_content_lib.execute_sut_cmd(resize_cmd.format(disk_name,partition_number,starting_sector,end),
                                                          "Resize disk of datastore",
                                                          self._command_timeout, self.DEFAULT_DIRECTORY_ESXI)
        growfs = "vmkfstools --growfs /vmfs/devices/disks/{}:{} /vmfs/devices/disks/{}:{}"
        output1 = self._common_content_lib.execute_sut_cmd(growfs.format(disk_name, partition_number, disk_name,partition_number),
                                                          "extend the datastore",
                                                          self._command_timeout, self.DEFAULT_DIRECTORY_ESXI)


    def cleanup(self, return_status):
        super(virtualizationvmwarecreatingextentsonexistingvmfs, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if virtualizationvmwarecreatingextentsonexistingvmfs.main()
             else Framework.TEST_RESULT_FAIL)