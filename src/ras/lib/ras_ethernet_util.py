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
import time
import re
from dtaf_core.lib.dtaf_constants import Framework
from src.lib.common_content_lib import CommonContentLib
from src.lib import content_exceptions
from src.ras.lib.ras_einj_common import RasEinjCommon

import sys


class RasEthernetUtils(RasEinjCommon):
    """
    Common ethernet functions useful for eDPC and general tests
    """
    OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC = 30
    _POST_UCE_RETRY_DELAY_IN_SEC = 900
    E810_network_interface_pattern = r'ice\s+\w+:\w+:\w+.\w\s(ens\d+f\d+).*'

    def __init__(self, log, os, cfg_opts, common_content_configuration):
        self._common_content_lib = CommonContentLib(log, os, cfg_opts)
        super(RasEthernetUtils, self).__init__(log, os, self._common_content_lib, common_content_configuration)
        self._log = log
        self._os = os

    def network_namespace_create(self, num_ns):
        """
        Create network namespaces to isolate ethernet cards in same IP subnet on same host, connected back to back
        :param num_ns: Number of desired namespaces, 1 per NIC endpoint under test.
        :return:
        """
        for i in range(1, int(num_ns) + 1):  # 1 is added to account for python range command usage
            create_ns = self._os.execute("ip netns add ns{}".format(i), self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
            if create_ns.cmd_failed():
                log_error = "Failed to run 'ip netns add ns{}' command with return value = '{}' and " \
                       "std_error='{}'..".format(i, create_ns.return_code, create_ns.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

    def ethernet_setup(self, ns_num, netdev, ip_addr):
        """
        Assign IP address to a NIC that has been moved to a network namespace
        :param ns_num: Number of network namespace that contains the NIC to be configured
        :param netdev: OS netdev name assigned to NIC (e.g. eth5, ens5s0f0 etc.)
        :param ip_addr: IPv4 address is dotted-decimal format (e.g. 192.168.0.2)
        :return: void
        """
        assign_ip_addr = self._os.execute("ip netns exec ns{} ifconfig {} {}".format(ns_num, netdev, ip_addr),
                                          self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        if assign_ip_addr.cmd_failed():
            log_error = "Failed to run 'ifconfig {} {}' command with return value = '{}' and " \
                        "std_error='{}'..".format(netdev, ip_addr, assign_ip_addr.return_code, assign_ip_addr.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def namespace_move(self, ns_num, netdev):
        """
        Move NIC netdevs to a network namespace
        :param ns_num: Network namespace number to move netdev to
        :param netdev: OS netdev name assigned to NIC (e.g. eth5, ens5s0f0 etc.)
        :return: void
        """
        assign_namespace = self._os.execute("ip link set {} netns ns{}".format(netdev, ns_num),
                                            self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        if assign_namespace.cmd_failed():
            log_error = "Failed to execute 'ip link set {} netns ns{}' command with return value = '{}' and " \
                            "std_error='{}'..".format(netdev, ns_num, assign_namespace.return_code,
                                                      assign_namespace.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def ping_test(self, source_namespace, ping_count, dest_ip):
        """
        Execute the ping command from within a network namespace
        :param source_namespace: The network namespace of the NIC sending the ping
        :param ping_count: The desired number of pings
        :param dest_ip: The IPv4 address to ping in dotted-decimal format (e.g. 192.168.0.2)
        :return: void
        """
        ns_ping_test = self._os.execute("ip netns exec {} ping -c {} {}".format(source_namespace, ping_count, dest_ip),
                                        self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        if ns_ping_test.cmd_failed():
            log_error = "Failed to execute 'ip netns exec {} ping -c {} {}' command with return value = '{}' and " \
                        "std_error='{}'..".format(source_namespace, ping_count, dest_ip, ns_ping_test.return_code,
                                                  ns_ping_test.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        else:
            self._log.info("Ping Test to {} successful, {} setup successful".format(dest_ip, source_namespace))

    def run_ethernet_traffic(self, iper_serv_namespace, iper_clnt_namespace, iper_srv_ip, iper_tst_dur,
                             iper_tst_threads, srv_node=None, clnt_node=None, iperf_ver='iperf'):
        """
        Run iperf based ethernet stress traffic
        :param iper_serv_namespace: The network namespace in which to run the iperf server
        :param iper_clnt_namespace: The network namespace in which to run the iperf client
        :param iper_srv_ip: The IP address of the iperf server
        :param iper_tst_dur: The duraton to run iperf in seconds.
        :param iper_tst_threads: The number of parallel "threads" to run, 10-15 is usually a good number.
        :param srv_node: The NUMA node to use for the iperf server memory bind, see note on clnt_node
        :param clnt_node: The NUMA node to use for the iperf client memory bind. Note, must use different node than srv.
        :param iperf_ver: The version of iperf to use, iperf2 is default but iperf3 can be used on systems w/o iperf2
        :return: void
        """
        if srv_node is None:
            self._os.execute_async("ip netns exec {} {} -s ".format(iper_serv_namespace, iperf_ver),
                                   cwd='', ps_name='iperfS')
        else:
            self._os.execute_async("numactl --membind={} ip netns exec {} {} -s ".format(int(srv_node), iper_serv_namespace,
                                    iperf_ver), cwd='', ps_name='iperfS')

        if clnt_node is None:
            self._os.execute_async("ip netns exec {} {} -c {} -t {} -P {} ".format(iper_clnt_namespace,
                                   iperf_ver, iper_srv_ip, iper_tst_dur, iper_tst_threads),
                                   cwd='', ps_name='iperfC')
        else:
            self._os.execute_async("numactl --membind={} ip netns exec {} {} -c {} -t {} -P {} ".format(int(clnt_node),
                                   iper_clnt_namespace, iperf_ver, iper_srv_ip, iper_tst_dur, iper_tst_threads),
                                   cwd='', ps_name='iperfC')

    def check_ethernet_traffic(self, namespace, netdev, uncorrectable=False):
        """
        Check after injection to see if the NIC endpoint is still configured and can still send traffic.

        Only 1 NIC needs to be checked in a back-to-back config.
        :param namespace: Namespace number of NIC to check for traffic
        :param netdev: OS netdev name of NIC to check for traffic
        :param uncorrectable: Flags that the injection type is uncorrectable
        :return: void
        """
        traffic_status = self._os.execute("ip netns exec {} sar -n DEV 1 1 | grep {}".format(namespace, netdev),
                                          self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        traffic_is_running = traffic_status.stdout
        packets_sec = traffic_is_running.split()
        netdev_index = packets_sec.index('{}'.format(netdev))
        packsec_value = packets_sec[(int(netdev_index + 1))]
        self._log.info("This is the status from SAR {}".format(traffic_status.stdout))
        self._log.info("This is the packets per second value {}".format(packsec_value))
        expected_min_pac_sec = 100
        if float(packsec_value) < expected_min_pac_sec:
            self._log.error("Traffic has failed")
            if uncorrectable:
                self._log.info("Pausing {} minutes after uncorrectable non-fatal error".format
                               (float(self._POST_UCE_RETRY_DELAY_IN_SEC / 60)))
                time.sleep(float(self._POST_UCE_RETRY_DELAY_IN_SEC))
                if float(packsec_value) < expected_min_pac_sec:
                    self._log.error("Traffic has failed")
                    sys.exit(Framework.TEST_RESULT_FAIL)
        else:
            self._log.info("Traffic appears to have continued after EINJ")

    def run_ptu(self, ptu_time):
        """
        Send an OS command to start the PTU program
        :param self:
        :param ptu_time: Time in seconds to run PTU
        :return: none
        """
        self._os.execute_async(cmd="/ptu/ptu -y -ct 3 -t {}".format(ptu_time), cwd='', ps_name='PTU')

    def check_running_stress(self):
        """
        Check to see if the requested stress programs are running before the test methods start.
        :param self:
        :return: void but result is sys exit and test result fail if one or more stress programs are not running.
        """
        stress_status = self._os.execute("screen -ls", self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)

        stress_list = stress_status.stdout
        status_iperf_s = stress_list.find('.iperfS')
        status_iperf_c = stress_list.find('.iperfC')
        status_ptu = stress_list.find('.PTU')
        self._log.info("These are the running stress programs: {}".format(stress_status.stdout))
        if status_iperf_s == -1 or status_iperf_c == -1 or status_ptu == -1:
            self._log.info("One or more stress programs failed to start")
            sys.exit(Framework.TEST_RESULT_FAIL)

    def prepare_sut_for_test(self):
        """
        Check system for required programs then calls network prep method

        :param self: self
        :return Fail if any of the steps fail.
        """

        self._log.info("checking for required programs")
        iperf_installed = self._os.execute('which iperf', self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        iperf3_installed = self._os.execute('which iperf3', self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        ptu_installed = self._os.execute('ls / | grep ptu', self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        numactl_installed = self._os.execute('which numastat', self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        sysstat_installed = self._os.execute('which sar', self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)

        if not iperf_installed.stdout or not iperf3_installed.stdout:
            self._log.error("iperf and iperf3 installs are required for this test")
            sys.exit(Framework.TEST_RESULT_FAIL)

        if not ptu_installed.stdout:
            self._log.error("ptu is required for this test and expected to be installed at /ptu")
            sys.exit(Framework.TEST_RESULT_FAIL)

        if not numactl_installed.stdout:
            self._log.error("numactl which provides numastat is required for this test")
            sys.exit(Framework.TEST_RESULT_FAIL)

        if not sysstat_installed.stdout:
            self._log.error("sysstat, which provides sar, is required for this test")
            sys.exit(Framework.TEST_RESULT_FAIL)

    def cleanup_ethernet(self, mod_name=None):
        """
        Clean up items specific to test that are not cleaned by the main DTAF cleanup. Also pre-cleans the system before
        a test is run.
        :param self:
        :param mod_name: The driver module name for rmmod/modprobe
        :return: none
        """
        self._log.info("Cleaning test configuration")
        self._os.execute("killall screen", self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        self._os.execute("ip netns del ns2", self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        self._os.execute("ip netns del ns1", self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        if mod_name is not None:
            self._os.execute("rmmod {}".format(mod_name), self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
            self._os.execute("modprobe {}".format(mod_name), self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        self._log.info("Finished cleanup")

    def inject_pcie_uncorrectable_errors(self, count, namespace, netdev, post_uce_inj_wait_secs, edpc_en=True):
        """
        Call the functions of the ras_einj_obj object to perform <count> PCIE uncorrectable error injections

        :param self: self
        :param count: The number of requested error injections
        :param namespace: The namespace that the ethernet endpoint receiving the injection is assigned to
        :param netdev: The Linux netdev name bound to ethernet SUT/DUT NIC endpoint hardware
        :param post_uce_inj_wait_secs: How long to wait in seconds after a UCE-NF error injection
        :param edpc_en: boolean for whether eDPC is set in the BIOS, Needed for cases where signalling changes
        :return: Boolean indicating successful error(s) injection and verification(s)
        """
        for i in range(int(count)):
            if edpc_en:
                inject_and_check_success = self.einj_inject_and_check(
                        error_type=self.EINJ_PCIE_UNCORRECTABLE_NONFATAL, edpc_en=True)
            else:
                inject_and_check_success = self.einj_inject_and_check(
                        error_type=self.EINJ_PCIE_UNCORRECTABLE_NONFATAL, edpc_en=False)
            if not inject_and_check_success:
                return False

            # call a program to verify traffic still running, which is why einj is looped here instead of using the
            # einj_inject_and_check object's "loops count" parameter.
            self.check_ethernet_traffic(namespace, netdev, uncorrectable=True)

            self._log.info(
                "Pausing {} secs after injection # {} of {}".format(post_uce_inj_wait_secs, i + 1, count))
            time.sleep(float(post_uce_inj_wait_secs))
        return True

    def inject_pcie_correctable_errors(self, count, namespace, netdev, post_ce_inj_wait_secs):
        """
        Call the functions of the ras_einj_obj object to perform <count> PCIE correctable error injections

        :param self: self
        :param count: The number of requested error injections
        :param namespace: The namespace that the ethernet endpoint receiving the injection is assigned to
        :param netdev: The Linux netdev name bound to ethernet SUT/DUT NIC endpoint hardware
        :param post_ce_inj_wait_secs: How long to wait in seconds after a CE error injection
        :return: Boolean indicating successful error(s) injection and verification(s)
        """
        for i in range(int(count)):
            if not self.einj_inject_and_check(error_type=self.EINJ_PCIE_CORRECTABLE):
                return False
            # call a program to verify traffic still running, which is why einj is looped here instead of using the
            # einj_inject_and_check object's "loops count" parameter.
            self._log.info(
                "Pausing {} secs after injection # {} of {}".format(post_ce_inj_wait_secs, i + 1, count))
            time.sleep(float(post_ce_inj_wait_secs))
            self.check_ethernet_traffic(namespace, netdev)
        return True

    def prepare_sut_network_for_test(self, num_ns, netdev1, netdev2, ip_addr1, ip_addr2):
        """ Set up ethernet for test using the methods in this library
        1) create number of namespaces defined by num ns
        2) Move 1st netdev to NS Namespace
        3) Repeat for 2nd netdev
        4) Set IP address for 1st netdev
        5) Repeat for 2nd netdev
        6) Disable audit daemon output to dmesg to keep it clean and as test specific as possible
        7) Ping from NS 1 > 2, 4 times, sleep 5 seconds to allow to complete.
        8) Ping from NS 2 > 1, 4 times, sleep 5 seconds to allow to complete.
        9) log confirmation

        num_ns: type, int or numeral str for desired number of network namespaces
        netdev1: type str, devname for the first ethernet adapter to be used (e.g. eth1, enp5s0f1, etc)
        netdev2: type str, devname for the second ethernet adapter
        ip_addr1: type str, IP address for first adapter in dotted decimal format (e.g. '192.168.1.15')
        ip_addr2: type str, IP address for second adapter in dotted decimal format (e.g. '192.168.1.25')
        return: void
        """

        self.network_namespace_create(num_ns)
        self.namespace_move('1', netdev1)
        self.namespace_move('2', netdev2)
        self.ethernet_setup('1', netdev1, ip_addr1)
        self.ethernet_setup('2', netdev2, ip_addr2)
        self._os.execute('auditctl -e 0', self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        ping_delay_in_sec = 5
        time.sleep(ping_delay_in_sec)
        self.ping_test('ns1', '4', ip_addr2)
        time.sleep(ping_delay_in_sec)
        self.ping_test('ns2', '4', ip_addr1)
        time.sleep(ping_delay_in_sec)
        self._log.info('Ethernet Prep Complete')

    def assign_ip_address_to_interface(self, ip_address, interface, net_mask=None, ns_num=None):
        """
        This method is used to assign a ip address to a specific ethernet interface

        ip_address - ip address to be assigned
        net_mask - netmask of the device
        interface - interface on which ip address would be assigned

        return - void
        """
        cmd_to_execute = "ip netns exec ns{} ".format(ns_num) if ns_num else ""

        cmd_to_execute += "ip address add {}/{} dev {}".format(ip_address, net_mask, interface) if net_mask else\
                           "ip address add {} dev {}".format(ip_address, interface)

        assign_ip = self._os.execute(cmd_to_execute, self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        if assign_ip.cmd_failed():
            log_error = "Failed to execute 'ip address add {} dev {}' command with return value = '{}' and " \
                        "std_error='{}'..".format(ip_address, interface, assign_ip.return_code,
                                                  assign_ip.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def set_interace_status(self, interface, status, ns_num=None):
        """
        This method is used to set the status of the interface

        interface - Ethernet interface
        status - status to set on the interface
        ns_num - name space

        return - void
        """
        cmd_to_execute = "ip netns exec ns{} ".format(ns_num) if ns_num else ""
        status_dict = {0: 'down', 1: 'up'}

        cmd_to_execute += "ip link set dev {} {}".format(interface, status_dict[status])
        set_interface = self._os.execute(cmd_to_execute, self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        if set_interface.cmd_failed():
            log_error = "Failed to execute 'ip link set dev {} {}' command with return value = '{}' and " \
                        "std_error='{}'..".format(interface, status_dict[status], set_interface.return_code,
                                                  set_interface.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def start_iperf_traffic(self, iper_srv_ip, iper_serv_namespace=None, iper_clnt_namespace=None, iper_tst_dur=120,
                             iper_tst_threads=1, iperf_ver='iperf', serv_bind_ip=None, clnt_bind_ip=None, iper_log_file=None):
        """
        Run iperf based traffic
        :param iper_serv_namespace: The network namespace in which to run the iperf server
        :param iper_clnt_namespace: The network namespace in which to run the iperf client
        :param iper_srv_ip: The IP address of the iperf server
        :param iper_tst_dur: The duraton to run iperf in seconds.
        :param iper_tst_threads: The number of parallel "threads" to run, 10-15 is usually a good number.
        :param serv_bind_ip: The IP to which the server needs to be binded
        :param clnt_bind_ip: The IP to which the client needs to be binded
        :param iperf_ver: The version of iperf to use, iperf2 is default but iperf3 can be used on systems w/o iperf2
        :param iper_log_file: Name of the file where the iperf traffic needs to be redirected
        :return: void
        """
        # Construct server command
        server_cmd = "ip netns exec {} ".format(iper_serv_namespace) if iper_serv_namespace else ""
        server_cmd += "{} -s".format(iperf_ver)
        if serv_bind_ip:
            server_cmd += " -B {}".format(serv_bind_ip)
        if iper_log_file:
            server_cmd += " --logfile {}".format(iper_log_file)
            self._os.execute("rm -rf {}".format(iper_log_file), self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        self._log.info("iperf server command - {}".format(server_cmd))
        self._os.execute_async(server_cmd, cwd='', ps_name='iperfS')

        # Construct client command
        client_cmd = "ip netns exec {} " if iper_clnt_namespace else ""
        client_cmd += "{} -c {} -t {} -P {}".format(iperf_ver, iper_srv_ip, iper_tst_dur, iper_tst_threads)
        if clnt_bind_ip:
            client_cmd += " -B {}".format(clnt_bind_ip)
        self._log.info("iperf client command - {}".format(client_cmd))
        self._os.execute_async(client_cmd, cwd='', ps_name='iperfC')

    def check_iperf_server_status(self, iperf_log_file):
        """
        This msthod used to check the connection status of the iperf server

        iperf_log_file (str) : File name where the iperf server output were captured
        return : None
        raise: Test Fail
        """
        server_output = self._os.execute("head {}".format(iperf_log_file), self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        self._log.debug("output of iperf server file {} :\n{}".format(iperf_log_file, server_output.stdout))
        if "Accepted connection" not in server_output.stdout:
            raise content_exceptions.TestFail("iperf Server is not started successfully")
        self._log.info("iperf server is started and connected to the client")

    def check_iperf_traffic_continuity(self, iperf_log_file):
        """
        This method check the iperf traffic continuity, raise exception if any iperf instance has 0 throughput
        iperf_log_file (str): File where the iperf server output were captured
        return : None
        raise: Test Fail
        """
        server_output = self._os.execute("cat {}".format(iperf_log_file), self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
        self._log.debug("iperf server output: \n{}".format(server_output.stdout))
        reg_ex = r'\[.*\]\s+.*sec\s+(\d+(?:\.\d+)?)\s+.*sec'
        matcher = re.findall(reg_ex, server_output.stdout, re.MULTILINE | re.IGNORECASE)
        if not matcher:
            raise content_exceptions.TestFail("Throughput values were not captured in the log file {}".format(iperf_log_file))
        converted_matcher = list(map(float, matcher))
        for values in converted_matcher:
            if values == 0:
                raise content_exceptions.TestFail("Network workload/iperf traffic was interrupted during the link speed degradation")

    def iperf_stop(self, iperf_version):
        """
        Stop iperf
        """
        self._os.execute("pkill {}".format(iperf_version), self.OS_NET_CMD_EXECUTE_TIMEOUT_IN_SEC)
