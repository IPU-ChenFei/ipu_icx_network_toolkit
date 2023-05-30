#!/usr/bin/env python

from enum import Enum


class OsType(Enum):
    WINDOWS = 'windows'
    REDHAT = 'redhat'
    CENTOS = 'centos'
    UBUNTU = 'ubuntu'
    ALIOS = 'alios'
    SLES = 'sles'
    ESXI = 'esxi'
    UEFI = 'uefi'


class GeneralDeviceType(object):
    """
    General device class
    """

    def __init__(self, width, speed):
        """
        Args:
            width: Maximum link width, e.g., 16 means x16
            speed: Maximum link speed, e.g., 8 means 8 GT/s
        """
        self._width = width
        self._speed = speed

    @property
    def width(self):
        return self._width

    @property
    def speed(self):
        return self._speed


class PcieDeviceType(GeneralDeviceType):
    def __init__(self, width, speed):
        super(PcieDeviceType, self).__init__(width, speed)


class OcpDeviceType(GeneralDeviceType):
    def __init__(self, width, speed):
        super(OcpDeviceType, self).__init__(width, speed)


class GeneralNicType(object):
    """
    General network NIC class
    """

    def __init__(self, family, rate):
        """
        Args:
            family: NIC family, e.g., SpringVille/FoxVille
            rate: Single port rate, e.g., 100 means 100 Gbps
        """
        self._family = family
        self._rate = rate

    @property
    def family(self):
        return self._family

    @property
    def rate(self):
        return self._rate


class PcieNicType(PcieDeviceType, GeneralNicType):
    def __init__(self, family, rate, width, speed):
        PcieDeviceType.__init__(self, width, speed)
        GeneralNicType.__init__(self, family, rate)


class OcpNicType(OcpDeviceType, GeneralNicType):
    def __init__(self, family, rate, width, speed):
        OcpDeviceType.__init__(self, width, speed)
        GeneralNicType.__init__(self, family, rate)


class NicOnSut(object):
    def __init__(self, sut, type):
        """
        Args:
            sut: SUT instance
            type: Test NIC type, PcieNicType/OcpNicType object
        """
        self._sut = sut
        self._type = type
        self.id_in_os = {}  # NIC flag dict on different SUT OS

    @property
    def sut(self):
        return self._sut

    @property
    def type(self):
        return self._type


class NicPort(object):
    def __init__(self, nic, ip):
        """
        Args:
            nic:
            ip:
        """
        self._nic = nic
        self._ip = ip

    @property
    def sut(self):
        return self._nic.sut

    @property
    def nic(self):
        return self._nic

    @property
    def ip(self):
        return self._ip


class NicPortConnection(object):
    """
    Representation about 1 test NIC connection on 2 SUTs
    SUT1 (NIC1, mac, ip) <------ cable -------> SUT2 (NIC1, mac, ip)
    """

    def __init__(self, nic1, ip1, nic2, ip2):
        """
        Args:
            nic1: NicOnSut object
            ip1: IP addr on port
            nic2: NicOnSut object
            ip2: IP addr on port
        """
        self._port1 = NicPort(nic1, ip1)
        self._port2 = NicPort(nic2, ip2)

    @property
    def port1(self):
        return self._port1

    @property
    def port2(self):
        return self._port2


class Connections(object):
    """
    Test connection config class that contains all NicPortConnection objects
    """
