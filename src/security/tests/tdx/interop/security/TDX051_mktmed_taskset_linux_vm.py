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
"""
    :MKTME-D Taskset TD guest testing:

    With MKKTME-D enabled, launch multiple TDVMs and move between sockets.
"""

import sys
import random

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdvm.TDX050_launch_multiple_tdvm_linux import MultipleTDVMLaunch
from src.security.tests.tdx.workloads.TDX049_launch_tdvm_mprime import TDGuestMprime


class MktmeDTdGuestTaskset(TDGuestMprime):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guests.  This recipe will only
            work for Linux OSs due to the use of taskset to move process affinity between logical CPUs.

            :Scenario: Enable Directory Mode and launch multiple TD guests.  Move TD guests between sockets with
            taskset and verify there are no MCEs.

            The number of TD guests launched is configured by the <TDX><NUMBER_OF_VMS> value defined in
            content_configuration.xml.

            :Phoenix IDs: 22012591811

            :Test steps:

                :1:  Enable Directory Mode.

                :2:  Launch multiple TD guests assigned to specific sockets.

                :3:  Run mprime on each TD guest.

                :4:  Move each TD guest to logical CPUs on alternate socket.

            :Expected results: TD guests should all boot, movement between logical CPUs should not yield MCEs.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(MktmeDTdGuestTaskset, self).__init__(test_log, arguments, cfg_opts)
        self._available_nodes = {}
        self._node_mapping = {}
        self.num_sockets = 0
        self.launch_vms = MultipleTDVMLaunch(test_log, arguments, cfg_opts)
        self.MIN_NUM_VMS = 10
        if self.launch_vms.tdx_properties[self.tdx_consts.NUMBER_OF_VMS] < self.MIN_NUM_VMS:
            self._log.warning(f"Minimum number of VMs set in content_configuration is too low "
                              f"{self.launch_vms.tdx_properties[self.tdx_consts.NUMBER_OF_VMS]} vs required "
                              f"{self.MIN_NUM_VMS}.  Setting number of VMs to boot to {self.MIN_NUM_VMS}.")
            self.launch_vms.tdx_properties[self.tdx_consts.NUMBER_OF_VMS] = self.MIN_NUM_VMS
        self.SHIFT_CYCLES = 20

    def prepare(self):
        if self.get_sockets() < 2:
            raise content_exceptions.TestSetupError("System does not have enough sockets for the test.  This test "
                                                    "requires at least two sockets on the system.")
        self.tdx_properties[self.tdx_consts.DIRECTORY_MODE] = True  # directory mode must be enabled
        super(MktmeDTdGuestTaskset, self).prepare()
        self._log.info("Checking taskset is installed on SUT.")
        self.install_collateral.yum_install("util-linux")
        # creating small vms, overriding config vm core count
        self.tdx_properties[self.tdx_consts.TD_GUEST_CORES] = 1
        self.stage_numa_tracking()
        random.seed()
        self.num_sockets = len(self._node_mapping.keys()) - 1  # -1 to line up with socket numbers 0-1 or 0-3
        # boot VMs
        self.launch_vms.execute()

    def execute(self):
        self.tdvms = self.launch_vms.tdvms
        # launch mprime on vms
        self._log.info("Setting up mprime")
        for vm in self.tdvms:
            idx = self.tdvms.index(vm)
            self.set_up_tool(idx=idx)
            self._log.info("Launching {} suite on VM {}.".format(self._tool_name, idx))
            log_file_name = "{}/tdvm-{}-{}.txt".format(self._tool_sut_folder_path, self._tool_name, idx)
            cmd = self._tool_sut_folder_path + "/" + self._tool_run_cmd.format(
                self._tool_run_time) + log_file_name
            self.ssh_to_vm(key=idx, cmd=cmd, async_cmd=True)
            self.check_process_running(key=idx, process_name=self._tool_name)
        self._log.info("Mprime is running on all TD guests.  Doing initial assignment of TD guests.")

        for vm in self.tdvms:
            idx = self.tdvms.index(vm)
            new_node = self.get_free_node(random_node=False)
            self.move_vm(key=idx, new_node=new_node, current_node=None)
        self._log.info("Initial socket assignment done.")

        for cycle in range(0, self.SHIFT_CYCLES):
            self._log.info("Starting iteration {} of {}".format(cycle, self.SHIFT_CYCLES))
            self.swap_sockets()
            self._log.info("Finished iteration {} of {}".format(cycle, self.SHIFT_CYCLES))
        return True

    def swap_sockets(self):
        """Iterates through all VMs and moves them to a node on an opposite socket."""
        self._log.info("Shuffling TD guest node assignments.")
        for vm in self.tdvms:
            idx = self.tdvms.index(vm)
            self._log.debug("Shuffling nodes for VM {}.".format(idx))
            current_node = self.get_current_node(self.get_pid(idx))
            current_socket = self.get_socket(current_node)
            new_node = self.get_free_node(random_node=True, current_socket=current_socket)
            self.move_vm(key=idx, new_node=new_node, current_node=current_node)

    def stage_numa_tracking(self):
        """Set up list to track numa nodes for all applicable sockets and which sockets to which nodes."""
        self._log.debug("Setting up numactl tracking list.")
        numa_nodes = self.os.execute("numactl --hardware | grep 'node [0-9] cpus'",
                                     self.command_timeout).stdout.strip()
        numa_nodes = numa_nodes.split('\n')
        for node in numa_nodes:
            split_node = node.split(":")
            key = split_node[0].split(" ")[1]
            value = split_node[1].lstrip()  # get rid of leading space creating empty node value
            self._node_mapping[key] = value.split(" ")
            self._available_nodes[key] = value.split(" ")
        self._log.debug("Numa mapping is done.")
        for key in self._node_mapping.keys():
            self._log.debug("numa mapping for socket {}: {}".format(key, self._node_mapping[key]))

    def move_vm(self, key=None, new_node=None, current_node=None):
        """Move node from a current node and to a new node.
        :param key: VM identifier.
        :type: int
        :param new_node: new node for VM to be assigned to.
        :type: str
        :param current_node: current node VM is assigned to.
        :type: str"""
        taskset_cmd = "taskset -cp {} {}"
        MOVE_SUCCEEDED = "new affinity list"
        pid = self.get_pid(key)
        result = self.os.execute(taskset_cmd.format(new_node, pid), self.command_timeout)
        if MOVE_SUCCEEDED not in result.stdout:
            raise content_exceptions.TestFail("Failed to move VM {} to node {}.  Output: {}".format(key, new_node,
                                                                                                    result.stderr))
        if current_node is not None:
            self.release_node(current_node)

    def get_pid(self, idx):
        """Get PID for running VM.
        :param idx: key identifier for the VM.
        :type: int
        :return: process id for running VM.
        :rtype: str"""
        grep_cmd = "ps aux | grep \'{}\' | grep -v grep | awk -F\' \' \'{{print $2}}\'"
        return self.os.execute(grep_cmd.format(self.tdvms[idx][self.tdx_consts.TD_GUEST_IMAGE_PATH]),
                               self.command_timeout).stdout.strip()

    def release_node(self, node=None):
        """Add node back to available node list.
        :param node: node to add back to node tracking list
        :type: int"""
        if node is None:
            raise ValueError("No node was provided to release!")
        node = str(node)
        socket = self.get_socket(node)
        if socket is not None:
            self._available_nodes[socket].append(node)
            self._log.debug("Added node {} back to available node list for socket {}.".format(node, socket))
        else:
            raise RuntimeError("Could not add {} node back to socket {} available node list.".format(node, socket))

    def capture_node(self, socket=None, node=None):
        """Remove node from available node list.
        :param socket: socket to remove node from
        :type: str
        :param node: node to remove from the list assigned to socket
        :type: str"""
        socket = str(socket)
        node = str(node)
        self._available_nodes[socket].remove(node)
        self._log.debug("Node {} has been removed from available nodes list for socket {}.  Current list: {}".format(
            node, socket, self._available_nodes[socket]
        ))

    def get_socket(self, node=None):
        """Get socket for numa node.
        :param node: node to look up.
        :type: str
        :return: socket node is on
        :rtype: str"""
        node = str(node)
        for key, value in self._node_mapping.items():
            if node in value:
                socket = key
                return socket
        raise content_exceptions.TestFail("Could not find assigned socket for node {}.  Node mapping: {}".format(
            node, self._node_mapping
        ))

    def get_free_node(self, new_socket=None, random_node=True, current_socket=None):
        """Get free node for a given socket and remove from node from available list.
        :param new_socket: socket to get a free node from
        :type: str
        :param random_node: Give random node instead of whatever is highest index in the list.
        :type: bool
        :param current_socket: socket current_node is assigned to
        :type: str
        :return: return_node:  node to be assigned
        :rtype: str"""
        if new_socket is None:
            self._log.debug("No socket provided for assignment, picking random socket.")
        while new_socket == current_socket or new_socket is None:
            new_socket = str(random.randint(0, self.num_sockets))  # pick random socket

        if random_node:  # pick a random node in given socket
            self._log.debug("Finding random node for socket {}...".format(new_socket))
            return_node = random.choice(self._available_nodes[new_socket])
            self._log.debug("Picked node {} from socket {}.".format(return_node, new_socket))
        else:  # get first available node for socket
            self._log.debug("Finding first node for socket {}...".format(new_socket))
            node_idx = 0  # get first node available
            return_node = self._available_nodes[new_socket][node_idx]

        self._log.debug("Selected node {}.  Removing from available nodes list.".format(return_node))
        self.capture_node(socket=new_socket, node=return_node)
        return return_node

    def get_current_node(self, pid=None):
        """Return node a pid is running on.
        :param pid: PID of VM process.
        :type: str
        :return: node that the logical CPU is using"""
        lcpu = self.os.execute("taskset -cp {}".format(pid),
                               self.command_timeout).stdout.strip()
        lcpu = lcpu.split(":")
        lcpu = lcpu[1].lstrip()
        return int(lcpu)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeDTdGuestTaskset.main() else Framework.TEST_RESULT_FAIL)
