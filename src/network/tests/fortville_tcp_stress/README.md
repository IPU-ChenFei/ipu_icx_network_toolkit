PHEONIX ID : 18014067723-PI_Networking_Fortville_TCPStress_W

BKM for Executing Networking Test Cases.
Requirement of hw for test case windows:
-> 1 host connected to 2 sut
-> two fortvile card(both SUT) , two P2P cable(Host to SUT1 and Host to  SUT2) and one SFP cable required(SUT1 to SUT2)

Process of Setting P2P Connection for windows fortville card:
-> 1 p2p cable connect from host to SUT1 and one more p2p cable connect from  host to SUT2
-> Assign Static IP to the USB to Ethernet Port on host to  SUT1 and host to  SUT2 with 192 Series Static IP like below example.
Example: maintain below like in system configuration.192.168.1.20 already static ip assigned for Sut1 and sut2 assign static ip 192.168.1.21 and both ip pingable
  </host>
    <suts>
        <sut ip="192.168.1.20">
            <platform type="reference" boardname="Archercity" name="EGS" />
            <silicon>
                <cpu>
				<sut_os name="Windows" subtype="Win" version="10" kernel="4.2">
                    <shutdown_delay>5.0</shutdown_delay>
                    <driver>
						<ssh>
                            <credentials user="Administrator" password="intel@123"/>
                            <ipv4>192.168.1.20</ipv4>
                        </ssh>
				
				

-> assign static ip for fortville port for SUT1 and SUT2 and same maintain in content configuration file.
			<sut1_ip>10.10.10.11</sut1_ip>  //{This is SUT1(192.168.1.20) Forville static ip assigned}
            <sut2_ip>10.10.10.10</sut2_ip>  //{This is SUT2(192.168.1.21) Forville static ip assigned}
            <sut2_usb_to_ethernet_ip>192.168.1.21</sut2_usb_to_ethernet_ip> //{Assign This is SUT2(192.168.1.21) Forville static ip}


->Process of Setting IP Address to Different Cards. 
 Fortville:
    -> It is External Card. 
    -> Need to Connect SFP Loop Back Cable for both Ports of Fortville Card.
    -> Since There is No Provision to Connect Lan Cable, need to set Static IP's to Fortville Ports (Taken Care 
   in Script)
