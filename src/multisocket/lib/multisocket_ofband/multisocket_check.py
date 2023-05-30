import getopt
import os
import sys
import re

from configparser import ConfigParser

from dtaf_core.lib.tklib.infra.sut import get_default_sut
from dtaf_core.lib.tklib.basic.log import logger

from src.multisocket.lib.multisocket import MultiSocket


class UPI:
    LINK_SPEED = {
        'sapphirerapids': {
            0x7F: 16.0,
            0x02: 16.0,
            0x01: 14.4,
            0x00: 12.8,
        },
        'graniterapids': {
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


mltskt_config_path = r"C:\BKCPkg\multisocket_ofband\mltskt_config.ini"
psr = ConfigParser()
psr.read(mltskt_config_path)


class MultisocketOutband:
    @staticmethod
    def check_upi_topology(log_path, degraded=False):
        log_path = os.path.join(log_path, "last_itp_cmd_out.txt")
        with open(log_path, "r") as r:
            itp_output = r.readlines()

        top = psr.get("config", "topology") if not degraded else psr.get("config", "degraded_top")
        plat = psr.get("config", "platform")
        assert top is not None and plat is not None
        logger.info(f"Got comparator {top} ready for compare")

        to_check = None
        if plat in ["SPR", "EMR"]:
            import EGS_topology
            to_check = EGS_topology.EGS_Topology[top]
        elif plat in ["GNR"]:
            import BHS_topology
            to_check = BHS_topology.BHS_Topology[top]
        assert to_check is not None, "Input topology to check might be wrong"
        r.close()

        top_find = re.findall(r'S\d_P\d\s<-+>\sS\d_P\d', "".join(itp_output))
        assert len(top_find) == len(to_check), "Case result check failed: topology not matching"

        for n in range(len(top_find)):
            logger.info(top_find[n] + " comparing to " + to_check[n])
            if top_find[n] != to_check[n]:
                raise RuntimeError("Case result check failed: topology not matching")

    @staticmethod
    def check_upi_link_speed(log_path):
        log_path = os.path.join(log_path, "last_itp_cmd_out.txt")
        with open(log_path, "r") as r:
            rdl = r.readlines()
        output = "".join(rdl)

        socket_name = output.splitlines()[0]

        topology = re.findall(r'S(\d)_P(\d)\s<-+>\sS(\d)_P(\d)', output)
        port_pair = {}
        for end0_socket, end0_port, end1_socket, end1_port in topology:
            port_pair[(end0_socket, end0_port)] = (end1_socket, end1_port)

        port_knobs = re.findall(r'Cpu(\d)P(\d)KtiLinkSpeed\|\s*\S+\s*\|\s*\S+\s*\|\s*(\S+)\s*\|', output)
        # last value is knob current value
        # sample: '| 6| 0102|                        Cpu0P0KtiLinkSpeed| 1|       7F  |       7F  |'
        ports_speed_setting = {}
        for socket_index, port_index, knob_value in port_knobs:
            ports_speed_setting[(socket_index, port_index)] = int(f'0x{knob_value}', 16)

        link_speed = re.findall(r"Socket (\d), Port (\d), Link Speed: (\d+\.\d+).*Status: Fast Mode.*", output)
        for socket_index, port_index, link_speed in link_speed:
            port_speed_knob_value = ports_speed_setting.get((socket_index, port_index))
            port_speed = UPI.LINK_SPEED.get(socket_name).get(port_speed_knob_value)

            mapping_port = port_pair[(socket_index, port_index)]
            mapping_port_speed_knob_value = ports_speed_setting.get((mapping_port[0], mapping_port[1]))
            mapping_port_speed = UPI.LINK_SPEED.get(socket_name).get(mapping_port_speed_knob_value)

            logger.debug(f"Checking port {socket_index} {port_index} \n"
                         f"Current read speed: {link_speed} \n"
                         f"Current port speed: {port_speed} \n"
                         f"Mapping speed: {mapping_port_speed} \n")
            if float(link_speed) != min(port_speed, mapping_port_speed):
                raise RuntimeError(f'link speed is error for socket {socket_index} port {port_index}')

    @staticmethod
    def check_upi_s_clm(log_path):
        log_path = os.path.join(log_path, "last_itp_cmd_out.txt")
        with open(log_path, "r") as r:
            itp_output = r.read()

        active_port = MultiSocket.get_activated_port_dict(itp_output)
        clm_output = itp_output[itp_output.find("socket"):]
        r.close()

        plat = psr.get("config", "platform")
        for output_line in clm_output.split("\n"):
            split_line = output_line.strip().split('-')
            socket_port = split_line[0].split(".")
            socket = socket_port[0][-1]
            port = None
            if plat in ["SPR", "EMR"]:
                port = socket_port[3][-1]
            elif plat in ["GNR"]:
                port = socket_port[4][-1]
            s_clm_value = split_line[1]

            logger.debug(f"Checking bandwidth on socket{socket} port {port}")
            if port in active_port[socket]:
                assert s_clm_value.strip() == '0x00000007', 's_clm value do not equal 0x00000007'
            else:
                logger.debug(f"Port{socket} on socket{port} is not activated, skipping checking process")

    @staticmethod
    def check_upi_print_error(log_path):
        log_path = os.path.join(log_path, "last_itp_cmd_out.txt")
        with open(log_path, "r") as r:
            rdl = r.readlines()
        output = "".join(rdl)
        r.close()

        for register_name in UPI.print_error_list:
            match_results = re.findall(f'{register_name}.*', output)
            if len(match_results) == 0:
                raise RuntimeError(f'Can not find information for register {register_name}')

            for result in match_results:
                register_values = result.split('|')[1:-1]
                for value in register_values:
                    assert value.strip() == '0x0', 'register value does not equal 0x0'

    @staticmethod
    def check_dmsg_win_log(os):
        sut = get_default_sut()

        if os.lower() == "windows":
            ret, out, err = sut.execute_host_cmd("Get-EventLog -LogName System -EntryType Error", powershell=True)
            if ret != 0:
                raise RuntimeError(f"Windows event log collection failed: {err}")
            else:
                assert len(out) == 0
        elif os.lower() == "linux":
            to_ignore = ["RAS: Correctable Errors collector initialized.",
                         "ERST: Error Record Serialization Table (ERST) support is initialized."]

            ret, out, err = sut.execute_shell_cmd("dmesg")
            for line in out.split("\n"):
                if "error" in line:
                    if to_ignore[0] not in line or to_ignore[1] not in line:
                        raise RuntimeError(f"Error detected in dmesg during stress test: {line}")
                if "Call Trace" in line:
                    raise RuntimeError(f"Error detected in dmesg during stress test: {line}")

            _, out, _ = sut.execute_shell_cmd("cat /sys/devices/system/clocksource/clocksource0/current_clocksource")
            # if "tsc" not in out:
            #     raise RuntimeError(f"Cat clocksource failed, tsc not returned upon execution: {out}")

        else:
            raise RuntimeError("Os variable input is wrong, please input either windows or linux")

    @staticmethod
    def set_degraded_top_in_file(degraded):
        psr.set('config', 'degraded_top', degraded)
        psr.write(open(mltskt_config_path, 'w'))


if __name__ == "__main__":
    topology, de_top_check, speed, bandwidth, error, os_log, log, degraded = False, False, False, False, False, None, None, None
    opts, args = getopt.getopt(sys.argv[1:], shortopts="-t-d-s-b-e",
                               longopts=["log=", "os_log=", "degraded="])

    for opt, val in opts:
        if opt == '-t':
            topology = True
        elif opt == '-d':
            topology = True
            de_top_check = True
        elif opt == '-s':
            speed = True
        elif opt == '-b':
            bandwidth = True
        elif opt == '-e':
            error = True
        elif opt == '--log':
            log = val
        elif opt == '--os_log':
            os_log = val
        elif opt == '--degraded':
            degraded = val

    try:
        assert log is not None

        if topology:
            MultisocketOutband.check_upi_topology(log, de_top_check)
        if speed:
            MultisocketOutband.check_upi_link_speed(log)
        if bandwidth:
            MultisocketOutband.check_upi_s_clm(log)
        if error:
            MultisocketOutband.check_upi_print_error(log)
        if os_log is not None:
            MultisocketOutband.check_dmsg_win_log(os_log)
        if degraded is not None:
            MultisocketOutband.set_degraded_top_in_file(degraded)

    except RuntimeError or AssertionError as re:
        exit(-1)
        raise re
