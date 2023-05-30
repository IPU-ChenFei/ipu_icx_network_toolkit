#!/usr/bin/env python

from dtaf_core.lib.tklib.basic.utility import get_config_item
from src.network.lib.interface import *
import sys


class EgsExecution:
    bootproto = 'static'
    sw_update_in_both_server_client = True


class WhtExecution:
    bootproto = 'static'
    sw_update_in_both_server_client = True


class BhsExecution:
    """
    bootproto: static/dhcp, dynamically or manually assign nic ip addrs
    sw_update_in_both_server_client: update driver/firmware in both server and client end
    """
    bootproto = 'static'
    sw_update_in_both_server_client = False


def execution_parameter(param):
    """
    Usage Demo: bootproto = execution_parameter('bootproto')
    """
    platform = get_config_item('defaults', 'platform')
    platform = platform.capitalize()
    clsname = platform + 'Execution'
    clsobj = getattr(sys.modules[__name__], clsname)
    return getattr(clsobj, param)


INTEL_NIC_SERIES = ('SpringVille', 'FoxVille', 'JacksonVille', 'OminiPath', 'PowerVille',
                    'FortVille', 'CarlsVille', 'MtEvans', 'ColumviaVille', 'ConnorsVille')

spr_pcie_type = PcieNicType(family='SpringVille', rate=1, width='1', speed='2.5')
fox_pcie_type = PcieNicType(family='FoxVille', rate=1, width='1', speed='2.5')
jac_pcie_type = PcieNicType(family='JacksonVille', rate=1, width='1', speed='2.5')
omi_pcie_type = PcieNicType(family='OminiPath', rate=1, width='1', speed='2.5')
pow_pcie_type = PcieNicType(family='PowerVille', rate=1, width='1', speed='2.5')
for_pcie_type = PcieNicType(family='FortVille', rate=1, width='1', speed='2.5')
edge_pcie_type = PcieNicType(family='FortVille', rate=1, width='1', speed='2.5')   # Edgewater
car_pcie_type = PcieNicType(family='CarlsVille', rate=1, width='8', speed='8')
sma_pcie_type = PcieNicType(family='MtEvans', rate=1, width='1', speed='2.5')
mel_pcie_type = PcieNicType(family='Mellanox', rate=100, width='16', speed='16')
bro_pcie_type = PcieNicType(family='Broadcom', rate=1, width='1', speed='2.5')
col_pcie_type = PcieNicType(family='ColumviaVille', rate=1, width='1', speed='2.5')
col_pcie_type2 = PcieNicType(family='ColumviaVille', rate=1, width='1', speed='2.5')
con_pcie_type = PcieNicType(family='ConnorsVille', rate=1, width='1', speed='2.5')
con_pcie_type2 = PcieNicType(family='ConnorsVille', rate=1, width='1', speed='2.5')

col_ocp_type = OcpNicType(family='ColumviaVille', rate=1, width='1', speed='2.5')
col_ocp_type2 = OcpNicType(family='ColumviaVille', rate=1, width='1', speed='2.5')
con_ocp_type = OcpNicType(family='ConnorsVille', rate=1, width='1', speed='2.5')
con_ocp_type2 = OcpNicType(family='ConnorsVille', rate=1, width='1', speed='2.5')

spr_pcie_spv_I210_1G = OcpNicType(family='SpringVille', rate=1, width='1', speed='2.5')
col_pcie_tocoma_rapids_E810_100G = OcpNicType(family='ColumviaVille', rate=100, width='16', speed='2.5')
col_pcie_salem_channel_E810_25G = OcpNicType(family='ColumviaVille', rate=25, width='16', speed='2.5')
col_pcie_island_rapids_E810_100G = OcpNicType(family='ColumviaVille', rate=100, width='16', speed='2.5')
col_pcie_clifton_channel_E810_25G = OcpNicType(family='ColumviaVille', rate=25, width='8', speed='2.5')
col_pcie_empire_flat_E810_100G = OcpNicType(family='ColumviaVille', rate=100, width='16', speed='2.5')
col_pcie_aspen_flat_E810_25G = OcpNicType(family='ColumviaVille', rate=25, width='8', speed='2.5')
lin_pcie_keystone_pond_XXX_10G = OcpNicType(family='Linkville ', rate=10, width='4', speed='2.5')
lin_pcie_keystone_pond_XXX_2_5G = OcpNicType(family='Linkville ', rate=2.5, width='2', speed='2.5')
con_pcie_beacon_point_E830_100G = OcpNicType(family='Connorsville ', rate=100, width='8', speed='2.5')
con_pcie_jasper_beach_E830_100G = OcpNicType(family='Connorsville ', rate=100, width='8', speed='2.5')
con_pcie_stanley_channel_E830_25G = OcpNicType(family='Connorsville ', rate=25, width='16', speed='2.5')
con_pcie_arcata_channel_E830_25G = OcpNicType(family='Connorsville ', rate=25, width='8', speed='2.5')
con_pcie_hunter_flat_E830_100G = OcpNicType(family='Connorsville ', rate=100, width='8', speed='2.5')
con_pcie_bailey_flat_E830_100G = OcpNicType(family='Connorsville ', rate=100, width='16', speed='2.5')
con_pcie_mckenzie_flat_E830_25G = OcpNicType(family='Connorsville ', rate=25, width='8', speed='2.5')


def nic_config(sut1, sut2, conn=None):
    """
    Pre-Defined NIC connections configuration

    Args:
        sut1: Sut instance
        sut2: Sut instance
        conn: NIC connection between SUTs

    Returns:
        Connections instance that contains all NicPortConnection representations, or single conn if conn
    """

    # NIC list in SUT1
    sut1.spr_pcie_spv_I210 = NicOnSut(sut1, spr_pcie_spv_I210_1G)
    sut1.spr_pcie_spv_I210.id_in_os[OsType.WINDOWS.value] = 'I210'
    sut1.spr_pcie_spv_I210.id_in_os[OsType.REDHAT.value] = 'I210'
    sut1.spr_pcie_spv_I210.id_in_os[OsType.CENTOS.value] = 'I210'
    sut1.spr_pcie_spv_I210.id_in_os[OsType.UBUNTU.value] = 'I210'
    sut1.spr_pcie_spv_I210.id_in_os[OsType.SLES.value] = 'I210'
    sut1.spr_pcie_spv_I210.id_in_os[OsType.ESXI.value] = 'I210'
    sut1.spr_pcie_spv_I210.id_in_os[OsType.UEFI.value] = 'I210'

    sut1.col_pcie_tocoma_E810 = NicOnSut(sut1, col_pcie_tocoma_rapids_E810_100G)
    sut1.col_pcie_tocoma_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut1.col_pcie_tocoma_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut1.col_pcie_tocoma_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut1.col_pcie_tocoma_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut1.col_pcie_tocoma_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut1.col_pcie_tocoma_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut1.col_pcie_tocoma_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut1.col_pcie_salem_E810 = NicOnSut(sut1, col_pcie_salem_channel_E810_25G)
    sut1.col_pcie_salem_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut1.col_pcie_salem_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut1.col_pcie_salem_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut1.col_pcie_salem_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut1.col_pcie_salem_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut1.col_pcie_salem_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut1.col_pcie_salem_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut1.col_pcie_island_E810 = NicOnSut(sut1, col_pcie_island_rapids_E810_100G)
    sut1.col_pcie_island_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut1.col_pcie_island_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut1.col_pcie_island_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut1.col_pcie_island_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut1.col_pcie_island_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut1.col_pcie_island_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut1.col_pcie_island_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut1.col_pcie_clifton_E810 = NicOnSut(sut1, col_pcie_clifton_channel_E810_25G)
    sut1.col_pcie_clifton_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut1.col_pcie_clifton_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut1.col_pcie_clifton_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut1.col_pcie_clifton_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut1.col_pcie_clifton_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut1.col_pcie_clifton_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut1.col_pcie_clifton_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut1.col_pcie_empire_E810 = NicOnSut(sut1, col_pcie_empire_flat_E810_100G)
    sut1.col_pcie_empire_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut1.col_pcie_empire_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut1.col_pcie_empire_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut1.col_pcie_empire_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut1.col_pcie_empire_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut1.col_pcie_empire_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut1.col_pcie_empire_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut1.col_pcie_aspen_E810 = NicOnSut(sut1, col_pcie_aspen_flat_E810_25G)
    sut1.col_pcie_aspen_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut1.col_pcie_aspen_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut1.col_pcie_aspen_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut1.col_pcie_aspen_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut1.col_pcie_aspen_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut1.col_pcie_aspen_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut1.col_pcie_aspen_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut1.lin_pcie_keystone_XXX = NicOnSut(sut1, lin_pcie_keystone_pond_XXX_10G)
    sut1.lin_pcie_keystone_XXX.id_in_os[OsType.WINDOWS.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX.id_in_os[OsType.REDHAT.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX.id_in_os[OsType.CENTOS.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX.id_in_os[OsType.UBUNTU.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX.id_in_os[OsType.SLES.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX.id_in_os[OsType.ESXI.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX.id_in_os[OsType.UEFI.value] = 'XXX'

    sut1.lin_pcie_keystone_XXX_1 = NicOnSut(sut1, lin_pcie_keystone_pond_XXX_2_5G)
    sut1.lin_pcie_keystone_XXX_1.id_in_os[OsType.WINDOWS.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX_1.id_in_os[OsType.REDHAT.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX_1.id_in_os[OsType.CENTOS.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX_1.id_in_os[OsType.UBUNTU.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX_1.id_in_os[OsType.SLES.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX_1.id_in_os[OsType.ESXI.value] = 'XXX'
    sut1.lin_pcie_keystone_XXX_1.id_in_os[OsType.UEFI.value] = 'XXX'

    sut1.con_pcie_beacon_E830 = NicOnSut(sut1, con_pcie_beacon_point_E830_100G)
    sut1.con_pcie_beacon_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut1.con_pcie_beacon_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut1.con_pcie_beacon_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut1.con_pcie_beacon_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut1.con_pcie_beacon_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut1.con_pcie_beacon_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut1.con_pcie_beacon_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut1.con_pcie_jasper_E830 = NicOnSut(sut1, con_pcie_jasper_beach_E830_100G)
    sut1.con_pcie_jasper_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut1.con_pcie_jasper_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut1.con_pcie_jasper_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut1.con_pcie_jasper_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut1.con_pcie_jasper_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut1.con_pcie_jasper_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut1.con_pcie_jasper_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut1.con_pcie_stanley_E830 = NicOnSut(sut1, con_pcie_stanley_channel_E830_25G)
    sut1.con_pcie_stanley_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut1.con_pcie_stanley_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut1.con_pcie_stanley_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut1.con_pcie_stanley_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut1.con_pcie_stanley_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut1.con_pcie_stanley_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut1.con_pcie_stanley_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut1.con_pcie_arcata_E830 = NicOnSut(sut1, con_pcie_arcata_channel_E830_25G)
    sut1.con_pcie_arcata_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut1.con_pcie_arcata_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut1.con_pcie_arcata_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut1.con_pcie_arcata_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut1.con_pcie_arcata_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut1.con_pcie_arcata_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut1.con_pcie_arcata_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut1.con_pcie_bailey_E830 = NicOnSut(sut1, con_pcie_bailey_flat_E830_100G)
    sut1.con_pcie_bailey_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut1.con_pcie_bailey_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut1.con_pcie_bailey_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut1.con_pcie_bailey_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut1.con_pcie_bailey_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut1.con_pcie_bailey_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut1.con_pcie_bailey_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut1.con_pcie_mckenzie_E830 = NicOnSut(sut1, con_pcie_mckenzie_flat_E830_25G)
    sut1.con_pcie_mckenzie_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut1.con_pcie_mckenzie_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut1.con_pcie_mckenzie_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut1.con_pcie_mckenzie_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut1.con_pcie_mckenzie_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut1.con_pcie_mckenzie_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut1.con_pcie_mckenzie_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut1.spr_pcie_nic = NicOnSut(sut1, spr_pcie_type)
    sut1.spr_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'I210'
    sut1.spr_pcie_nic.id_in_os[OsType.REDHAT.value] = 'I210'
    sut1.spr_pcie_nic.id_in_os[OsType.CENTOS.value] = 'I210'
    sut1.spr_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'I210'
    sut1.spr_pcie_nic.id_in_os[OsType.SLES.value] = 'I210'
    sut1.spr_pcie_nic.id_in_os[OsType.ESXI.value] = 'I210'
    sut1.spr_pcie_nic.id_in_os[OsType.UEFI.value] = 'I210'

    sut1.fox_pcie_nic = NicOnSut(sut1, fox_pcie_type)
    sut1.fox_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'I225'
    sut1.fox_pcie_nic.id_in_os[OsType.REDHAT.value] = 'I225'
    sut1.fox_pcie_nic.id_in_os[OsType.CENTOS.value] = 'I225'
    sut1.fox_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'I225'
    sut1.fox_pcie_nic.id_in_os[OsType.SLES.value] = 'I225'
    sut1.fox_pcie_nic.id_in_os[OsType.ESXI.value] = 'I225'
    sut1.fox_pcie_nic.id_in_os[OsType.UEFI.value] = 'I225'

    sut1.jac_pcie_nic = NicOnSut(sut1, jac_pcie_type)
    sut1.jac_pcie_nic.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.jac_pcie_nic.id_in_os[OsType.REDHAT.value] = '710'
    sut1.jac_pcie_nic.id_in_os[OsType.CENTOS.value] = '710'
    sut1.jac_pcie_nic.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.jac_pcie_nic.id_in_os[OsType.SLES.value] = '710'
    sut1.jac_pcie_nic.id_in_os[OsType.ESXI.value] = '710'
    sut1.jac_pcie_nic.id_in_os[OsType.UEFI.value] = '710'

    sut1.omi_pcie_nic = NicOnSut(sut1, omi_pcie_type)
    sut1.omi_pcie_nic.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.omi_pcie_nic.id_in_os[OsType.REDHAT.value] = '710'
    sut1.omi_pcie_nic.id_in_os[OsType.CENTOS.value] = '710'
    sut1.omi_pcie_nic.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.omi_pcie_nic.id_in_os[OsType.SLES.value] = '710'
    sut1.omi_pcie_nic.id_in_os[OsType.ESXI.value] = '710'
    sut1.omi_pcie_nic.id_in_os[OsType.UEFI.value] = '710'

    sut1.pow_pcie_nic = NicOnSut(sut1, pow_pcie_type)
    sut1.pow_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'I350'
    sut1.pow_pcie_nic.id_in_os[OsType.REDHAT.value] = 'I350'
    sut1.pow_pcie_nic.id_in_os[OsType.CENTOS.value] = 'I350'
    sut1.pow_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'I350'
    sut1.pow_pcie_nic.id_in_os[OsType.SLES.value] = 'I350'
    sut1.pow_pcie_nic.id_in_os[OsType.ESXI.value] = 'I350'
    sut1.pow_pcie_nic.id_in_os[OsType.UEFI.value] = 'I350'

    sut1.for_pcie_nic = NicOnSut(sut1, for_pcie_type)
    sut1.for_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'Ethernet Converged Network Adapter X710'
    sut1.for_pcie_nic.id_in_os[OsType.REDHAT.value] = '\'X710 for 10GbE SFP+\''
    sut1.for_pcie_nic.id_in_os[OsType.CENTOS.value] = '\'X710 for 10GbE SFP+\''
    sut1.for_pcie_nic.id_in_os[OsType.UBUNTU.value] = '\'X710 for 10GbE SFP+\''
    sut1.for_pcie_nic.id_in_os[OsType.SLES.value] = '\'X710 for 10GbE SFP+\''
    sut1.for_pcie_nic.id_in_os[OsType.ESXI.value] = '\'X710 for 10GbE SFP+\''
    sut1.for_pcie_nic.id_in_os[OsType.UEFI.value] = '\'X710 for 10GbE SFP+\''

    sut1.edge_pcie_nic = NicOnSut(sut1, edge_pcie_type)
    sut1.edge_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'XXV710'
    sut1.edge_pcie_nic.id_in_os[OsType.REDHAT.value] = 'XXV710'
    sut1.edge_pcie_nic.id_in_os[OsType.CENTOS.value] = 'XXV710'
    sut1.edge_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'XXV710'
    sut1.edge_pcie_nic.id_in_os[OsType.SLES.value] = 'XXV710'
    sut1.edge_pcie_nic.id_in_os[OsType.ESXI.value] = 'XXV710'
    sut1.edge_pcie_nic.id_in_os[OsType.UEFI.value] = 'XXV710'

    sut1.car_pcie_nic = NicOnSut(sut1, car_pcie_type)
    sut1.car_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'X710-T'
    sut1.car_pcie_nic.id_in_os[OsType.REDHAT.value] = '\'X710 for 10GBASE-T\''
    sut1.car_pcie_nic.id_in_os[OsType.CENTOS.value] = '\'X710 for 10GBASE-T\''
    sut1.car_pcie_nic.id_in_os[OsType.UBUNTU.value] = '\'X710 for 10GBASE-T\''
    sut1.car_pcie_nic.id_in_os[OsType.SLES.value] = '\'X710 for 10GBASE-T\''
    sut1.car_pcie_nic.id_in_os[OsType.ESXI.value] = '\'X710 for 10GBASE-T\''
    sut1.car_pcie_nic.id_in_os[OsType.UEFI.value] = '\'X710 for 10GBASE-T\''

    sut1.sma_pcie_nic = NicOnSut(sut1, sma_pcie_type)
    sut1.sma_pcie_nic.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.sma_pcie_nic.id_in_os[OsType.REDHAT.value] = '710'
    sut1.sma_pcie_nic.id_in_os[OsType.CENTOS.value] = '710'
    sut1.sma_pcie_nic.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.sma_pcie_nic.id_in_os[OsType.SLES.value] = '710'
    sut1.sma_pcie_nic.id_in_os[OsType.ESXI.value] = '710'
    sut1.sma_pcie_nic.id_in_os[OsType.UEFI.value] = '710'

    sut1.mel_pcie_nic = NicOnSut(sut1, mel_pcie_type)
    sut1.mel_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'Mellanox'
    sut1.mel_pcie_nic.id_in_os[OsType.REDHAT.value] = 'Mellanox'
    sut1.mel_pcie_nic.id_in_os[OsType.CENTOS.value] = 'Mellanox'
    sut1.mel_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'Mellanox'
    sut1.mel_pcie_nic.id_in_os[OsType.SLES.value] = 'Mellanox'
    sut1.mel_pcie_nic.id_in_os[OsType.ESXI.value] = 'Mellanox'
    sut1.mel_pcie_nic.id_in_os[OsType.UEFI.value] = 'Mellanox'

    sut1.bro_pcie_nic = NicOnSut(sut1, bro_pcie_type)
    sut1.bro_pcie_nic.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.bro_pcie_nic.id_in_os[OsType.REDHAT.value] = '710'
    sut1.bro_pcie_nic.id_in_os[OsType.CENTOS.value] = '710'
    sut1.bro_pcie_nic.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.bro_pcie_nic.id_in_os[OsType.SLES.value] = '710'
    sut1.bro_pcie_nic.id_in_os[OsType.ESXI.value] = '710'
    sut1.bro_pcie_nic.id_in_os[OsType.UEFI.value] = '710'

    sut1.col_pcie_nic = NicOnSut(sut1, col_pcie_type)
    sut1.col_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut1.col_pcie_nic.id_in_os[OsType.REDHAT.value] = 'E810'
    sut1.col_pcie_nic.id_in_os[OsType.CENTOS.value] = 'E810'
    sut1.col_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut1.col_pcie_nic.id_in_os[OsType.SLES.value] = 'E810'
    sut1.col_pcie_nic.id_in_os[OsType.ESXI.value] = 'E810'
    sut1.col_pcie_nic.id_in_os[OsType.UEFI.value] = 'E810'

    sut1.col_pcie_nic_2 = NicOnSut(sut1, col_pcie_type2)
    sut1.col_pcie_nic_2.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut1.col_pcie_nic_2.id_in_os[OsType.REDHAT.value] = 'E810'
    sut1.col_pcie_nic_2.id_in_os[OsType.CENTOS.value] = 'E810'
    sut1.col_pcie_nic_2.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut1.col_pcie_nic_2.id_in_os[OsType.SLES.value] = 'E810'
    sut1.col_pcie_nic_2.id_in_os[OsType.ESXI.value] = 'E810'
    sut1.col_pcie_nic_2.id_in_os[OsType.UEFI.value] = 'E810'

    sut1.con_pcie_nic = NicOnSut(sut1, con_pcie_type)
    sut1.con_pcie_nic.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.con_pcie_nic.id_in_os[OsType.REDHAT.value] = '710'
    sut1.con_pcie_nic.id_in_os[OsType.CENTOS.value] = '710'
    sut1.con_pcie_nic.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.con_pcie_nic.id_in_os[OsType.SLES.value] = '710'
    sut1.con_pcie_nic.id_in_os[OsType.ESXI.value] = '710'
    sut1.con_pcie_nic.id_in_os[OsType.UEFI.value] = '710'

    sut1.con_pcie_nic_2 = NicOnSut(sut1, con_pcie_type2)
    sut1.con_pcie_nic_2.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.con_pcie_nic_2.id_in_os[OsType.REDHAT.value] = '710'
    sut1.con_pcie_nic_2.id_in_os[OsType.CENTOS.value] = '710'
    sut1.con_pcie_nic_2.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.con_pcie_nic_2.id_in_os[OsType.SLES.value] = '710'
    sut1.con_pcie_nic_2.id_in_os[OsType.ESXI.value] = '710'
    sut1.con_pcie_nic_2.id_in_os[OsType.UEFI.value] = '710'

    sut1.col_ocp_nic = NicOnSut(sut1, col_ocp_type)
    sut1.col_ocp_nic.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.col_ocp_nic.id_in_os[OsType.REDHAT.value] = '710'
    sut1.col_ocp_nic.id_in_os[OsType.CENTOS.value] = '710'
    sut1.col_ocp_nic.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.col_ocp_nic.id_in_os[OsType.SLES.value] = '710'
    sut1.col_ocp_nic.id_in_os[OsType.ESXI.value] = '710'
    sut1.col_ocp_nic.id_in_os[OsType.UEFI.value] = '710'

    sut1.col_ocp_nic_2 = NicOnSut(sut1, col_ocp_type2)
    sut1.col_ocp_nic_2.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.col_ocp_nic_2.id_in_os[OsType.REDHAT.value] = '710'
    sut1.col_ocp_nic_2.id_in_os[OsType.CENTOS.value] = '710'
    sut1.col_ocp_nic_2.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.col_ocp_nic_2.id_in_os[OsType.SLES.value] = '710'
    sut1.col_ocp_nic_2.id_in_os[OsType.ESXI.value] = '710'
    sut1.col_ocp_nic_2.id_in_os[OsType.UEFI.value] = '710'

    sut1.con_ocp_nic = NicOnSut(sut1, con_ocp_type)
    sut1.con_ocp_nic.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.con_ocp_nic.id_in_os[OsType.REDHAT.value] = '710'
    sut1.con_ocp_nic.id_in_os[OsType.CENTOS.value] = '710'
    sut1.con_ocp_nic.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.con_ocp_nic.id_in_os[OsType.SLES.value] = '710'
    sut1.con_ocp_nic.id_in_os[OsType.ESXI.value] = '710'
    sut1.con_ocp_nic.id_in_os[OsType.UEFI.value] = '710'

    sut1.con_ocp_nic_2 = NicOnSut(sut1, con_ocp_type2)
    sut1.con_ocp_nic_2.id_in_os[OsType.WINDOWS.value] = '710'
    sut1.con_ocp_nic_2.id_in_os[OsType.REDHAT.value] = '710'
    sut1.con_ocp_nic_2.id_in_os[OsType.CENTOS.value] = '710'
    sut1.con_ocp_nic_2.id_in_os[OsType.UBUNTU.value] = '710'
    sut1.con_ocp_nic_2.id_in_os[OsType.SLES.value] = '710'
    sut1.con_ocp_nic_2.id_in_os[OsType.ESXI.value] = '710'
    sut1.con_ocp_nic_2.id_in_os[OsType.UEFI.value] = '710'

    # NIC list in SUT2
    sut2.spr_pcie_spv_I210 = NicOnSut(sut2, spr_pcie_spv_I210_1G)
    sut2.spr_pcie_spv_I210.id_in_os[OsType.WINDOWS.value] = 'I210'
    sut2.spr_pcie_spv_I210.id_in_os[OsType.REDHAT.value] = 'I210'
    sut2.spr_pcie_spv_I210.id_in_os[OsType.CENTOS.value] = 'I210'
    sut2.spr_pcie_spv_I210.id_in_os[OsType.UBUNTU.value] = 'I210'
    sut2.spr_pcie_spv_I210.id_in_os[OsType.SLES.value] = 'I210'
    sut2.spr_pcie_spv_I210.id_in_os[OsType.ESXI.value] = 'I210'
    sut2.spr_pcie_spv_I210.id_in_os[OsType.UEFI.value] = 'I210'

    sut2.col_pcie_tocoma_E810 = NicOnSut(sut2, col_pcie_tocoma_rapids_E810_100G)
    sut2.col_pcie_tocoma_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut2.col_pcie_tocoma_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut2.col_pcie_tocoma_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut2.col_pcie_tocoma_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut2.col_pcie_tocoma_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut2.col_pcie_tocoma_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut2.col_pcie_tocoma_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut2.col_pcie_salem_E810 = NicOnSut(sut2, col_pcie_salem_channel_E810_25G)
    sut2.col_pcie_salem_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut2.col_pcie_salem_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut2.col_pcie_salem_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut2.col_pcie_salem_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut2.col_pcie_salem_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut2.col_pcie_salem_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut2.col_pcie_salem_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut2.col_pcie_island_E810 = NicOnSut(sut2, col_pcie_island_rapids_E810_100G)
    sut2.col_pcie_island_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut2.col_pcie_island_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut2.col_pcie_island_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut2.col_pcie_island_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut2.col_pcie_island_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut2.col_pcie_island_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut2.col_pcie_island_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut2.col_pcie_clifton_E810 = NicOnSut(sut2, col_pcie_clifton_channel_E810_25G)
    sut2.col_pcie_clifton_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut2.col_pcie_clifton_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut2.col_pcie_clifton_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut2.col_pcie_clifton_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut2.col_pcie_clifton_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut2.col_pcie_clifton_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut2.col_pcie_clifton_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut2.col_pcie_empire_E810 = NicOnSut(sut2, col_pcie_empire_flat_E810_100G)
    sut2.col_pcie_empire_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut2.col_pcie_empire_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut2.col_pcie_empire_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut2.col_pcie_empire_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut2.col_pcie_empire_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut2.col_pcie_empire_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut2.col_pcie_empire_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut2.col_pcie_aspen_E810 = NicOnSut(sut2, col_pcie_aspen_flat_E810_25G)
    sut2.col_pcie_aspen_E810.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut2.col_pcie_aspen_E810.id_in_os[OsType.REDHAT.value] = 'E810'
    sut2.col_pcie_aspen_E810.id_in_os[OsType.CENTOS.value] = 'E810'
    sut2.col_pcie_aspen_E810.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut2.col_pcie_aspen_E810.id_in_os[OsType.SLES.value] = 'E810'
    sut2.col_pcie_aspen_E810.id_in_os[OsType.ESXI.value] = 'E810'
    sut2.col_pcie_aspen_E810.id_in_os[OsType.UEFI.value] = 'E810'

    sut2.lin_pcie_keystone_XXX = NicOnSut(sut2, lin_pcie_keystone_pond_XXX_10G)
    sut2.lin_pcie_keystone_XXX.id_in_os[OsType.WINDOWS.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX.id_in_os[OsType.REDHAT.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX.id_in_os[OsType.CENTOS.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX.id_in_os[OsType.UBUNTU.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX.id_in_os[OsType.SLES.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX.id_in_os[OsType.ESXI.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX.id_in_os[OsType.UEFI.value] = 'XXX'

    sut2.lin_pcie_keystone_XXX_1 = NicOnSut(sut2, lin_pcie_keystone_pond_XXX_2_5G)
    sut2.lin_pcie_keystone_XXX_1.id_in_os[OsType.WINDOWS.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX_1.id_in_os[OsType.REDHAT.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX_1.id_in_os[OsType.CENTOS.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX_1.id_in_os[OsType.UBUNTU.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX_1.id_in_os[OsType.SLES.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX_1.id_in_os[OsType.ESXI.value] = 'XXX'
    sut2.lin_pcie_keystone_XXX_1.id_in_os[OsType.UEFI.value] = 'XXX'

    sut2.con_pcie_beacon_E830 = NicOnSut(sut2, con_pcie_beacon_point_E830_100G)
    sut2.con_pcie_beacon_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut2.con_pcie_beacon_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut2.con_pcie_beacon_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut2.con_pcie_beacon_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut2.con_pcie_beacon_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut2.con_pcie_beacon_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut2.con_pcie_beacon_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut2.con_pcie_jasper_E830 = NicOnSut(sut2, con_pcie_jasper_beach_E830_100G)
    sut2.con_pcie_jasper_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut2.con_pcie_jasper_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut2.con_pcie_jasper_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut2.con_pcie_jasper_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut2.con_pcie_jasper_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut2.con_pcie_jasper_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut2.con_pcie_jasper_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut2.con_pcie_stanley_E830 = NicOnSut(sut2, con_pcie_stanley_channel_E830_25G)
    sut2.con_pcie_stanley_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut2.con_pcie_stanley_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut2.con_pcie_stanley_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut2.con_pcie_stanley_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut2.con_pcie_stanley_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut2.con_pcie_stanley_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut2.con_pcie_stanley_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut2.con_pcie_arcata_E830 = NicOnSut(sut2, con_pcie_arcata_channel_E830_25G)
    sut2.con_pcie_arcata_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut2.con_pcie_arcata_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut2.con_pcie_arcata_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut2.con_pcie_arcata_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut2.con_pcie_arcata_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut2.con_pcie_arcata_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut2.con_pcie_arcata_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut2.con_pcie_bailey_E830 = NicOnSut(sut2, con_pcie_bailey_flat_E830_100G)
    sut2.con_pcie_bailey_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut2.con_pcie_bailey_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut2.con_pcie_bailey_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut2.con_pcie_bailey_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut2.con_pcie_bailey_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut2.con_pcie_bailey_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut2.con_pcie_bailey_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut2.con_pcie_mckenzie_E830 = NicOnSut(sut2, con_pcie_mckenzie_flat_E830_25G)
    sut2.con_pcie_mckenzie_E830.id_in_os[OsType.WINDOWS.value] = 'E830'
    sut2.con_pcie_mckenzie_E830.id_in_os[OsType.REDHAT.value] = 'E830'
    sut2.con_pcie_mckenzie_E830.id_in_os[OsType.CENTOS.value] = 'E830'
    sut2.con_pcie_mckenzie_E830.id_in_os[OsType.UBUNTU.value] = 'E830'
    sut2.con_pcie_mckenzie_E830.id_in_os[OsType.SLES.value] = 'E830'
    sut2.con_pcie_mckenzie_E830.id_in_os[OsType.ESXI.value] = 'E830'
    sut2.con_pcie_mckenzie_E830.id_in_os[OsType.UEFI.value] = 'E830'

    sut2.spr_pcie_nic = NicOnSut(sut2, spr_pcie_type)
    sut2.spr_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'I210'
    sut2.spr_pcie_nic.id_in_os[OsType.REDHAT.value] = 'I210'
    sut2.spr_pcie_nic.id_in_os[OsType.CENTOS.value] = 'I210'
    sut2.spr_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'I210'
    sut2.spr_pcie_nic.id_in_os[OsType.SLES.value] = 'I210'
    sut2.spr_pcie_nic.id_in_os[OsType.ESXI.value] = 'I210'
    sut2.spr_pcie_nic.id_in_os[OsType.UEFI.value] = 'I210'

    sut2.fox_pcie_nic = NicOnSut(sut2, fox_pcie_type)
    sut2.fox_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'I225'
    sut2.fox_pcie_nic.id_in_os[OsType.REDHAT.value] = 'I225'
    sut2.fox_pcie_nic.id_in_os[OsType.CENTOS.value] = 'I225'
    sut2.fox_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'I225'
    sut2.fox_pcie_nic.id_in_os[OsType.SLES.value] = 'I225'
    sut2.fox_pcie_nic.id_in_os[OsType.ESXI.value] = 'I225'
    sut2.fox_pcie_nic.id_in_os[OsType.UEFI.value] = 'I225'

    sut2.jac_pcie_nic = NicOnSut(sut2, jac_pcie_type)
    sut2.jac_pcie_nic.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.jac_pcie_nic.id_in_os[OsType.REDHAT.value] = '350'
    sut2.jac_pcie_nic.id_in_os[OsType.CENTOS.value] = '350'
    sut2.jac_pcie_nic.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.jac_pcie_nic.id_in_os[OsType.SLES.value] = '350'
    sut2.jac_pcie_nic.id_in_os[OsType.ESXI.value] = '350'
    sut2.jac_pcie_nic.id_in_os[OsType.UEFI.value] = '350'

    sut2.omi_pcie_nic = NicOnSut(sut2, omi_pcie_type)
    sut2.omi_pcie_nic.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.omi_pcie_nic.id_in_os[OsType.REDHAT.value] = '350'
    sut2.omi_pcie_nic.id_in_os[OsType.CENTOS.value] = '350'
    sut2.omi_pcie_nic.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.omi_pcie_nic.id_in_os[OsType.SLES.value] = '350'
    sut2.omi_pcie_nic.id_in_os[OsType.ESXI.value] = '350'
    sut2.omi_pcie_nic.id_in_os[OsType.UEFI.value] = '350'

    sut2.pow_pcie_nic = NicOnSut(sut2, pow_pcie_type)
    sut2.pow_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'I350'
    sut2.pow_pcie_nic.id_in_os[OsType.REDHAT.value] = 'I350'
    sut2.pow_pcie_nic.id_in_os[OsType.CENTOS.value] = 'I350'
    sut2.pow_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'I350'
    sut2.pow_pcie_nic.id_in_os[OsType.SLES.value] = 'I350'
    sut2.pow_pcie_nic.id_in_os[OsType.ESXI.value] = 'I350'
    sut2.pow_pcie_nic.id_in_os[OsType.UEFI.value] = 'I350'

    sut2.for_pcie_nic = NicOnSut(sut2, for_pcie_type)
    sut2.for_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'Ethernet Converged Network Adapter X710'
    sut2.for_pcie_nic.id_in_os[OsType.REDHAT.value] = '\'X710 for 10GbE SFP+\''
    sut2.for_pcie_nic.id_in_os[OsType.CENTOS.value] = '\'X710 for 10GbE SFP+\''
    sut2.for_pcie_nic.id_in_os[OsType.UBUNTU.value] = '\'X710 for 10GbE SFP+\''
    sut2.for_pcie_nic.id_in_os[OsType.SLES.value] = '\'X710 for 10GbE SFP+\''
    sut2.for_pcie_nic.id_in_os[OsType.ESXI.value] = '\'X710 for 10GbE SFP+\''
    sut2.for_pcie_nic.id_in_os[OsType.UEFI.value] = '\'X710 for 10GbE SFP+\''

    sut2.edge_pcie_nic = NicOnSut(sut2, edge_pcie_type)
    sut2.edge_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'XXV710'
    sut2.edge_pcie_nic.id_in_os[OsType.REDHAT.value] = 'XXV710'
    sut2.edge_pcie_nic.id_in_os[OsType.CENTOS.value] = 'XXV710'
    sut2.edge_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'XXV710'
    sut2.edge_pcie_nic.id_in_os[OsType.SLES.value] = 'XXV710'
    sut2.edge_pcie_nic.id_in_os[OsType.ESXI.value] = 'XXV710'
    sut2.edge_pcie_nic.id_in_os[OsType.UEFI.value] = 'XXV710'

    sut2.car_pcie_nic = NicOnSut(sut2, car_pcie_type)
    sut2.car_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'X710-T'
    sut2.car_pcie_nic.id_in_os[OsType.REDHAT.value] = '\'X710 for 10GBASE-T\''
    sut2.car_pcie_nic.id_in_os[OsType.CENTOS.value] = '\'X710 for 10GBASE-T\''
    sut2.car_pcie_nic.id_in_os[OsType.UBUNTU.value] = '\'X710 for 10GBASE-T\''
    sut2.car_pcie_nic.id_in_os[OsType.SLES.value] = '\'X710 for 10GBASE-T\''
    sut2.car_pcie_nic.id_in_os[OsType.ESXI.value] = '\'X710 for 10GBASE-T\''
    sut2.car_pcie_nic.id_in_os[OsType.UEFI.value] = '\'X710 for 10GBASE-T\''

    sut2.sma_pcie_nic = NicOnSut(sut2, sma_pcie_type)
    sut2.sma_pcie_nic.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.sma_pcie_nic.id_in_os[OsType.REDHAT.value] = '350'
    sut2.sma_pcie_nic.id_in_os[OsType.CENTOS.value] = '350'
    sut2.sma_pcie_nic.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.sma_pcie_nic.id_in_os[OsType.SLES.value] = '350'
    sut2.sma_pcie_nic.id_in_os[OsType.ESXI.value] = '350'
    sut2.sma_pcie_nic.id_in_os[OsType.UEFI.value] = '350'

    sut2.mel_pcie_nic = NicOnSut(sut2, mel_pcie_type)
    sut2.mel_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'Mellanox'
    sut2.mel_pcie_nic.id_in_os[OsType.REDHAT.value] = 'Mellanox'
    sut2.mel_pcie_nic.id_in_os[OsType.CENTOS.value] = 'Mellanox'
    sut2.mel_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'Mellanox'
    sut2.mel_pcie_nic.id_in_os[OsType.SLES.value] = 'Mellanox'
    sut2.mel_pcie_nic.id_in_os[OsType.ESXI.value] = 'Mellanox'
    sut2.mel_pcie_nic.id_in_os[OsType.UEFI.value] = 'Mellanox'

    sut2.bro_pcie_nic = NicOnSut(sut2, bro_pcie_type)
    sut2.bro_pcie_nic.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.bro_pcie_nic.id_in_os[OsType.REDHAT.value] = '350'
    sut2.bro_pcie_nic.id_in_os[OsType.CENTOS.value] = '350'
    sut2.bro_pcie_nic.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.bro_pcie_nic.id_in_os[OsType.SLES.value] = '350'
    sut2.bro_pcie_nic.id_in_os[OsType.ESXI.value] = '350'
    sut2.bro_pcie_nic.id_in_os[OsType.UEFI.value] = '350'

    sut2.col_pcie_nic = NicOnSut(sut2, col_pcie_type)
    sut2.col_pcie_nic.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut2.col_pcie_nic.id_in_os[OsType.REDHAT.value] = 'E810'
    sut2.col_pcie_nic.id_in_os[OsType.CENTOS.value] = 'E810'
    sut2.col_pcie_nic.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut2.col_pcie_nic.id_in_os[OsType.SLES.value] = 'E810'
    sut2.col_pcie_nic.id_in_os[OsType.ESXI.value] = 'E810'
    sut2.col_pcie_nic.id_in_os[OsType.UEFI.value] = 'E810'

    sut2.col_pcie_nic_2 = NicOnSut(sut2, col_pcie_type2)
    sut2.col_pcie_nic_2.id_in_os[OsType.WINDOWS.value] = 'E810'
    sut2.col_pcie_nic_2.id_in_os[OsType.REDHAT.value] = 'E810'
    sut2.col_pcie_nic_2.id_in_os[OsType.CENTOS.value] = 'E810'
    sut2.col_pcie_nic_2.id_in_os[OsType.UBUNTU.value] = 'E810'
    sut2.col_pcie_nic_2.id_in_os[OsType.SLES.value] = 'E810'
    sut2.col_pcie_nic_2.id_in_os[OsType.ESXI.value] = 'E810'
    sut2.col_pcie_nic_2.id_in_os[OsType.UEFI.value] = 'E810'

    sut2.con_pcie_nic = NicOnSut(sut2, con_pcie_type)
    sut2.con_pcie_nic.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.con_pcie_nic.id_in_os[OsType.REDHAT.value] = '350'
    sut2.con_pcie_nic.id_in_os[OsType.CENTOS.value] = '350'
    sut2.con_pcie_nic.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.con_pcie_nic.id_in_os[OsType.SLES.value] = '350'
    sut2.con_pcie_nic.id_in_os[OsType.ESXI.value] = '350'
    sut2.con_pcie_nic.id_in_os[OsType.UEFI.value] = '350'

    sut2.con_pcie_nic_2 = NicOnSut(sut2, con_pcie_type2)
    sut2.con_pcie_nic_2.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.con_pcie_nic_2.id_in_os[OsType.REDHAT.value] = '350'
    sut2.con_pcie_nic_2.id_in_os[OsType.CENTOS.value] = '350'
    sut2.con_pcie_nic_2.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.con_pcie_nic_2.id_in_os[OsType.SLES.value] = '350'
    sut2.con_pcie_nic_2.id_in_os[OsType.ESXI.value] = '350'
    sut2.con_pcie_nic_2.id_in_os[OsType.UEFI.value] = '350'

    sut2.col_ocp_nic = NicOnSut(sut2, col_ocp_type)
    sut2.col_ocp_nic.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.col_ocp_nic.id_in_os[OsType.REDHAT.value] = '350'
    sut2.col_ocp_nic.id_in_os[OsType.CENTOS.value] = '350'
    sut2.col_ocp_nic.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.col_ocp_nic.id_in_os[OsType.SLES.value] = '350'
    sut2.col_ocp_nic.id_in_os[OsType.ESXI.value] = '350'
    sut2.col_ocp_nic.id_in_os[OsType.UEFI.value] = '350'

    sut2.col_ocp_nic_2 = NicOnSut(sut2, col_ocp_type2)
    sut2.col_ocp_nic_2.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.col_ocp_nic_2.id_in_os[OsType.REDHAT.value] = '350'
    sut2.col_ocp_nic_2.id_in_os[OsType.CENTOS.value] = '350'
    sut2.col_ocp_nic_2.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.col_ocp_nic_2.id_in_os[OsType.SLES.value] = '350'
    sut2.col_ocp_nic_2.id_in_os[OsType.ESXI.value] = '350'
    sut2.col_ocp_nic_2.id_in_os[OsType.UEFI.value] = '350'

    sut2.con_ocp_nic = NicOnSut(sut2, con_ocp_type)
    sut2.con_ocp_nic.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.con_ocp_nic.id_in_os[OsType.REDHAT.value] = '350'
    sut2.con_ocp_nic.id_in_os[OsType.CENTOS.value] = '350'
    sut2.con_ocp_nic.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.con_ocp_nic.id_in_os[OsType.SLES.value] = '350'
    sut2.con_ocp_nic.id_in_os[OsType.ESXI.value] = '350'
    sut2.con_ocp_nic.id_in_os[OsType.UEFI.value] = '350'

    sut2.con_ocp_nic_2 = NicOnSut(sut2, con_ocp_type2)
    sut2.con_ocp_nic_2.id_in_os[OsType.WINDOWS.value] = '350'
    sut2.con_ocp_nic_2.id_in_os[OsType.REDHAT.value] = '350'
    sut2.con_ocp_nic_2.id_in_os[OsType.CENTOS.value] = '350'
    sut2.con_ocp_nic_2.id_in_os[OsType.UBUNTU.value] = '350'
    sut2.con_ocp_nic_2.id_in_os[OsType.SLES.value] = '350'
    sut2.con_ocp_nic_2.id_in_os[OsType.ESXI.value] = '350'
    sut2.con_ocp_nic_2.id_in_os[OsType.UEFI.value] = '350'

    # NIC testing connections between 2 SUTs
    # MAC addr (get by script), IP addr (set by script)
    conns = Connections()

    # SpringVille Subnet: IPv4 (192.168.3.x), IPv6 (fd00:1762:3::x)
    conns.spr_conn_v6 = NicPortConnection(sut1.spr_pcie_nic, 'fd00:1762:3::1',
                                          sut2.spr_pcie_nic, 'fd00:1762:3::2')
    conns.spr_conn_v4 = NicPortConnection(sut1.spr_pcie_nic, '192.168.3.1',
                                          sut2.spr_pcie_nic, '192.168.3.2')
    conns.spr_conn_v6_spv_I210_1G = NicPortConnection(sut1.spr_pcie_spv_I210, 'fd00:1762:3::1',
                                          sut2.spr_pcie_spv_I210, 'fd00:1762:3::2')
    conns.spr_conn_v4_spv_I210_1G = NicPortConnection(sut1.spr_pcie_spv_I210, '192.168.3.1',
                                          sut2.spr_pcie_spv_I210, '192.168.3.2')
    # FoxVille Subnet: IPv4 (192.168.4.x), IPv6 (fd00:1762:4::x)
    conns.fox_conn_v6 = NicPortConnection(sut1.fox_pcie_nic, 'fd00:1762:4::1',
                                          sut2.fox_pcie_nic, 'fd00:1762:4::2')
    conns.fox_conn_v4 = NicPortConnection(sut1.fox_pcie_nic, '192.168.4.1',
                                          sut2.fox_pcie_nic, '192.168.4.2')

    # JacksonVille Subnet: IPv4 (192.168.5.x), IPv6 (fd00:1762:5::x)
    conns.jac_conn_v6 = NicPortConnection(sut1.jac_pcie_nic, 'fd00:1762:5::1',
                                          sut2.jac_pcie_nic, 'fd00:1762:5::2')
    conns.jac_conn_v4 = NicPortConnection(sut1.jac_pcie_nic, '192.168.5.1',
                                          sut2.jac_pcie_nic, '192.168.5.2')

    # OminiPath Subnet: IPv4 (192.168.6.x), IPv6 (fd00:1762:6::x)
    conns.omi_conn_v6 = NicPortConnection(sut1.omi_pcie_nic, 'fd00:1762:6::1',
                                          sut2.omi_pcie_nic, 'fd00:1762:6::2')
    conns.omi_conn_v4 = NicPortConnection(sut1.omi_pcie_nic, '192.168.6.1',
                                          sut2.omi_pcie_nic, '192.168.6.2')

    # PowerVille Subnet: IPv4 (192.168.7.x), IPv6 (fd00:1762:7::x)
    conns.pow_conn_v6 = NicPortConnection(sut1.pow_pcie_nic, 'fd00:1762:7::1',
                                          sut2.pow_pcie_nic, 'fd00:1762:7::2')
    conns.pow_conn_v4 = NicPortConnection(sut1.pow_pcie_nic, '192.168.7.5',
                                          sut2.pow_pcie_nic, '192.168.7.6')

    # FortVille Subnet: IPv4 (192.168.8.x), IPv6 (fd00:1762:8::x)
    conns.for_conn_v6 = NicPortConnection(sut1.for_pcie_nic, 'fd00:1762:8::1',
                                          sut2.for_pcie_nic, 'fd00:1762:8::2')
    conns.for_conn_v4 = NicPortConnection(sut1.for_pcie_nic, '192.168.8.5',
                                          sut2.for_pcie_nic, '192.168.8.6')
    conns.edge_conn_v6 = NicPortConnection(sut1.edge_pcie_nic, 'fd00:1762:8::1',
                                           sut2.edge_pcie_nic, 'fd00:1762:8::2')
    conns.edge_conn_v4 = NicPortConnection(sut1.edge_pcie_nic, '192.168.8.1',
                                           sut2.edge_pcie_nic, '192.168.8.2')

    # CarlsVille Subnet: IPv4 (192.168.9.x), IPv6 (fd00:1762:9::x)
    conns.car_conn_v6 = NicPortConnection(sut1.car_pcie_nic, 'fd00:1762:9::1',
                                          sut2.car_pcie_nic, 'fd00:1762:9::2')
    conns.car_conn_v4 = NicPortConnection(sut1.car_pcie_nic, '192.168.9.5',
                                          sut2.car_pcie_nic, '192.168.9.6')
    conns.car_conn_v4_02 = NicPortConnection(sut1.car_pcie_nic, '192.168.9.3',
                                             sut2.car_pcie_nic, '192.168.9.4')

    # ColumviaVille Subnet: IPv4 (192.168.10.x), IPv6 (fd00:1762:10::x)
    conns.col_conn_v6 = NicPortConnection(sut1.col_pcie_nic, 'fd00:1762:10::1',
                                          sut2.col_pcie_nic, 'fd00:1762:10::2')
    conns.col_conn_v4 = NicPortConnection(sut1.col_pcie_nic, '192.168.10.5',
                                          sut2.col_pcie_nic, '192.168.10.6')
    conns.col_conn_v4_02 = NicPortConnection(sut1.col_pcie_nic, '192.168.10.3',
                                             sut2.col_pcie_nic, '192.168.10.4')
    conns.col_conn_v4_03 = NicPortConnection(sut1.col_pcie_nic, 'fd00:1762:10::5',
                                             sut2.col_pcie_nic, 'fd00:1762:10::6')
    conns.col_conn_v6_tocoma_rapids_E810_100G = NicPortConnection(sut1.col_pcie_tocoma_E810, 'fd00:1762:10::1',
                                          sut2.col_pcie_tocoma_E810, 'fd00:1762:10::2')
    conns.col_conn_v4_tocoma_rapids_E810_100G = NicPortConnection(sut1.col_pcie_tocoma_E810, '192.168.10.1',
                                          sut2.col_pcie_tocoma_E810, '192.168.10.2')
    conns.col_conn_v4_tocoma_rapids_E810_100G_2 = NicPortConnection(sut1.col_pcie_tocoma_E810, '192.168.10.3',
                                                                  sut2.col_pcie_tocoma_E810, '192.168.10.4')

    conns.col_conn_v6_salem_channel_E810_100G = NicPortConnection(sut1.col_pcie_salem_E810, 'fd00:1762:15::1',
                                                                  sut2.col_pcie_salem_E810, 'fd00:1762:15::2')
    conns.col_conn_v4_salem_channel_E810_100G = NicPortConnection(sut1.col_pcie_salem_E810, '192.168.15.1',
                                                                  sut2.col_pcie_salem_E810, '192.168.15.2')
    conns.col_conn_v4_salem_channel_E810_100G_2 = NicPortConnection(sut1.col_pcie_salem_E810, '192.168.15.3',
                                                                    sut2.col_pcie_salem_E810, '192.168.15.4')

    conns.col_conn_v6_island_rapids_E810_100G = NicPortConnection(sut1.col_pcie_island_E810, 'fd00:1762:16::1',
                                                                  sut2.col_pcie_island_E810, 'fd00:1762:16::2')
    conns.col_conn_v4_island_rapids_E810_100G = NicPortConnection(sut1.col_pcie_island_E810, '192.168.16.1',
                                                                  sut2.col_pcie_island_E810, '192.168.16.2')
    conns.col_conn_v4_island_rapids_E810_100G_2 = NicPortConnection(sut1.col_pcie_island_E810, '192.168.16.3',
                                                                    sut2.col_pcie_island_E810, '192.168.16.4')

    conns.col_conn_v6_clifton_channel_E810_100G = NicPortConnection(sut1.col_pcie_clifton_E810, 'fd00:1762:17::1',
                                                                  sut2.col_pcie_clifton_E810, 'fd00:1762:17::2')
    conns.col_conn_v4_clifton_channel_E810_100G = NicPortConnection(sut1.col_pcie_clifton_E810, '192.168.17.1',
                                                                  sut2.col_pcie_clifton_E810, '192.168.17.2')
    conns.col_conn_v4_clifton_channel_E810_100G_2 = NicPortConnection(sut1.col_pcie_clifton_E810, '192.168.17.3',
                                                                    sut2.col_pcie_clifton_E810, '192.168.17.4')

    conns.col_conn_v6_empire_flat_E810_100G = NicPortConnection(sut1.col_pcie_empire_E810, 'fd00:1762:18::1',
                                                                  sut2.col_pcie_empire_E810, 'fd00:1762:18::2')
    conns.col_conn_v4_empire_flat_E810_100G = NicPortConnection(sut1.col_pcie_empire_E810, '192.168.18.1',
                                                                  sut2.col_pcie_empire_E810, '192.168.18.2')
    conns.col_conn_v4_empire_flat_E810_100G_2 = NicPortConnection(sut1.col_pcie_empire_E810, '192.168.18.3',
                                                                    sut2.col_pcie_empire_E810, '192.168.18.4')

    conns.col_conn_v6_aspen_flat_E810_100G = NicPortConnection(sut1.col_pcie_aspen_E810, 'fd00:1762:19::1',
                                                                  sut2.col_pcie_aspen_E810, 'fd00:1762:19::2')
    conns.col_conn_v4_aspen_flat_E810_100G = NicPortConnection(sut1.col_pcie_aspen_E810, '192.168.19.1',
                                                                  sut2.col_pcie_aspen_E810, '192.168.19.2')
    conns.col_conn_v4_aspen_flat_E810_100G_2 = NicPortConnection(sut1.col_pcie_aspen_E810, '192.168.19.3',
                                                                    sut2.col_pcie_aspen_E810, '192.168.19.4')

    conns.col_conn_v6_keystone_pond_XXX_10G = NicPortConnection(sut1.lin_pcie_keystone_XXX, 'fd00:1762:20::1',
                                                                  sut2.lin_pcie_keystone_XXX, 'fd00:1762:20::2')
    conns.col_conn_v4_keystone_pond_XXX_10G = NicPortConnection(sut1.lin_pcie_keystone_XXX, '192.168.20.1',
                                                                  sut2.lin_pcie_keystone_XXX, '192.168.20.2')
    conns.col_conn_v4_keystone_pond_XXX_10G_2 = NicPortConnection(sut1.lin_pcie_keystone_XXX, '192.168.20.3',
                                                                    sut2.lin_pcie_keystone_XXX, '192.168.20.4')

    conns.col_conn_v6_keystone_pond_XXX_2_5G = NicPortConnection(sut1.lin_pcie_keystone_XXX_1, 'fd00:1762:21::1',
                                                                  sut2.lin_pcie_keystone_XXX_1, 'fd00:1762:21::2')
    conns.col_conn_v4_keystone_pond_XXX_2_5G = NicPortConnection(sut1.lin_pcie_keystone_XXX_1, '192.168.21.1',
                                                                  sut2.lin_pcie_keystone_XXX_1, '192.168.21.2')
    conns.col_conn_v4_keystone_pond_XXX_2_5G_2 = NicPortConnection(sut1.lin_pcie_keystone_XXX_1, '192.168.21.3',
                                                                    sut2.lin_pcie_keystone_XXX_1, '192.168.21.4')

    conns.col_conn_v6_beacon_point_E830_100G = NicPortConnection(sut1.con_pcie_beacon_E830, 'fd00:1762:22::1',
                                                                  sut2.con_pcie_beacon_E830, 'fd00:1762:22::2')
    conns.col_conn_v4_beacon_point_E830_100G = NicPortConnection(sut1.con_pcie_beacon_E830, '192.168.22.1',
                                                                  sut2.con_pcie_beacon_E830, '192.168.22.2')
    conns.col_conn_v4_beacon_point_E830_100G_2 = NicPortConnection(sut1.con_pcie_beacon_E830, '192.168.22.3',
                                                                    sut2.con_pcie_beacon_E830, '192.168.22.4')

    conns.col_conn_v6_jasper_beach_E830_100G = NicPortConnection(sut1.con_pcie_jasper_E830, 'fd00:1762:23::1',
                                                                  sut2.con_pcie_jasper_E830, 'fd00:1762:23::2')
    conns.col_conn_v4_jasper_beach_E830_100G = NicPortConnection(sut1.con_pcie_jasper_E830, '192.168.23.1',
                                                                  sut2.con_pcie_jasper_E830, '192.168.23.2')
    conns.col_conn_v4_jasper_beach_E830_100G_2 = NicPortConnection(sut1.con_pcie_jasper_E830, '192.168.23.3',
                                                                    sut2.con_pcie_jasper_E830, '192.168.23.4')

    conns.col_conn_v6_stanley_channel_E830_25G = NicPortConnection(sut1.con_pcie_stanley_E830, 'fd00:1762:24::1',
                                                                  sut2.con_pcie_stanley_E830, 'fd00:1762:24::2')
    conns.col_conn_v4_stanley_channel_E830_25G = NicPortConnection(sut1.con_pcie_stanley_E830, '192.168.24.1',
                                                                  sut2.con_pcie_stanley_E830, '192.168.24.2')
    conns.col_conn_v4_stanley_channel_E830_25G_2 = NicPortConnection(sut1.con_pcie_stanley_E830, '192.168.24.3',
                                                                    sut2.con_pcie_stanley_E830, '192.168.24.4')

    conns.col_conn_v6_arcata_channel_E830_25G = NicPortConnection(sut1.con_pcie_arcata_E830, 'fd00:1762:25::1',
                                                                  sut2.con_pcie_arcata_E830, 'fd00:1762:25::2')
    conns.col_conn_v4_arcata_channel_E830_25G = NicPortConnection(sut1.con_pcie_arcata_E830, '192.168.25.1',
                                                                  sut2.con_pcie_arcata_E830, '192.168.25.2')
    conns.col_conn_v4_arcata_channel_E830_25G_2 = NicPortConnection(sut1.con_pcie_arcata_E830, '192.168.25.3',
                                                                    sut2.con_pcie_arcata_E830, '192.168.25.4')

    conns.col_conn_v6_bailey_flat_E830_100G = NicPortConnection(sut1.con_pcie_bailey_E830, 'fd00:1762:26::1',
                                                                  sut2.con_pcie_bailey_E830, 'fd00:1762:26::2')
    conns.col_conn_v4_bailey_flat_E830_100G = NicPortConnection(sut1.con_pcie_bailey_E830, '192.168.26.1',
                                                                  sut2.con_pcie_bailey_E830, '192.168.26.2')
    conns.col_conn_v4_bailey_flat_E830_100G_2 = NicPortConnection(sut1.con_pcie_bailey_E830, '192.168.26.3',
                                                                    sut2.con_pcie_bailey_E830, '192.168.26.4')

    conns.col_conn_v6_mckenzie_flat_E830_25G = NicPortConnection(sut1.con_pcie_mckenzie_E830, 'fd00:1762:27::1',
                                                                  sut2.con_pcie_mckenzie_E830, 'fd00:1762:27::2')
    conns.col_conn_v4_mckenzie_flat_E830_25G = NicPortConnection(sut1.con_pcie_mckenzie_E830, '192.168.27.1',
                                                                  sut2.con_pcie_mckenzie_E830, '192.168.27.2')
    conns.col_conn_v4_mckenzie_flat_E830_25G_2 = NicPortConnection(sut1.con_pcie_mckenzie_E830, '192.168.27.3',
                                                                    sut2.con_pcie_mckenzie_E830, '192.168.27.4')

    # ConnorsVille Subnet: IPv4 (192.168.11.x), IPv6 (fd00:1762:11::x)
    conns.con_conn_v6 = NicPortConnection(sut1.con_pcie_nic, 'fd00:1762:11::1',
                                          sut2.con_pcie_nic, 'fd00:1762:11::2')
    conns.con_conn_v4 = NicPortConnection(sut1.con_pcie_nic, '192.168.11.1',
                                          sut2.con_pcie_nic, '192.168.11.2')

    # SmartNic Subnet: IPv4 (192.168.12.x), IPv6 (fd00:1762:12::x)
    conns.sma_conn_v6 = NicPortConnection(sut1.sma_pcie_nic, 'fd00:1762:12::1',
                                          sut2.sma_pcie_nic, 'fd00:1762:12::2')
    conns.sma_conn_v4 = NicPortConnection(sut1.sma_pcie_nic, '192.168.12.1',
                                          sut2.sma_pcie_nic, '192.168.12.2')

    # Mellanox Subnet: IPv4 (192.168.13.x), IPv6 (fd00:1762:13::x)
    conns.mel_conn_v6 = NicPortConnection(sut1.mel_pcie_nic, 'fd00:1762:13::1',
                                          sut2.mel_pcie_nic, 'fd00:1762:13::2')
    conns.mel_conn_v4 = NicPortConnection(sut1.mel_pcie_nic, '192.168.13.1',
                                          sut2.mel_pcie_nic, '192.168.13.2')

    # Broadcom Subnet: IPv4 (192.168.14.x), IPv6 (fd00:1762:14::x)
    conns.bro_conn_v6 = NicPortConnection(sut1.bro_pcie_nic, 'fd00:1762:14::1',
                                          sut2.bro_pcie_nic, 'fd00:1762:14::2')

    conns.bro_conn_v4 = NicPortConnection(sut1.bro_pcie_nic, '192.168.14.1',
                                          sut2.bro_pcie_nic, '192.168.14.2')

    if conn:
        return conns.__dict__[conn]
    else:
        return conns
