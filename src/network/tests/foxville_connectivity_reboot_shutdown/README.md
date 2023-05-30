Download the Network Drivers from BKC and Update the Path in content_configuration.xml in drivers/network_drivers
Network Cable has to be Connected to Foxville Port and Need to Enable Serial Communication in SUT.

Serial Communication setup details:

1.	Disable serial login from OS using below commands
a.	Edit grub file “/etc/sysconfig/grub”  & remove the console values 
GRUB_TIMEOUT=5
GRUB_DISTRIBUTOR="$(sed 's, release .*$,,g' /etc/system-release)"
GRUB_DEFAULT=saved
GRUB_DISABLE_SUBMENU=true
GRUB_TERMINAL_OUTPUT="console"
GRUB_CMDLINE_LINUX="crashkernel=auto resume=/dev/mapper/rhel-swap rd.lvm.lv=rhel/root rd.lvm.lv=rhel/swap xfs ignore_loglevel intel_idle.max_cstate=0 processor.max_cstate=1 iommu=on idle=poll"
GRUB_DISABLE_RECOVERY="true"
GRUB_ENABLE_BLSCFG=true


b.	Recreate grub.cfg file by running below command
grub2-mkconfig -o /boot/grub2/grub.cfg

2.	Download sut_agent from below link and copy to SUT
https://af01p-png.devtools.intel.com/artifactory/webapp/#/artifacts/browse/tree/General/dtaf-framework-release-png-local/sutagent/1.11.0/sutagent-1.11.0-py2.py3-none-any.whl 

pip3 install sutagent-1.11.0-py2.py3-none-any.whl –proxy http://proxy-chain.intel.com:911

3.	Got to folder in SUT ‘/usr/local/lib/python3.6/site-packages/sutagent’
a.	Update sut_agent.ini as below
[SUT]
serial = /dev/ttyS0 
serial_auto_detect = False
serial_enable = True
network_enable = False
ip = 127.0.0.1
port = 5555

b.	Update run.sh and setup.sh, replace python2.7 with python3
c.	Modify python code sut_agent.py as below (line 235)

self.enable_timer()
# preexec_fn = None if SutConfig().is_windows() else os.setsid()    comment this line
try:
         # self.proc = subprocess.Popen(self.cmd, shell=True, preexec_fn=preexec_fn,
         #                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
         self.proc = subprocess.Popen(self.cmd, shell=True, start_new_session=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


4.	base_sut_os_provider.py (dtaf_core)

def is_alive(self): (function)

Line no:174; change to 15
data = self.execute("dir", 15)
5.	Below files make it executable.
chmod +x run.sh
chmod +x setup.sh

After changing the executable file. Please run.
./setup.sh


6.	Go to .config folder and check below folder is available.
Autostart

Make it to executable folder. (autostart/run.sh.desktop)
chmod +x autostart


Once all done once reboot the system. Sut agent will start automatically.
(After reboot sutagent terminal will open in the SUT)

	
System configuration Update:
<sut_os id="serial" name="Linux" subtype="RHEL" version="8.2" kernel="4.2">
                    <shutdown_delay>5.0</shutdown_delay>
                    <driver>
                        <com>
							<port>COM100</port>
                            <baudrate>115200</baudrate>
							<timeout>5</timeout>
                        </com>
                    </driver>
                </sut_os>
<sut_os id="SSH" name="Linux" subtype="RHEL" version="8.2" kernel="4.2">
                    <shutdown_delay>5.0</shutdown_delay>
                    <driver>
                        <ssh>
                            <credentials user="root" password="password"/>
                            <ipv4>10.219.171.2</ipv4>
                        </ssh>
                    </driver>
                </sut_os>

Content_Configuration Update:
    <drivers>
        <network_drivers>C:\Automation\BKC\Drivers\25_1.zip</network_drivers>
    </drivers>
