#!/usr/bin/env python

"""
// Hardware Setup Topology
Connect 2 SUTs by a directed cable with test NIC (Or, connect a SUT to a network switch)
SUT1 (NIC) <==========> SUT2 (NIC)
SUT1 (NIC) <==========> NIC Switch
"""


from src.network.inband.network._topology.highlevel_steps import *


# 1001: network_connectivity_enable_disable_l
execute_command('python network.py --step=test_server_connectivity_enable_disable')


# 1002: network_connectivity_reboot_l
reset_to('linux')
execute_command('python network.py --step=test_server_client_connect')


# 1003: network_connectivity_hibernate_w
execute_command('rundll32 powrprof.dll,SetSuspendState 1,1,0')
wait_for(checker_power_state('s5'), 30) 	# low level
push_power_button()        					# low level
wait_for(check_environment('linux'), 30)	# low level
execute_command('python network.py --step=test_server_client_connect')


########################################################################################################################
# Fixme: 1> PI_Networking_Columbiaville_PCIe_ConnectivityEnableDisable_L
boot_to('linux')
execute_command('python network.py --step=prepare_server_client_connection --conn=col_conn_v4')
execute_command('python network.py --step=prepare_server_client_ipaddr')
execute_command('python network.py --step=test_server_client_connect')
run_tcd_block('1001', 3)


########################################################################################################################
# Fixme: 2> PI_Networking_Columbiaville_PCIe_ConnectivityEnableDisable_W
boot_to('windows')
execute_command('python network.py --step=prepare_server_client_connection --conn=col_conn_v4')
execute_command('python network.py --step=prepare_server_client_ipaddr')
execute_command('python network.py --step=test_server_client_connect')
run_tcd_block('1001', 3)


# Fixme: 3> PI_Networking_Columbiaville_PCIe_ConnectivityReboot_L
boot_to('linux')
execute_command('python network.py --step=prepare_server_client_connection --conn=col_conn_v4')
execute_command('python network.py --step=prepare_server_client_ipaddr')
execute_command('python network.py --step=test_server_client_connect')
run_tcd_block('1002', 3)


# Fixme: 4> PI_Networking_Columbiaville_PCIe_ConnectivityReboot_W
boot_to('windows')
execute_command('python network.py --step=prepare_server_client_connection --conn=col_conn_v4')
execute_command('python network.py --step=prepare_server_client_ipaddr')
execute_command('python network.py --step=test_server_client_connect')
run_tcd_block('1002', 3)


# Fixme: 5> PI_Networking_Columbiaville_PCIe_ConnectivityHibernation_W
boot_to('windows')
execute_command('python network.py --step=prepare_server_client_connection --conn=col_conn_v4')
execute_command('python network.py --step=prepare_server_client_ipaddr')
execute_command('python network.py --step=test_server_client_connect')
run_tcd_block('1003', 3)


# Fixme: 6> PI_Networking_Columbiaville_PCIe_SRIOV_W
boot_to('BIOS Setup')
set_feature('VTd', 'Enable')
reset_to('windows')
execute_command('python network.py --step=prepare_server_client_connection --conn=col_conn_v4')
execute_command('python network.py --step=test_server_enable_windows_sriov')
execute_command('python network.py --step=test_server_new_windows_vm')
execute_command('python network.py --step=test_server_new_windows_vswitch')
execute_command('python network.py --step=test_server_attach_windows_vswitch_to_vm')
execute_command('python network.py --step=test_server_check_windows_vm_nic')


# Fixme: 7> PI_Networking_Columbiaville_PCIe_TCPStress_L
boot_to('linux')
execute_command('python network.py --step=prepare_server_client_connection --conn=col_conn_v4')
execute_command('python network.py --step=prepare_server_client_ipaddr')
execute_command('python network.py --step=test_server_client_connect')
execute_command('python network.py --step=test_client_start_iperf_server')
execute_command('python network.py --step=test_server_work_as_iperf_sender')
execute_command('python network.py --step=test_server_work_as_iperf_receiver')
execute_command('python network.py --step=test_server_client_cleanup_iperf')


# Fixme: 8> PI_Networking_Columbiaville_PCIe_TCPStress_W
boot_to('windows')
execute_command('python network.py --step=prepare_server_client_connection --conn=col_conn_v4')
execute_command('python network.py --step=prepare_server_client_ipaddr')
execute_command('python network.py --step=test_server_client_connect')
execute_command('python network.py --step=test_client_start_iperf_server')
execute_command('python network.py --step=test_server_work_as_iperf_sender')
execute_command('python network.py --step=test_server_work_as_iperf_receiver')
execute_command('python network.py --step=test_server_client_cleanup_iperf')


# Fixme: 9> PI_Networking_Columbiaville_OCP_TCPStress_L
boot_to('linux')
execute_command('python network.py --step=prepare_server_client_connection --conn=con_conn_v4')
execute_command('python network.py --step=prepare_server_client_ipaddr')
execute_command('python network.py --step=test_server_client_connect')
execute_command('python network.py --step=test_client_start_iperf_server')
execute_command('python network.py --step=test_server_work_as_iperf_sender')
execute_command('python network.py --step=test_server_work_as_iperf_receiver')
execute_command('python network.py --step=test_server_client_cleanup_iperf')


# Fixme: 10> PI_Networking_Columbiaville_OCP_TCPStress_W
boot_to('windows')
execute_command('python network.py --step=prepare_server_client_connection --conn=con_conn_v4')
execute_command('python network.py --step=prepare_server_client_ipaddr')
execute_command('python network.py --step=test_server_client_connect')
execute_command('python network.py --step=test_client_start_iperf_server')
execute_command('python network.py --step=test_server_work_as_iperf_sender')
execute_command('python network.py --step=test_server_work_as_iperf_receiver')
execute_command('python network.py --step=test_server_client_cleanup_iperf')


########################################################################################################################
########################################################################################################################
########################################################################################################################


# TODO: 6> DV_PlatformStress_IO_AllNICConfig_L
boot_to('linux')
execute_command('setenforce 0')						# On sut1
execute_command('systemctl stop firewalld')         # On sut1
execute_command('python network.py --execute_cmd "setenforce 0" --remote')				       # On sut2
execute_command('python network.py --execute_cmd "systemctl stop firewalld" --remote')         # On sut2
execute_command('ifconfig eth1 192.168.3.1/24 up')	# On sut1
execute_command('python network.py --execute_cmd "ifconfig eth2 192.168.3.2/24 up" --remote')  # On sut2
execute_command('ping -c 5 192.168.3.2')			# On sut1

# Export directory on sut2
execute_command('python network.py --execute_cmd "mkdir -p /home/nfstemp" --remote')		   # On sut2
execute_command('python network.py --execute_cmd "touch /home/nfstemp/target" --remote')	   # On sut2
execute_command('python network.py --execute_cmd "echo "/home/nfstemp 192.168.3.1(rw,sync,no_root_squash)" > /etc/exports" --remote')	# On sut2
execute_command('python network.py --execute_cmd "systemctl restart nfs-server" --remote')	   # On sut2

# Mount sut2 folder on sut1
execute_command('mkdir -p /home/testdir')
execute_command('mount 192.168.3.2:/home/nfstemp /home/testdir')
execute_command('ls /home/testdir | grep -i target')

# Fio nfs read/write stress on sut1
execute_command('fio --randrepeat=1 --ioengine=mmap --direct=1 --gtod_reduce=1 --name=testnfs --readwrite=randrw --rwmixread=75 --size=4G --filename=/home/testdir/testfile | grep -i testnfs: (groupid=0, jobs=1): err= 0')


# TODO: 7> PI_Networking_Columbiaville_PCIe_PXE_L
boot_to('BIOS Setup')
set_feature('EfiNetwork', 'Enable')
reset_to('linux')

execute_command('ifconfig eth1 192.168.3.1/24 up')	# On sut1
execute_command('python network.py --execute_cmd "ifconfig eth2 192.168.3.2/24 up" --remote')	# On sut2
execute_command('ping -c 5 192.168.3.2')			# On sut1

# Setup pxe server on sut2
execute_command('python network.py --execute_cmd "dos2unix pxe_uefi.sh" --remote')		# On sut2
execute_command('python network.py --execute_cmd "sh pxe_uefi.sh 192.168.3.2" --remote')# On sut2
execute_command('python network.py --execute_cmd "systemctl status dhcpd.service | grep -i Active: active (running)" --remote')	# On sut2
execute_command('python network.py --execute_cmd "systemctl status tftp.service | grep -i Active: active (running)" --remote')	# On sut2

# Boot from pxe
reset_to('BIOS Setup')
bios_setup_enter_path('Boot Manager Menu', 'UEFI PXEv4 (MAC:{})')		# Q: Cannot enter specific bios path
search_from_bioslog('NBP file downloaded successfully')					# Q: No such function


# TODO: 8> PI_Networking_Columbiaville_PCIe_NVMUpgrade_L
boot_to('linux')
file_transfer('E810_NVMUpdatePackage_v3_00_linux.tar.gz', '/E810_NVMUpdatePackage_v3_00_linux.tar.gz')
execute_command('unzip -o /E810_NVMUpdatePackage_v3_00_linux.tar.gz -d /e810update')
execute_command('/e810update/nvmupdate64e -u -l -o update.log -c nvmupdate.cfg | grep -i -E "Update successful|No update"')
reset_to('linux')


# TODO: 9> PI_Networking_Columbiaville_PCIe_BondingFaultTolerance_L
boot_to('linux')

execute_command('ifconfig eth10 192.168.3.1/24 up') # On sut1
execute_command('python network.py --execute_cmd "ifconfig eth11 192.168.3.2/24 up" --remote')	# On sut2
execute_command('ping -c 5 192.168.3.2')			# On sut1
execute_command('ifconfig eth20 192.168.3.3/24 up') # On sut1
execute_command('python network.py --execute_cmd "ifconfig eth21 192.168.3.4/24 up" --remote')	# On sut2
execute_command('ping -c 5 192.168.3.4')			# On sut1

# Create bond on sut1 and sut2
# On sut1
execute_command('rm -rf /etc/sysconfig/network-scripts/*bond*')
execute_command('nmcli connection delete bond1')

execute_command('nmcli con add type bond con-name bond1 ifname bond1 mode active-backup')
execute_command('nmcli con add type bond-slave ifname eth10 master bond1')
execute_command('nmcli con up bond-slave-eth10')
execute_command('nmcli con add type bond-slave ifname eth11 master bond1')
execute_command('nmcli con up bond-slave-eth11')
execute_command('nmcli con modify bond1 connection.autoconnect yes')
execute_command('nmcli con modify bond1 ipv4.address 192.168.3.100/24')
execute_command('nmcli con modify bond1 ipv4.method manual')
execute_command('nmcli con up bond1')

# On sut2
execute_command('python network.py --execute_cmd "rm -rf /etc/sysconfig/network-scripts/*bond*" --remote')  # On sut2
execute_command('python network.py --execute_cmd "nmcli connection delete bond2" --remote')		            # On sut2

execute_command('python network.py --execute_cmd "nmcli con add type bond con-name bond1 ifname bond2 mode active-backup" --remote')   # On sut2
execute_command('python network.py --execute_cmd "nmcli con add type bond-slave ifname eth20 master bond2" --remote')	# On sut2
execute_command('python network.py --execute_cmd "nmcli con up bond-slave-eth20" --remote')		                        # On sut2
execute_command('python network.py --execute_cmd "nmcli con add type bond-slave ifname eth21 master bond2" --remote')	# On sut2
execute_command('python network.py --execute_cmd "nmcli con up bond-slave-eth21" --remote')		                        # On sut2
execute_command('python network.py --execute_cmd "nmcli con modify bond2 connection.autoconnect yes" --remote')         # On sut2
execute_command('python network.py --execute_cmd "nmcli con modify bond2 ipv4.address 192.168.3.200/24" --remote')		# On sut2
execute_command('python network.py --execute_cmd "nmcli con modify bond2 ipv4.method manual" --remote')		            # On sut2
execute_command('python network.py --execute_cmd "nmcli con up bond2" --remote')		                                # On sut2

execute_command('python network.py --execute_cmd "ping -I 192.168.1.100 192.168.1.200" --remote')		                # On sut2

# Disconnect first connection, to check bonding works
execute_command('ifconfig eth10 down')
execute_command('ifconfig eth20 down')
execute_command('ping -I 192.168.1.100 192.168.1.200')

# Connect first connection, and disconnect second connection, to checking bonding works
execute_command('ifconfig eth10 up')
execute_command('ifconfig eth20 up')
execute_command('ifconfig eth11 down')
execute_command('ifconfig eth21 down')
execute_command('ping -I 192.168.1.100 192.168.1.200')


# TODO: 10> PI_Networking_Columbiaville_PCIe_DriverInstallUninstall_L
boot_to('linux')
file_transfer('ice-1.6.4.tar.gz', '/usr/local/src/ice-1.6.4.tar.gz')
execute_command('tar -zxf /usr/local/src/ice-1.6.4.tar.gz')
execute_command('cd /usr/local/src/ice-xxx/src && make install')
execute_command('rmmod ice')
execute_command('modprobe ice ')
execute_command('lsmod | grep -i ice')
execute_command('lspci | grep -i E810')

# Check driver version
execute_command('modinfo ice')
execute_command('ethtool -i eth1')

# Uninstall driver
execute_command('rmmod ice')
execute_command('lsmod | grep -i ice ; test $? != 0')

# Reinstall driver
execute_command('modprobe ice')
execute_command('lsmod | grep -i ice')


