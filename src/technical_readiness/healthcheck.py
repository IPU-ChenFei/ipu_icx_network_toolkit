'''
Copyright (c) 2022, Intel Corporation. All rights reserved.
Intention is to use HSDES query and platform config to generate, trigger and
update results back to HSDES using CommandCenter and HSDES rest APIs

Title          : healthcheck.py
Author(s)      : Shubham Swati Prasad

Documentation:
BKM Link               :  https://wiki.ith.intel.com/display/DCGBKC/healthcheck+tool

Command Line to execute:  python healthcheck.py

Dependency Files:
Additional packages needed:

'''
from collections import OrderedDict
import pysvtools.bitmanip as bm
from namednodes import sv
import ipccli
import sapphirerapids.toolext.bootscript.toolbox.fuse_info as fuseinfo
import sapphirerapids.mc.sprAddressTranslator as at
import sapphirerapids.upi.upiUtils as utils
import json
import xml.etree.ElementTree as info
import pysvtools.pciedebug.ltssm as ltssm
import os
import os.path
import sapphirerapids.upi.upiStatus as us
import svtools.logging.toolbox as toolbox
import platform
import subprocess
import re

dummy_logger = toolbox.getLogger("upiStatus")
dummy_logger.setFile("upi.log")
dummy_logger.setFileFormat('simple')
dummy_logger.setFileLevel(toolbox.DEBUGALL)
_log = toolbox.getLogger("upiStatus")

speed = {"GEN1":"2.5","GEN2":"5","GEN3":"8","GEN4":"16","GEN5":"32"}
slots1 = {"pxp0.port2":"slot_d","pxp1.port1":"slot_e","pxp2.port4":"right_riser_top","pxp3.port3":"right_riser_bottom","pxp4.port5":"","pxp5.port2":"mcio_s1_pxp5_pcieg_port2"}
slots0 = {"pxp0.pcieg4.dmi":"","pxp0.port1":"","pxp1.port1":"left_riser_bottom","pxp2.port4":"left_riser_top","pxp3.port3":"slot_b","pxp4.port5":"","pxp5.port2":"mcio_s0_pxp5_pcieg_port2"}
topoLinkDict1 = {}
topoLinkDict2 = {}
sList = []
pList = []
srList = []
prList = []


def qdf_no_of_sockets():
    itp = ipccli.baseaccess()
    itp.unlock()
    itp.forcereconfig()

    sv.refresh()

    sv.sockets.tile0.fuses.load_fuse_ram()

    fuseInfoObj = fuseinfo.FuseInfo()
    qdf_name = fuseInfoObj.get_qdf_str(sv.socket0, 0)

    print("QDF Name:", qdf_name)
    mytree = info.parse("Hardware_And_Software_Configurations.xml")
    root = mytree.getroot()
    for qdf in root.iter('qdf'):
        qdf.text = str(qdf_name)
    for no_of_sockets in root.iter('num_of_sockets'):
        no_of_sockets.text = str(len(utils.getSockets()))
        break

    for qdf in root.iter('Socket'):
        qdf.attrib["QDF"] = str(qdf_name)
    for num_of_sockets in root.iter('content'):
        num_of_sockets.attrib["no_of_sockets"] = str(len(utils.getSockets()))
        break

    mytree.write('Hardware_And_Software_Configurations.xml')

    with open('System_Details.txt', 'r+') as f:
        data = json.load(f)
    data["<PROGRAM>_Platform_HW_Details"]["Board"]["Socket"]["QDF"] = qdf_name

    with open('System_Details.txt', 'w') as f:
        json.dump(data, f, indent=4)
    print("QDF End")

def dimm_config_fun(socket=None, hbm=None, mc=None, ch=None, show=True, get_ddrt_size=False, log=_log):

    with open('System_Details.txt', 'r+') as f:
       data = json.load(f)

    if get_ddrt_size:
        sxp_size_dict = at.get_sxp_size_dict(log=log)
    else:
        sxp_size_dict = OrderedDict()

    pretty_name = {"DDR": "DDR", "two_lm": "2LM", "pm": "AD", "pm_blk": "Block"}
    dimm_config_dict = {"size": OrderedDict()}
    dimm_config_dict["size"]["DDR"] = 0
    dimm_config_dict["size"]["two_lm"] = 0
    dimm_config_dict["size"]["pm"] = 0
    dimm_config_dict["size"]["pm_blk"] = 0

    socket_list = at.get_socket_list(socket=socket, fun_name="get_dimm_config", log=log)
    for skt in socket_list:
        if skt.name not in dimm_config_dict:
            dimm_config_dict[skt.name] = {"size": OrderedDict()}
            dimm_config_dict[skt.name]["size"]["DDR"] = 0
            dimm_config_dict[skt.name]["size"]["two_lm"] = 0
            dimm_config_dict[skt.name]["size"]["pm"] = 0
            dimm_config_dict[skt.name]["size"]["pm_blk"] = 0
        hbm_num = -1  # Supressing HBM as we will not be using get_dimm_config with HBM
        print_socket = True
        if hasattr(skt.uncore.memss, 'mcs'):  # Testing for existence due to the SPR-HBM project.
            for mcobj in skt.uncore.memss.mcs:
                mc_num = mcobj.target_info['instance']
                if mc is not None and mc_num != mc:
                    continue
                print_mc = True
                for chobj in mcobj.chs:
                    ch_num = chobj.target_info['instance']
                    if ch is not None and ch_num != ch:
                        continue

                    print_channel = True
                    for slot in range(at.get_max("dimm", log=log) + 1):
                        err_code, output_str = at.decode_mtr(skt, hbm_num, mc_num, ch_num, slot, log=log)
                        if output_str == "No dimm present":
                            # check for a ddrt dimm
                            ddrt_cfg = at.get_ddrt_cfg(skt, hbm_num, mc_num, ch_num)
                            if ddrt_cfg.getfieldobject("slot%d" % slot):
                                output_str = "DDRT2 Dimm"

                                if mc_num not in dimm_config_dict[skt.name]:
                                    dimm_config_dict[skt.name][mc_num] = {}
                                if ch_num not in dimm_config_dict[skt.name][mc_num]:
                                    dimm_config_dict[skt.name][mc_num][ch_num] = {'GB': 0, 'used': -1}

                                if skt.name in sxp_size_dict and \
                                        mc_num in sxp_size_dict[skt.name] and \
                                        ch_num in sxp_size_dict[skt.name][mc_num] and \
                                        slot in sxp_size_dict[skt.name][mc_num][ch_num]:
                                    for key, size in sxp_size_dict[skt.name][mc_num][ch_num][slot].items():
                                        dimm_config_dict[skt.name]["size"][key] += size
                                        dimm_config_dict["size"][key] += size
                                        dimm_config_dict[skt.name][mc_num][ch_num]['GB'] += bm.number2readable(size,
                                                                                                               'G').coef
                                        r_size = bm.number2readable(size)
                                        output_str += " %s %.2f%s" % (pretty_name[key], r_size.coef, r_size.unit)

                        if output_str == "No dimm present":
                            continue

                        if mc_num not in dimm_config_dict[skt.name]:
                            dimm_config_dict[skt.name][mc_num] = {}
                        if ch_num not in dimm_config_dict[skt.name][mc_num]:
                            dimm_config_dict[skt.name][mc_num][ch_num] = {'GB': 0, 'used': -1}

                        if print_socket and show:
                            log.result("")
                            log.result("%s:" % skt.name)
                            print_socket = False
                        if print_mc and show:
                            log.result("  Mc%d:" % mc_num)
                            print_mc = False
                        if print_channel and show:
                            log.result("    Ch%d:" % ch_num)
                            print_channel = False

                        color_string = ""
                        if err_code:
                            color_string = "\001ired\001"
                        elif output_str.count("DDRT") == 0:
                            split_list = output_str.split()
                            split_list = split_list[1].split('GB')
                            if split_list:
                                gb = int(split_list[0])
                            else:
                                split_list = output_str.split('MB')
                                if split_list:
                                    gb = int(split_list[0]) / 1024.0
                                else:
                                    log.error("Unable to decode '%s' to add to totalGB" % output_str)
                                    gb = 0
                            size = gb * 0x40000000
                            dimm_config_dict[skt.name]["size"]["DDR"] += size
                            dimm_config_dict["size"]["DDR"] += size
                            dimm_config_dict[skt.name][mc_num][ch_num]['GB'] += gb
                            color_string = ""
                        if show:
                            log.result("%s      Dimm %d:  %s" % (color_string, slot, output_str))
                        new_dict1 = {"%sMC%d" % (skt.name, mc_num): {
                            "DIMM%d"%(slot): {
                                "MemoryType": "%s"%(output_str.split(" ",1)[0]),
                                "Size": "%s"%(output_str.split(" ",3)[1]),
                                "Vendor": "Hynix, [Samsung, Micron]",
                                "Speed": "5600, [4800, 4400,...]",
                                "DIMMType": "9x4, [8x2...]"
                            }}}
                        data["<PROGRAM>_Platform_HW_Details"]["Board"]["Socket"].update(new_dict1)
        if show and not print_socket:  # There was a dimm on this socket
            log.result("")
            for key, size in dimm_config_dict[skt.name]["size"].items():
                # Don't print this information if we didn't collect it
                if not get_ddrt_size and key in ["two_lm", "pm", "pm_blk"]:
                    continue
                r_size = bm.number2readable(size)
                log.result("  %5s: %7.2f%sB" % (pretty_name[key], r_size.coef, r_size.unit))
    if show:
        log.result("")
        for key, size in dimm_config_dict["size"].items():
            # Don't print this information if we didn't collect it
            if not get_ddrt_size and key in ["two_lm", "pm", "pm_blk"]:
                continue
            r_size = bm.number2readable(size)
            log.result("Total %5s: %7.2f%sB" % (pretty_name[key], r_size.coef, r_size.unit))
        log.result("")

    with open('System_Details.txt', 'w') as f:
        json.dump(data, f, indent=4)

def cpu_pcie_fun():
    mytree = info.parse("Hardware_And_Software_Configurations.xml")
    root = mytree.getroot()
    for elem in root.findall("content"):
        for y in elem.findall('Platform_Board'):
            b = y.find("CPU")
            c = b.find("Socket")
            d = c.find("IO")
            for e in d.findall("PCIe"):
                children = e.findall('Slot')
                for child in children:
                    e.remove(child)

    mytree.write("Hardware_And_Software_Configurations.xml")

    ltssm.sls()
    date = ltssm.date
    num_of_soc = len(utils.getSockets())
    data = None
    if os.path.exists("eip_%d%02d%02d.log" % (date.tm_year, date.tm_mon, date.tm_mday)):
        with open(
                os.path.join(os.getcwd(), "eip_%d%02d%02d.log" % (date.tm_year, date.tm_mon, date.tm_mday))) as outputF:
            data = "".join(outputF.readlines())
            data = data.split("SOCKET")[-num_of_soc:]
    if data:
        for soc in range(num_of_soc):
            print("Socket{}".format(soc))
            data_soc = data[soc]
            pcie_data = re.findall("Port (pxp.*) \(pcieg\d\) is (\w\d)  \(ilw=x\d\) \((GEN\d).*\). LTSSM = UP",
                                   (data_soc))



            for i in pcie_data:
                print(i)
                port, width, gen = i
                print(width)

                for elem in root.findall("content"):
                    for x in elem.findall("pcie"):

                        b = x.find("pcie_device_population")
                        c = b.find("SPR")
                        if soc == 0:
                            d = c.find(slots0[port])
                            d.find("pcie_device_width").text = width
                            d.find("pcie_device_speed_in_gt_sec").text = speed[gen]
                        else:
                            d = c.find(str(slots1[port]))
                            d.find("pcie_device_width").text = width
                            d.find("pcie_device_speed_in_gt_sec").text = speed[gen]

                slot = ""
                if soc == 0:
                    slot = slots0[port]

                else:
                    slot = slots1[port]
                for element in root.iter('PCIe'):
                    new_subelement = info.Element("Slot", Bus="", BusWidth=width, DeviceID="", Function="",
                                                  HotPlugable="Yes/No", ID="", Revid="", Slot=slot, VendorID="",
                                                  subsystemID="")
                    element.append(new_subelement)
                    break
                with open('System_Details.txt', 'r+') as f:
                    sd_data = json.load(f)
                sd_data["<PROGRAM>_Platform_HW_Details"]["Board"]["Socket"]["IO"]["PCIe_SLOT"]["Slot"] = slot

                sd_data["<PROGRAM>_Platform_HW_Details"]["Board"]["Socket"]["IO"]["PCIe_SLOT"]["Width"] = width
                with open('System_Details.txt', 'w') as f:
                    json.dump(sd_data, f, indent=4)
                mytree.write("Hardware_And_Software_Configurations.xml")

def upi_fun():
    mytree = info.parse("Hardware_And_Software_Configurations.xml")
    root = mytree.getroot()
    for elem in root.findall("content"):
        for y in elem.findall('Platform_Board'):
            b = y.find("CPU")
            c = b.find("Socket")
            d = c.find("IO")
            for e in d.findall("UPI"):
                children = e.findall('PORT')
                for child in children:
                    e.remove(child)
    mytree.write('Hardware_And_Software_Configurations.xml')
    us.printTopology()
    topoStr = ""
    topoLinks = ""
    topoDraw = ""
    numConnectedSkts = 0
    numConnectedPorts = 0

    # first decide how many sockets
    socketList = utils.getSockets()
    topoStr += str(len(socketList)) + "S"


    connections = {}
    portsCounted = False

    # determine connections
    for skt in socketList:

        sktHasConnectedPort = False
        fpga = False

        if "fpga" not in skt.target_info["deviceName"]:
            connections[skt.target_info["socketNum"]] = {}
        else:
            fpga = True
            if len(socketList) < 3:
                connections[utils.getFpgaSocket(skt)] = {}
            elif len(socketList) < 5:
                connections[utils.getFpgaSocket(skt)] = {}

        ports = [x[1] for x in utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))]

        for port in ports:

            # make connection
            try:
                if "fpga" not in skt.target_info["deviceName"]:
                    peer = utils.getPeerDevice(skt.target_info["socketNum"], port)
                elif "fpga" in skt.target_info["deviceName"]:

                    peer = utils.getPeerDevice(utils.getFpgaSocket(skt), port)

            except:
                peer = []
            if peer == []: continue

            # connect in map and drawing
            sktHasConnectedPort = True
            if "fpga" not in skt.target_info["deviceName"] and "fpga" not in peer[0].target_info["deviceName"]:
                connections[skt.target_info["socketNum"]][port] = [peer[0].target_info["socketNum"], peer[1]]
            elif "fpga" in skt.target_info["deviceName"] and "fpga" not in peer[0].target_info["deviceName"]:

                connections[utils.getFpgaSocket(skt)][port] = [peer[0].target_info["socketNum"], peer[1]]
            elif "fpga" not in skt.target_info["deviceName"] and "fpga" in peer[0].target_info["deviceName"]:

                connections[skt.target_info["socketNum"]][port] = [utils.getFpgaSocket(peer[0]), peer[1]]

            numConnectedPorts += 1
            if "fpga" not in skt.target_info["deviceName"] and "fpga" not in peer[0].target_info["deviceName"]:
                topoLinks += "S%d_P%d <------> S%d_P%d\n" % (
                    skt.target_info["socketNum"], port, peer[0].target_info["socketNum"], peer[1])
                topoLinkDict1[skt.target_info["socketNum"]] = port
                topoLinkDict2[peer[0].target_info["socketNum"]] = peer[1]
                sList.append("S%d" % (skt.target_info["socketNum"]))
                pList.append(port)
                srList.append(peer[0].target_info["socketNum"])
                prList.append("%d" % (peer[1]))
                for element in root.iter('UPI'):
                    new_subelement = info.Element("PORT", Speed="", ID="", Socket_ID=str(skt.target_info["socketNum"]), Port_ID=str(port),
                                                  Connected_Socket_ID=str(peer[0].target_info["socketNum"]), Connected_Port_ID=str(int(peer[1])))
                    element.append(new_subelement)

            elif "fpga" in skt.target_info["deviceName"] and "fpga" not in peer[0].target_info["deviceName"]:

                topoLinks += "S%d_P%d <------> S%d_P%d\n" % (
                    utils.getFpgaSocket(skt), port, peer[0].target_info["socketNum"], peer[1])
                topoLinkDict1[utils.getFpgaSocket(skt)] = port
                topoLinkDict2[peer[0].target_info["socketNum"]] = peer[1]
                sList.append("S%d" % (utils.getFpgaSocket(skt)))
                pList.append(port)
                srList.append(peer[0].target_info["socketNum"])
                prList.append(peer[1])
                for element in root.iter('UPI'):
                    new_subelement = info.Element("PORT", Speed="", ID="", Socket_ID=str(utils.getFpgaSocket(skt)), Port_ID=str(port),
                                                  Connected_Socket_ID=str(peer[0].target_info["socketNum"]), Connected_Port_ID=str(int(peer[1])))
                    element.append(new_subelement)
            elif "fpga" not in skt.target_info["deviceName"] and "fpga" in peer[0].target_info["deviceName"]:
                topoLinks += "S%d_P%d <------> S%d_P%d\n" % (
                    skt.target_info["socketNum"], port, utils.getFpgaSocket(peer[0]), peer[1])
                topoLinkDict1[skt.target_info["socketNum"]] = port
                topoLinkDict2[utils.getFpgaSocket(peer[0])] = peer[1]
                sList.append(skt.target_info["socketNum"])
                pList.append(port)
                srList.append(utils.getFpgaSocket(peer[0]))
                prList.append(peer[1])
                for element in root.iter('UPI'):
                    new_subelement = info.Element("PORT", Speed="", ID="", Socket_ID=str(skt.target_info["socketNum"]), Port_ID=str(port),
                                                  Connected_Socket_ID=str(utils.getFpgaSocket(peer[0])), Connected_Port_ID=str(int(peer[1])))
                    element.append(new_subelement)




        if sktHasConnectedPort: numConnectedSkts += 1

        # don't draw if greater than 4S

        if "fpga" not in skt.target_info["deviceName"] and skt.target_info["socketNum"] > 3:
            draw = False

        # remove sockets that aren't connected to anything
    keysToRemove = []
    for socket in connections:
        if connections[socket] == {}:
            keysToRemove.append(socket)
    while len(keysToRemove) > 0:
        connections.pop(keysToRemove.pop())

    # finish string
    if numConnectedSkts == 0: numConnectedSkts += 1
    topoStr = "%dS%dQ" % (numConnectedSkts, numConnectedPorts / 2)
    print(topoStr)
    print(topoLinks)
    print(topoLinkDict1)
    print(topoLinkDict2)
    print("left socket list=", sList)
    print("left port list=", pList)
    print("Right socket list=", srList)
    print("Right port list=", prList)


    for upi_layout_design in root.iter('content'):
        upi_layout_design.attrib["UPI_Layout_Design"] = str(topoStr)
        break

    mytree.write("Hardware_And_Software_Configurations.xml")
    print("CPU Info End")

def BIOS_version_fun():
    print("os name:",platform.system())
    cmd = ''
    if platform.system() == 'Windows':
        cmd = "wmic bios get smbiosbiosversion"
    elif platform.system() == 'Linux':
        cmd = "dmidecode | grep -i -m 1 Version"
    # This is our shell command, executed by Popen.

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    for i in range(2):
        line = p.stdout.readline()
        if i == 0:
            continue
        if not line:
            break
        print("BIOS version:",line.decode('utf-8').strip())
        with open('System_Details.txt', 'r+') as f:
            data = json.load(f)
        data["<PROGRAM>_Platform_SW_Details"]["Board"]["Silicon_Firmware_Version"]["BIOS_Version"] = line.decode('utf-8').strip()

        with open('System_Details.txt', 'w') as f:
            json.dump(data, f, indent=4)

def OS_KERNEl_VERSION_fun():

    mytree = info.parse("Hardware_And_Software_Configurations.xml")
    root = mytree.getroot()

    for os_name in root.iter('os'):
        os_name.attrib["name"] = str(platform.system())
        if platform.system() == 'Windows':
            os_name.attrib['version'] = platform.release()
        elif platform.system() == 'Linux':
            os_name.attrib['version'] = subprocess.Popen("lsb_release -d", stdout=subprocess.PIPE, shell=True).communicate()[0].decode('utf-8').strip()
    for version in root.iter('kernel'):
        if platform.system() == 'Windows':
            version.attrib['version'] = str(platform.version())
        elif platform.system() == 'Linux':
            version.attrib['version'] = subprocess.Popen("uname -r", stdout=subprocess.PIPE, shell=True).communicate()[0].decode('utf-8').strip()
    mytree.write('Hardware_And_Software_Configurations.xml')

def main():
    qdf_no_of_sockets()
    dimm_config_fun()
    cpu_pcie_fun()
    upi_fun()
    OS_KERNEl_VERSION_fun()
    BIOS_version_fun()

if __name__ == "__main__":
    main()
