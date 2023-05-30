
from subprocess import Popen, PIPE
import os
from xml.etree import ElementTree as eTree
import sys
import fileinput
import re


class cmdscript:
    def __init__(self):
        self.cmdprompt = None
        data = argument_parser()
        if data[3] == 'pve-common':

            self.commands_host_pvecommon =[

                'python --version',
                'mkdir C:\Automation',
                'Copy automation\\example_system_configuration_windows.txt C:\\Automation\\system_configuration.txt'
                ]
                
            self.commands_host1_pvecommon =[
                'setx PYTHONPATH "."',
                'setx path "%PATH%;C:\Python27"',
                'setx path "%PATH%;C:\Python27\Scripts"',
                'python -m pip install --upgrade pip --proxy=http://proxy01.iind.intel.com:911',
                r'python -m pip install -r requirements_python2.txt --proxy=http://proxy01.iind.intel.com:911',
                'powershell Set-ExecutionPolicy RemoteSigned',
                'powershell Restart-Service WinRM',
                "powershell Set-Item WSMan:\localhost\Client\TrustedHosts -Value '*' -force",
                ]
        
        if data[3] == 'dtaf':

            self.commands_host_dtaf =[

                'python3 --version',
                'mkdir C:\Automation',
                'Copy src\seamless\system_configuration_windows.xml C:\\Automation\\system_configuration.xml' 
                ]
                
            self.commands_host1_dtaf =[
                'setx PYTHONPATH ".;..\dtaf_core\src"',
                'setx path "%PATH%;C:\Python36"',
                'setx path "%PATH%;C:\Python36\Scripts"',
                'python3 -m pip install --upgrade pip --proxy=http://proxy01.iind.intel.com:911',
                r'python3 -m pip install -r requirements_py3_modified.txt --proxy=http://proxy01.iind.intel.com:911',
                'powershell Set-ExecutionPolicy RemoteSigned',
                "powershell Set-Item WSMan:\localhost\Client\TrustedHosts -Value '*' -force",
                ]

    def run_system(self, command):
        output = os.system(command)
        if (output == 1):
            raise RuntimeError("Command: '" + command + "' failed, check for error")

    def start_cmdprompt(self, command):

        if (self.cmdprompt is None or self.cmdprompt.poll is not None):
            print("Starting command prompt")
            self.cmdprompt = Popen(['cmd.exe'], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)

    def run_command(self, command, get_output=False, echo_output=True):
        self.start_cmdprompt(command)
        (p_out, err) = self.cmdprompt.communicate('C:\Windsows\System32\cmd.exe -c "command"')
        output = ""
        if get_output:
            print("reading output: ", p_out)
            p_out = p_out.split('\n')
            for line in p_out:
                output = output + line.rstrip() + '\n'
                if echo_output:
                    print(line.rstrip())

            print(err)

        return output
    
    def set_up_host(self):

        data = argument_parser()
        if data[3] == 'pve-common':
            try:
                for cmd in self.commands_host_pvecommon:
                    print("command: ", cmd)
                    if cmd == 'mkdir C:\Automation':
                        if os.path.exists('C:\Automation'):
                            continue
                        else:
                            self.run_system(cmd)
                    if cmd == 'Copy automation\\example_system_configuration_windows.txt C:\\Automation\\system_configuration.txt':
                        if os.path.exists('C:\\Automation\\system_configuration.txt'):
                            continue
                        elif data[4] == 'windows':
                            self.run_system(cmd)
                        elif data[4] == 'linux':
                            self.run_system('Copy automation\\example_system_configuration_linux.txt C:\\Automation\\system_configuration.txt')
                            continue
                    self.run_system(cmd)
                setupfileEdit()
                for cmd in self.commands_host1_pvecommon:
                    print("command: ", cmd)
                    self.run_system(cmd)

            except RuntimeError as e:
                print(e)

        if data[3] == 'dtaf':
            try:
                for cmd in self.commands_host_dtaf:
                    print("command: ", cmd)
                    if cmd == 'mkdir C:\Automation':
                        if os.path.exists('C:\Automation'):
                            continue
                        else:
                            self.run_system(cmd)
                    elif cmd == 'Copy src\seamless\system_configuration_windows.xml C:\\Automation\\system_configuration.xml':
                        if os.path.exists('C:\\Automation\\system_configuration.xml'):
                            continue
                        elif data[4] == 'windows':
                            self.run_system(cmd)
                        elif data[4] == 'linux':
                            self.run_system('Copy src\seamless\system_configuration_linux.xml C:\\Automation\\system_configuration.xml')
                            continue
                    self.run_system(cmd)
                setupfileEdit()
                for cmd in self.commands_host1_dtaf:
                    print("command: ", cmd)
                    self.run_system(cmd)
            except RuntimeError as e:
                print(e)
    
def argument_parser():
    arguments = len(sys.argv) - 1

    
    position = 1
    data = []
    while (arguments >= position):
        
        data.append(sys.argv[position])
        position = position + 1
    
    return data

def setupfileEdit():
    
    data = argument_parser()

    if data[3] == 'pve-common':
        
        for line in fileinput.input('C:\\Automation\\system_configuration.txt', inplace = True):
        
            if line.startswith("sut_ip::"):
                print ("sut_ip::{}".format(data[0]))
                    
            elif line.startswith("sut_bmc_ip::"):
                print ("sut_bmc_ip::{}".format(data[1]))

            elif line.startswith("ras_pi_ip::"):
                print ("ras_pi_ip::{}".format(data[2]))
            
            else:
                print (line.strip())
        
    
    elif data[3] == 'dtaf':

        tree = eTree.ElementTree()
        if sys.platform == 'win32':
            tree.parse(r'C:\\Automation\\system_configuration.xml')
        else:
            tree.parse('/opt/Automation/consolelog_configuration.xml')
        root = tree.getroot()
        sut_ip_attr = root.find('suts/sut')
        sut_ip_attr.set('ip',data[0])
        root.find('suts/sut/providers/sut_os/driver/ssh/ipv4').text = data[0]
        root.find('suts/sut/providers/bios/driver/xmlcli/ip').text = data[0]
        root.find('suts/sut/silicon/bmc/ip').text = data[1]
        root.find('suts/sut/providers/flash/driver/redfish/ip').text = data[1]
        root.find('suts/sut/providers/dc/driver/ipmi/ip').text = data[1]
        root.find('suts/sut/providers/ac/driver/pdupi/ip').text = data[2]
        root.find('suts/sut/providers/ac/driver/pi/ip').text = data[2]
        root.find('suts/sut/providers/dc/driver/pi/ip').text = data[2]
        root.find('suts/sut/providers/physical_control/driver/pi/ip').text = data[2]
        print(tree)
        tree.write('C:\\Automation\\system_configuration.xml')    


host = cmdscript()
host.set_up_host()
