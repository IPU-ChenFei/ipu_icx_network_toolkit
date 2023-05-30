### Pre-requisite for all Manageability test cases

1. BMC Lan cable and serial cable must be connected to SUT.
2. In system_configuration.xml fie, add <bmc> tag with BMC IP address and <credentials> tag with BMC username and 
   password as below:--
    <suts>
        <sut>
            <silicon>
                <bmc>
                    <ip>10.219.164.136</ip>
                    <credentials user="debuguser" password="0penBmc1"/>
                </bmc>
            </silicon>
        </sut>
    </suts>
   
3. Set the below all path in system path variable.
    a. C:\Intel\DFPython\bin\
    b. C:\Python36\Scripts\
    c. C:\Python36\
    d. C:\Python36\Lib
    e. C:\Python36\python.exe
   
4. Create a config file under C:\Automation folder with Hostname as filename.
   In content, replace the SUT IP and BMC IP as per the hardware configuration.
   
_Below is the content for cfg file._

**hostname.cfg**
############################################################################
# Node Manager python tool configuration file
#

[Section0]

# IP address of the BMC/ME the tool will be accessing
ipaddress = 10.219.164.136

#OS IP address
osip = 10.219.170.136

# FW sku. nm or dcmi. default=nm
sku = nm

# dell or intel. default=intel
targettype = intel
#targettype = dell

# lan, idracserial, kcs. default=lan
#interface = redfish_ipmi
interface = lan

# ivt or hsx. If left blank, default to ivt
cpuname = spr

#Ignition FW stack using IPMI with no NM bridging 
#bmcver =OpenNM_IPMI

#Ignition FW stack using Redfish to the BMC
#bmcver =OpenNM_Redfish

#OpenBMC with NM bridging to PCH
bmcver = open

username = debuguser
password = 0penBmc1

osver = win
ptupath = "C:\Program Files\Intel\Power Thermal Utility for ICX\PTU.exe"

############################################################################
	
	
	
