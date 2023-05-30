from src.network.lib import *


def setup_dhcp_server(sut,conn):
    logger.info("install dhcp server and restart")
    sut.execute_shell_cmd('yum – y install dhcp')
    dhcp_ip = conn.port2.ip
    subnet = '.'.join(dhcp_ip.split('.')[0:3])+'.0'
    range1 = '.'.join(dhcp_ip.split('.')[0:3])+'.200'
    range2 = '.'.join(dhcp_ip.split('.')[0:3])+'.250'
    routers = '.'.join(dhcp_ip.split('.')[0:3])+'.1'
    sut.execute_shell_cmd(f"echo 'option domain-name \"example.org\";\n"
                           f"option domain-name-servers ns1.example.org, ns2.example.org;\n"
                           f"default-lease-time 600;\n"
                           f"max-lease-time 7200;\n"
                           f"log-facility local7;\n"
                           f"subnet {subnet} netmask 255.255.255.0 {{ \n"
                           f"range {range1} {range2};\n"
                           f"option {routers};\n "
                           f"}}\n' > /etc/dhcp/dhcpd.conf")

    sut.execute_shell_cmd('systemctl restart dhcpd.service')

