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

from dtaf_core.lib.dtaf_constants import Framework

from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions


class PiVirtualizationRhelKvmVmSnapshotting(VirtualizationCommon):
    """
    HPALM ID: 80289
    HPALM TITLE: Pi_Virtualization_Rhel_Kvm_Vm_Snapshotting
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Create VM.
    2. Create a test file in the VM.
    3. Take snapshot of the VM.
    4. Delete the test file in VM.
    5. Verify it.
    6. Then restore the snapshot of the VM.
    7. Verify that the test file is present in the VM after restoring the snapshot.
    """
    VM = [VMs.RHEL]
    VM_NAME = None
    SNAPSHOT_NAME = None
    TEST_FILE_CONTENT = "This is a Test File"
    TEST_FILE_NAME = "test.txt"
    TEST_CASE_ID = ["H80289", "Pi_Virtualization_Rhel_Kvm_Vm_Snapshotting"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationRhelKvmVmSnapshotting object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiVirtualizationRhelKvmVmSnapshotting, self).__init__(test_log, arguments, cfg_opts)

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        3. Take snapshot of the VM.
        4. Delete the test file in VM.
        5. Verify it.
        6. Then restore the snapshot of the VM.
        7. Verify that the test file is present in the VM after restoring the snapshot.

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            self.VM_NAME = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(self.VM_NAME)
            self.create_vm(self.VM_NAME, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(self.VM_NAME, self.VM[index])
            # creating a testfile on VM
            vm_os_obj = self.create_vm_host(self.VM_NAME, self.VM[index])
            test_cmd_opt_obj = vm_os_obj.execute("echo '{}' >>/root/{}".format(self.TEST_FILE_CONTENT,
                                                                               self.TEST_FILE_NAME), 100)
            self._log.debug("stdout of testfile create command:\n {}".format(test_cmd_opt_obj.stdout))
            self._log.error("stderr of testfile create command:\n {}".format(test_cmd_opt_obj.stderr))
            # create the snapshot
            self.SNAPSHOT_NAME = self.VM_NAME + "_SNP"
            self.create_snapshot_of_linux_vm(self.VM_NAME, self.SNAPSHOT_NAME)
            # delete the testfile
            delete_cmd_obj = vm_os_obj.execute("rm -rf /root/{}".format(self.TEST_FILE_NAME), 100)
            self._log.debug("stdout of testfile create command:\n {}".format(delete_cmd_obj.stdout))
            self._log.error("stderr of testfile create command:\n {}".format(delete_cmd_obj.stderr))
            # verify the file is actually removed or not
            verify_file_present_obj = vm_os_obj.execute("ls", 60, cwd="/root")
            if self.TEST_FILE_NAME in verify_file_present_obj.stdout:
                raise content_exceptions.TestFail("Failed to remove the test file from VM")
            self._log.info("Successfully removed the Test file")

            # retrieve the snapshot
            self.restore_snapshot_of_linux_vm(self.VM_NAME, self.SNAPSHOT_NAME)

            # verify file is present
            self._log.info("verifying Test file presence in the VM after restoring the snapshot")
            if not vm_os_obj.check_if_path_exists("/root/{}".format(self.TEST_FILE_NAME)):
                raise content_exceptions.TestFail("Test File is not present in VM after restoring the snapshot")
            self._log.info("Successfully verified the Test File presence in the VM after restoring the snapshot")

            # verify file content
            file_content_obj = vm_os_obj.execute("cat /root/{}".format(self.TEST_FILE_NAME), 60)
            self._log.debug("stdout of file content:\n{}".format(file_content_obj.stdout))
            self._log.error("stderr of file content:\n{}".format(file_content_obj.stderr))
            if self.TEST_FILE_CONTENT not in file_content_obj.stdout:
                raise content_exceptions.TestFail("Test File content is not matching after restoring the snapshot")
            self._log.info("Test File content also matched after restoring the snapshot")

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        self.delete_snapshot_of_linux_vm(self.VM_NAME, self.SNAPSHOT_NAME)
        super(PiVirtualizationRhelKvmVmSnapshotting, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationRhelKvmVmSnapshotting.main()
             else Framework.TEST_RESULT_FAIL)
