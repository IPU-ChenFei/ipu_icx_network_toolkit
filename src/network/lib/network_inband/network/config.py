#!/usr/bin/env python

from src.network.inband.common.log import log
from src.network.inband.common.util import CFGParser
import os

RUNTIME = '__runtime.ini'
DEFAULT_NETWORK_CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "network", "network.ini"))
RUNTIME = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "network", "__runtime.ini"))
CFG = 'network.ini'
CFGParser.init_cfg(DEFAULT_NETWORK_CONFIG_FILE)
#CFGParser.init_cfg(RUNTIME)

class NicServer:
    platform = CFGParser.read_cfg('server', 'platform')
    bootproto = CFGParser.read_cfg('server', 'bootproto')
    osname = CFGParser.read_cfg('server', 'osname')


class NicClient:
    osname = CFGParser.read_cfg('client', 'osname')
    ipaddr = CFGParser.read_cfg(osname, 'ipaddr')
    username = CFGParser.read_cfg(osname, 'username')
    password = CFGParser.read_cfg(osname, 'password')

    @classmethod
    def attribute(cls):
        members = []
        for m in dir(cls):
            if not (m.startswith('__') or callable(getattr(cls, m))):
                members.append(m)
        return members


class NicConnection:
    class __Nic:
        def __init__(self, name):
            self.__vendor = CFGParser.read_cfg(name, 'vendor')
            self.__rate = CFGParser.read_cfg(name, 'rate')
            self.__width = CFGParser.read_cfg(name, 'width')
            self.__speed = CFGParser.read_cfg(name, 'speed')
            self.__id_in_windows = CFGParser.read_cfg(name, 'id_in_windows')
            self.__id_in_redhat = CFGParser.read_cfg(name, 'id_in_redhat')
            self.__id_in_centos = CFGParser.read_cfg(name, 'id_in_centos')
            self.__id_in_ubuntu = CFGParser.read_cfg(name, 'id_in_ubuntu')
            self.__id_in_sles = CFGParser.read_cfg(name, 'id_in_sles')
            self.__id_in_alios = CFGParser.read_cfg(name, 'id_in_alios')
            self.__id_in_esxi = CFGParser.read_cfg(name, 'id_in_esxi')
            self.__id_in_uefi = CFGParser.read_cfg(name, 'id_in_uefi')

        @property
        def vendor(self):
            return self.__vendor

        @property
        def rate(self):
            return float(self.__rate)

        @property
        def width(self):
            return self.__width

        @property
        def speed(self):
            return self.__speed

        @property
        def id_in_windows(self):
            return self.__id_in_windows

        @property
        def id_in_redhat(self):
            return self.__id_in_redhat

        @property
        def id_in_centos(self):
            return self.__id_in_centos

        @property
        def id_in_ubuntu(self):
            return self.__id_in_ubuntu

        @property
        def id_in_sles(self):
            return self.__id_in_sles

        @property
        def id_in_alios(self):
            return self.__id_in_alios

        @property
        def id_in_esxi(self):
            return self.__id_in_esxi

        @property
        def id_in_uefi(self):
            return self.__id_in_uefi

        @classmethod
        def attribute(cls):
            members = []
            for m in dir(cls):
                if not (m.startswith('__') or callable(getattr(cls, m))):
                    members.append(m)
            return members

    def __init__(self, name):
        _conn = CFGParser.read_cfg_tuple_to_list('connection', name)
        assert len(_conn) == 4, \
            f'ERROR: [connection]/{name} is not valid, correct FORMAT with: ' \
            f'(server_nic, server_ip, client_nic, client_ip)'

        _server_nc = _conn[0]
        _server_ip = _conn[1]
        _client_nc = _conn[2]
        _client_ip = _conn[3]

        self.__server_nc = NicConnection.__Nic(_server_nc)
        self.__server_ip = _server_ip
        self.__client_nc = NicConnection.__Nic(_client_nc)
        self.__client_ip = _client_ip

        # Replace with runtime attributes if exists
        # Always filled by runtime APIs, and saved in [_runtime_attribute]
        _runtime_server_ip = CFGParser.read_cfg('_runtime_attribute', f'{name}.server_ip', RUNTIME)
        _runtime_client_ip = CFGParser.read_cfg('_runtime_attribute', f'{name}.client_ip', RUNTIME)
        _runtime_server_port = CFGParser.read_cfg('_runtime_attribute', f'{name}.server_port', RUNTIME)
        _runtime_client_port = CFGParser.read_cfg('_runtime_attribute', f'{name}.client_port', RUNTIME)
        _runtime_server_mac = CFGParser.read_cfg('_runtime_attribute', f'{name}.server_mac', RUNTIME)
        _runtime_client_mac = CFGParser.read_cfg('_runtime_attribute', f'{name}.client_mac', RUNTIME)

        self.__server_ip = _runtime_server_ip if _runtime_server_ip else self.__server_ip
        self.__client_ip = _runtime_client_ip if _runtime_client_ip else self.__client_ip

        self.__server_port = _runtime_server_port if _runtime_server_port else None
        self.__client_port = _runtime_client_port if _runtime_client_port else None
        self.__server_mac = _runtime_server_mac if _runtime_server_mac else None
        self.__client_mac = _runtime_client_mac if _runtime_client_mac else None

    @property
    def server_nic(self):
        return self.__server_nc

    @property
    def client_nic(self):
        return self.__client_nc

    @property
    def server_ip(self):
        return self.__server_ip

    @property
    def client_ip(self):
        return self.__client_ip

    @server_ip.setter
    def server_ip(self, value):
        self.__server_ip = value

    @client_ip.setter
    def client_ip(self, value):
        self.__client_ip = value

    @property
    def server_port(self):
        return self.__server_port

    @server_port.setter
    def server_port(self, value):
        self.__server_port = value

    @property
    def client_port(self):
        return self.__client_port

    @client_port.setter
    def client_port(self, value):
        self.__client_port = value

    @property
    def server_mac(self):
        return self.__server_mac

    @server_mac.setter
    def server_mac(self, value):
        self.__server_mac = value

    @property
    def client_mac(self):
        return self.__client_mac

    @client_mac.setter
    def client_mac(self, value):
        self.__client_mac = value


def usage_demo():
    print(
        NicServer.platform,
        NicClient.ipaddr
    )

    conn = NicConnection('spr_conn_v4')
    for attr in conn.server_nic.attribute():
        print(eval(f'conn.server_nic.{attr}'))

    print(
        conn.server_nic.vendor,
        conn.server_nic.id_in_redhat,
        conn.server_ip
    )


if __name__ == '__main__':
    usage_demo()
