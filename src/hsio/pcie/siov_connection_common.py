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
import time
import os


from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.provider.vm_provider import VMs
from src.provider.stressapp_provider import StressAppTestProvider


class SiovConnectionCommon(IoVirtualizationCommon):
    """
    This Class is Used as Common Class For all the Siov connection Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of SiovConnectionCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        if bios_config_file:
            bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), bios_config_file)
        super(SiovConnectionCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.VM = [VMs.RHEL]
        self.SUBNET_MASK = self._common_content_configuration.get_subnet_mask()
        self.GATEWAY_IP = self._common_content_configuration.get_gateway_ip()
        self.SUT_STATIC_IP = self._common_content_configuration.get_sut_static_ip()
        self.VM_STATIC_IP = self._common_content_configuration.get_vm_static_ip()
        self.IAVF_MODULE_NAME = "iavf"

    def prepare(self):  # type: () -> None
        """
        prepare
        1. enable iommu.
        2. create mdev.
        """
        super(SiovConnectionCommon, self).prepare()

        # Enabling Kernal and qemu-kvm file check
        self.enable_siov_kernel_options()
        if not self.is_qemu_kvm_installed():
            self.install_qemu_kvm()

        # Extract installed VM image
        self.vm_file_path = self.extract_installed_vm_image_linux(self.VM[0])
        self._log.info("VM image to be used for SIOv - {}".format(self.vm_file_path))

        # Setting up mdev for SIOV
        self.uuid = self.get_mdev_instance()

    def execute(self):
        """
        This method is to execute:

        1. attach SIOV to VM.
        2. check iavf interface in VM
        3. run Iperf traffic between sut and VM

        :return: True or False
        """
        # Attaching mdev to VM
        self.attach_and_launch_mdev_with_linux_vm(self.uuid, self.vm_file_path)

        # find iavf interface in VM
        vm_iavf_interface = self.find_interface_on_linux(self.vm_os_obj, self.IAVF_MODULE_NAME)[0]

        # Assigning static IPs to both interfaces on SUT and VM side
        self._log.info("Assigning static IP to mdev interface on SUT side - {}\niavf interface on VM side - {}  ".
                       format(self.mdev_index[0], vm_iavf_interface))
        self.assign_static_ip_to_vm(self.os, self.mdev_index[0], self.SUT_STATIC_IP,
                                    self.SUBNET_MASK, self.GATEWAY_IP)
        self.assign_static_ip_to_vm(self.vm_os_obj, vm_iavf_interface, self.VM_STATIC_IP,
                                    self.SUBNET_MASK, self.GATEWAY_IP)

        # checking if iavf interface on VM is getting pinged from SUT and vice-versa
        self._log.info("checking if iavf interface on VM is getting pinged from SUT and vice versa")
        if self.check_vm_ping_linux(self.vm_os_obj, self.VM[0], self.SUT_STATIC_IP):
            if self.check_vm_ping_linux(self.os, self.VM[0], self.VM_STATIC_IP):
                return True
        return False

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        2. Destroy mdev
        """
        try:
            self.virtualization_obj.vm_provider.destroy_vm(self.VM[0])
        except:
            self._log.info("Unable to Destroy the VM")
        self._log.info("deleting mdev created")
        self.os.execute(self.DELETE_MDEV_CMD, self._command_timeout)
        super(SiovConnectionCommon, self).cleanup(return_status)

    def enable_siov_kernel_options(self):
        """
        Enable kernel options: intel_iommu=on , sm_on
        Reboot

        :param None
        :return True/False
        """
        self._log.info("Enabling Kernel option on SUT - intel_iommu=on , sm_on")
        common_content_lib = self._common_content_lib
        if self.virtualization_obj.is_intel_iommu_enabled(common_content_lib):
            self._log.info("Intel IOMMU is already enabled by kernel")
            return True
        else:
            self._log.info("Enabling Intel IOMMU")
            self._log.info("Updating the grub config file")
            common_content_lib.update_kernel_args_and_reboot([self.SIOV_KERNEL_OPTIONS])
            self._log.info("Successfully enabled intel_iommu by kernel")
            return self.virtualization_obj.is_intel_iommu_enabled(common_content_lib)

    def get_mdev_instance(self):
        """
        This method will create mdev with a freshly generated UUID to the given interface and driver.

        :param None
        :Return UUID of mdev
        """
        self.mdev_index = self.find_siov_interface_on_sut()
        bus_id = self.os.execute((self.GET_BUSID_CMD.format(self.mdev_index[0]) + " | awk '/0000/{print $2}'"), self._command_timeout).stdout.strip()
        return self._vm_provider_obj.create_mdev_instance(mdev_bus_id=bus_id)

    def attach_and_launch_mdev_with_linux_vm(self, uuid, vm_file_path):
        """
        This method will attach the mdev instance created to the VM

        :param uuid: UUID of MDEV
        :param vm_file_path: Installed VM file path to attach with
        :return None
        """
        self._log.info("Attaching and spawning VM with SIOV...")
        self.os.execute_async(self.SIOV_WITH_VM_LAUNCH_CMD.format(uuid, vm_file_path), cwd="/root")
        time.sleep(self.WAIT_TIME_TO_SPAWN_VM_SEC)

    def run_iperf_and_verify_linux(self, server, client, os_type=None, sut_iperf_path=None, ip=None,
                                   tool_execution_time_seconds=21600, vm_name=None, bidirectional=False):
        """
        This method is to run iperf between a server and client, also verify it.

        :param server - server os object
        :param client - client os object
        :param os_type - OS type - "RHEl"
        :param sut_iperf_path - iperf tool folder path
        :param tool_execution_time_seconds - time delay in sec to run iperf
        :param vm_name - VM name
        :param bidirectional - for bidirectional
        """
        # starting server Iperf
        self._log.info("Starting Iperf as a server")
        self.run_iperf_as_server(server, os_type, sut_iperf_path, tool_execution_time_seconds, vm_name, bidirectional)

        # starting client Iperf
        self._log.info("Starting Iperf as a client")
        self.run_iperf_as_client(client, os_type, sut_iperf_path, ip, tool_execution_time_seconds, vm_name, bidirectional)

        stress_app = StressAppTestProvider.factory(self._log, self.cfg_opts, client)
        tool_execution_time_seconds -= self.TWO_MIN_IN_SEC
        while tool_execution_time_seconds > 0:
            if tool_execution_time_seconds/self.WAIT_TIME_IN_SEC == 0:
                if not stress_app.check_app_running(app_name="iperf3", stress_test_command="iperf3 -c"):
                    raise content_exceptions.TestFail("iperf3 (Client) is not running on Linux VM")

                self._log.info("Iperf3 is running on -{} VM as expected".format(vm_name))
            tool_execution_time_seconds -= 1
        time.sleep(self.TWO_MIN_IN_SEC)
        self._log.info("Iperf run successfully.....................")
