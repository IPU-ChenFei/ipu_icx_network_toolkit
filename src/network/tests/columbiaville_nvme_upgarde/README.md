        BKM for Executing Networking Test Cases.
	
	"In Host please do setup":
		go to command prompt :
		 -dflaunch -s
		 -pip install lxml

Process of Setting P2P Connection:
-> Connect one USB to Ethernet Adapter in between Host and Sut.
-> Assign Static IP to the USB to Ethernet Port on SUT with 192 Series Static IP.
-> 192 Series IP Address of SUT must be pingable from HOST.
-> Update System Config file with 192 Series IP Address of SUT.

<sut_os name="Linux" subtype="RHEL" version="8.2" kernel="4.2">
                    <shutdown_delay>5.0</shutdown_delay>
					<driver>
						<ssh>
							<credentials user="root" password="password"/>
							<ipv4>192.168.1.20</ipv4>
						</ssh> 
                    </driver>
</sut_os>


Process of Setting IP Address to Different Cards.

Columbiaville card required to connect for thi stest case.
    -> Need to Connect SFP Loop Back Cable for both Ports of Columbiaville Card.
    -> Need to set Static IP's to Columbiaville Ports example: 192.168.1.5 
	
	in content config xml file please verify the both path and file name and file should available.
	<drivers>
        <network_drivers>C:\Automation\BKC\Drivers\Intel_LAN_v26.zip</network_drivers>
    </drivers>
	
	Also this file should maintain:
		<Network>
                <!-- <pass_through_device_name>Intel(R) I210 Gigabit Network Connection,Intel(R) Ethernet Converged Network Adapter X710</pass_through_device_name>-->
                <pass_through_device_name>Intel(R) Ethernet Network Adapter E810-XXV-4</pass_through_device_name>
                <driver_tool_path>C:\Automation\Tools\Windows\intel_lan_v26.zip</driver_tool_path>
        </Network>
	

	
  