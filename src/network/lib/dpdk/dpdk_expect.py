import importlib
import re
import time
import traceback
import sys
import pexpect

from ppexpect import LinuxChildShell

DPDK_PATH = None
VLAN_LOG = '/home/BKCPkg/domains/network/vlan.log'
SEND_PACKET_1 = '/home/BKCPkg/domains/network/send_package1.log'
SEND_PACKET_2 = '/home/BKCPkg/domains/network/send_package2.log'
SEND_PACKET_3 = '/home/BKCPkg/domains/network/send_package3.log'
PMD_1 = '/home/BKCPkg/domains/network/pmd1.log'
PMD_2 = '/home/BKCPkg/domains/network/pmd2.log'
PKT_1 = '/home/BKCPkg/domains/network/PKT.log'
L2FWD = '/home/BKCPkg/domains/network/L2.log'
L3FWD = '/home/BKCPkg/domains/network/L3.log'
RXTX = '/home/BKCPkg/domains/network/RXTX.log'
RXTX_TOP = '/home/BKCPkg/domains/network/RXTX_top.log'
PKTGEN_TIME = 1800
flag = 'flag.txt'


class LinuxChildShellLog(LinuxChildShell):
    def send(self, cmd):
        """
        Send cmd to child process and print cmd
        """
        print(f'Execute expect cmd >>> {cmd}')
        return self.child.sendline(cmd)

    def output(self):
        """
        Results from child process
        """
        res = self.child.before + self.child.after
        print(res.decode('utf-8'))
        return res


def __dynamic_import(module):
    """
    dynamic import
    :param module:module name
    :return: module
    """
    return importlib.import_module(module)


def __ssh_connect(ip):
    cs = None
    try:
        print(f'+++++ ssh {ip} +++++ ')
        cs = LinuxChildShellLog(f'ssh {ip}')
        a = cs.expect(['password:', 'The authenticity of host'])
        if a == 0:
            cs.send('password')
            cs.expect(']#')
            print('connect successful !')
        if a == 1:
            print('this ip will be added to know_host files!')
            cs.send('yes')
            cs.expect('password:')
            cs.send('password')
            cs.expect(']#')

    except pexpect.EOF:
        traceback.print_exc()
    return cs


def start_dpdk_L2fwd(path):
    print(f'+++++ start_L2fwd +++++ ')
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{L2FWD}', 'wb')
    cs.child.logfile = temp_file
    cs.run(r'./dpdk-l2fwd -c 0xffff -n 4 -- -p 3', exp="]#",intr_timeout=20)
    cs.send('\r\n')
    cs.expect(']#')
    cs.output()
    cs.kill()
    temp_file.close()


def start_dpdk_L3fwd(path):
    print(f'+++++ start_L3fwd +++++ ')
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{L3FWD}', 'wb')
    cs.child.logfile = temp_file
    cs.run(r'./dpdk-l3fwd -c 606 -n 4 -- -p 0x3 --config="(0,0,1),(0,1,2),(1,0,9),(1,1,10)"', exp=']#',intr_timeout=20)
    cs.send('\r\n')
    cs.expect(']#')
    cs.output()
    cs.kill()
    temp_file.close()


def start_dpdk_RXTX(path):
    print(f'+++++ start_RXTX +++++ ')
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{RXTX}', 'wb')
    cs.child.logfile = temp_file
    # cs.send(r'./dpdk-rxtx_callbacks -c 2 -n 4')
    # time.sleep(20)
    # cs.child.sendcontrol('c')
    cs.run(r'./dpdk-rxtx_callbacks -c 2 -n 4', exp=']#', intr_timeout=20)
    cs.send('\r\n')
    cs.expect(']#')
    # cs.send('export TERM=dumb')
    # cs.run(f'top > {RXTX_TOP}', exp=']#', intr_timeout=20)
    cs.output()
    cs.kill()
    temp_file.close()


def start_dpdk_pmd(path):
    print(f'+++++ start_pmd +++++ ')
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{PMD_1}', 'wb')
    cs.child.logfile = temp_file
    cs.send(r"dpdk-testpmd -c7 -n3 -- -i --nb-cores=2 --nb-ports=2 --total-num-mbufs=8192")
    time.sleep(5)
    cs.expect('testpmd>')

    cs.send("set fwd mac")
    cs.expect('testpmd>')
    time.sleep(2)
    cs.send('start tx_first')
    time.sleep(30)
    cs.expect('testpmd>')
    time.sleep(2)
    res = cs.output()
    print(res.decode('utf-8'))
    cs.send('show port stats all')
    cs.expect('testpmd>')
    time.sleep(10)
    cs.send('stop')
    cs.expect('testpmd>')
    cs.send('quit')
    res = cs.output()
    print(res.decode('utf-8'))
    print('close!!!')
    cs.kill()
    temp_file.close()


def start_dpdk_pmd1(path):
    print(f'+++++ start_pmd +++++ ')
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{PMD_2}', 'wb')
    cs.child.logfile = temp_file
    cs.send(r"dpdk-testpmd -c 0xffff -n3 -- -i --nb-cores=4 --nb-ports=2 --total-num-mbufs=8192 --rxd=1024 --txd=1024")
    cs.expect('testpmd>')
    cs.send("set fwd mac")
    cs.expect("testpmd>")
    cs.send('start')
    cs.expect("testpmd>")
    res = cs.output()
    print(res)
    time.sleep(40)
    cs.kill()
    temp_file.close()


def start_dpdk_pktgen(args):
    mac1 = args[0]
    mac2 = args[1]
    path = args[-1]
    print(f'+++++ start_pktgen +++++ ')
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{PKT_1}', 'wb')
    cs.child.logfile = temp_file
    cs.send(r'./pktgen -c 0xffff -n 4 -- -P -m "[1-2:3-4].0, [5-6:7-8].1"')
    cs.expect("Pktgen:/>")
    cs.send('set 0 dst mac {}'.format(mac1))
    cs.expect("Pktgen:/>")
    cs.send('set 1 dst mac {}'.format(mac2))
    cs.expect("Pktgen:/>")
    cs.send("set 0-1 size 512")
    cs.expect("Pktgen:/>")
    cs.send('start all')
    time.sleep(PKTGEN_TIME)
    cs.expect("Pktgen:/>")
    cs.send("stop all")
    cs.expect("Pktgen:/>")
    res = cs.output()
    # type = sys.getfilesystemencoding()
    # print(res.decode('UTF-8').encode(type))
    # res = remove_terminal_sequences()
    print(res)
    cs.kill()
    temp_file.close()


def start_dpdk(path):
    #
    print(f'+++++ start_dpdk +++++ ')
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{SEND_PACKET_1}', 'wb')
    cs.child.logfile = temp_file
    cs.send('./build/app/dpdk-testpmd -c 0xfffe -n 4  -- -i --max-pkt-len=1518')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('set promisc 0 off')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('set fwd mac')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('start')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))
    cs.child.logfile = temp_file
    time.sleep(40)
    cs.send('show port stats all')
    cs.expect('testpmd>')
    cs.send('stop')
    cs.expect('testpmd>')
    cs.send('quit')
    res = cs.output()
    print(res.decode('utf-8'))
    print('close!!!')
    cs.kill()
    temp_file.close()


def start_dpdk_2(path):
    #
    print(f'+++++ start_dpdk +++++ ')
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{SEND_PACKET_2}', 'wb')
    cs.child.logfile = temp_file
    cs.send('./build/app/dpdk-testpmd -c 0xfffe -n 4  -- -i --max-pkt-len=94')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('set promisc 0 off')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('set fwd mac')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('start')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.child.logfile = temp_file
    time.sleep(30)
    cs.send('show port stats all')
    cs.expect('testpmd>')
    cs.send('stop')
    cs.expect('testpmd>')
    cs.send('quit')
    res = cs.output()
    print(res.decode('utf-8'))
    print('close!!!')
    cs.kill()
    temp_file.close()


def start_dpdk_3(path):
    #
    print(f'+++++ start_dpdk +++++ ')
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{SEND_PACKET_3}', 'wb')
    cs.child.logfile = temp_file
    cs.send('./build/app/dpdk-testpmd -c 0xfffe -n 4  -- -i --max-pkt-len=9000')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('set promisc 0 off')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('set fwd mac')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('start')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    time.sleep(40)
    cs.send('show port stats all')
    cs.expect('testpmd>')
    cs.send('stop')
    cs.expect('testpmd>')
    cs.send('quit')
    res = cs.output()
    print(res.decode('utf-8'))
    print('close!!!')
    cs.kill()
    temp_file.close()


def start_dpdk_vlan(path):
    print(f'+++++ start_dpdk_vlan +++++ ')
    cs = __ssh_connect('localhost')
    # step 2
    cs.send(f'cd {path}')
    # save log
    temp_file = open(f'{VLAN_LOG}', 'wb')
    cs.child.logfile = temp_file
    cs.send('./build/app/dpdk-testpmd -c 0xfffe -n 4  -- -i')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('vlan set filter on 0')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    cs.send('vlan set strip off 0')
    cs.expect('testpmd>')

    cs.send('vlan set qinq_strip off 0')
    cs.expect('testpmd>')

    cs.send('show port info 0')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))

    # step 3
    cs.send('set promisc 0 off')
    cs.expect('testpmd>')
    # step 4

    cs.send('rx_vlan add 1 0')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))
    # step 5
    cs.send('show port info 0')
    cs.send('set fwd mac')
    cs.expect('testpmd>')

    cs.send('start')
    cs.expect('testpmd>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(60)
    cs.send('show port stats all')
    cs.expect('testpmd>')
    cs.send('stop')
    cs.expect('testpmd>')
    cs.send('quit')
    res = cs.output()
    print(res.decode('utf-8'))
    print('close!!!')
    cs.kill()
    temp_file.close()


def send_packet1(args):
    # type:(list) ->None
    # if len(args) > 2:
    mac = args[0]
    iface = args[1]
    # else:
    #     print('required args mac and iface')
    #     sys.exit()
    cs = __ssh_connect('localhost')
    DPDK_PATH = args[-1]
    cs.send(f'cd {DPDK_PATH}')
    print(DPDK_PATH)
    cs.send('./run_scapy')
    cs.expect('>>>')
    time.sleep(10)
    cs.send(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="AB"*40)], iface="{iface}", count=20)')
    print(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="AB"*40)], iface="{iface}", count=10)')
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(10)
    cs.send(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="A"*1480)], iface="{iface}", count=10)')
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(10)
    cs.send(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="A"*1481)], iface="{iface}", count=20)')
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(20)

    # cs.send(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="A"*56)], iface="{iface}", count=10)')
    # cs.expect('>>>')
    # res = cs.output()
    # print(res.decode('utf-8'))
    #
    # cs.send(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="A"*57)], iface="{iface}", count=10)')
    # cs.expect('>>>')
    # res = cs.output()
    # print(res.decode('utf-8'))
    cs.kill()
    # cs = __ssh_connect('localhost')
    # cs.send(f'cd {path}')
    # cs.send('./build/app/dpdk-testpmd -c 0xfffe -n 4  -- -i')
    # cs.expect('testpmd>')
    print('send_packet1 send successful!')


def send_packet2(args):
    mac = args[0]
    iface = args[1]
    # else:
    #     print('required args mac and iface')
    #     sys.exit()
    cs = __ssh_connect('localhost')
    DPDK_PATH = args[-1]
    cs.send(f'cd {DPDK_PATH}')
    print(DPDK_PATH)
    cs.send('./run_scapy')
    cs.expect('>>>')
    time.sleep(10)
    cs.send(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="A"*56)], iface="{iface}", count=20)')
    print(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="A"*56)], iface="{iface}", count=10)')
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(10)
    cs.send(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="A"*57)], iface="{iface}", count=20)')
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(20)
    cs.kill()


def send_packet3(args):
    mac = args[0]
    iface = args[1]
    cs = __ssh_connect('localhost')
    DPDK_PATH = args[-1]
    cs.send(f'cd {DPDK_PATH}')
    print(DPDK_PATH)
    cs.send('./run_scapy')
    cs.expect('>>>')
    time.sleep(10)
    cs.send(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="A"*8962)], iface="{iface}", count=20)')
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(10)
    cs.send(f'sendp([Ether(dst="{mac}")/IP()/Raw(load="A"*8963)], iface="{iface}", count=20)')
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(30)
    cs.kill()


def send_packet_vlan(args):
    # type:(list) ->None
    mac = args[0]
    iface = args[1]
    DPDK_PATH = args[-1]
    cs = __ssh_connect('localhost')
    cs.send(f'cd {DPDK_PATH}')
    cs.send('./run_scapy')
    cs.expect('>>>')
    time.sleep(10)
    cmd = f'sendp([Ether(dst="{mac}")/Dot1Q(id=0x8100,vlan=1)/IP(len=46)/Raw(load="X"*46)],iface="{iface}", count=100)'
    cs.send(cmd)
    print(cmd)
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(10)
    cmd = f'sendp([Ether(dst="{mac}")/Dot1Q(id=0x8100,vlan=0)/IP(len=46)/Raw(load="X"*46)],iface="{iface}", count=100)'
    print(cmd)
    cs.send(cmd)
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(10)
    cmd = f'sendp([Ether(dst="{mac}")/IP(len=46)/Raw(load="X"*46)],iface="{iface}",count=100)'
    cs.send(cmd)
    print(cmd)
    cs.expect('>>>')
    res = cs.output()
    print(res.decode('utf-8'))
    time.sleep(40)
    cs.kill()


if __name__ == '__main__':
    print(len(sys.argv))

    # opts, args = getopt.getopt(sys.argv[1:], shortopts="",
    #                            longopts=["path="])
    #
    # for opt, val in opts:
    #     if opt == '--path':
    #         DPDK_PATH = val
    #         print(DPDK_PATH)
    if len(sys.argv) >= 3:
        print(len(sys.argv))
        module = __dynamic_import('dpdk_expect')
        # python dpdk_expect.py method_name args path

        if len(sys.argv) > 3:
            # With parameters
            getattr(module, sys.argv[1])(sys.argv[2:])
        else:
            # Without parameters
            getattr(module, sys.argv[1])(sys.argv[-1])
    else:
        print('args value no correct')
        print('python dpdk_expect.py send_packet2 mac iface path')
        sys.exit()
