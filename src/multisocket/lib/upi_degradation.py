from dtaf_core.lib.tklib.basic.const import OS
from dtaf_core.lib.tklib.basic.utility import get_xml_prvd
from dtaf_core.lib.tklib.infra.xtp.itp import PythonsvSemiStructured, CscriptsSemiStructured
from dtaf_core.lib.tklib.steps_lib.os_scene import OperationSystem
from dtaf_core.lib.tklib.steps_lib.uefi_scene import UefiShell

from src.multisocket.lib.multisocket import MultiSocket
from itertools import combinations

from dtaf_core.lib.tklib.basic.log import logger

links_to_fail_4s = {
    "topology_full_1": {
        "link_1": [("S0P0", "S3P0"), ("S1P1", "S2P1"), "TOPOLOGY_4S_Degradation_9"],
        "link_2": [("S0P2", "S2P2"), ("S1P2", "S3P2"), "TOPOLOGY_4S_Degradation_10"],
        "link_3": [("S0P1", "S1P0"), ("S2P0", "S3P1"), "TOPOLOGY_4S_Degradation_11"]
    },
    "topology_full_2": {
        "link_1": [("S0P3", "S3P2"), ("S1P3", "S2P2"), "TOPOLOGY_4S_Degradation_12"],
        "link_2": [("S0P2", "S2P3"), ("S1P2", "S3P3"), "TOPOLOGY_4S_Degradation_13"],
        "link_3": [("S0P0", "S1P0"), ("S1P0", "S0P0"), "TOPOLOGY_4S_Degradation_14"]
    },
    "topology_full_3": {
        "link_1": ["(S0P3", "S3P2)", ("S1P2", "S2P3"), "TOPOLOGY_4S_Degradation_15"],
        "link_2": [("S0P2", "S2P2"), ("S1P3", "S3P3"), "TOPOLOGY_4S_Degradation_16"],
        "link_3": [("S0P0", "S1P1"), ("S2P0", "S3P1"), "TOPOLOGY_4S_Degradation_17"]
    },
    "topology_full_4": {
        "link_1": [("S0P3", "S3P3"), ("S1P3", "S2P3"), "TOPOLOGY_4S_Degradation_18"],
        "link_2": [("S0P1", "S2P1"), ("S1P1", "S3P1"), "TOPOLOGY_4S_Degradation_19"],
        "link_3": [("S0P2", "S1P2"), ("S1P2", "S0P2"), "TOPOLOGY_4S_Degradation_20"]
    },
    "topology_full_5": {
        "link_1": [("S0P2", "S3P2"), ("S1P2", "S2P2"), "TOPOLOGY_4S_Degradation_21"],
        "link_2": [("S0P1", "S2P1"), ("S1P0", "S3P0"), "TOPOLOGY_4S_Degradation_22"],
        "link_3": [("S0P0", "S1P1"), ("S2P0", "S3P1"), "TOPOLOGY_4S_Degradation_23"]
    }
}


class UpiDegrade(object):
    sut = None
    itp = None
    my_os = None
    check_instance = None

    def __init__(self, sut, glb, lcl, itplib):
        self.sut = sut
        if itplib == "cscripts":
            self.itp = CscriptsSemiStructured(glb, lcl)
        elif itplib == "pythonsv":
            self.itp = PythonsvSemiStructured(get_xml_prvd('cpu').find('.//family').text, glb, lcl)
        self.my_os = OperationSystem[OS.get_os_family(self.sut.default_os)]
        self.check_instance = MultiSocket(itplib, self.itp)

    def __del__(self):
        self.itp.exit()

    def link_check_and_reset(self, degraded_top):
        # check UPI details after degradation
        self.check_instance.check_upi_topology(degraded_top)
        self.check_instance.check_upi_link_speed(self.sut)
        self.check_instance.check_upi_s_clm()
        self.check_instance.check_upi_print_error()

        self.itp.execute("cli.CvLoadDefaults()")
        # self.my_os.s5_cycle_step(self.sut)
        UefiShell.reset_cycle_step(self.sut)

    def link_degrade_4s_full(self, top_pair):
        for links in top_pair.keys():
            link1 = top_pair[links][0]  # start from SxPx-SxPx, SxPx-SxPx level
            link2 = top_pair[links][1]
            degraded_top = top_pair[links][2]

            # degrade on single-link level
            # self.single_link_degrade(link1, degraded_top)
            # self.single_link_degrade(link2, degraded_top)

            # degrade on multiple link level
            for port in link1:  # loop SxPx level
                # take combination by choosing 2 out of 3
                comb = combinations([port, link2[0], link2[1]], 2)
                logger.info(f"\nstart to disable link {link1} port {port}")
                # loop thru first two combination and degrade all three ports at 3rd
                self.degrade_in_comb(comb, port, degraded_top)

            # degrade all 4 ports in this link pair
            logger.debug(f"Cpu{link1[0][1]}P{link1[0][3]}KtiPortDisable=0x1, "
                         f"Cpu{link1[1][1]}P{link1[1][3]}KtiPortDisable=0x1, "
                         f"Cpu{link2[0][1]}P{link2[0][3]}KtiPortDisable=0x1, "
                         f"Cpu{link2[1][1]}P{link2[1][3]}KtiPortDisable=0x1, "
                         f"DfxSystemDegradeMode=0x2")
            self.itp.execute("cli.CvProgKnobs("
                             f"'Cpu{link1[0][1]}P{link1[0][3]}KtiPortDisable=0x1, "
                             f"Cpu{link1[1][1]}P{link1[1][3]}KtiPortDisable=0x1, "
                             f"Cpu{link2[0][1]}P{link2[0][3]}KtiPortDisable=0x1, "
                             f"Cpu{link2[1][1]}P{link2[1][3]}KtiPortDisable=0x1, "
                             f"DfxSystemDegradeMode=0x2')")
            # self.my_os.s5_cycle_step(self.sut)
            UefiShell.reset_cycle_step(self.sut)

            self.link_check_and_reset(degraded_top)

    def single_link_degrade(self, link, degraded_top):
        logger.info("\ndegrade single link: ", link)

        # degrade two ports in order
        for port in link:
            logger.debug(f"Cpu{port[1]}P{port[3]}KtiPortDisable=0x1, "
                         f"DfxSystemDegradeMode=0x2")
            self.itp.execute("cli.CvProgKnobs("
                             f"'Cpu{port[1]}P{port[3]}KtiPortDisable=0x1, "
                             f"DfxSystemDegradeMode=0x2')")
            UefiShell.reset_cycle_step(self.sut)
            # self.my_os.s5_cycle_step(self.sut)

            self.link_check_and_reset(degraded_top)

        # degrade both ports
        logger.debug(f"Cpu{link[0][1]}P{link[0][3]}KtiPortDisable=0x1, "
                     f"Cpu{link[1][1]}P{link[1][3]}KtiPortDisable=0x1, "
                     f"DfxSystemDegradeMode=0x2")
        self.itp.execute("cli.CvProgKnobs("
                         f"'Cpu{link[0][1]}P{link[0][3]}KtiPortDisable=0x1, "
                         f"Cpu{link[1][1]}P{link[1][3]}KtiPortDisable=0x1, "
                         f"DfxSystemDegradeMode=0x2')")
        self.link_check_and_reset(degraded_top)

    def degrade_in_comb(self, input_comb, input_port, degraded_top):
        count = 0
        for p in input_comb:
            if count == 2:
                logger.debug(f"Cpu{input_port[1]}P{input_port[3]}KtiPortDisable=0x1, "
                             f"Cpu{p[0][1]}P{p[0][3]}KtiPortDisable=0x1, "
                             f"Cpu{p[1][1]}P{p[1][3]}KtiPortDisable=0x1, "
                             f"DfxSystemDegradeMode=0x2")
                self.itp.execute("cli.CvProgKnobs("
                                 f"'Cpu{input_port[1]}P{input_port[3]}KtiPortDisable=0x1, "
                                 f"Cpu{p[0][1]}P{p[0][3]}KtiPortDisable=0x1, "
                                 f"Cpu{p[1][1]}P{p[1][3]}KtiPortDisable=0x1, "
                                 f"DfxSystemDegradeMode=0x2')")
            else:
                logger.debug(f"execute "
                             f"Cpu{p[0][1]}P{p[0][3]}KtiPortDisable=0x1, "
                             f"Cpu{p[1][1]}P{p[1][3]}KtiPortDisable=0x1, "
                             f"DfxSystemDegradeMode=0x2")
                self.itp.execute("cli.CvProgKnobs("
                                 f"'Cpu{input_port[1]}P{input_port[3]}KtiPortDisable=0x1, "
                                 f"Cpu{p[0][1]}P{p[0][3]}KtiPortDisable=0x1, "
                                 f"Cpu{p[1][1]}P{p[1][3]}KtiPortDisable=0x1, "
                                 f"DfxSystemDegradeMode=0x2')")
            UefiShell.reset_cycle_step(self.sut)
            # self.my_os.s5_cycle_step(self.sut)

            self.link_check_and_reset(degraded_top)
            count += 1
