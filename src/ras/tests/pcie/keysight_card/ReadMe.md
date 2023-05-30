For All Keysight Card:
Below Config changes require:

content_configuration.xml
Keysight Card socket and port need to update
<keysight_pcie_card>
   <socket>0</socket>
   <pxp_port>pxp3.pxp5.port0</pxp_port>
</keysight_pcie_card>

Keysight Card AC Cycle:
Need to update the driver tag according to Controller used for AC cycle 
<provider>
    <ac>
        <driver>
			<pdu brand="raritan" model="px-5052R">
            <ip>10.190.177.25</ip>
            <port>22</port>
            <username>admin</username>
            <password>intel@123</password>
            <timeout>5</timeout>
            <outlets>
                <outlet>4</outlet>
            </outlets>
			</pdu>
        </driver>
        <timeout>
            <power_on>5</power_on>
            <power_off>5</power_off>
        </timeout>
    </ac>
</provider>
