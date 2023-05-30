#!/usr/bin/env python

import sys
import socket
import struct


def wake_on_lan(macaddr, broadcast):
    """
    Wake up a system by magic packet

    Magic Packet:
        1. UDP packet within payload: 6 types of all FF, followed by sixteen repetitions of target MAC address
        2. UDP port always be
            0: reserved port
            7: echo protocol
            9: discard protocol
    """
    mac = macaddr.split(':')
    if len(mac) != 6:
        print('Invalid MAC address')
        print('MAC addr should be like: 11:22:33:44:55:66')
        return

    # 1. Create magic packet
    suffix = struct.pack('BBBBBB',
                         int(mac[0], 16),
                         int(mac[1], 16),
                         int(mac[2], 16),
                         int(mac[3], 16),
                         int(mac[4], 16),
                         int(mac[5], 16),
                         )

    magic = b'\xff' * 6 + suffix * 16
    print(magic)

    # 2. Send to wakeup
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(magic, (broadcast, 9))  # discard protocol
    sock.close()


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        mac = sys.argv[1]
        ip = sys.argv[2]
        wake_on_lan(mac, ip)
