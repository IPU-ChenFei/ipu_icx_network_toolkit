#!/usr/bin/env python
import os
import re
import time
import importlib

# from basic.const import *
from dtaf_core.lib.tklib.basic.const import SUT_STATUS, SUT_PLATFORM
from dtaf_core.lib.tklib.basic.testcase import Case
from dtaf_core.lib.tklib.basic.log import logger
from dtaf_core.lib.tklib.basic.config import LOG_PATH
from src.network.lib.config import *
from dtaf_core.lib.tklib.steps_lib.os_scene import Linux, Windows, OperationSystem
from dtaf_core.lib.tklib.steps_lib.uefi_scene import UefiShell
from dtaf_core.lib.tklib.basic.utility import ParameterParser

def val_os(sutos):
    if sutos.lower() == 'redhat':
        return RedhatNicOp
    elif sutos.lower() == 'centos':
        return CentOSNicOp
    elif sutos.lower() == 'sles':
        return SlesNicOp
    elif sutos.lower() == 'ubuntu':
        return UbuntuNicOp
    elif sutos.lower() == 'alios':
        return AliOSNicOp
    elif sutos.lower() == 'windows':
        return WindowsNicOp
    else:
        raise RuntimeError('Not supported OS: {}'.format(sutos))

def muti_nic_config(sut1, sut2):
    conn = ParameterParser.parse_parameter("conn").strip().split(',')
    #conn = ['col_conn_v4', 'col_conn_v4_02']
    conns = []
    for ip in conn:
        conns.append(nic_config(sut1, sut2, ip))
    return conns

def run_template(package, script):
    t = importlib.import_module("src.network.tests.{}.{}".format(package, script.strip(".py")))
    test_main = getattr(t, "test_main")
    test_main()
    exit(t.Result.returncode)


class GenericNicOp(object):
    OS = SUT_STATUS.UNKNOWN
    tool_path = None
    cmd_ixvss = None
    ping = None
    reboot = True
    ipv4_network_tag = "HWADDR,IPADDR,NAME"
    ipv6_network_tag = "HWADDR,IPV6ADDR,NAME"
    ipv6_enable = False
    common_path = os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def ip_assign(cls, *conn):
        """
        Assign IP address for each test connection, and ping through to make sure connection works fine

        This API should handle different testing OS
          1. For windows, it supports both client and server OS
            * Win10 Pro
            * LTSC (Long Term Support Channel)
              * Win Server 2024/2023/2021/2019/2016
            * SAC (Semi Annual Channel)
              * Win Server 23H2/23H1/22H1/21H1
          2. For Linux, it supports below POR OS
            * RHEL 8.x, 9.x
            * CentOS 8.x, 9.x
            * SLES 15 SPx, 16 SPx
            * Ubuntu 22.04, 23.04+
          3. For Vmware, will support in future
            * ESXi 8.0u2, 9.0u

        For each *conn, follow below logic for stability
          1. recommend to use script on SUT OS for completing this for each port
              * stop network service
              * clean current configuration for *conn
              * setup network configuration
              * restart network service
          2. check connection works fine for port1 and port2
          3. Sample Code
              * conn = *conn[0]
              * port1 = conn.port1
              * port2 = conn.port2
              * sut1 = port1.sut
              * sut2 = port2.sut
              * sut1.execute_shell_cmd(cls.cmd_ip)
              * sut2.execute_shell_cmd(cls.cmd_ip)
              * sut1.execute_shell_cmd('ping port2 on sut2')

        Args:
            *conn: interface.NicPortConnection object

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """

        for con_index, conn in enumerate(conn):
            port1 = conn.port1
            port2 = conn.port2
            sut1 = port1.sut
            sut2 = port2.sut
            #sut2.execute_shell_cmd_async("ping 192.168.0.3 -t")
            #ret = sut1.ssh_connection(60, sut1.check_ssh_status)
            cls.ip_config(port1, con_index)
            #ret = sut2.ssh_connection(60, sut2.check_ssh_status)
            cls.ip_config(port2, con_index)
            out = sut1.execute_shell_cmd(cls.ping.format(port2.ip), timeout=30)[1]
            out2 = sut2.execute_shell_cmd(cls.ping.format(port1.ip), timeout=30)[1]

            if not (cls.ping_result_check(out) and cls.ping_result_check(out2)):
                raise RuntimeError(f'ping from {port1.ip} to {port2.ip} fail')

    @classmethod
    def ip_config(cls, port, con_index):
        raise NotImplementedError

    @classmethod
    def fw_update_in_uefi(cls, drv, cwd, *conn):
        """
        Update NIC FW in uefi, and check results are correct
        All defined NIC type should be covered from config.xxx_xxx_type
        Only operates on SUT1
        Recommend to use script on SUT OS for completing this

        Args:
            drv: file system name end with ':', e.g. fs2:
            cwd: fw folder path, without file system name
            *conn: interface.NicPortConnection object

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        assert isinstance(drv, str)
        assert drv.endswith(':')
        assert isinstance(cwd, str)

        log_filename = 'update.log'
        update_cmd = f'nvmupdate64e -u -l -o {log_filename} -c nvmupdate.cfg'

        for conn in conn:
            port1 = conn.port1
            sut1 = port1.sut
            assert sut1.bios.in_uefi()

            # change directory to cwd for command is not supporting for running in absolute path
            ret = sut1.execute_uefi_cmd(drv, end_pattern=r'FS\d+:')
            if 'is not a valid mapping' in ret:
                raise RuntimeError('invalid drv path')
            ret = sut1.execute_uefi_cmd(f'cd {cwd}', end_pattern=r'FS\d+:')
            if 'is not a directory' in ret:
                raise RuntimeError('invalid cwd param')

            ret = sut1.execute_uefi_cmd(update_cmd, timeout=60 * 20, end_pattern=r'FS\d+:')
            logger.info(f'execute update cmd {update_cmd} and command running information is:{ret}')
            ret = sut1.execute_uefi_cmd(f'cat {log_filename}', end_pattern=r'FS\d+:')
            logger.info(f'update information is:{ret}')

            if 'Reboot is required to complete the update process' in ret:
                UefiShell.reset_cycle_step(sut1)
            else:
                logger.info(f'No update')

            # restore to root directory
            sut1.execute_uefi_cmd('cd \\')

    @classmethod
    def fw_update_in_os(cls, fw_update_path, *conn):
        """
        Update NIC FW, and check results are correct
        All defined NIC type should be covered from config.xxx_xxx_type
        Recommend to use script on SUT OS for completing this

        Args:
            fw_update_path: fw update folder path in host, and the directory contain nvmupdate64e file, without sub directory
            *conn: interface.NicPortConnection object

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        for conn in conn:
            port1 = conn.port1
            port2 = conn.port2
            sut1 = port1.sut
            sut2 = port2.sut

            update_callback = cls.__get_fw_update_in_os_callback(port1.nic.type.family)
            update_callback(sut1, fw_update_path)
            update_callback(sut2, fw_update_path)

    @classmethod
    def __get_fw_update_in_os_callback(cls, nic_type):
        """
        get firmware update callback for nic type

        Args:
            nic_type: nic family type

        Returns:
            Callable: callback function for nic type

        Raises:
            ValueError: If any errors
        """
        if nic_type == 'Mellanox':
            return cls.__fw_update_in_os_mellanox
        elif nic_type in INTEL_NIC_SERIES:
            return cls.__fw_update_in_os_intel
        else:
            raise ValueError(f'No support for this nic_type:{nic_type}')

    @classmethod
    def __fw_update_in_os_intel(cls, sut, fw_update_path):
        """
        Update NIC FW, and check results are correct

        Args:
            sut: sut instance
            fw_update_path: fw update folder path in host

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
            cmd_name = './nvmupdate64e'
            os_scene = Linux
        elif sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
            cmd_name = 'nvmupdatew64e.exe'
            os_scene = Windows
        else:
            raise RuntimeError('Not supported os')

        cwd = fw_update_path

        if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
            sut.execute_shell_cmd(f'chmod 777 nvmupdate64e', cwd=cwd)

        # run update command and save log
        ret_code, stdout, stderr = sut.execute_shell_cmd(f'{cmd_name} -u -l -o update.log -c nvmupdate.cfg',
                                                         timeout=60 * 10, cwd=cwd)
        logger.info(f'update fw return code = {ret_code}')
        logger.info(f'update fw process log:{stdout}')
        logger.debug(f'update fw stderr:{stderr}')

        reboot = 'Reboot is required to complete the update process' in stdout

        if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
            ret_code, stdout, stderr = sut.execute_shell_cmd('cat update.log', cwd=cwd)
        elif sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
            ret_code, stdout, stderr = sut.execute_shell_cmd('type update.log', cwd=cwd)
        logger.info(f'update fw result log:{stdout}')

        if reboot:
            logger.info('Update successfully, start reboot')
            os_scene.reset_cycle_step(sut)
        else:
            logger.info('No update')

    @classmethod
    def __fw_update_in_os_mellanox(cls, sut, fw_update_path):
        """
        Update mellanox firmware, and check results are correct

        Args:
            sut: sut instance
            fw_update_path: fw update folder path in host

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
            os_scene = Linux
        elif sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
            os_scene = Windows
        else:
            raise RuntimeError('Not supported os')

        # setup MFT tool firstly
        # install MFT tool
        cwd = fw_update_path
        if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
            # unzip setup compress file
            _, tgz_file, _ = sut.execute_shell_cmd(f'ls *.tgz', timeout=60 * 10, cwd=cwd)
            tgz_file = tgz_file.replace('\n', '')
            sut.execute_shell_cmd(f'tar zxf {tgz_file}', timeout=60 * 10, cwd=cwd)
            folder_name = tgz_file.replace('.tgz', '')
            # run install script
            _, stdout, _ = sut.execute_shell_cmd(f'./install.sh --without-user', timeout=60 * 10,
                                                 cwd=f'{cwd}/{folder_name}')
            logger.info(f'install mft tool info:\n{stdout}')
            assert 'In order to start mst, please run "mst start".' in stdout
            # start mst service
            _, stdout, _ = sut.execute_shell_cmd(f'mst start', timeout=60 * 10, cwd='/etc/init.d')
            logger.info(f'start mst service:\n{stdout}')
        elif sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
            _, setup_file, _ = sut.execute_shell_cmd(r'dir WinMFT*.exe /b', cwd=cwd)
            setup_file = setup_file.replace('\n', '')
            sut.execute_shell_cmd(f'{setup_file} /v/qn', timeout=60 * 10, cwd=cwd)

        # update fw by MFT tool
        # query device name
        _, stdout, _ = sut.execute_shell_cmd('mst status')
        logger.info(f'query NIC info:\n{stdout}')
        devs = re.findall(r'mt[\d\w]+', stdout)
        if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
            devs = [f'/dev/mst/{dev}' for dev in devs]
        if len(devs) == 0:
            raise RuntimeError('No mellanox card can be found')

        # query available image bin files
        if sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
            _, stdout, _ = sut.execute_shell_cmd(r'ls *.bin', cwd=cwd)
        elif sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
            _, stdout, _ = sut.execute_shell_cmd(r'dir fw-*MCX*.bin /b', cwd=cwd)
        logger.info(f'query firmware bin file:\n{stdout}')
        bin_files = re.findall(r'fw.+\.bin', stdout)
        if len(bin_files) == 0:
            raise RuntimeError('No firmware bin file can be found')

        # query psid and fw version for each bin file
        bin_file_info = []
        for bin_file in bin_files:
            _, stdout, _ = sut.execute_shell_cmd(f'flint -i {bin_file} q', timeout=30, cwd=cwd)
            bin_file_info.append({
                'psid': re.search(r'(?!PSID:\s+)MT_\d+', stdout).group(),
                'fw_version': re.search(r'(?!FW Version:\s+)\d[\d\.]+', stdout).group()
            })

        # match each device to available image bin file according to check psid and fw version
        update = False
        for dev in devs:
            _, stdout, _ = sut.execute_shell_cmd(f'flint -d {dev} q', timeout=30, cwd=cwd)
            logger.info(f'current device info is:\n{stdout}')
            dev_psid = re.search(r'(?!PSID:\s+)MT_\d+', stdout).group()
            dev_fw_version = re.search(r'(?!FW Version:\s+)\d[\d\.]+', stdout).group()
            for bin_info in bin_file_info:
                # match device with image bin file with psid value
                if bin_info['psid'] == dev_psid:
                    if bin_info['fw_version'] == dev_fw_version:
                        logger.info(f'device {dev} has latest firmware image, no update happen')
                    else:
                        logger.info(f'update device {dev} with image file {bin_file}')
                        logger.info(f'update fw version from {dev_fw_version} to {bin_info["fw_version"]}')
                        ret_code, stdout, stderr = sut.execute_shell_cmd(f'flint -y -d {dev} -i {bin_file} burn',
                                                                         timeout=60 * 10, cwd=cwd)
                        logger.info(f'burn firmware bin file result is:{ret_code}')
                        logger.info(f'burn firmware bin file process info is:\n{stdout}')
                        logger.debug(f'burn firmware bin file process err is:\n{stderr}')

                        if ret_code != 0:
                            raise RuntimeError('update firmware error, please check log')

                        update = True
                    break

        if update:
            os_scene.reset_cycle_step(sut)

    @classmethod
    def dv_install_in_os(cls, drv_install_path, *conn):
        """
        Install NIC drivers, and check and check results are correct
        All defined NIC type should be covered from config.xxx_xxx_type
        Recommend to use script on SUT OS for completing this

        Args:
            drv_install_path: drive install folder path in host
            *conn: interface.NicPortConnection object

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        for conn in conn:
            port1 = conn.port1
            port2 = conn.port2
            sut1 = port1.sut
            sut2 = port2.sut

            if sut1.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
                install_callback = WindowsNicOp.get_dv_install_callback(port1.nic.type.family)
                install_callback(sut1, drv_install_path)
            else:
                install_callback = LinuxNicOp.get_dv_install_callback(port1.nic.type.family)
                install_callback(sut1, drv_install_path)

            if sut2.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
                install_callback = WindowsNicOp.get_dv_install_callback(port2.nic.type.family)
                install_callback(sut2, drv_install_path)
            else:
                install_callback = LinuxNicOp.get_dv_install_callback(port2.nic.type.family)
                install_callback(sut2, drv_install_path)

    @classmethod
    def _ixvss_prepare_open_share_service(cls, sut):
        """
        open share service before start ixvss tool

        Args:
            sut: client sut instance

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        raise RuntimeError('should be implemented in subclass')

    @classmethod
    def ixvss_stress(cls, duration, package, configuration, flow, *conn):
        """
        Run iwvss/ilvss tool for network io stress, and check results meet connection requirement
        Recommend to use script on SUT OS for completing this

        Args:
            duration: stress timeout
            package: the path of package file for ixvss, recommend to use absolute path
            configuration: configuration name in package
            flow: flow name in package
            *conn: interface.NicPortConnection object

        Returns:
            None
        """
        if not issubclass(cls, WindowsNicOp) and not issubclass(cls, LinuxNicOp):
            raise RuntimeError('only support windows and linux now')

        if not isinstance(duration, int):
            raise RuntimeError('duration must be type of int')

        for conn_inst in conn:
            port1 = conn_inst.port1
            port2 = conn_inst.port2
            sut1 = port1.sut
            sut2 = port2.sut

            if issubclass(cls, WindowsNicOp):
                logger.debug(f'open share on sut 2 with ip {port2.ip}')
                cls._ixvss_prepare_open_share_service(sut2)

            logger.debug(f'run vss on sut1 with ip {port1.ip}')
            ret_code, stdout, stderr = sut1.execute_shell_cmd(
                cls.cmd_ixvss.format(package=package, configuration=configuration, duration=duration, flow=flow),
                60 * duration * 10, cls.tool_path_ixvss)
            # temporarily remove ret code check, because error is for other module test
            # if ret_code != 0:
            #     raise RuntimeError(f'run ixVSS failure, please check log')

            # check ixVSS log, search in verbose log
            re_pattern = f'VERBOSE NET\d+\.NET\d+\n+.*{port2.ip}.*'
            net_conns = re.findall(re_pattern, stdout)
            if len(net_conns) == 0:
                raise RuntimeError(f'No test connection was found for {port1.ip} connected to {port2.ip}')

            found = False
            for net_conn in net_conns:
                if port2.ip in net_conn:
                    logger.debug(f'find available connection: \n{net_conn}')

                    net_name = re.search(r'(NET\d+)\.NET\d+', net_conn).group(1)
                    re_pattern = f'PASSED {net_name}.SYNCIO_NET\d+G'
                    re_search_ret = re.search(re_pattern, stdout)
                    if re_search_ret is None:
                        raise RuntimeError(f'No test connection was found for {port1.ip} connected to {port2.ip}')
                    else:
                        logger.debug(f'ixVSS test passed for {port1.ip} connected to {port2.ip}')

                    found = True
                    break

            if not found:
                raise RuntimeError(f'ixVSS test failed for {port1.ip} connected to {port2.ip}')

    # @classmethod
    # def iperf_stress(cls, duration, proto='tcp', *conn):
    #     """
    #     Run iperf stress with duration seconds, and check results meet connection requirements
    #     Recommend to use script on SUT OS for completing this
    #     Need to run 4 iperf threads for getting the correct tcp throughput (especially for high speed/rate connection)
    #
    #     Args:
    #         duration: stress time, unit is second
    #         proto: tcp/udp
    #         *conn: interface.NicPortConnection object
    #
    #     Returns:
    #         None
    #
    #     Raises:
    #         RuntimeError: If any errors
    #     """
    #     MAX_PROCESS_NUM = 4
    #     DEFAULT_PORT_NO = 5201
    #
    #     if proto != 'tcp':
    #         raise RuntimeError('iperf_stress only support tcp test')
    #
    #     for conn_inst in conn:
    #         port1 = conn_inst.port1
    #         port2 = conn_inst.port2
    #         sut1 = port1.sut
    #         sut2 = port2.sut
    #
    #         log_folder_name = 'iperf_test'
    #         if sut2.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
    #             remote_folder_path = cls.tool_path + '\\iperf3\\' + log_folder_name
    #             cmd = f'{cls.tool_path}\\iperf3\\iperf3.exe'
    #         else:
    #             remote_folder_path = cls.tool_path + '/' + log_folder_name
    #             cmd = 'iperf3'
    #
    #         logger.info(f'-----------kill all iperf3 server process on sut1-----------')
    #         if sut1.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
    #             _, stdout, _ = sut1.execute_shell_cmd('tasklist /FI \"IMAGENAME eq iperf3.exe\"', 30)
    #             if 'iperf3.exe' in stdout:
    #                 sut1.execute_shell_cmd('taskkill /F /IM iperf3.exe', 30)
    #         else:
    #             _, stdout, _ = sut1.execute_shell_cmd(f'ps -e | grep iperf3', 30)
    #             if stdout != '':
    #                 sut1.execute_shell_cmd('kill -9 $(pidof iperf3)')
    #
    #         # create new log folder for running iperf3 in sut
    #         exit_code, stdout, stderr = sut1.execute_shell_cmd(f'mkdir {remote_folder_path}')
    #         if exit_code == 1 and 'exist' in stderr:
    #             OperationSystem[sut1.SUT_PLATFORM].remove_folder(sut1, remote_folder_path)
    #             sut1.execute_shell_cmd(f'mkdir {remote_folder_path}')
    #         exit_code, stdout, stderr = sut2.execute_shell_cmd(f'mkdir {remote_folder_path}')
    #         if exit_code == 1 and 'exist' in stderr:
    #             OperationSystem[sut2.SUT_PLATFORM].remove_folder(sut2, remote_folder_path)
    #             sut2.execute_shell_cmd(f'mkdir {remote_folder_path}')
    #
    #         logger.info(f'-----------start iperf3 server on sut1-----------')
    #         for i in range(MAX_PROCESS_NUM):
    #             port_no = DEFAULT_PORT_NO + i
    #             # --one-off flag mean iperf3 server will stop service after one client test
    #             if sut1.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
    #                 log_file = f'{remote_folder_path}\\server_{port_no}.txt'
    #             else:
    #                 log_file = f'{remote_folder_path}/server_{port_no}.txt'
    #             sut1.execute_shell_cmd_async(f'{cmd} -s --one-off -p {port_no} > {log_file}')
    #
    #         logger.info('-----------start iperf3 client on sut2-----------')
    #         for i in range(MAX_PROCESS_NUM):
    #             port_no = DEFAULT_PORT_NO + i
    #             if sut2.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
    #                 log_file = f'{remote_folder_path}\\client_{port_no}.txt'
    #             else:
    #                 log_file = f'{remote_folder_path}/client_{port_no}.txt'
    #             sut2.execute_shell_cmd_async(f'{cmd} -c {port1.ip} -p {port_no} -t {duration} > {log_file}')
    #
    #         # wait for iperf3 finish transfer
    #         if duration >= 60 * 5:
    #             sleep_time = duration + 90
    #         else:
    #             sleep_time = duration * 1.2
    #         logger.info(f'-----------sleep {sleep_time} sec to wait for iperf3 finish transfer-----------')
    #         time.sleep(sleep_time)
    #
    #         # download log file to check result
    #         sut1.download_to_local(remote_folder_path, LOG_PATH)
    #         sut2.download_to_local(remote_folder_path, LOG_PATH)
    #
    #         # calc sum of transfer and bandwith
    #         transfer = 0
    #         bandwidth = 0
    #         for root, dirs, files in os.walk(os.path.join(LOG_PATH, log_folder_name)):
    #             for file in files:
    #                 if file.startswith('client_') and file.endswith('.txt'):
    #                     log_file = os.path.join(root, file)
    #                     with open(log_file, 'r') as fs:
    #                         data = fs.read()
    #                         receiver_str = re.search(r'.*sec(.*/sec).*receiver', data).group(1)
    #                         receiver_data = re.split(r'\s+', receiver_str.strip())
    #                         transfer += float(receiver_data[0])
    #                         bandwidth += float(receiver_data[2])
    #
    #         transfer_unit = receiver_data[1]
    #         bandwidth_unit = receiver_data[3]
    #
    #         logger.debug(f'iperf total transfer = {transfer} {transfer_unit}')
    #         logger.debug(f'iperf total bandwidth = {bandwidth} {bandwidth_unit}')
    #
    #         # convert data to unified unit
    #         transfer = cls.__iperf3_data_conversion(transfer, transfer_unit[0], bandwidth_unit[0])
    #
    #         logger.debug(f'check transfer > bandwidth / 8 * duration * 0.8 with unit {bandwidth_unit[0]}Bytes')
    #
    #         if transfer > bandwidth / 8 * duration * 0.8:
    #             logger.info(
    #                 f'test iperf3 stress from {port1.nic.type.family} with {port1.ip} to {port2.nic.type.family} with {port2.ip} pass')
    #         else:
    #             raise RuntimeError(
    #                 f'test iperf3 stress from {port1.nic.type.family} with {port1.ip} to {port2.nic.type.family} with {port2.ip} fail')

    @classmethod
    def iperf_stress(cls, duration, proto='tcp', *conn):
        """
        Run iperf stress with duration seconds, and check results meet connection requirements
        Recommend to use script on SUT OS for completing this
        Need to run 4 iperf threads for getting the correct tcp throughput (especially for high speed/rate connection)

        Args:
            duration: stress time, unit is second
            proto: tcp/udp
            *conn: interface.NicPortConnection object

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        MAX_PROCESS_NUM = 4
        DEFAULT_PORT_NO = 5201
        IPERF2_PROCESS_MIN = 14
        IPERF2_PROCESS_MAX = 30

        if proto != 'tcp':
            raise RuntimeError('iperf_stress only support tcp test')

        for conn_inst in conn:
            port1 = conn_inst.port1
            port2 = conn_inst.port2
            sut1 = port1.sut
            sut2 = port2.sut

            log_folder_name = 'iperf_test'
            if sut2.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
                remote_folder_path = cls.tool_path + '\\iperf2\\' + log_folder_name
                cmd = f'{cls.tool_path}\\iperf2\\iperf2.exe'
            else:
                remote_folder_path = cls.tool_path + '/' + log_folder_name
                cmd = 'iperf3'

            logger.info(f'-----------kill all iperf2 server process on sut1-----------')
            if sut1.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
                _, stdout, _ = sut1.execute_shell_cmd('tasklist /FI \"IMAGENAME eq iperf.exe\"', 30)
                if 'iperf.exe' in stdout:
                    sut1.execute_shell_cmd('taskkill /F /IM iperf.exe', 30)
            else:
                _, stdout, _ = sut1.execute_shell_cmd(f'ps -e | grep iperf3', 30)
                if stdout != '':
                    sut1.execute_shell_cmd('kill -9 $(pidof iperf3)')

            # create new log folder for running iperf3 in sut
            exit_code, stdout, stderr = sut1.execute_shell_cmd(f'mkdir {remote_folder_path}')
            if exit_code == 1 and 'exist' in stderr:
                OperationSystem[sut1.SUT_PLATFORM].remove_folder(sut1, remote_folder_path)
                sut1.execute_shell_cmd(f'mkdir {remote_folder_path}')
            exit_code, stdout, stderr = sut2.execute_shell_cmd(f'mkdir {remote_folder_path}')
            if exit_code == 1 and 'exist' in stderr:
                OperationSystem[sut2.SUT_PLATFORM].remove_folder(sut2, remote_folder_path)
                sut2.execute_shell_cmd(f'mkdir {remote_folder_path}')

            if sut1.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
                for i in range(IPERF2_PROCESS_MIN, IPERF2_PROCESS_MAX):
                    logger.info(f'-----------start iperf2 server on sut1-----------')
                    port_no = DEFAULT_PORT_NO
                    log_file = f'{remote_folder_path}\\server_{port_no}_{i}.txt'
                    sut1.execute_shell_cmd_async(f'{cmd} -s  -p {port_no} -P {i}> {log_file}')
                    logger.info('-----------start iperf2 client on sut2-----------')
                    log_file = f'{remote_folder_path}\\client_{port_no}_{i}.txt'
                    sut2.execute_shell_cmd_async(f'{cmd} -c {port1.ip} -p {port_no} -t {duration} -P {i}> {log_file}')

                    if duration >= 60 * 5:
                        sleep_time = duration + 90
                    else:
                        sleep_time = duration * 1.2
                    logger.info(f'-----------sleep {sleep_time} sec to wait for iperf2 finish transfer-----------')
                    time.sleep(sleep_time)

                    # download log file to check result
                    sut1.download_to_local(remote_folder_path, LOG_PATH)
                    sut2.download_to_local(remote_folder_path, LOG_PATH)

                    # calc sum of transfer and bandwith
                    transfer = 0
                    bandwidth = 0
                    for root, dirs, files in os.walk(os.path.join(LOG_PATH, log_folder_name)):
                        for file in files:
                            if file.startswith('client_{}_{}'.format(port_no, i)) and file.endswith('.txt'):
                                log_file = os.path.join(root, file)
                                with open(log_file, 'r') as fs:
                                    data = fs.read()
                                    receiver_str = re.search(r'.*SUM.*sec(.*/sec)', data).group(1)
                                    receiver_data = re.split(r'\s+', receiver_str.strip())
                                    transfer = float(receiver_data[0])
                                    bandwidth = float(receiver_data[2])

                    transfer_unit = receiver_data[1]
                    bandwidth_unit = receiver_data[3]

                    logger.debug(f'iperf total transfer = {transfer} {transfer_unit}')
                    logger.debug(f'iperf total bandwidth = {bandwidth} {bandwidth_unit}')

                    # convert data to unified unit
                #    transfer = cls.__iperf3_data_conversion(transfer, transfer_unit[0], bandwidth_unit[0])
                    logger.debug(f'iperf2 port num = {i} bandwidth = {bandwidth}')
                    if bandwidth > port1.nic.type.rate * 0.8:
                        break

                if bandwidth > port1.nic.type.rate * 0.8:
                    logger.info(
                        f'test iperf2 stress from {port1.nic.type.family} with {port1.ip} to {port2.nic.type.family} with {port2.ip} pass')
                else:
                    raise RuntimeError(
                        f'test iperf2 stress from {port1.nic.type.family} with {port1.ip} to {port2.nic.type.family} with {port2.ip} fail')

            #LINUX
            else:
                if sut1.SUT_PLATFORM == SUT_PLATFORM.LINUX:
                    for i in range(MAX_PROCESS_NUM):
                        port_no = DEFAULT_PORT_NO + i
                        log_file = f'{remote_folder_path}/server_{port_no}.txt'
                        sut1.execute_shell_cmd_async(f'{cmd} -s --one-off -p {port_no} > {log_file}')
                if sut2.SUT_PLATFORM == SUT_PLATFORM.LINUX:
                    for i in range(MAX_PROCESS_NUM):
                        port_no = DEFAULT_PORT_NO + i
                        log_file = f'{remote_folder_path}/client_{port_no}.txt'
                        sut2.execute_shell_cmd_async(f'{cmd} -c {port1.ip} -p {port_no} -t {duration} > {log_file}')
                # wait for iperf3 finish transfer
                if duration >= 60 * 5:
                    sleep_time = duration + 90
                else:
                    sleep_time = duration * 1.2
                logger.info(f'-----------sleep {sleep_time} sec to wait for iperf3 finish transfer-----------')
                time.sleep(sleep_time)

                # download log file to check result
                sut1.download_to_local(remote_folder_path, LOG_PATH)
                sut2.download_to_local(remote_folder_path, LOG_PATH)

                # calc sum of transfer and bandwith
                transfer = 0
                bandwidth = 0
                for root, dirs, files in os.walk(os.path.join(LOG_PATH, log_folder_name)):
                    for file in files:
                        if file.startswith('client_') and file.endswith('.txt'):
                            log_file = os.path.join(root, file)
                            with open(log_file, 'r') as fs:
                                data = fs.read()
                                receiver_str = re.search(r'.*sec(.*/sec).*receiver', data).group(1)
                                receiver_data = re.split(r'\s+', receiver_str.strip())
                                transfer += float(receiver_data[0])
                                bandwidth += float(receiver_data[2])

                transfer_unit = receiver_data[1]
                bandwidth_unit = receiver_data[3]

                logger.debug(f'iperf total transfer = {transfer} {transfer_unit}')
                logger.debug(f'iperf total bandwidth = {bandwidth} {bandwidth_unit}')

                # convert data to unified unit
            #    transfer = cls.__iperf3_data_conversion(transfer, transfer_unit[0], bandwidth_unit[0])

                logger.debug(f'check transfer > bandwidth / 8 * duration * 0.8 with unit {bandwidth_unit[0]}Bytes')

                if bandwidth > port1.nic.type.rate * 0.8:
                #if transfer > bandwidth / 8 * duration * 0.8:
                    logger.info(
                        f'test iperf3 stress from {port1.nic.type.family} with {port1.ip} to {port2.nic.type.family} with {port2.ip} pass')
                else:
                    raise RuntimeError(
                        f'test iperf3 stress from {port1.nic.type.family} with {port1.ip} to {port2.nic.type.family} with {port2.ip} fail')

    @classmethod
    def __iperf3_data_conversion(cls, number, old_unit, new_unit):
        UNIT = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y', 'B')

        old_unit_index = UNIT.index(old_unit.upper())
        new_unit_index = UNIT.index(new_unit.upper())

        return number * (1024 ** (old_unit_index - new_unit_index))

    @classmethod
    def switch_infiniband_mode(self, sut, mode, sutos='rhel'):
        if sutos == "rhel":
            sut.execute_shell_cmd("mst start & systemctl start opensm")
            _, stdout, _ = sut.execute_shell_cmd("mst status |grep -i mt | awk -F ' ' '{print $1}'")
            retcode, _, _ = sut.execute_shell_cmd(
                "mlxconfig -y -d {} query |grep -i link_type |grep {}".format(stdout.strip(), mode))
            if retcode != 0:
                num = 1 if mode == "IB" else 2
                _, stdout, _ = sut.execute_shell_cmd("mst status |grep -i mt | awk -F ' ' '{print $1}'")
                sut.execute_shell_cmd(
                    "mlxconfig -y -d {0} set LINK_TYPE_P1={1} LINK_TYPE_P2={1}".format(stdout.strip(), num))
                sut.execute_shell_cmd("systemctl stop opensm")
                retcode = sut.execute_shell_cmd("mlxfwreset -y --device {} reset".format(stdout.strip()), timeout=300)[
                    0]
                assert retcode == 0
                time.sleep(10)
                sut.execute_shell_cmd("mst start & systemctl start opensm")
                retcode, _, _ = sut.execute_shell_cmd(
                    "mlxconfig -y -d {} query |grep -i link_type |grep {}".format(stdout.strip(), mode))
                Case.expect("set infiniband mode to {} successful".format(mode), retcode == 0)
        else:
            mft_path = "C:\\Program Files\\Mellanox\\WinMFT"
            stdout = sut.execute_shell_cmd("mst status", cwd=mft_path)[1]
            mst_dev = re.search("MST devices:[\d\D]*\s+(\w+)", stdout).group(1)
            mode_value = 1 if mode == "IB" else 2
            retcode = sut.execute_shell_cmd(
                "mlxconfig.exe -y -d {0} set LINK_TYPE_P1={1} LINK_TYPE_P2={1}".format(mst_dev, mode_value),
                cwd=mft_path)[0]
            Case.expect("set mellanox to ETH mode", retcode == 0)
            retcode = sut.execute_shell_cmd("mlxfwreset -y --device {} reset".format(mst_dev), timeout=300)[0]
            Case.expect("reset mellanox successfully", retcode == 0)
            time.sleep(10)

    @classmethod
    def unzip_tools(cls, sut, tool, unzip_dir, flag=False):
        if sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
            logger.info(f"Start to unzip {tool} ...")
            if tool.endswith(".exe"):
                ret, out, err = sut.execute_shell_cmd(f"unzip.exe -o {tool} -d {unzip_dir}", cwd=cls.tool_path)
            else:
                ret, out, err = sut.execute_shell_cmd("Expand-Archive -Force -Path {} -DestinationPath {}".format(tool, unzip_dir), powershell=True, cwd=cls.tool_path)
                assert ret == 0
                if flag:
                    logger.info("decompress file need to unzip again")
                    exe_file = "{}.exe".format(tool.strip(".zip"))
                    logger.info("Start to unzip {} ...".format(exe_file))
                    ret, out, err = sut.execute_shell_cmd(r"unzip.exe -o .\{0}\{1} -d {0}".format(unzip_dir, exe_file), cwd=cls.tool_path)
            if ret == 0 and err == "":
                return True
        elif sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
            if tool.endswith(".zip"):
                cmd = "unzip -o {} -d {}".format(tool, unzip_dir)
            elif tool.endswith('.rpm'):
                cmd = "rpm -ivh {} --force".format(tool)
            else:
                cmd = "mkdir -p {1} && tar -zxvf {0} -C {1}".format(tool, unzip_dir)
            ret, out, err = sut.execute_shell_cmd(cmd, cwd=cls.tool_path)
            if ret == 0 and err == "":
                sut.execute_shell_cmd("chmod 777 {}/*".format(cls.tool_path))
                return True
        logger.warning("fail to decompress tool {}".format(tool))
        return False

    @classmethod
    def unzip7z_tools(cls, sut, tool, unzip_dir, flag=False):
        if sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS:
            logger.info(f"Start to unzip {tool} ...")
            if tool.endswith(".exe"):
                ret, out, err = sut.execute_shell_cmd(f"unzip.exe -o {tool} -d {unzip_dir}", cwd=cls.tool_path)
            else:
                ret, out, err = sut.execute_shell_cmd(
                    "Expand-Archive -Force -Path {} -DestinationPath {}".format(tool, unzip_dir), powershell=True,
                    cwd=cls.tool_path)
                assert ret == 0
                if flag:
                    logger.info("decompress file need to unzip again")
                    exe_file = "{}.exe".format(tool.strip(".zip"))
                    logger.info("Start to unzip {} ...".format(exe_file))
                    path ='{}\{}'.format(cls.tool_path,unzip_dir)
                    sut.execute_shell_cmd("move 7z.exe  {0}".format(path), cwd=cls.tool_path, timeout=600)
                    sut.execute_shell_cmd(r"7z.exe x -y {0} -aoa".format(exe_file), cwd=path, timeout=600)
                    #sut.execute_shell_cmd(r"A",cwd=cls.tool_path)
            if ret == 0 and err == "":
                return True
        elif sut.SUT_PLATFORM == SUT_PLATFORM.LINUX:
            if tool.endswith(".zip"):
                cmd = "unzip -o {} -d {}".format(tool, unzip_dir)
            elif tool.endswith('.rpm'):
                cmd = "rpm -ivh {} --force".format(tool)
            else:
                cmd = "mkdir -p {1} && tar -zxvf {0} -C {1}".format(tool, unzip_dir)
            ret, out, err = sut.execute_shell_cmd(cmd, cwd=cls.tool_path)
            if ret == 0 and err == "":
                sut.execute_shell_cmd("chmod 777 {}/*".format(cls.tool_path))
                return True
        logger.warning("fail to decompress tool {}".format(tool))
        return False


class LinuxNicOp(GenericNicOp):
    tool_path = '/home/BKCPkg/domains/network'
    cmd_ixvss = r'./t /pkg {package} /reconfig /pc {configuration} /flow {flow} /run /minutes {duration} /V -1 /quit'
    tool_path_ixvss = r'/opt/ilvss/'
    cmd_fio = r'fio --randrepeat=1 --ioengine=mmap --direct=1 --gtod_reduce=1 --name=testnfs --readwrite=randrw --rwmixread=75 --size=4G --filename={test_path}'
    ping = "ping -c 20 {}"
    reboot = "shutdown -r +1"

    check_os_system = "cat /etc/os-release  | egrep -i '^id=' | awk -F '=' '{print $2}'"
    pci_serial_numbers = "lspci | grep -i {}"
    ifcfg_name = "/sys/bus/pci/devices/0000:{}/net/"

    @staticmethod
    def ping_result_check(ping_stdout):
        loss_data = re.search(r'(\d+)% packet loss', ping_stdout).group(1)
        # if loss percentage larger than 60%, check fail
        if int(loss_data) > 60:
            return False
        else:
            return True

    @classmethod
    def ip_config(cls, port, nic_port_index):
        sut = port.sut
        # step 1 get sut OS system
        sut_os_type = sut.execute_shell_cmd(cls.check_os_system)[1].strip().replace("\"", "")
        if 'rhel' in sut_os_type:
            sut_os_type = "redhat"

        # step 2 Get the corresponding network card (PCI) name according to the system
        nic_id = port.nic.id_in_os.get(sut_os_type)

        # step 3 Get the MAC addresses of all network ports under the network card
        ether_name = cls.get_ether_name(sut, nic_id, nic_port_index)

        # work around for Mellanox ib mode, use 'ifconfig <ether_name> <ip>/24 up' to set ip directly
        if ether_name.startswith('ib'):
            ret, _, _ = sut.execute_shell_cmd(f'ifconfig {ether_name} {port.ip}/24 up')
            assert ret == 0
            _, stdout, _ = sut.execute_shell_cmd(f'ifconfig {ether_name}')
            assert f'inet {port.ip}' in stdout

            return

        # step 4 Compared with the incoming Mac, if it is wrong, it will prompt or report an error. If it matches, it will set the network card
        mac_address = cls.get_mac_address(sut, nic_id, nic_port_index)

        # step 5 Configure different network card configuration files according to the system
        cur_path = os.path.dirname(os.path.abspath(__file__))
        ifcfg_template = cls.ifcfg.replace(' ', '')
        if cls.ipv6_enable:
            network_tag = cls.ipv6_network_tag.split(",")
        else:
            network_tag = cls.ipv4_network_tag.split(",")
        network_tag_value = (mac_address, port.ip, ether_name)

        for i in range(len(network_tag)):
            old_str = f'{network_tag[i]}='
            new_str = f'{network_tag[i]}={network_tag_value[i]}'
            ifcfg_template = ifcfg_template.replace(old_str, new_str)

        new_cfg_filename = 'ifcfg-{}'.format(ether_name)

        with open(os.path.join(cur_path, new_cfg_filename), 'w') as f:
            f.write(ifcfg_template)

        # step 6 upload network configuration file
        local_file_path = os.path.join(cur_path, os.path.join(cur_path, new_cfg_filename))
        sut.upload_to_remote(local_file_path, "/tmp/")

        #  step 7 delete locate network configuration file
        os.remove(local_file_path)

        # step 8 move network configuration file to /etc/sysconfig/network-scripts/
        sut.execute_shell_cmd(f'cp -rf /tmp/{new_cfg_filename}  {cls.network_path}')

        # step 9 restart network manager
        if "redhat" or "centos" in sut_os_type:
            sut.execute_shell_cmd(f"ifup {ether_name}", timeout=60)
        else:
            sut.execute_shell_cmd(cls.restart_network_cmd, timeout=60)

    @classmethod
    def get_mac_address(cls, sut, nic_id, nic_port_index):
        _, nics, _ = sut.execute_shell_cmd(f'lspci | grep -i {nic_id}')
        if nics == '':
            raise RuntimeError(f'can not find any nic according to id {nic_id}')
        nics = str(nics)[:-1].split('\n')

        nic_info = nics[nic_port_index].strip().split(' ')
        bdf = nic_info[0]
        _, ether_name, _ = sut.execute_shell_cmd(f'ls /sys/bus/pci/devices/0000:{bdf}/net')
        ether_name = str(ether_name).replace('\n', '')
        _, mac, _ = sut.execute_shell_cmd(f'ifconfig {ether_name} | grep -i ether')
        mac = str(mac).strip().split(' ')

        return mac[1]

    @classmethod
    def get_ether_name(cls, sut, nic_id, nic_port_index):
        _, nics, _ = sut.execute_shell_cmd(f'lspci | grep -i {nic_id}')
        if nics == '':
            raise RuntimeError(f'can not find any nic according to id {nic_id}')
        nics = str(nics)[:-1].split('\n')

        nic_info = nics[nic_port_index].strip().split(' ')
        bdf = nic_info[0]
        _, ether_name, std_err = sut.execute_shell_cmd(f'ls /sys/bus/pci/devices/0000:{bdf}/net')
        if ether_name == '':
            raise RuntimeError(f'can not get ether name for {std_err}')
        ether_name = str(ether_name).replace('\n', '')

        return ether_name

    @classmethod
    def fio_stress(cls, *conn):
        """
        Run fio tool for network io stress, and check results meet connection requirement

        Args:
            *conn: interface.NicPortConnection object

        Returns:
            None
        """
        for conn_inst in conn:
            port1 = conn_inst.port1
            port2 = conn_inst.port2
            sut1 = port1.sut
            sut2 = port2.sut

            logger.debug('Disable SEL Linux & firewall')
            sut1.execute_shell_cmd('setenforce 0')
            sut1.execute_shell_cmd('systemctl stop firewalld')
            sut2.execute_shell_cmd('setenforce 0')
            sut2.execute_shell_cmd('systemctl stop firewalld')

            logger.debug('SUT2 exports directory to SUT1 for remote nfs mount')
            sut2.execute_shell_cmd('mkdir -p /home/nfstemp')
            sut2.execute_shell_cmd('touch /home/nfstemp/target')
            sut2.execute_shell_cmd(f'echo "/home/nfstemp {port1.ip}(rw,sync,no_root_squash)" > /etc/exports')
            sut2.execute_shell_cmd('systemctl restart nfs-server')
            ret, stdout, stderr = sut2.execute_shell_cmd('showmount -e')
            Case.expect('nfs service is open', f'/home/nfstemp {port1.ip}' in stdout)

            logger.debug('SUT1 mount SUT2 directory')
            sut1.execute_shell_cmd('mkdir -p /home/testdir')
            sut1.execute_shell_cmd(f'mount {port2.ip}:/home/nfstemp /home/testdir')
            ret, stdout, stderr = sut1.execute_shell_cmd('ls /home/testdir')
            Case.expect('sut1 mount sut2 share folder successfully', 'target' in stdout)

            ret, stdout, stderr = sut1.execute_shell_cmd(cls.cmd_fio.format(test_path='/home/testdir/testfile'),
                                                         timeout=60000)

            logger.debug('restore env')
            sut1.execute_shell_cmd('umount /home/testdir')
            sut2.execute_shell_cmd('systemctl stop nfs-server')
            sut2.execute_shell_cmd('rm -f -r /home/nfstemp')

            assert ret == 0, 'command complete with error'
            assert 'testnfs: (groupid=0, jobs=1): err= 0' in stdout, 'fio stress test with error'

    @classmethod
    def get_dv_install_callback(cls, nic_type):
        """
        get driver install callback for nic type

        Args:
            nic_type: nic type

        Returns:
            Callable: callback function for nic type

        Raises:
            RuntimeError: If any errors
        """
        if nic_type == 'Mellanox':
            return cls.__dv_install_mellanox
        elif nic_type in INTEL_NIC_SERIES:
            return cls.__dv_install_intel
        else:
            raise ValueError(f'No support for this nic_type:{nic_type}')

    @classmethod
    def __dv_install_intel(cls, sut, drv_install_path):
        """
        Update Intel NIC driver, and check results are correct

        Args:
            sut: sut instance
            drv_install_path: drive install folder path in host

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        assert sut.SUT_PLATFORM == SUT_PLATFORM.LINUX

        drv_package_name = os.path.basename(drv_install_path)

        logger.info('-----run make install to compile the driver module-----')
        cwd = f'{drv_install_path}/src'
        ret, stdout, stderr = sut.execute_shell_cmd(f'make install', timeout=60 * 5, cwd=cwd)
        logger.info(f'compile the driver module info:\n{stdout}')
        logger.debug(f'compile the driver module err:\n{stderr}')

        logger.info('-----load the module-----')
        # before loading module, clear dmesg firstly
        sut.execute_shell_cmd(f'dmesg -C', timeout=60 * 5)

        module_name = drv_package_name.split('-')[0]
        # rmmod command -- remove old driver,  -v for command modprobe is enable more messages
        ret, stdout, stderr = sut.execute_shell_cmd(f'rmmod {module_name}; modprobe -v {module_name}', timeout=60 * 5)
        logger.info(f'load module info: {stdout}')
        logger.debug(f'load module err: {stderr}')

        logger.info('-----get interface name of nic from dmesg-----')
        ret, stdout, stderr = sut.execute_shell_cmd(f'dmesg', timeout=60 * 5)
        logger.info(f'load module dmesg info:\n{stdout}')
        devs = re.findall(r'ADDRCONF\(NETDEV_UP\):(.*):', stdout)
        devs = set(devs)

        # check driver information to make sure installation is correct
        for dev in devs:
            dev = str(dev).rstrip()
            _, drv_info, _ = sut.execute_shell_cmd(f'ethtool -i {dev}')
            logger.info(f'driver information for {dev} is:\n{drv_info}')
            if re.search(f'driver:\s+{module_name}', drv_info) is None:
                raise RuntimeError('driver module is not correct, please check install log')

            ret = re.search(f'version:\s+(\d[\d\.]+)', drv_info)
            drv_version = ret.group(1)
            if drv_version not in drv_package_name:
                raise RuntimeError('driver version is not correct, please check install log')

    @classmethod
    def __dv_install_mellanox(cls, sut, drv_install_path):
        """
        Update MELLANOX NIC driver, and check results are correct

        Args:
            sut: sut instance
            drv_install_path: drive install folder path in host

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        assert sut.SUT_PLATFORM == SUT_PLATFORM.LINUX

        cwd = drv_install_path

        ret_code, stdout, stderr = sut.execute_shell_cmd('ls *.iso', cwd=cwd)
        iso_file = stdout.replace('\r\n', '').strip()

        # mount iso file to /mnt
        sut.execute_shell_cmd(f'mount -o ro,loop {iso_file} /mnt', timeout=60 * 10, cwd=cwd)
        # install driver only without fw update
        ret_code, stdout, stderr = sut.execute_shell_cmd('./mlnxofedinstall --force --without-fw-update',
                                                         timeout=60 * 10, cwd='/mnt')
        logger.info(f'install driver info:\n{stdout}')
        logger.debug(f'install driver err info:\n{stderr}')

        if 'Installation finished successfully' not in stdout:
            raise RuntimeError('Install driver failed, please check log')

        Linux.reset_cycle_step(sut)


class RedhatNicOp(LinuxNicOp):
    network_path = "/etc/sysconfig/network-scripts/"
    restart_network_cmd = "sudo nmcli networking off && sudo nmcli networking on"
    ifcfg = """
        HWADDR=
        TYPE=Ethernet
        PROXY_METHOD=none
        BROWSER_ONLY=no
        BOOTPROTO=static
        DEFROUTE=yes
        IPV4_FAILURE_FATAL=no
        IPV6INIT=yes
        IPV6_AUTOCONF=yes
        IPV6_DEFROUTE=yes
        IPV6_FAILURE_FATAL=no
        IPV6_ADDR_GEN_MODE=stable-privacy
        IPV6ADDR=
        NAME=
        ONBOOT=yes
        IPADDR=
        PREFIX=24
    """


class CentOSNicOp(LinuxNicOp):
    network_path = "/etc/sysconfig/network-scripts/"
    restart_network_cmd = "sudo nmcli networking off && sudo nmcli networking on"
    ifcfg = """
        HWADDR=
        TYPE=Ethernet
        PROXY_METHOD=none
        BROWSER_ONLY=no
        BOOTPROTO=static
        DEFROUTE=yes
        IPV4_FAILURE_FATAL=no
        IPV6INIT=yes
        IPV6_AUTOCONF=yes
        IPV6_DEFROUTE=yes
        IPV6_FAILURE_FATAL=no
        IPV6_ADDR_GEN_MODE=stable-privacy
        IPV6ADDR=
        NAME=
        ONBOOT=yes
        IPADDR=
        PREFIX=24
    """


class SlesNicOp(LinuxNicOp):
    network_path = "/etc/sysconfig/network/"
    restart_network_cmd = "service network restart"
    ifcfg = """
        IPADDR=
        NETMASK=255.255.255.0
        BOOTPROTO=static
        STARTMODE='auto'
        NAME=
        HWADDR=
    """


class UbuntuNicOp(LinuxNicOp):
    pass


class AliOSNicOp(LinuxNicOp):
    pass


class WindowsNicOp(GenericNicOp):
    tool_path = 'C:\\BKCPkg\\domains\\network'
    cmd_ixvss = r't /pkg {package} /reconfig /pc {configuration} /flow {flow} /run /minutes {duration} /V -1 /quit'
    tool_path_ixvss = 'c:\\iwVSS'
    ping = "ping -n 20 {}"
    reboot = "shutdown -r -t 60"

    @staticmethod
    def ping_result_check(ping_stdout):
        loss_data = re.search(r'\((\d+)%\sloss\)', ping_stdout).group(1)
        # if loss percentage larger than 60%, check fail
        if int(loss_data) > 60:
            return False
        else:
            return True

    @classmethod
    def ip_config(cls, port, nic_port_index):
        sut = port.sut
        if sut.default_os == 'Windows Boot Manager':
            os_type = 'windows'
        nic_id = port.nic.id_in_os.get(os_type)
        pci_name = cls.get_ether_name(sut, nic_id, nic_port_index)

        if cls.ipv6_enable:
            clear_cmd = f'netsh interface ipv6 delete address "{pci_name}" {port.ip}'
            if port.ip in sut.execute_shell_cmd('ipconfig')[1]:
                sut.execute_shell_cmd(clear_cmd)
                time.sleep(1)
            cmd = f'netsh interface ipv6 add address "{pci_name}" {port.ip}'
        else:
            cmd = f'netsh interface ip set address name="{pci_name}" source=static addr={port.ip} mask=255.255.255.0'
        sut.execute_shell_cmd(cmd)

    @classmethod
    def get_mac_address(cls, sut, nic_id, nic_port_index):
        _, stdout, _ = sut.execute_shell_cmd('ipconfig/all')
        nic_info = stdout.split('Ethernet adapter')

        mac_addresses = []
        for info in nic_info:
            if nic_id in info:
                pci_mac = re.search(r'Physical Address[\.\s]+:(.+)', info)
                mac_addresses.append(pci_mac.group(1).strip())

        if len(mac_addresses) == 0:
            raise RuntimeError(f'can not find any nic according to id {nic_id}')

        mac_addresses.sort(key=lambda mac_address: mac_address[-2:])

        return mac_addresses[nic_port_index]

    @classmethod
    def get_ether_name(cls, sut, nic_id, nic_port_index):
        _, stdout, _ = sut.execute_shell_cmd('ipconfig/all')
        nic_info = stdout.split('Ethernet adapter')

        ether_info = []
        for info in nic_info:
            if nic_id in info:
                pci_mac = re.search(r'Physical Address[\.\s]+:(.+)', info)
                pci_mac = pci_mac.group(1).strip()

                pci_name = re.search(r'(Ethernet[\d\s]*):', info)
                pci_name = pci_name.group(1).strip()

                ether_info.append((pci_name, pci_mac))

        if len(ether_info) == 0:
            raise RuntimeError(f'can not find any nic according to id {nic_id}')

        # order by mac address
        ether_info.sort(key=lambda pci_info: pci_info[1][-2:])

        return ether_info[nic_port_index][0]

    @classmethod
    def _ixvss_prepare_open_share_service(cls, sut):
        """
        open share service before start ixvss tool

        Args:
            sut: client sut instance

        Returns:
            None
        """
        # check and open SMB2 share service if it is not opened
        # command reference: https://docs.microsoft.com/zh-cn/windows-server/storage/file-server/troubleshoot/
        # detect-enable-and-disable-smbv1-v2-v3
        ret = sut.execute_shell_cmd('Get-SmbServerConfiguration | Select EnableSMB2Protocol', powershell=True)
        if 'False' in ret[1]:
            sut.execute_shell_cmd('Set-SmbServerConfiguration -EnableSMB2Protocol $true -force', powershell=True)
            ret = sut.execute_shell_cmd('Get-SmbServerConfiguration | Select EnableSMB2Protocol', powershell=True)
            assert 'True' in ret[1], 'open SMB2 share service fail'

        # check and share C partition as share name 'C$' and give full permission to everyone
        ret = sut.execute_shell_cmd('net share C$')
        if 'C:\\' not in ret[1] and 'Everyone, FULL' not in ret[1]:
            ret = sut.execute_shell_cmd('net share C$=C:\\ /GRANT:Everyone,FULL /remark:\"Default share\"')
            assert 'shared successfully' in ret[1], 'share C partition fail'

    @classmethod
    def get_dv_install_callback(cls, nic_type):
        """
        get driver install callback for nic type

        Args:
            nic_type: nic type

        Returns:
            Callable: callback function for nic type

        Raises:
            RuntimeError: If any errors
        """
        if nic_type == 'Mellanox':
            return cls.__dv_install_mellanox
        elif nic_type in INTEL_NIC_SERIES:
            return cls.__dv_install_intel
        else:
            raise ValueError(f'No support for this nic_type:{nic_type}')

    @classmethod
    def __dv_install_intel(cls, sut, drv_install_path):
        """
        Update NIC driver for intel, and check results are correct

        Args:
            sut: sut instance
            drv_install_path: drive install folder path in host

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        # ref link: https://downloadmirror.intel.com/30400/eng/readme_26_1.htm
        assert sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS
        cwd = drv_install_path
        install_cmd = f'DxSetup.exe /qn /liew {cwd}\\install.log'

        # run install command and save log
        sut.execute_shell_cmd(install_cmd, timeout=60 * 10, cwd=cwd)
        ret_code, stdout, stderr = sut.execute_shell_cmd('type install.log', cwd=cwd)
        logger.info(f'install driver result log:{stdout}')

        if 'success or error status: 0' not in stdout:
            raise RuntimeError('Install driver failed, please check log')

        Windows.reset_cycle_step(sut)

    @classmethod
    def __dv_install_mellanox(cls, sut, drv_install_path):
        assert sut.SUT_PLATFORM == SUT_PLATFORM.WINDOWS

        ret_code, stdout, stderr = sut.execute_shell_cmd('dir MLNX_*.exe /b', cwd=drv_install_path)
        install_cmd = stdout.replace('\r\n', '').strip()
        install_cmd = f'{install_cmd} /S /v/qn /v"/l*vx {drv_install_path}\\install.log"'

        # run install command and save log
        sut.execute_shell_cmd(install_cmd, timeout=60 * 10, cwd=drv_install_path)
        ret_code, stdout, stderr = sut.execute_shell_cmd('type install.log', cwd=drv_install_path)
        logger.info(f'install driver result log:\n{stdout}')

        if 'success or error status: 0' not in stdout:
            raise RuntimeError('Install driver failed, please check log')

        Windows.reset_cycle_step(sut)
