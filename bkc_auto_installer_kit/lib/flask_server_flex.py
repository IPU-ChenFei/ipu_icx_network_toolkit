#jan-01-2021 created skelton
import re
import os
import sys
import time
import json
import ctypes
import socket
import ntpath
import ctypes
import zipfile
import fileinput
import requests
import datetime
import paramiko
import threading
import subprocess
import xml.etree.ElementTree as ET
session = requests.session()
requests.urllib3.disable_warnings()
from subprocess import Popen,PIPE,STDOUT
flask_invt = r"C:\flask_inventory.txt"
flask_location = os.getcwd()
service_ip = socket.gethostbyname(socket.gethostname())
#Initializing Library Requiremnet for Flask
try:
    from flask import Flask, request, abort, jsonify, send_from_directory
except:
    print("FLASK service not installed")
    try:
        if sys.platform == 'win32':
            try:
                a=subprocess.check_output("c:\python36\python.exe -m pip install --upgrade pip --proxy http://proxy-dmz.intel.com:912", shell=True)
            except:
                subprocess.check_output(
                    "C:\Python27\python.exe -m pip install --upgrade pip --proxy=\"http://proxy-dmz.intel.com:912\"",
                    shell=True)
            a = subprocess.check_output("python -m pip install flask --proxy=\"http://proxy-dmz.intel.com:912\"", shell=True)
            print("INstallation Done")
            from flask import Flask, jsonify, request
        else:
            subprocess.check_output(
                "export http_proxy=http://proxy-chain.intel.com:911;export https_proxy=http://proxy-dmz.intel.com:912;sudo pip install flask",
                shell=True)
    except:
        print("Flask Missing ")

try:
    import socket
    hostname = socket.gethostname()
    ipadd = socket.gethostbyname(hostname)
except:
    ipadd = "Hostmachine_ipaddress"
    print("socket Library Not Found")
    pass

try:
    import configparser
    config = configparser.ConfigParser()
    config.read(flask_invt)
except:
    print("configparser Libraries not installed")
    try:
        if sys.platform == 'win32':
            try:
                a = subprocess.check_output(
                    "python -m pip install configparser --proxy=\"http://proxy-dmz.intel.com:912\"", shell=True)
            except:
                subprocess.check_output(
                    "C:\Python27\python.exe -m pip install --upgrade pip --proxy=\"http://proxy-dmz.intel.com:912\"",
                    shell=True)
                a = subprocess.check_output(
                    "python -m pip install configparser --proxy=\"http://proxy-dmz.intel.com:912\"", shell=True)
                import configparser
                config = configparser.ConfigParser()
                config.read(flask_invt)
        else:
            print("linux not yet coded")
    except:
        print(
            "configparser library missing install it manually pip install configparser --proxy=http://proxy-dmz.intel.com:912")

#Initializing Library Requirement for pdu
try:
    from raritan import rpc
    from raritan.rpc import pdumodel
except:
    print("PDU Libraries not installed")
    try:
        if sys.platform == 'win32':
            try:
                a=subprocess.check_output("python -m pip install cloudshell-pdu-raritan==1.0.55 --proxy=http://proxy-dmz.intel.com:912",shell=True)
            except:
                subprocess.check_output(
                    "C:\Python27\python.exe -m pip install --upgrade pip --proxy=http://proxy-dmz.intel.com:912",
                    shell=True)
                a = subprocess.check_output(
                    "python -m pip install cloudshell-pdu-raritan==1.0.55 --proxy=http://proxy-dmz.intel.com:912", shell=True)
                print("INstallation Done")
                from raritan import rpc
                from raritan.rpc import pdumodel
        else:
            print("linux not yet coded")
    except:
        print("PDU control library missing install it manually pip install cloudshell-pdu-raritan==1.0.55 --proxy=http://proxy-dmz.intel.com:912")

#info passing hostmachine details
try:
    import socket
    hostname = socket.gethostname()
    host_ipadd = socket.gethostbyname(hostname)
except:
    ipadd = "rpi_ipaddress"
    print("socket Library Not Found")
    pass

try:
    import zipfile
except:
    if sys.platform == 'win32':
        try:
            a = subprocess.check_output(
                "python -m pip install zipfile --proxy=http://proxy-dmz.intel.com:912", shell=True)
        except:
            subprocess.check_output(
                "C:\Python27\python.exe -m pip install --upgrade pip --proxy=http://proxy-dmz.intel.com:912",
                shell=True)
            a = subprocess.check_output(
                "python -m pip install zipfile --proxy=http://proxy-dmz.intel.com:912", shell=True)
            import zipfile
    else:
        print("linux not yet coded")

UPLOAD_DIRECTORY = "C:\\flask_firmware\\"
BANINO_DIRECTORY ="C:\\banino\code\\"
try:
    if not os.path.exists(UPLOAD_DIRECTORY):
        subprocess.check_output("mkdir C:\\flask_firmware\\",shell=True)
        time.sleep(1)
        subprocess.check_output("mkdir C:\\flask_firmware\\bmc", shell=True)
        time.sleep(1)
        subprocess.check_output("mkdir C:\\flask_firmware\\ifwi", shell=True)
        subprocess.check_output("mkdir C:\\flask_firmware\\cpld", shell=True)
except:
    print("This is a Not a Windows Machine")
    pass

post_code = "C:\\postcode\\rfat_modified.tcl"
try:
    if not os.path.exists(post_code):
        subprocess.check_output("mkdir C:\\postcode\\",shell=True)
        time.sleep(1)
        subprocess.check_output("curl -X GET bdcspiec010.gar.corp.intel.com/files/postcode.zip --output C:\\cpld_postcode.zip",shell=True)
        with zipfile.ZipFile("C:\\cpld_postcode.zip", 'r') as zip_ref:
            zip_ref.extractall("C:\\")
            zipfile.close()
except:
    print("This is a Not a Windows Machine")
    pass

try:
    if not os.path.exists(BANINO_DIRECTORY):
        print("Banino Doesn't exists")
        subprocess.check_output("curl -X GET bdcspiec010.gar.corp.intel.com/files/banino.zip --output C:\\banino.zip",shell=True)
        with zipfile.ZipFile("C:\\banino.zip", 'r') as zip_ref:
            zip_ref.extractall("C:\\")
            zipfile.close()
except Exception as ex:
    print("error",ex)
    pass

def pdu_configure(outlet,ip,usr,pwd):
    try:
        f=open(flask_invt,'w')
        print("aaaaaaaaa")
        f.write("[pdu]\noutlet="+str(outlet)+"\nip="+str(ip)+"\nusername="+str(usr)+"\npassword="+str(pwd)+"")
        f.close()
        return True
    except Exception as ex:
        print (ex)
        return False

app = Flask(__name__)
class PduDriver():
    def __init__(self,pusr=None,ppwd=None,pip=None,poutlet=None):
        if (sys.platform != 'win32'):
            tree = ET.parse('/home/Automation/system_configuration.xml')
        else:
            tree = ET.parse('C:\Automation\system_configuration.xml')
        root = tree.getroot()

        try:
            for item in root.iter('ac'):
                ip = item.find('./driver/pdu/ip')
                username = item.find('./driver/pdu/username')
                password = item.find('./driver/pdu/password')
                outlet = item.find('./driver/pdu/outlets/outlet')
        except Exception as ex:
            print("Mismatched Syntax in system_configuratio.xml Properly Check the syntax")


        # try:
        #     ret = subprocess.check_output("ping -n 3 " + ip.text, shell=True)
        #     if ("0% loss" in str(ret)):
        #         print('\nPDU is alive')
        # except Exception as ex:
        #     print("\nPDU is in Turned OFF State or Mentioned Raritan IP is not Correct Ping Failed to PDU {0}".format(
        #         ip.text))
        #     sys.exit(0)
        #

        if pusr:
            self.username = pusr
        else:
            self.username = username.text
        if ppwd:
            self.password = ppwd
        else:
            self.password = password.text
        if poutlet:
            self.outlets =poutlet
        else:
            self.outlets = outlet.text
        self.port = 22
        if pip:
            self.ip = pip
        else:
            self.ip = ip.text
        print("\nChecking the Credentials of PDU ip {0} \"{1} {2}\" And Outlet \"{3}\" Status \n".format(self.ip,self.username,self.password,self.outlets))
        self.invoke_timeout = 5
        self.powerstate_timeout = 20
        self.cmd_on = ["power outlets {} on /y \n".format(outlet.text)]
        self.cmd_off = ["power outlets {} off /y \n".format(outlet.text)]
        self.cmd_show = ["show outlets {} \n".format(self.outlets)]
        self.recv_data = b''
        #print("Extracted PDU INFORMATION  ===> ", ip.text, username.text, password.text, outlet.text)

    def get_recv_data(self, ssh):
        self.recv_data = b''
        self.recv_data = ssh.recv(1024)

    def wait_for_invoke(self, ssh):
        nowtime = datetime.datetime.now()
        while (datetime.datetime.now() - nowtime).seconds < int(self.invoke_timeout):
            t = threading.Thread(target=self.get_recv_data, args=[ssh])
            t.setDaemon(True)
            t.start()
            t.join(3)
            if b'#' in self.recv_data or b'>' in self.recv_data:
                return
        time.sleep(int(self.invoke_timeout))

    def _execute(self, cmd_list):
        ssh = None
        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=self.ip, port=self.port,
                           username=self.username, password=self.password)
            ssh = client.get_transport().open_session()
            ssh.get_pty()
            ssh.invoke_shell()
            self.wait_for_invoke(ssh)
            for cmd in cmd_list:
                num = 0
                while num < 3:
                    ssh.sendall(cmd)
                    time.sleep(0.5)
                    num += 1
        except Exception as ex:
            print("[%s] %s target failed, the reason is %s"
                  % (datetime.datetime.now(), self.ip, str(ex)))
            raise ex
        finally:
            ssh.close()
            client.close()

    def _check_dict_value(self, dict_data):
        data = set(dict_data.values())
        if len(data) > 1:
            return False
        elif len(data) == 1 and list(data)[0]:
            return True
        elif len(data) == 1 and not list(data)[0]:
            return False
        else:
            return None

    def ac_power_on(self, timeout=None):
        self._execute(self.cmd_on)
        return self.get_ac_power_state(timeout)

    def ac_power_off(self, timeout=None):
        self._execute(self.cmd_off)
        return self.get_ac_power_state(timeout)

    def get_ac_power_state(self, timeout):
        ssh = None
        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=self.ip, port=self.port, username=self.username,
                           password=self.password, timeout=timeout)
            ssh = client.get_transport().open_session()
            ssh.get_pty()
            ssh.invoke_shell()
            self.wait_for_invoke(ssh)
            state_list = {}
            for cmd in self.cmd_show:
                num = 0
                while num < 3:
                    ssh.sendall(cmd)
                    time.sleep(0.5)
                    ret_data = ssh.recv(1024).decode("utf-8")
                    if 'On' in ret_data:
                        state_list[cmd] = True
                    elif 'Off' in ret_data:
                        state_list[cmd] = False
                    num += 1
            return self._check_dict_value(state_list)
        except Exception as ex:
            print("[%s] %s target failed, the reason is %s"
                  % (datetime.datetime.now(), self.ip, str(ex)))
            raise ex
        finally:
            ssh.close()
            client.close()


def aconfromacoff(pusr=None,ppwd=None,pip=None,poutlet=None):
    try:
        pdu = PduDriver(pusr,ppwd,pip,poutlet)
        a=pdu.ac_power_on(timeout=None)
        print(a)
        if(a==True):
            if (pdu.get_ac_power_state(5) == True):
                return True
        else:
            return False
    except Exception as ex:
        print(ex)
        return "Error"

def acofffromacon(pusr=None,ppwd=None,pip=None,poutlet=None,timeouton=None):
    try:
        pdu = PduDriver(pusr,ppwd,pip,poutlet)
        a=pdu.ac_power_off(timeout=None)
        print(a)
        if( a == False):
            if (pdu.get_ac_power_state(5) == False):
                return True
        else:
            return False
    except Exception as ex:
        print(ex)
        return "Error"
#Banino==================================================================================================================================
class BaninoDriver():
    def __init__(self):
        self._power_cmd = r"C:\banino\code\Banino_SXState"
        self.chip_write_verification_ifwi = False
        self.chip_write_verification_bmc = False
        self.ladybird = ctypes.cdll.LoadLibrary(r"C:\banino\code\Banino_SXState\x64\ladybird.dll")

    def banino_sx_sft_prepare(self):
        if not os.path.isfile("c:\\banino"):
            try:
                subprocess.check_output("rmdir /s /q c:\\banino", shell=True)
            except:
                pass
            try:
                subprocess.check_output("mkdir c:\\banino", shell=True)
            except:
                pass
            subprocess.check_output(
                "curl --silent -u sys_degsi1:czhfi20$ -X GET https://ubit-artifactory-ba.intel.com/artifactory/dcg-dea-srvplat-local/Automation_Tools/CI_Tools/banino.zip --output C:\\banino\\banino.zip",
                shell=True)
            time.sleep(5)
            with zipfile.ZipFile("c:\\banino\\banino.zip", 'r') as zip_ref:
                zip_ref.extractall("c:\\banino\\")
            print("Download LadyBird flash, Banino Application, SX code ------------------------------- [OK]")

    def banino_serial_setup(self):
        ladybird = ctypes.cdll.LoadLibrary(r"C:\banino\code\Banino_SXState\x64\ladybird.dll")
        buffer = (ctypes.c_int * 32)()
        lbBuffer = (ctypes.c_byte * 512)()
        ladybirddDevices = ladybird.findDevices(512, ctypes.c_void_p(ctypes.addressof(lbBuffer)))
        for i in range(2):
            s = str(hex(
                (lbBuffer[i * 12 + 7] << 24) + (lbBuffer[i * 12 + 6] << 16) + (lbBuffer[i * 12 + 5] << 8) + lbBuffer[
                    i * 12 + 4]))
        res = int(s, 16)
        lb_serial = (str(res))
        # print(lb_serial)
        file_name = r'C:\banino\code\Banino_SXState\config.xml'
        with fileinput.FileInput(file_name, inplace=True, backup='.bak') as file:
            for line in file:
                print(line.replace("117972993", lb_serial), end='')
            file.close()
        print(
            "\n Ladybird Serial is identified and Changed in the config.xml --------------------------------------- [OK]")

    def conect_relay(self, relay_num, relay_port):
        try:
            relay_state = self.ladybird.GetRelayState(1, relay_num, relay_port)
            print("Relay_status {0}".format(relay_state))
            if relay_state == 1:
                print("Relay Connected")
                return True
            else:
                self.ladybird.SetRelayState(1, relay_num, relay_port, 1)
                time.sleep(1)
                relay_state = self.ladybird.GetRelayState(1, relay_num, relay_port)
                if relay_state == 1:
                    print("Connecting Relay Successful")
                    return True
                else:
                    print("Connecting Relay Fail")
                    raise
        except Exception as ex:
            print("Relay Connect Error {0}".format(ex))
            raise

    def conect_relay_custom(self, relay_port):
        """
        SetRelayState(unsigned int baninoNumber, unsigned int relayGroup, unsigned int relayNumber, unsigned int relayState)
        relayGroup 2
        relayNumber 1 - 7
        """
        try:
            relay_state = self.ladybird.GetRelayState(1, 2, relay_port)
            print("Relay_status {0}".format(relay_state))
            if (relay_state == 1):
                print("Relay Connected")
                return True
            else:
                self.ladybird.SetRelayState(1, 2, relay_port, 1)
                time.sleep(1)
                relay_state = self.ladybird.GetRelayState(1, 2, relay_port)
                if (relay_state == 1):
                    print("Connecting Custom Relay Number {0} Successful".format(relay_port))
                    return True
                else:
                    print("Connecting Custom Relay Number {0} Failed".format(relay_port))
                    raise
        except Exception as ex:
            print("Custom Relay Connect Error {0}".format(ex))
            raise

    def disconnect_relay_custom(self, relay_port):
        """
        SetRelayState(unsigned int baninoNumber, unsigned int relayGroup, unsigned int relayNumber, unsigned int relayState)
        relayGroup 2
        relayNumber 1 - 7
        """
        try:
            relay_state = self.ladybird.GetRelayState(1, 2, relay_port)
            print("Relay_status {0}".format(relay_state))
            if (relay_state == 0):
                print("Relay Disconnected")
                return True
            else:
                self.ladybird.SetRelayState(1, 2, relay_port, 0)
                time.sleep(1)
                relay_state = self.ladybird.GetRelayState(1, 2, relay_port)
                if (relay_state == 0):
                    print("Disconnecting Custom Relay Number {0} Successful".format(relay_port))
                    return True
                else:
                    print("Disconnecting Custom Relay Number {0} Failed".format(relay_port))
                    raise
        except Exception as ex:
            print("Custom Relay Disconnect Error {0}".format(ex))
            raise

    def disconnect_relay(self, relay_num, relay_port):
        try:
            relay_state = self.ladybird.GetRelayState(1, relay_num, relay_port)
            if (relay_state == 0):
                print("Relay Disconnected")
                return True
            else:
                self.ladybird.SetRelayState(1, relay_num, relay_port, 0)
                time.sleep(1)
                relay_state = self.ladybird.GetRelayState(1, relay_num, relay_port)
                if relay_state == 0:
                    print("Disconnecting Relay Successful")
                    return True
                else:
                    print("Disconnecting Relay Fail")
                    raise
        except Exception as ex:
            print("Relay Disconnect Error {0}".format(ex))
            raise

    def connect_usb_to_sut(self, timeout=None):
        """
        Connect shared USB drive to the system under test.
        :exception Banino_Error: Banino Library Throws Error.
        """
        try:
            print("start to switch usb disk to sut")
            lbHandle = self.ladybird.OpenByBaninoNumber(1, 2)
            self.ladybird.SetGpioDirection(lbHandle, 1, 0x6000000, 0x6000000)
            self.ladybird.SetGpioState(lbHandle, 1, 0x4000000, 0x00)
            time.sleep(2)
            print("Short Relay_1_4")
            self.ladybird.SetGpioState(lbHandle, 1, 0x2000000, 0x00)
            self.ladybird.SetGpioState(lbHandle, 1, 0x4000000, 0x4000000)
            time.sleep(3)
            # self.self.ladybird.close(lbHandle)
            return True
        except Exception as ex:
            print("Switch_Flash_Disk Usb_To_Sut_Failure {0}".format(ex))
            raise

    def connect_usb_to_host(self, timeout=None):
        """
        Connect shared USB drive to the lab host.
        :exception Banino_Error: Banino Library Throws Error.
        """
        try:
            print("start to switch usb disk to host")
            lbHandle = self.ladybird.OpenByBaninoNumber(1, 2)
            self.ladybird.SetGpioDirection(lbHandle, 1, 0x6000000, 0x6000000)
            self.ladybird.SetGpioState(lbHandle, 1, 0x4000000, 0x00)
            time.sleep(2)
            print("Short Relay_1_4")
            self.ladybird.SetGpioState(lbHandle, 1, 0x2000000, 0x2000000)
            self.ladybird.SetGpioState(lbHandle, 1, 0x4000000, 0x4000000)
            time.sleep(3)
            # self.self.ladybird.close(lbHandle)
            return True
        except Exception as ex:
            print("Switch_Flash_Disk Usb_To_Host_Failure {0}".format(ex))
            raise

    def disconnect_usb(self, timeout=None):
        """
        Dis-connect USB drive From SUT and Host.
        :exception Banino_Error: Banino Library Throws Error.
        """
        try:
            print("start to Disconnect switch usb from Host and SUT")
            lbHandle = self.ladybird.OpenByBaninoNumber(1, 2)
            self.ladybird.SetGpioDirection(lbHandle, 1, 0x6000000, 0x6000000)
            self.ladybird.SetGpioState(lbHandle, 1, 0x4000000, 0x00)
            time.sleep(2)
            print("Short Relay_1_4")
            self.ladybird.SetGpioState(lbHandle, 1, 0x00, 0x00)
            time.sleep(3)
            # self.self.ladybird.close(lbHandle)
            return True
        except Exception as ex:
            print("Switch_Flash_Disk Usb_To_Host_Failure {0}".format(ex))
            raise

    def set_clear_cmos(self, timeout=None):
        """
        Clears the current configured data with factory setting
        :exception Banino_Error: Banino Library Throws Error.
        """
        try:
            if (self.conect_relay(1, 3) != True):
                print("Short Clear COMS Pin Failed")
                raise
            else:
                print("Short Clear COMS Pin pass")
            time.sleep(5)
            if (self.disconnect_relay(1, 3) != True):
                print("Open Clear COMS pin failed")
                raise
            else:
                print("Open Clear COMS Jumper Connected")
            return True
        except Exception as ex:
            print("Clear CMOS Failed To Happen {0}".format(ex))
            raise

    def dc_power_on(self, timeout=None):
        """
        :send DC_POWER_ON command to Gpio Turn The Relay to go High for Short Duration which physically interact with Front Panel Gpio.
        :return: True or None
        :exception Banino_Error: Banino Library Throws Error.
        """
        try:
            num = 1
            port = 1
            self.ladybird.SetRelayState(1, num, port, 1)
            relay_state = self.ladybird.GetRelayState(1, num, port)
            print("Short switch power button is {0}".format(relay_state))
            time.sleep(1)
            self.ladybird.SetRelayState(1, num, port, 0)
            time.sleep(1)
            relay_state = self.ladybird.GetRelayState(1, num, port)
            print("short switch power button is {0}".format(relay_state))
            return True
        except Exception as ex:
            print("Dc-Power ON via Banino Failed To Happen {0}".format(ex))
            raise

    def dc_power_off(self, timeout=None):
        """
        :send DC_POWER_OFF command to Gpio To Turn The Relay to go High which physically interact with Front Panel Gpio.
        :return: True or None
        :exception Banino_Error: Banino Library Throws Error.
        """
        try:
            num = 1
            port = 1
            self.ladybird.SetRelayState(1, num, port, 1)
            relay_state = self.ladybird.GetRelayState(1, num, port)
            print("short switch power off button is {}".format(relay_state))
            time.sleep(5)
            self.ladybird.SetRelayState(1, num, port, 0)
            time.sleep(1)
            relay_state = self.ladybird.GetRelayState(1, num, port)
            print("short switch power button is {}".format(relay_state))
            return True
        except Exception as ex:
            print("Dc-Power OFF via Banino Failed To Happen {0}".format(ex))
            raise

    def get_dc_power_state(self):
        """
        This API shields platform and control box difference.
        according to the platform setting in Config module,
        which signals' voltage need to be got are different support.
        Power states dependent on platform power schematic.
        :return:
        On      -   True
        Off     -   NONE
       :exception Banino_Error: Banino Library Throws Error.
        """
        output = os.popen(str("cd ") + self._power_cmd + str("& SxState.exe")).read()
        power_status = output.strip()
        print(power_status)
        if (power_status == "S0"):
            print("S0 State Detected")
            return True
        elif (power_status == "S5"):
            print("S5 State Detected")

    def get_sx_power_state(self):
        """
        :return Actuall state of the platform, combines function of get dc power and ac power
        :exception Banino_Error: Banino Library Throws Error.
        """
        try:
            output = os.popen(str("cd ") + self._power_cmd + str("& SxState.exe")).read()
            power_status = output.strip()
            print(power_status)
            return power_status
        except Exception as ex:
            print("Error Occured During Banino State Detection {0}".format(ex))
            raise

    def dc_power_reset(self):
        """
        :send DC_Reset command to Gpio To Turn The Relay to go High which physically interact with Front Panel Gpio.
        :return: True or None
        :exception Banino_Error: Banino Library Throws Error.
        """
        try:
            num = 1
            port = 2
            self.ladybird.SetRelayState(1, num, port, 1)
            relay_state = self.ladybird.GetRelayState(1, num, port)
            print("Short switch reset button is {0}".format(relay_state))
            time.sleep(2)
            self.ladybird.SetRelayState(1, num, port, 0)
            time.sleep(2)
            relay_state = self.ladybird.GetRelayState(1, num, port)
            print("short switch power button is {0}".format(relay_state))
            return True
        except Exception as ex:
            print("Dc-Power ON via Banino Failed To Happen {0}".format(ex))
            raise

    def read_s3_pin(self):
        # type: () -> bool
        """
        Read the state of the S3 pin
        :return: True if S3 pin is indicating SUT is in S3, None otherwise.
        """
        output = os.popen(str("cd ") + self._power_cmd + str("& SxState.exe")).read()
        power_status = output.strip()
        print(power_status)
        if (power_status == "S3"):
            print("S3 State Detected")
            return True
        else:
            print("S3 State is Not Detected")

    def read_s4_pin(self):
        # type: () -> bool
        """
        Read the state of the S4 pin
        :return: True if S4 pin is indicating SUT is in S4, None otherwise.
        """
        output = os.popen(str("cd ") + self._power_cmd + str("& SxState.exe")).read()
        power_status = output.strip()
        print(power_status)
        if (power_status == "S4"):
            print("Get S4 State Success")
            return True
        else:
            print("S4 State is Not Detected")

    def get_ac_power_state(self):

        output = os.popen(str("cd ") + self._power_cmd + str("& SxState.exe")).read()
        power_status = output.strip()
        print(power_status)
        if (power_status == "G3"):
            print("G3 State Detected")
        else:
            print("G3 State is Not Detected")
            return True

    def program_jumper(self, state, gpio_pin_number, timeout=""):
        """
        program_jumper controls the gpio pins of Banino
        :param timeout:
        :param gpio_pin_number:
        :param state=set or unset this makes the gpio pin high or low to communicate with the relay
        gpio_pin_number which pins that needs to be programmed
        :return: True
        :exception Banino_Error: Banino Gpio Library Throws Error.
        """
        try:
            if (str(state) == "set"):
                if (self.conect_relay_custom(gpio_pin_number) == True):
                    return True
                else:
                    return False
            elif (str(state) == "unset"):
                if (self.disconnect_relay_custom(gpio_pin_number) == True):
                    return True
                else:
                    return False
        except Exception as ex:
            print("Failed to " + str(state) + " Jumper for Custom Relay Group 2 Channel {0}{1}".format(ex,
                                                                                                                 gpio_pin_number))
            raise

    def chip_flash(self, path=None, image_name=None):
        """
        This function takes care of identifying and erasing and writing a new image from a location.
        it takes the ifwi image or the bmc image based on the modification/creation time it is going to take the latest time by default of the image.
        Image for flashing will be taken from the "+str(root)+"/firmware/ folder name is firmware from this the image will be taken.
        path in this are fixed path even though folders don't exists it will created it,2nd time run it will copy them
        """
        if self.conect_relay_custom(1) != True:
            print("connect VCC relay fail, please check the hard connection")
            return False
        if self.conect_relay(1, 5) != True:
            print("connect VCC relay fail, please check the hard connection")
            return False
        try:
            print("Starting to do Flash IFWI with mentioned Version {0}".format(image_name))
            lbHandle = self.ladybird.OpenByBaninoNumber(1, 3)
            print("{0}".format(lbHandle))
            flashDevice = 0
            flashStartAddress = 0
            image_namepath = path + image_name
            filePath = ctypes.create_string_buffer(bytes(image_namepath, 'utf-8'))
            writeSize = os.path.getsize(filePath.value)
            print("{0} object, size {1}".format(filePath, writeSize))
            fileOffset = 0
            result = 1
            result = self.ladybird.FlashReady(lbHandle, ctypes.c_char(flashDevice))
            if (result != 0):
                print("FlashReady:{}, IFWI SPI Chip not Detected".format(result))
                return False
            else:
                print("FlashReady:{}, IFWI SPI Chip have Detected".format(result))

            print("Start to Erase SPI flash Chip")
            result = self.ladybird.FlashErase(lbHandle, ctypes.c_char(flashDevice))
            if (result != 0):
                print("FlashErase:{}, Erase IFWI SPI chip Erase fail".format(result))
                return False
            else:
                print("FlashErase:{}, Erase IFWI chip passed ".format(result))
            print("Start to Write IFWI file to flash")
            result = self.ladybird.FlashWriteFile(lbHandle, ctypes.c_char(flashDevice), flashStartAddress, writeSize,
                                                  filePath, fileOffset)
            if (result != 0):
                print("FlashWriteFile:{}, Burning IFWI SPI chip fail".format(result))
                return False
            else:
                print("FlashWriteFile:{}, Burning IFWI SPI chip pass".format(result))
            if (self.chip_write_verification_ifwi == False):
                print("Skipped to Verify SPI IFWI Chip")
            else:
                print("Start to Verify write file")
                result = self.ladybird.FlashVerifyFile(lbHandle, ctypes.c_char(flashDevice), flashStartAddress,
                                                       writeSize, filePath, fileOffset)
                if (result != 0):
                    print("FlashVerifyFile:{}, Verify IFWI SPI chip fail".format(result))
                    return False
                else:
                    print("FlashVerifyFile:{}, Verify IFWI SPI chip pass".format(result))
            print("Flash IFWI successful")
            self.ladybird.Close(lbHandle)
            return True
        except Exception as ex:
            print("Error --> {0}".format(ex))
            return False
        finally:
            if (self.disconnect_relay_custom(1) != True):
                print("disconnect VCC relay fail")
                return False
            if (self.disconnect_relay(1, 5) != True):
                print("disconnect VCC relay fail")
                return False

    def chip_flash_bmc(self, path=None, image_name=None):
        """
        This function takes care of identifying and erasing and writing a new image from a location.
        it takes the ifwi image or the bmc image based on the modification/creation time it is going to take the latest time by default of the image.
        Image for flashing will be taken from the "+str(root)+"/firmware/ folder name is firmware from this the image will be taken.
        path in this are fixed path even though folders don't exists it will created it,2nd time run it will copy them
        """
        if (self.conect_relay_custom(1) != True):
            print("connect VCC relay fail, please check the hard connection")
            return False
        if self.conect_relay(1, 5) != True:
            print("connect VCC relay fail, please check the hard connection")
            return False
        try:
            print("Starting to do Flash BMC with mentioned Version {0}".format(image_name))
            lbHandle = self.ladybird.OpenByBaninoNumber(1, 1)
            flashDevice = 0
            flashStartAddress = 0
            image_namepath = path + image_name
            filePath=ctypes.create_string_buffer(bytes(image_namepath,'utf-8'))
            writeSize = os.path.getsize(filePath.value)
            print("{0} object, size {1}".format(filePath, writeSize))
            fileOffset = 0
            result = 1
            result = self.ladybird.FlashReady(lbHandle, ctypes.c_char(flashDevice))
            if(result != 0):
                print("FlashReady:{}, BMC Chip not Detectected".format(result))
                return False
            else:
                print("FlashReady:{}, BMC Chip have Detected".format(result))
            print("Start to Erase flash")
            result = self.ladybird.FlashErase(lbHandle, ctypes.c_char(flashDevice))
            if(result != 0):
                print("FlashErase:{}, Erase bmc chip Erase fail".format(result))
                return False
            else:
                print("FlashErase:{}, Erase bmc chip passed ".format(result))
            print("Start to Write BMC file to flash")
            result = self.ladybird.FlashWriteFile(lbHandle, ctypes.c_char(flashDevice), flashStartAddress, writeSize, filePath, fileOffset)
            if(result != 0):
                print("FlashWriteFile:{}, Burning bmc chip fail".format(result))
                return False
            else:
                print("FlashWriteFile:{}, Burning bmc chip pass".format(result))
            if (self.chip_write_verification_bmc == False):
                print("Skipped to Verify SPI BMC Chip")
            else:
                print("Start to Veritfy write file")
                result = self.ladybird.FlashVerifyFile(lbHandle, ctypes.c_char(flashDevice), flashStartAddress, writeSize,
                                                       filePath, fileOffset)
                if (result != 0):
                    print("FlashVerifyFile:{}, Verify BMC chip fail".format(result))
                    return False
                else:
                    print("FlashVerifyFile:{}, Verify BMC chip pass".format(result))
            print("Flash BMC successfully verified")
            self.ladybird.Close(lbHandle)
            return True
        except Exception as ex:
            print("Error --> {0}".format(ex))
            return False
        finally:
            if (self.disconnect_relay_custom(1) != True):
                print("disconnect VCC relay fail")
                return False
            if (self.disconnect_relay(1, 5) != True):
                print("disconnect VCC relay fail")
                return False

class redfish():
    def __init__(self,atf_iso=None,usr=None,pwd=None,ip=None):
        if (sys.platform != 'win32'):
            tree = ET.parse('/home/Automation/system_configuration.xml')
        else:
            tree = ET.parse('C:\Automation\system_configuration.xml')
        root = tree.getroot()
        try:
            for item in root.findall('./suts/sut/providers'):
                type = item.find('./physical_control/driver/redfish/bmc_type')
                username = item.find('./physical_control/driver/redfish/username')
                password = item.find('./physical_control/driver/redfish/password')
                ip = item.find('./physical_control/driver/redfish/ip')
            #print("Extracted INFORMATION  ===> ", ip.text, username.text, password.text, type.text)
        except Exception as ex:
            pass
        if usr:
            rusr=usr
        else:
            rusr=username.text
            if not rusr:
                rusr = "debuguser"
        if pwd:
            rpwd = pwd
        else:
            rpwd =password.text
            if not rpwd:
                rpwd = "0penBmc1"
        if ip:
            rip= ip
        else:
            rip =  ip.text
        self.iso_image_url_atf = atf_iso
        self.bmc_login_username = rusr
        self.bmc_login_password = rpwd
        self.bmc_ip = rip
        self.atf_username = "sys_degsi1"
        self.atf_password = "czhfi20$"


    # MOUNTING IMAGE From ATF:
    def mount_image(self):
        url = (
            r'https://{0}/redfish/v1/Managers/bmc/VirtualMedia/Slot_3/Actions/VirtualMedia.InsertMedia'.format(self.bmc_ip))
        auth1 = (self.bmc_login_username, self.bmc_login_password)
        data = {'Image': self.iso_image_url_atf, 'TransferProtocolType': 'HTTPS', 'UserName': self.atf_username,
                'Password': self.atf_password}
        print("data inside",self.bmc_login_username, self.bmc_login_password,self.iso_image_url_atf,self.atf_username,self.atf_password)
        data = json.dumps(data)
        header = {'Content-type': 'application/json'}
        reps = session.post(url, auth=auth1, verify=False, headers=header, data=data)
        print(reps.status_code)
        if (reps.status_code == 200):
            print("Media Mount from Artifactory location IS successfull")
            return True
        else:
            print("Error Media Mount Unsuccessfull from ATF")
            return False

    def unmount_image(self):
        # UNMOUNT Image From ATF:
        try:
            url = (
                r'https://{0}/redfish/v1/Managers/bmc/VirtualMedia/Slot_3/Actions/VirtualMedia.EjectMedia'.format(self.bmc_ip))
            print("data inside", self.bmc_login_username, self.bmc_login_password)
            auth1 = (self.bmc_login_username, self.bmc_login_password)
            data = {}
            data = json.dumps(data)
            header = {'Content-type': 'application/json'}
            reps = session.post(url, auth=auth1, verify=False, headers=header, data=data,timeout=(8,12))
            print(reps.status_code,reps.elapsed)
            if (reps.status_code == 200):
                print("Media unmount Successfull from Artifactory location")
                return True
            else:
                print("Unable to unMount Media From Given Artifactory Location")
                return False
        except Exception as ex:
            print("Unable to unMount Media From Given Artifactory Location {0}".format(ex))
            return True

def mount_vmm_redfish(atf_iso,rusr=None,rpwd=None,rip=None):
    rfish = redfish(atf_iso,rusr,rpwd,rip)
    for i in range(0,5):
        time.sleep(3)
        ret = rfish.mount_image()
        if ret == True:
            return True
        else:
            print("Tried Mounting {0}".format(i))
    return False

def unmount_vmm_redfish(rusr=None,rpwd=None,rip=None):
    rfish = redfish(None,rusr,rpwd,rip)
    if (rfish.unmount_image() == True):
        return True
    else:
        return False

#-------------------------------------------------------------------------------------------------------------------
banino = BaninoDriver()
def shutdown(timeoutoff=None):
    banino = BaninoDriver()
    if(banino.dc_power_off(timeoutoff) == True):
        return True
    else:
        return False

def wake_up(timeouton=None):
    banino = BaninoDriver()
    if(banino.dc_power_on(timeouton) == True):
        return True
    else:
        return False

def clearcmos():
    if(banino.set_clear_cmos() == True):
        return True
    else:
        return False

def dcdetection():
    if(banino.get_dc_power_state() == True):
        return True
    else:
        return False

def reboot():
    if(banino.dc_power_reset() == True):
        return True
    else:
        return False

def acdetection():
    if(banino.get_ac_power_state() == True):
        return True
    else:
        return False

def usb_switch_to_sut():
    if (banino.connect_usb_to_sut() == True):
        return True
    else:
        return False

def usb_disconnect():
    if (banino.disconnect_usb() == True):
        return True
    else:
        return False

def usb_switch_to_host():
    if (banino.connect_usb_to_host() == True):
        return True
    else:
        return False

def flash_ifwi(name):
    if(banino.chip_flash(path="C:\\flask_firmware\\ifwi\\",image_name=name) == True):
        return True
    else:
        return False

def flash_bmc(name):
    if(banino.chip_flash_bmc(path="C:\\flask_firmware\\bmc\\",image_name=name) == True):
        return True
    else:
        return False

def update():
    try:
        print(flask_location)
        subprocess.check_output(
            "curl -X GET bdcspiec010.gar.corp.intel.com/files/flask_windows/flask_server_flex.py --output "+flask_location+"\\flask_server_flex.py", shell=True)
        return True
    except Exception as ex:
        return ex

class UsbblasterDriver():
    def __init__(self):
        if (sys.platform != 'win32'):
            tree = ET.fromstring('/home/Automation/system_configuration.xml')
        else:
            tree = ET.parse('C:\Automation\system_configuration.xml')
        root = tree.getroot()
        # root = ET.fromstring()
        try:
            for item in root.findall('./suts/sut/providers'):
                cpld_app_path = item.find('./flash/driver/usbblaster/cpld_application_path')
                if os.path.exists(cpld_app_path.text):
                    # print("PATH Exists for Quartus Application")
                    cmd = cpld_app_path.text
                else:
                    print(
                        "PATH For Quartus Application Doesn't Exists Check path in system_configuration File \nor\n Install Aquartus Application")
                    sys.exit(1)
        except Exception as ex:
            print("Mismatched Syntax in system_configuration.xml Properly Check the syntax {0}".format(ex))

        print("Make Sure SUT is Turned ON for Detecting CPLD")
        if cmd:
            self.__cpld_app_path = cmd
        else:
            self.__cpld_app_path = r"C:\intelFPGA_pro\18.1\qprogrammer\\bin64"
        self.__cpld_app_path += "\quartus_pgm.exe"

    def health_status_check_usbblaster(self):
        cmd = (self.__cpld_app_path + " -c 1 -a")
        try:
            ret = subprocess.check_output(cmd, shell=True)
            print("{0}".format(ret))
            if "Quartus Prime Programmer was successful. 0 errors, 0 warnings" in str(ret):
                print("Quartus Programming USB Blaster is Detected In Host Machine")
                return True
        except Exception as ex:
            #print("Errors Quartus USB Blaster Is Not Detected {0}".format(ex))
            return False

    def chip_flash_primary(self, path=None, image_name=None):
        if(self.health_status_check_usbblaster() != True):
            return False
        cpld_image_name = path+"\\"+image_name
        cmd=(self.__cpld_app_path+" -c 1 --mode=JTAG --operation="+"\"p;"+cpld_image_name+"\"")
        try:
            print("CPLD Primary Frimware Flashing Is In Progress")
            ret=subprocess.check_output(cmd,shell=True)
            print("output {0}".format(ret))
            if "0 errors, 0 warnings" in str(ret):
                print("CPLD Flashing for Primary Chip is Successful")
                return True
            else:
                print("Failed To Flash CPLD Primary Chip")
                return False
        except Exception as ex:
            print("Errors Caught During CPLD Primary firmware Flashing {0}".format(ex))
            raise

    def chip_flash_secondary(self, path=None, image_name=None):
        if (self.health_status_check_usbblaster() != True):
            return False
        cpld_image_name = path + "\\" + image_name
        cmd = (self.__cpld_app_path + " -c 1 --mode=JTAG --operation=" + "\"p;" + cpld_image_name + "\"@2")
        try:
            print("CPLD  Secondary Frimware Flashing Is In Progress")
            ret = subprocess.check_output(cmd, shell=True)
            print("output {0}".format(ret))
            if "0 errors, 0 warnings" in str(ret):
                print("CPLD Flashing for Secondary Chip is Successful")
                return True
            else:
                print("Failed To Flash CPLD Secondary Chip")
                return False
        except Exception as ex:
            print("Errors Caught During CPLD Secondary firmware Flashing {0}".format(ex))
            raise

    def read_postcode(self):
        self.__cpld_app_path = r"C:\intelFPGA_pro\18.1\qprogrammer\bin64\quartus_stp_tcl -t rfat_modified.tcl"
        try:
            self.__cpld_app_path = "cd C:\postcode &&" + self.__cpld_app_path
            print("log",self.__cpld_app_path)
            output = Popen(self.__cpld_app_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
            cmd = output.stdout.read()
            cmd = str(cmd)
            ind = (str(cmd).index("BIOS CODE:"))
            post_code = (cmd[int(ind + 11):int(ind + 13)])
            print(post_code)
            return True,post_code
        except Exception as ex:
            #print("Errors Caught While Reading Postcode {0}".format(ex))
            return False

cpld =UsbblasterDriver()
def platform_postcode():
    try:
        ret=cpld.read_postcode()
        print("aaaa",ret)
        if(ret[0] == True):
            return ret[1]
        else:
            return "N/A"
    except Exception as ex:
        #print(ex)
        return "N/A"

def quartus_usb_check():
    try:
        if(cpld.health_status_check_usbblaster() == True):
            return True
        else:
            return False
    except Exception as ex:
        #print(ex)
        return False

def flash_cpld1(path,img):
    try:
        if (cpld.chip_flash_primary(path,img) == True):
            return True
        else:
            return False
    except Exception as ex:
        # print(ex)
        return False

def flash_cpld2(path,img):
    try:
        if (cpld.chip_flash_secondary(path,img) == True):
            return True
        else:
            return False
    except Exception as ex:
        # print(ex)
        return False

###
def ifwi_download_extract(ifwi_path):
    head, tail = ntpath.split(ifwi_path)
    try:
        subprocess.check_output("rmdir /s /q C:\\flask_firmware\ifwi", shell=True)
        subprocess.check_output("mkdir C:\\flask_firmware\ifwi", shell=True)
    except Exception as ex:
        print(ex)
        pass

    ret = subprocess.check_output("cd " + str("C:\\flask_firmware\ifwi") + " && curl -u  sys_degsi1:czhfi20$ -X GET " + str(ifwi_path) +
                                  " --output "+tail, shell=True)
    Dnd_img_path = "C:\\flask_firmware\ifwi\\"+str(tail)
    raw_path = "C:\\flask_firmware\ifwi"
    if (os.path.exists(Dnd_img_path) == True):
        if (zipfile.is_zipfile(Dnd_img_path) == True):
            with zipfile.ZipFile(Dnd_img_path, 'r') as zip_ref:
                zip_ref.extractall(str(raw_path))
            print("IFWI Image Extracted Successfull")
            ifwi_file_name=subprocess.check_output("cd " + str("C:\\flask_firmware\ifwi") + " && dir /w", shell=True)
            return True,ifwi_file_name
        elif (".7z" in Dnd_img_path):
            print(
                "User Has Given IFWI Image .7z Zip File Directly {0}".format(Dnd_img_path))
            subprocess.check_output("cd " + str("C:\\flask_firmware\ifwi") + "&& py7zr x " + Dnd_img_path, shell=True)
        else:
            print(
                "Downloaded File Is Not A IFWI ZIP/7Z Image File,Artifactory Path Is Not Given Properly")
            return False,"Downloaded File Is Not A IFWI ZIP/7Z Image File,Artifactory Path Is Not Given Properly"
    else:
        return False

def bmc_download_extract(ifwi_path):
    head, tail = ntpath.split(ifwi_path)
    try:
        subprocess.check_output("rmdir /s /q C:\\flask_firmware\\bmc", shell=True)
        subprocess.check_output("mkdir C:\\flask_firmware\\bmc", shell=True)
    except Exception as ex:
        print(ex)
        pass

    ret = subprocess.check_output("cd " + str("C:\\flask_firmware\\bmc") + " && curl -u  sys_degsi1:czhfi20$ -X GET " + str(ifwi_path) +
                                  " --output "+tail, shell=True)
    Dnd_img_path = "C:\\flask_firmware\\bmc\\"+str(tail)
    raw_path = "C:\\flask_firmware\\bmc"
    if (os.path.exists(Dnd_img_path) == True):
        if (zipfile.is_zipfile(Dnd_img_path) == True):
            with zipfile.ZipFile(Dnd_img_path, 'r') as zip_ref:
                zip_ref.extractall(str(raw_path))
            print("IFWI Image Extracted Successfull")
            ifwi_file_name=subprocess.check_output("cd " + str("C:\\flask_firmware\\bmc") + " && dir /w", shell=True)
            return True,ifwi_file_name
        elif (".7z" in Dnd_img_path):
            print(
                "User Has Given BMC Image .7z Zip File Directly {0}".format(Dnd_img_path))
            subprocess.check_output("cd " + str("C:\\flask_firmware\\bmc") + "&& py7zr x " + Dnd_img_path, shell=True)
        else:
            print(
                "Downloaded File Is Not A IFWI ZIP/7Z Image File,Artifactory Path Is Not Given Properly")
            return False,"Downloaded File Is Not A IFWI ZIP/7Z Image File,Artifactory Path Is Not Given Properly"
    else:
        return False

def cpld_download_extract(ifwi_path):
    head, tail = ntpath.split(ifwi_path)
    # try:
    #     subprocess.check_output("rmdir /s /q C:\\flask_firmware\cpld", shell=True)
    #     subprocess.check_output("mkdir C:\\flask_firmware\cpld", shell=True)
    # except Exception as ex:
    #     print(ex)
    #     pass

    ret = subprocess.check_output("cd " + str("C:\\flask_firmware\cpld") + " && curl -u  sys_degsi1:czhfi20$ -X GET " + str(ifwi_path) +
                                  " --output "+tail, shell=True)
    Dnd_img_path = "C:\\flask_firmware\cpld\\"+str(tail)
    raw_path = "C:\\flask_firmware\cpld"
    if (os.path.exists(Dnd_img_path) == True):
        if (zipfile.is_zipfile(Dnd_img_path) == True):
            with zipfile.ZipFile(Dnd_img_path, 'r') as zip_ref:
                zip_ref.extractall(str(raw_path))
            print("IFWI Image Extracted Successfull")
            ifwi_file_name=subprocess.check_output("cd " + str("C:\\flask_firmware\cpld") + " && dir /w", shell=True)
            return True,ifwi_file_name
        elif (".7z" in Dnd_img_path):
            print(
                "User Has Given IFWI Image .7z Zip File Directly {0}".format(Dnd_img_path))
            subprocess.check_output("cd " + str("C:\\flask_firmware\cpld") + "&& py7zr x " + Dnd_img_path, shell=True)
        else:
            print(
                "Downloaded File Is Not A IFWI ZIP/7Z Image File,Artifactory Path Is Not Given Properly")
            return False,"Downloaded File Is Not A IFWI ZIP/7Z Image File,Artifactory Path Is Not Given Properly"
    else:
        return False

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/')
def homepage():
    ret = subprocess.check_output("hostname", shell=True)
    ret = ret.strip()
    return "Version 1.1 19-April-2022 whiteTigress"

@app.route('/help',methods=['GET'])
@app.route('/options',methods=['GET'])
def informer():
    return (
            "\ndownload/ifwi or bmc or cpld/ATF_ifiw_ZIP_PATH  --------- just given the Artifactory path it will downlaod on the NUC \n \t eg:- curl -X GET "+(service_ip)+"/download/ifwi/https://ubit-artifactory-ba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-RHEL/EGS-SRV-RHEL-22.10.1.1C/Packages/IFWI/2022.09.3.06_0075.d01_v1/2022.09.3.06_0075.d01.zip \n\nimg_upload ---- uploading .rom/.bin/.pof From your Device To HostMachine ""\n""\t eg:- curl -T full_location_path of image_name .bin|.rom |.pof -X POST http://" + str(
        ipadd) + "/img_upload/ifwi/ or bmc/ or cpld/ \n\t \nwrite_chip/bmc/xxx.rom ----- Flashes the choosen BMC image under \"C:\\flask_firmware\\bmc\" \nwrite_chip/ifwi/xxx.bin ----- Flashes the choosen IFWI image under \"C:\\flask_firmware\ifwi\" \nwrite_chip/cpld1 or cpld2/xxx.pof ----- Flashes the choosen CPLD image under \"C:\\flask_firmware\\cpld\" \n\ndcpower/0 ------- To DC Turn Off Platform \ndcpower/1 ------- To DC Turn On Platform \n\nvmm/0/bmc_ipaddress/bmc_username/bmc_passwprd  ----- 0 is for unmount an iso Virtual Media Drive \n \t eg :- curl -X GET {0}/vmm/0/10.XX.XX.XX/debuguser/0penBmc1 \t \nvmm/1/bmc_ipaddress/bmc_username/bmc_passwprd/ATF_iso_path  ----- 1 is for mount an iso Virtual Media Drive \n \t eg :- curl -X GET {0}/vmm/1/10.XX.XX.XX/debuguser/0penBmc1/https://ubit-artifactory-ba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-RHEL/EGS-SRV-RHEL-22.10.1.1C/Images/rhel-8.5.0-20211013.2_ai_FRE_IA-64_EGS-SRV-RHEL-22.10.1.1C.iso \n\nacpower/0/pdu_ip/pdu_username/pdu_password/pdu_outlet ------- AC POWER OFF \n \t eg :- curl -X GET {0}/acpower/0/10.XX.XX.XX/admin/intel@123/18 \nacpower/1/pdu_ip/pdu_username/pdu_password/pdu_outlet ------- AC POWER ON \n \t eg :- curl -X GET {0}/acpower/1/10.XX.XX.XX/admin/intel@123/18 \n\nacpower/0 ------- DTAF Already Configured To AC Power Turn Off Platform \nacpower/1 ------- DTAF Already Configured To AC Power Turn ON Platform \nclearcmos \nreboot \npostcode \nusb2host  ----- USB Device TO HOST Machine \nusb2sut   ----- USB Device TO HOST Machine \nusbdiscnt ----- USB DISCONNECT FROM BOTH SUT AND HOST \ndcdetect \nacdetect \nupdate ----- Updates Latest Flask Service".format(service_ip))

@app.route('/',methods=['GET','POST'])
def index():
    if(required.method == 'POST'):
        some_json = request.get_json()
        return jsonify({'you sent':some_json}),201
    else:
        return jsonify({"Power on"})

@app.route('/clearcmos',methods=['GET'])
def platform_clearcmos():
    if(clearcmos()==True):
        return "ClearCmos Command Issued"
    else:
        return "N/A"

@app.route('/postcode',methods=['GET'])
def platform_pstcode():
    ret=platform_postcode()
    if(ret=="N/A"):
        return "N/A"
    else:
        return ret

@app.route('/cpld/check',methods=['GET'])
def quartus_check():
    if(quartus_usb_check() == True):
        return "USB-Blaster is Detected --- [ok]"
    else:
        return "Quartus path is Wrong or Device Not Connected to Platform"

@app.route('/dcdetect',methods=['GET'])
def platform_dcpower():
    if dcdetection()==True:
        return "DC power detected"
    else:
        return "N/A"

@app.route('/reboot',methods=['GET'])
def platform_reboot():
    if(reboot()==True):
        return "Reboot Command Issued"

@app.route('/update',methods=['GET'])
def flask_update():
    if(update()==True):
        print(flask_location)
        return "Flask SCript Updated Command Issued"

@app.route('/acdetect',methods=['GET'])
def platform_acpower():
    if(acdetection()==True):
        return "AC power detected"
    else:
        return "N/A"

@app.route('/usb2host', methods=['GET'])
def usb2host():
    if (usb_switch_to_host() == True):
        return "USB Switch to Host Done"
    else:
        return "Failed to Switch the Usb To Host"


@app.route('/usbdiscnt', methods=['GET'])
def usbdisconnect():
    if (usb_disconnect() == True):
        return "USB Disconnect Done"
    else:
        return "Failed to Disconnect USB"


@app.route('/usb2sut', methods=['GET'])
def usb2sut():
    if (usb_switch_to_sut() == True):
        return "USB Switch to SUT Done"
    else:
        return "Failed to Switch the Usb To SUT"

@app.route('/acpower/config/<string:outlet_number>/<string:pdu_ip>/<string:pdu_username>/<string:pdu_password>',methods=['GET'])
def pdu_config(outlet_number,pdu_ip,pdu_username,pdu_password):
    try:
        if(pdu_configure(outlet_number,pdu_ip,pdu_username,pdu_password) == True):
                return str("PDU configured With Outlet --> {0} \nPDU_IP_Address --> {1}\npdu_username --> {2}\npdu_password --> {3}").format(outlet_number,pdu_ip,pdu_username,pdu_password)
        else:
            return "Failed to Configure PDU"
    except Exception as ex:
        return str("Make sure PDU Credentials are Proper")

@app.route('/dcpower/num/',defaults={'timeout':None},methods=['GET'])
@app.route('/dcpower/<int:num>',methods=['GET'])
@app.route('/dcpower/<int:num>/<int:timeout>',methods=['GET'])
def dcpower(num,timeout=None):
    if num == 0:
        if(shutdown(timeoutoff=timeout)==True):
            return "DC Power Turned OFF and Verified"
        else:
            return "Failed To DC Power Turned OFF"
    elif num == 1:
        if(wake_up(timeouton=timeout)==True):
            return "Dc Power Turned ON and Verfied"
        else:
            return "Failed To DC Power Turned ON"
    else:
        return "Invalid Input:-\n 0 is Turn Power OFF \n 1 is Turn Power On"

# @app.route('/multi/<string:operation>/<int:num>/<int:ip>',defaults={'timeout':None},methods=['GET'])
# def multi_role_action(operation,int,ip=None):
#     if str(operation).lower() == "":
#         if(shutdown(timeoutoff=timeout)==True):
#             return "DC Power Turned OFF and Verified"
#         else:
#             return "Failed To DC Power Turned OFF"
#     elif num == 1:
#         if(wake_up(timeouton=timeout)==True):
#             return "Dc Power Turned ON and Verfied"
#         else:
#             return "Failed To DC Power Turned ON"
#     else:
#         return "Invalid Input:-\n 0 is Turn Power OFF \n 1 is Turn Power On"


@app.route('/acpower/num',defaults={'timeout':None},methods=['GET'])
@app.route('/acpower/<int:num>',methods=['GET'])
@app.route('/acpower/<int:num>/<string:ip>',methods=['GET'])
@app.route('/acpower/<int:num>/<string:ip>/<string:username>',methods=['GET'])
@app.route('/acpower/<int:num>/<string:ip>/<string:username>/<string:password>',methods=['GET'])
@app.route('/acpower/<int:num>/<string:ip>/<string:username>/<string:password>/<int:outlet>',methods=['GET'])
def acpower(num,username=None,password=None,ip=None,outlet=None):
    try:
        if num == 0:
            if(acofffromacon(pusr=username,ppwd=password,pip=ip,poutlet=outlet)==True):
                return "Power Turned OFF and Verified"
            else:
                return "AC Power OFF Failed Make sure PDU IP/Credentials are Correct curl -X GET {0}/help".format(service_ip)
        elif num == 1:
            if(aconfromacoff(pusr=username,ppwd=password,pip=ip,poutlet=outlet)==True):
                return "Power Turned ON and Verified"
            else:
                return "AC Power ON Failed Make sure PDU IP/Credentials are Correct curl -X GET {0}/help".format(service_ip)
        else:
            return "Invalid Input:-\n 0 is Turn Power OFF \n 1 is Turn Power On"
    except Exception as ex:
        return "Make sure PDU Credentials are Correct curl =X GET {0}/help".format(service_ip)

@app.route('/download/<string:frimware>/<path:img>',methods=['GET'])
def download_frimware(frimware=None,img=None):
    if str(frimware).lower() == "ifwi":
        ret= ifwi_download_extract(img)
        if(ret[0] == True):
            file = ret[1].split()
            return str("Downloaded Image ---> " + str(file[15:25]))
        else:
            return "Failure"
    elif str(frimware).lower() == "bmc":
        ret= bmc_download_extract(img)
        if(ret[0] == True):
            file = ret[1].split()
            return str("Downloaded Image ---> " + str(file[15:25]))
        else:
            return "Failure"
    elif (str(frimware).lower() in ["cpld"]):
        ret= cpld_download_extract(img)
        if(ret[0] == True):
            file = ret[1].split()
            return str("Downloaded Image ---> " + str(file[15:25]))
        else:
            return "Failure"

@app.route('/vmm/num/',defaults={'ip':None},methods=['GET'])
@app.route('/vmm/<int:num>/',defaults={'ip':None},methods=['GET'])
@app.route('/vmm/<int:num>/<string:ip>',methods=['GET'])
@app.route('/vmm/<int:num>/<string:ip>/<string:username>',methods=['GET'])
@app.route('/vmm/<int:num>/<string:ip>/<string:username>/<string:password>',methods=['GET'])
@app.route('/vmm/<int:num>/<string:ip>/<string:username>/<string:password>',methods=['GET'])
@app.route('/vmm/<int:num>/<string:ip>/<string:username>/<string:password>/<path:img>',methods=['GET'])
def mount_vmm(num,username=None,password=None,ip=None,img=None):
    try:
        if num == 0:
            print("")
        else:
            if img == None:
                return "Do Given Image iso Artifactory Path"
            elif not "iso" in str(img):
                return "Artifactory Link PATH has to have iso in the url"
    except Exception as ex:
        return "curl -X GET {0}/help".format(service_ip)
    try:
        if num == 1:
            if(mount_vmm_redfish(img,username,password,ip) == True):
                return "ISO-Artifacotry Image MOUNT Succesful",img
            else:
                return "Failed to mount image check bmc certificate --- Try Again FOR HRLP curl -X GET {0}/help".format(service_ip)
        elif num == 0:
            if(unmount_vmm_redfish(username,password,ip) == True):
                return "ISO-Artifacotry Image UNMOUNT Succesful", img
            else:
                return "Failed to Unmount image check bmc certificate --- Try Again FOR HRLP curl -X GET {0}/help".format(service_ip)
    except Exception as ex:
        print("Exepetion From Service --->  ",ex)
        #return str("Mounting OS Image Failed {0}".format(ex))

@app.route("/img_upload/<type>/<filename>", methods=["POST"])
def upload_img_file(type,filename):
    try:
        if "/" in filename:
            abort(400, "no subdirectories directories allowed")
        if(type.lower() == "bmc"):
            with open(os.path.join(UPLOAD_DIRECTORY+str("bmc"), filename), "wb") as fp:
                fp.write(request.data)
        elif(type.lower() == "ifwi"):
            with open(os.path.join(UPLOAD_DIRECTORY+str("ifwi"), filename), "wb") as fp:
                fp.write(request.data)
        elif (type.lower() == "cpld"):
            with open(os.path.join(UPLOAD_DIRECTORY + str("cpld"), filename), "wb") as fp:
                fp.write(request.data)
        return str("uploading Image "+str(filename)+"... Completed")
    except Exception as ex:
        return str("Uploading Image Failed {0}".format(ex))

@app.route('/write_chip/<string:type>/<string:img>',methods=['GET'])
@app.route('/write_chip/',defaults={'img':None},methods=['GET'])
@app.route('/write_chip/',defaults={'type':None},methods=['GET'])
def chip_write(img=None,type=None):
    try:
        start = time.time()
        if(type.lower() == "ifwi"):
            if(flash_ifwi(img) == True):
                end2 = time.time()
                turn_off_via_cmd = (abs(start - end2))
                turn_off_via_cmd = ("{:05.2f}".format(turn_off_via_cmd))
                return str("Flashing IFWI Chip With "+str(img)+"Image ... Successfull It Took {0}".format(turn_off_via_cmd))
            else:
                return str("Flashing Failed For IFWI Chip || Make sure Platform is Turned OFF || Image Name & Available")
        elif(type.lower() == "bmc"):
            if(flash_bmc(img) == True):
                end2 = time.time()
                turn_off_via_cmd = (abs(start - end2))
                turn_off_via_cmd = ("{:05.2f}".format(turn_off_via_cmd))
                return str("Flashing BMC Chip With " + str(img) + "Image ... Successful It Took {0}".format(turn_off_via_cmd))
            else:
                return str("Flashing Failed For BMC Chip || Make sure Platform is Turned OFF || Image Name & Available")
        elif (type.lower() == "cpld1"):
            path="C:\\flask_firmware\cpld\\"
            if (flash_cpld1(path,img) == True):
                end2 = time.time()
                turn_off_via_cmd = (abs(start - end2))
                turn_off_via_cmd = ("{:05.2f}".format(turn_off_via_cmd))
                return str(
                    "Flashing Cpld Chip With " + str(img) + "Image ... Successful It Took {0}".format(turn_off_via_cmd))
            else:
                return str("Flashing Failed For CPLD Primary Chip || Make sure Platform is Turned OFF || Image Name & Available")
        elif (type.lower() == "cpld2"):
            path="C:\\flask_firmware\cpld\\"
            if (flash_cpld2(path,img) == True):
                end2 = time.time()
                turn_off_via_cmd = (abs(start - end2))
                turn_off_via_cmd = ("{:05.2f}".format(turn_off_via_cmd))
                return str(
                    "Flashing CPLD Chip With " + str(img) + "Image ... Successful It Took {0}".format(turn_off_via_cmd))
            else:
                return str("Flashing Failed For CPLD Secondary Chip || Make sure Platform is Turned OFF || Image Name & Available")
    except Exception as ex:
        return str("Do Give Proper Syntax  write_chip/chip_type/image_name \nchip_type ifwi or BMC \nifwi_image_name.bin or bmc_img_name.rom")


if __name__ == "__main__":
    app.run(host="0.0.0.0",threaded=True,port=80,debug=True)
