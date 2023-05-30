import re
from configparser import ConfigParser
from typing import Match, Pattern
from dtaf_core.lib.tklib.basic.const import SUT_STATUS
from dtaf_core.lib.tklib.basic.log import logger

from src.configuration.tkconfig import bios_knob

from dtaf_core.lib.os_lib import OsCommandResult
from dtaf_core.providers.sut_os_provider import SutOsProvider


class UPI:
    LINK_SPEED = {
        'SPR': {
            0x7F: 16.0,
            0x02: 16.0,
            0x01: 14.4,
            0x00: 12.8,
        },
        'GNR': {
            0x7F: 24.0,
            0x02: 16.0,
            0x03: 20.0,
            0x04: 24.0,
        }
    }

    print_error_list = [
        # "kti_mc_ad",
        "ktiph_rxl0c_err_s",  # work around: stand for ktiph_rxl0c_err_sts
        "ktiph_rxl0c_err_l",  # work around: stand for ktiph_rxloc_err_log0 & ktiph_rxloc_err_log1
        "ktiph_l0pexit_err",
        "ktierrcnt0_cntr",
        "ktierrcnt1_cntr",
        "ktierrcnt2_cntr",
        "kticrcerrcnt",
        "ktiles",
        # "ktidbgerrst0",
        # "ktidbgerrst1",
        "bios_kti_err_st"
    ]

_LIN_NUM_SOCKETS_RE: Pattern[str] = re.compile(r"Socket\(s\):\s+(?P<num>[0-9]+)")

mltskt_config_path = r"C:\BKCPkg\multisocket_ofband\mltskt_config.ini"
psr = ConfigParser()
psr.read(mltskt_config_path)

class MultiSocket:
    itplib = ""
    itp = None

    def __init__(self, in_itplib, in_itp):
        self.itplib = in_itplib
        self.itp = in_itp

        if self.itplib.lower() == "pythonsv":
            self.itp.execute("import upi.upiStatus as us")
            self.itp.execute('import pysvtools.xmlcli.XmlCli as cli')
        elif self.itplib.lower() == "cscripts":
            self.itp.execute("import commlibs.qpi.xnmupi.xnmupi as u")
            self.itp.execute("from pysvtools.xmlcli import XmlCli as cli")
        else:
            raise RuntimeError("itplib input should be either pythonsv or cscripts")

        self.itp.execute('cli.clb._setCliAccess("itpii")')
        self.itp.execute('cli.clb.AuthenticateXmlCliApis=True')

    def check_upi_topology(self, degraded_top=None):
        itp_output = self.itp.execute("us.printTopology()") if self.itplib == "pythonsv" else self.itp.execute("u._upistatus.printTopology()")

        top = psr.get("config", "topology") if degraded_top is None else degraded_top
        plat = psr.get("config", "platform")
        assert top is not None and plat is not None
        logger.info(f"Got comparator {top} ready for compare")
        assert top is not None and plat is not None

        to_check = None
        if plat in ["SPR", "EMR"]:
            from src.multisocket.lib.multisocket_ofband import EGS_topology
            to_check = EGS_topology.EGS_Topology[top]
        elif plat in ["GNR"]:
            from src.multisocket.lib.multisocket_ofband import BHS_topology
            to_check = BHS_topology.BHS_Topology[top]
        assert to_check is not None, "Input topology to check might be wrong"

        top_find = re.findall(r'S\d_P\d\s<-+>\sS\d_P\d', "".join(itp_output))
        assert len(top_find) == len(to_check), "Case result check failed: topology not matching"

        for n in range(len(top_find)):
            logger.info(top_find[n] + " comparing to " + to_check[n])
            if top_find[n] != to_check[n]:
                raise RuntimeError("Case result check failed: topology not matching")

    def check_upi_link_speed(self, sut):
        # convert upi topology to port pair with dict data structure
        topology_output = self.itp.execute("us.printTopology()") if self.itplib == "pythonsv" else self.itp.execute("u._upistatus.printTopology()")
        topology = re.findall(r'S\d_P\d\s<-+>\sS\d_P\d', topology_output)
        assert len(topology) > 0
        port_pair = {}
        for mapping in topology:
            match_result = re.match(r'S(\d)_P(\d)\s<-+>\sS(\d)_P(\d)', mapping)
            end0_socket = match_result.group(1)
            end0_port = match_result.group(2)
            end1_socket = match_result.group(3)
            end1_port = match_result.group(4)
            port_pair[(end0_socket, end0_port)] = (end1_socket, end1_port)
        ports_speed_setting = self.get_ports_speed_setting(port_pair.keys())

        output = self.itp.execute("us.printLinkSpeed()") if self.itplib == "pythonsv" else self.itp.execute("u._upistatus.printLinkSpeed()")

        pattern = re.compile(r"Socket (\d), Port (\d), Link Speed: (\d+\.\d+).*Status: Fast Mode.*")
        for output_line in output.splitlines():
            match_result = pattern.match(output_line)
            if match_result is not None:
                socket_number = match_result.group(1)
                port_number = match_result.group(2)
                link_speed = match_result.group(3)

                port_speed_knob_value = ports_speed_setting.get((socket_number, port_number))
                port_speed = UPI.LINK_SPEED.get(sut.socket_name).get(port_speed_knob_value)

                mapping_port = port_pair[(socket_number, port_number)]
                mapping_port_speed_knob_value = ports_speed_setting.get((mapping_port[0], mapping_port[1]))
                mapping_port_speed = UPI.LINK_SPEED.get(sut.socket_name).get(mapping_port_speed_knob_value)

                if float(link_speed) != min(port_speed, mapping_port_speed):
                    raise RuntimeError(f'link speed is error for socket {socket_number} port {port_number}')

    def check_upi_s_clm(self):
        output = self.itp.execute("print(sv.sockets.uncore.upi.upis.ktireut_ph_css.s_clm)") if self.itplib == "pythonsv" \
            else self.itp.execute("print(sv.sockets.ios.uncore.upi.upis.upi_regs.ktireut_ph_css.s_clm)")

        top = self.itp.execute("us.printTopology()") if self.itplib == "pythonsv" \
            else self.itp.execute("u._upistatus.printTopology()")
        active_port = MultiSocket.get_activated_port_dict(top)

        plat = psr.get("config", "platform")
        for output_line in output.split("\n"):
            split_line = output_line.strip().split('-')
            socket_port = split_line[0].split(".")
            socket = socket_port[0][-1]
            if plat in ["SPR", "EMR"]:
                port = socket_port[3][-1]
            elif plat in ["GNR"]:
                port = socket_port[4][-1]
            s_clm_value = split_line[1]

            logger.info(f"Checking bandwidth on socket{socket} port {port}")
            if port in active_port[socket]:
                assert s_clm_value.strip() == '0x00000007', 's_clm value do not equal 0x00000007'
            else:
                logger.info(f"Port{socket} on socket{port} is not activated, skipping checking process")

    def check_upi_print_error(self):
        output = self.itp.execute("us.printErrors()") if self.itplib.lower() == "pythonsv" else self.itp.execute("u._upistatus.printErrors()")

        for register_name in UPI.print_error_list:
            match_results = re.findall(f'{register_name}.*', output)
            if len(match_results) == 0:
                raise RuntimeError(f'Can not find information for register {register_name}')

            for result in match_results:
                register = result.split('|')[0]
                register_values = result.split('|')[1:-1]
                for value in register_values:
                    assert value.strip() == '0x0', f'register {register} value does not equal 0x0'

    @staticmethod
    def pcie_check(pcie_key, sut):
        if sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX:
            ret, pcie, err = sut.execute_shell_cmd(f"lspci | grep -i {pcie_key}")
            if ret != 0:
                raise RuntimeError(err)
            bus_id = pcie.split(" ")[0]

            ret, vendor_id, err = sut.execute_shell_cmd(f"lspci -n | grep -i {bus_id}")
            if ret != 0:
                raise RuntimeError(err)
            vendor_id = vendor_id.split(" ")[-3]

            ret, pcie_width, err = sut.execute_shell_cmd(f"lspci -n -d {vendor_id} -vvv | grep --color Width")
            if ret != 0:
                raise RuntimeError(err)
            pcie_info = pcie_width

        else:
            ret, pcie, err = sut.execute_shell_cmd("wmic path win32_pnpentity where "
                                                   f"\"name like '%{pcie_key}%'\" get name, deviceid")
            if pcie.strip() == "":
                raise RuntimeError(err)
            logger.info("Get windows PCI info: " + pcie.strip())
            pcie_info = pcie.strip()

        logger.info(pcie_info)
        return pcie_info

    def get_ports_speed_setting(self, ports):
        knob_name_template = bios_knob('qpi_port_link_speed_template_xmlcli')
        knobs_name = [knob_name_template.format(socket_number, port_number) for socket_number, port_number in ports]
        knob_query = [f'{name}=0x0' for name in knobs_name]
        knob_query = ','.join(knob_query)
        output = self.itp.execute(f'cli.CvReadKnobs("{knob_query}")')
        result_lines = re.findall(r'.*KtiLinkSpeed\|.*', output)
        # last value is knob current value
        # sample: '| 6| 0102|                        Cpu0P0KtiLinkSpeed| 1|       7F  |       7F  |'
        knobs_value = [str(result[1:-1]).split('|')[-1].strip() for result in result_lines]
        knobs_value = [int(f'0x{value}', 16) for value in knobs_value]

        return dict(zip(ports, knobs_value))

    @staticmethod
    def get_activated_port_dict(output):
        topology = re.findall(r'S(\d)_P(\d)\s<-+>\sS(\d)_P(\d)', output)
        port_dict = {}
        for end0_socket, end0_port, end1_socket, end1_port in topology:
            if end0_socket not in port_dict.keys():
                port_dict[end0_socket] = {end0_port}
            else:
                port_dict[end0_socket].add(end0_port)

        return port_dict

