from src.network.lib import *
CASE_DESC = [
    'connect sut1 col nic port to sut2 col nic port cable',
    'create 4 VMs on both SUT1 and SUT2',
    'disable vmdq on ethernet, then run iperf stress for 300 sec on all vms',
    'enable vmdq on ethernet, then run iperf stress for 300 sec on all vms',
    'compare two stress result'
]

VM_NUM = 4
VM_CMD_PREFIX = ("$account = 'administrator' ; $password = 'intel_123'",
                 "$secpwd = convertTo-secureString $password -asplaintext -force",
                 "$cred = new-object System.Management.Automation.PSCredential -argumentlist $account, $secpwd")


def __execute_powershell_cmd(self, cmd, timeout=600):
    ret, stdout, stderr = self.execute_shell_cmd(cmd, powershell=True, timeout=timeout)
    return ret, stdout, stderr


def __set_vmdq(sut, eth_name, is_enable):
    if is_enable:
        enable_value = 'Enabled'
    else:
        enable_value = 'Disabled'
    set_vmdq_cmd = 'Set-NetAdapterAdvancedProperty -Name "{}" -DisplayName "Virtual Machine Queues" -DisplayValue "{}"'
    sut.execute_powershell_cmd(set_vmdq_cmd.format(eth_name, enable_value,timeout=180))
    get_vmdq_cmd = 'Get-NetAdapterAdvancedProperty -Name "{}" -DisplayName "Virtual Machine Queues"'
    ret, stdout, stderr = sut.execute_powershell_cmd(get_vmdq_cmd.format(eth_name))
    Case.expect('set vmdq successfully', enable_value in stdout)


def __get_vm_name(index):
    return 'vm{}'.format(index)


def __install_vm(sut):
    vhdx_template_path = r'c:\BKCPkg\domains\network'
    vhdx_template_filename = r'WIN.vhdx'
    sut.execute_powershell_cmd(r"Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart")
    sut.execute_powershell_cmd(r"Install-WindowsFeature -Name RSAT-Hyper-V-Tools")
    # reset ???
    for i in range(VM_NUM):
        new_vhdm_filename = 'WIN_vm{}.vhdx'.format(i)
        sut.execute_powershell_cmd(
            'copy {0}\\{1} {0}\\{2}'.format(vhdx_template_path, vhdx_template_filename, new_vhdm_filename))
        vm_name = __get_vm_name(i)
        ret = sut.execute_powershell_cmd(
            'New-VM -Name {} -MemoryStartupBytes 2GB -VHDPath {}\\{}'.format(vm_name, vhdx_template_path,
                                                                             new_vhdm_filename))
        Case.expect('install new vm successfully', ret[0] == 0)


def __add_network_to_vm(sut, eth_name):
    sut.execute_powershell_cmd(
        "new-vmswitch -name 'vmdq_vswitch' -allowmanagementos $True -netadaptername '{}'".format(eth_name))
    for i in range(VM_NUM):
        vm_name = __get_vm_name(i)
        ret = sut.execute_powershell_cmd(
            r"add-vmnetworkadapter -vmname {0} -switchname 'vmdq_vswitch' ; start-VM -name {0}".format(vm_name))
        Case.expect('start vm successfully', ret[0] == 0)

    # sleep for a while to wait for vm finish booting
    time.sleep(60)

    for i in range(VM_NUM):
        # try to run dir command in vm to make sure vm is stable what can execute command
        vm_name = __get_vm_name(i)
        retry = 0
        while retry < 15:
            ret, _, stderr = sut.execute_powershell_cmd(__get_vm_cmd(vm_name, 'dir'))
            if ret == 0 and stderr == '':
                break
            else:
                retry += 1
                time.sleep(30)
        if retry >= 15:
            raise RuntimeError(f'can not execute command in {vm_name} of {sut.sut_name}')


def __get_vm_cmd(vm_name, cmd):
    vm_cmd_template = (*VM_CMD_PREFIX, "Invoke-Command -VMName {} -Credential $cred -ScriptBlock {}")
    vm_cmd = ' ; '.join(vm_cmd_template)
    script_block = '{' + cmd + '}'
    vm_cmd = vm_cmd.format(vm_name, script_block)

    return vm_cmd


def __get_vm_ether_ip(sut_index, vm_index):
    """
            sut1                    sut2
    vm0     192.168.10.10-----------192.168.10.20
    vm1     192.168.10.11-----------192.168.10.21
    vm2     192.168.10.12-----------192.168.10.22
    vm3     192.168.10.13-----------192.168.10.23
    """
    return '192.168.10.{}{}'.format(sut_index + 1, vm_index)


def __set_vm_netadapter_ip(sut1, sut2):
    for i in range(VM_NUM):
        # set sut1 vm{i} ip
        get_netadapter_cmd = "wmic path win32_networkadapter get \'Description,NetConnectionID,NetEnabled\'"
        sut1_vm_name = __get_vm_name(i)
        ret = sut1.execute_powershell_cmd(__get_vm_cmd(sut1_vm_name, get_netadapter_cmd))
        vm_ether_name = re.search(".*Hyper.*(Ethernet \d+)\s+TRUE", ret[1]).group(1)
        turn_off_firewall_cmd = "netsh advfirewall set allprofiles state off"
        ret = sut1.execute_powershell_cmd(__get_vm_cmd(sut1_vm_name, turn_off_firewall_cmd))
        Case.expect('turn off firewall successfully', ret[0] == 0)
        sut1_vm_ip = __get_vm_ether_ip(0, i)
        set_ip_cmd = 'netsh interface ip set address \'{}\' static {} 255.255.0.0'.format(vm_ether_name, sut1_vm_ip)
        ret = sut1.execute_powershell_cmd(__get_vm_cmd(sut1_vm_name, set_ip_cmd))
        Case.expect('set ip successfully', ret[0] == 0)

        # set sut2 vm{i} ip
        get_netadapter_cmd = "wmic path win32_networkadapter get \'Description,NetConnectionID,NetEnabled\'"
        sut2_vm_name = __get_vm_name(i)
        ret = sut2.execute_powershell_cmd(__get_vm_cmd(sut2_vm_name, get_netadapter_cmd))
        vm_ether_name = re.search(".*Hyper.*(Ethernet \d+)\s+TRUE", ret[1]).group(1)
        turn_off_firewall_cmd = "netsh advfirewall set allprofiles state off"
        ret = sut2.execute_powershell_cmd(__get_vm_cmd(sut2_vm_name, turn_off_firewall_cmd))
        Case.expect('turn off firewall successfully', ret[0] == 0)
        sut2_vm_ip = __get_vm_ether_ip(1, i)
        set_ip_cmd = 'netsh interface ip set address \'{}\' static {} 255.255.0.0'.format(vm_ether_name, sut2_vm_ip)
        ret = sut2.execute_powershell_cmd(__get_vm_cmd(sut2_vm_name, set_ip_cmd))
        Case.expect('set ip successfully', ret[0] == 0)

        # ping sut1 vm{i} to sut2 vm{i} to make sure network connectable
        ping_cmd = 'ping -n 10 {}'.format(sut2_vm_ip)
        ret = sut1.execute_powershell_cmd(__get_vm_cmd(sut1_vm_name, ping_cmd))
        loss_data = re.search(r'\((\d+)%\sloss\)', ret[1]).group(1)
        # if loss percentage larger than 20%, check fail
        Case.expect('ping sut2 {} {} successfully'.format(sut2_vm_name, sut2_vm_ip), int(loss_data) < 20)

        ping_cmd = 'ping -n 10 {}'.format(sut1_vm_ip)
        ret = sut2.execute_powershell_cmd(__get_vm_cmd(sut2_vm_name, ping_cmd))
        loss_data = re.search(r'\((\d+)%\sloss\)', ret[1]).group(1)
        # if loss percentage larger than 20%, check fail
        Case.expect('ping sut1 {} {} successfully'.format(sut1_vm_name, sut1_vm_ip), int(loss_data) < 20)


def __upload_to_vm(self, vm_name, local_path, remote_path):
    upload_cmd_template = (*VM_CMD_PREFIX,
                           r"$session = New-PSSession -vmname {} -Credential $cred",
                           r"Copy-Item -ToSession $session -Path {} -Destination {}")
    upload_cmd = " ; ".join(upload_cmd_template)
    upload_cmd = upload_cmd.format(vm_name, local_path, remote_path)

    self.execute_powershell_cmd(upload_cmd)


def __download_from_vm(self, vm_name, remote_path, local_path):
    download_cmd_template = (*VM_CMD_PREFIX,
                             r"$session = New-PSSession -vmname {} -Credential $cred",
                             r"Copy-Item -FromSession $session -Path {} -Destination {}")
    download_cmd = " ; ".join(download_cmd_template)
    download_cmd = download_cmd.format(vm_name, remote_path, local_path)

    self.execute_powershell_cmd(download_cmd)


def __vm_execute_shell_cmd_async(self, vm_name, cmd):
    local_path = os.path.join(LOG_PATH, 'vm_shell_cmd_async.bat')
    with open(os.path.join(LOG_PATH, 'vm_shell_cmd_async.bat'), 'w') as file:
        file.write(cmd)
    self.upload_to_remote(local_path, 'c:\\')
    temp_cmd_file = 'c:\\vm_shell_cmd_async.bat'
    self.upload_to_vm(vm_name, temp_cmd_file, temp_cmd_file)
    self.execute_powershell_cmd(
        __get_vm_cmd(vm_name, f'schtasks /create /f /sc onstart /tn _taskname /tr {temp_cmd_file}'))
    self.execute_powershell_cmd(__get_vm_cmd(vm_name, 'schtasks /run /tn _taskname'))
    self.execute_powershell_cmd(__get_vm_cmd(vm_name, 'schtasks /delete /f /tn _taskname'))
    self.execute_powershell_cmd(__get_vm_cmd(vm_name, f'del {temp_cmd_file}'))
    self.execute_powershell_cmd(f'del {temp_cmd_file}')


def __run_iperf_stress_in_vm(sut1, sut1_eth_name, sut2, sut2_eth_name):
    # enable and install Hyper-V
    __install_vm(sut1)
    __install_vm(sut2)

    # add net adapter to vm
    __add_network_to_vm(sut1, sut1_eth_name)
    __add_network_to_vm(sut2, sut2_eth_name)

    # set vm net adapter IP address
    __set_vm_netadapter_ip(sut1, sut2)

    # upload iperf tool to vm
    vm_work_path = r'C:\Users\Administrator\Documents'
    for i in range(VM_NUM):
        vm_name = __get_vm_name(i)
        sut1.upload_to_vm(vm_name, r'C:\BKCPkg\domains\network\iperf3\iperf3.exe', vm_work_path)
        sut1.upload_to_vm(vm_name, r'C:\BKCPkg\domains\network\iperf3\cygwin1.dll', vm_work_path)
        sut2.upload_to_vm(vm_name, r'C:\BKCPkg\domains\network\iperf3\iperf3.exe', vm_work_path)
        sut2.upload_to_vm(vm_name, r'C:\BKCPkg\domains\network\iperf3\cygwin1.dll', vm_work_path)

    # start iperf3 server in sut1 vm
    for i in range(VM_NUM):
        vm_name = __get_vm_name(i)
        iperf_server_cmd = f'{vm_work_path}\\iperf3.exe -s --one-off > c:\\{vm_name}_iperf.txt'
        sut1.vm_execute_shell_cmd_async(vm_name, iperf_server_cmd)

    # start iperf3 client in sut2 vm
    test_duration = 300  # unit is second
    for i in range(VM_NUM):
        vm_name = __get_vm_name(i)
        sut1_vm_up = __get_vm_ether_ip(0, i)
        iperf_client_cmd = f'{vm_work_path}\\iperf3.exe -c {sut1_vm_up} -t {test_duration} > c:\\{vm_name}_iperf.txt'
        sut2.vm_execute_shell_cmd_async(vm_name, iperf_client_cmd)

    # wait for iperf test end
    Case.sleep(test_duration * 1.2 if test_duration > 300 else test_duration + 90)


def __clean_up_vm(*sut_list):
    for sut_inst in sut_list:
        sut_inst.execute_powershell_cmd(r"stop-vm -Name * ; remove-vmswitch -Name * -force ; remove-vm -Name * -force")


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)
    try:
        Case.prepare("prepare steps")
        boot_to(sut1, sut1.default_os)
        Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

        Case.step('set ipv4')
        valos.ip_assign(conn)

        Case.step("add dynamically method to sut object for extending more function")
        ret, out, err = sut1.execute_shell_cmd('BCDEdit /set hypervisorlaunchtype auto')
        ret, out, err = sut2.execute_shell_cmd('BCDEdit /set hypervisorlaunchtype auto')
        sut1.execute_powershell_cmd = types.MethodType(__execute_powershell_cmd, sut1)
        sut2.execute_powershell_cmd = types.MethodType(__execute_powershell_cmd, sut2)
        sut1.upload_to_vm = types.MethodType(__upload_to_vm, sut1)
        sut2.upload_to_vm = types.MethodType(__upload_to_vm, sut2)
        sut1.download_from_vm = types.MethodType(__download_from_vm, sut1)
        sut2.download_from_vm = types.MethodType(__download_from_vm, sut2)
        sut1.vm_execute_shell_cmd_async = types.MethodType(__vm_execute_shell_cmd_async, sut1)
        sut2.vm_execute_shell_cmd_async = types.MethodType(__vm_execute_shell_cmd_async, sut2)

        Case.step('get ethernet name which will run iperf stress')
        sut1_nic_id = conn.port1.nic.id_in_os.get(sutos)
        sut1_eth_name = valos.get_ether_name(sut1, sut1_nic_id, 0)

        sut2_nic_id = conn.port2.nic.id_in_os.get(sutos)
        sut2_eth_name = valos.get_ether_name(sut2, sut2_nic_id, 0)

        Case.step('enable VT-d and disable ethernet VMDQ')
        set_bios_knobs_step(sut1, *bios_knob('enable_vtd_xmlcli'))
        set_bios_knobs_step(sut2, *bios_knob('enable_vtd_xmlcli'))
        __set_vmdq(sut1, sut1_eth_name, False)
        __set_vmdq(sut2, sut2_eth_name, False)

        Case.step('run iperf stress')
        try:
            __run_iperf_stress_in_vm(sut1, sut1_eth_name, sut2, sut2_eth_name)
        except Exception as e:
            # clean up vm resource before raise exception
            __clean_up_vm(sut1, sut2)
            raise e

        Case.step("download log file")
        for i in range(VM_NUM):
            vm_name = __get_vm_name(i)
            sut2.download_from_vm(vm_name, f'c:\\{vm_name}_iperf.txt', f'c:\\{vm_name}_iperf.txt')
            sut2.download_to_local(f'c:\\{vm_name}_iperf.txt', os.path.join(LOG_PATH, f'vmdq_disable'))

        Case.step('stop vm, remove vm and vm switch to release resource')
        __clean_up_vm(sut1, sut2)

        Case.step('enable ethernet VMDQ')
        __set_vmdq(sut1, sut1_eth_name, True)
        __set_vmdq(sut2, sut2_eth_name, True)

        Case.step('run iperf stress')
        try:
            __run_iperf_stress_in_vm(sut1, sut1_eth_name, sut2, sut2_eth_name)
        except Exception as e:
            # clean up vm resource before raise exception
            __clean_up_vm(sut1, sut2)
            raise e

        Case.step("download log file")
        for i in range(VM_NUM):
            vm_name = __get_vm_name(i)
            sut2.download_from_vm(vm_name, f'c:\\{vm_name}_iperf.txt', f'c:\\{vm_name}_iperf.txt')
            sut2.download_to_local(f'c:\\{vm_name}_iperf.txt', os.path.join(LOG_PATH, f'vmdq_enable'))

        Case.step("stop vm, remove vm and vm switch to release resource")
        __clean_up_vm(sut1, sut2)
        #set_bios_knobs_step(sut1, *bios_knob('disable_vtd_xmlcli'))
        #set_bios_knobs_step(sut2, *bios_knob('disable_vtd_xmlcli'))

        Case.step("compare two test result")
        disable_result = 0
        for i in range(VM_NUM):
            folder = os.path.join(LOG_PATH, 'vmdq_disable')
            file_path = os.path.join(folder, f'vm{i}_iperf.txt')
            with open(file_path, 'r') as fs:
                data = fs.read()
                receiver_str = re.search(r'.*sec(.*/sec).*receiver', data).group(1)
                receiver_data = re.split(r'\s+', receiver_str.strip())
                disable_result += float(receiver_data[0])
        logger.debug(f'total transfer {disable_result} {receiver_data[1]} by vmdq disable')

        enable_result = 0
        for i in range(VM_NUM):
            folder = os.path.join(LOG_PATH, 'vmdq_enable')
            file_path = os.path.join(folder, f'vm{i}_iperf.txt')
            with open(file_path, 'r') as fs:
                data = fs.read()
                receiver_str = re.search(r'.*sec(.*/sec).*receiver', data).group(1)
                receiver_data = re.split(r'\s+', receiver_str.strip())
                enable_result += float(receiver_data[0])
        logger.debug(f'total transfer {enable_result} {receiver_data[1]} by vmdq enable')


    except Exception as e:
        # clean up vm resource before raise exception
        __clean_up_vm(sut1, sut2)
        sut2.execute_shell_cmd("shutdown -r -t 0")
        timeout = 15 * 10 * 60
        logger.info("Wait for the system to enter OS")
        while timeout > 1:
            if sut2.check_system_in_os():
                logger.info("System now back to OS")
                break
            timeout -= 1

        if timeout == 0:
            raise RuntimeError("Wait for the system to reboot timed out")
        raise e



def clean_up(sut):
    from dtaf_core.lib.tklib.steps_lib import cleanup
    if Result.returncode != 0:
        cleanup.to_s5(sut)


def test_main():
    # ParameterParser parses all the embed parameters
    # --help to see all allowed parameters
    user_parameters = ParameterParser.parse_embeded_parameters()
    # add your parameter parsers with list user_parameters

    # if you would like to hardcode to disable clearcmos
    # ParameterParser.bypass_clearcmos = True

    # if commandline provide sut description file by --sut <json file>
    #       generate sut instance from given json file
    #       if multiple files have been provided in command line, only the 1st will take effect for get_default_sut
    #       to get multiple sut, call function get_sut_list instead
    # otherwise
    #       default sut configure file will be loaded
    #       which is defined in basic.config.DEFAULT_SUT_CONFIG_FILE
    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)
    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
