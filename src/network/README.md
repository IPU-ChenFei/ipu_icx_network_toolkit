BKM for Executing Networking Test Cases.

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

<sut_os name="Windows" subtype="Win" version="10" kernel="4.2"> 
                     <shutdown_delay>5.0</shutdown_delay> 
					 <driver>
                        <ssh> 
                           <credentials user="Administrator" password="intel@123"/> 
                             <ipv4>192.168.1.52</ipv4> 
                         </ssh> 
                    </driver>  
</sut_os>

Process of Setting IP Address to Different Cards.

1.Carlsville :
-> It is External Card.
-> Need to Connect Lan Cable to Carlsville Port inorder to obtain dhcp ip address to Carlsville Port.

2. Columbiaville :
    -> It is External Card. 
    -> Need to Connect SFP Loop Back Cable for both Ports of Columbiaville Card.
    -> Since There is No Provision to Connect Lan Cable, need to set Static IP's to Columbiaville Ports (Taken Care 
   in Script)
   
3. Fortville:
    -> It is External Card. 
    -> Need to Connect SFP Loop Back Cable for both Ports of Fortville Card.
    -> Since There is No Provision to Connect Lan Cable, need to set Static IP's to Fortville Ports (Taken Care 
   in Script)
   
4. Foxville:
    -> It is Inbuilt Card(Default).
    -> Need to Connect Lan Cable to Foxville Port inorder to obtain DHCP Ip address for Foxville Port.
   
5. Jacksonville:
    -> It is Inbuilt Card but need to do Hardwork rework to enable Jacksonville by disabling foxville.
    -> Need to Connect Lan Cable to Jacksonville Port inorder to obtain DHCP Ip address for Jacksonville Port.
   
