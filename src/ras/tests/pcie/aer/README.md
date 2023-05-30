**Hardware Setups:**

1. In order to run the AER test cases, We need to have Pcie cards to be inserted in any of the socket


**Pre-requisites: (Mandatory)**
1. Before running the test cases, Please update the below configurations in Content_configuration.xml file,

**Path for file:** src/configuration/content_configuration.xml 
**Content to update:** 
<content><ras>
<aer_pcie_slot_info>
<socket>**_1,7_**</socket>
<pxp_port>**_pxp0.pcieg5.port2,pxp0.pcieg5.port2_**</pxp_port>
</aer_pcie_slot_info>
</ras></content>

** Please update the sockets and pcie ports(separated by Comma, if it is more than one socket or port) where the actual H/W is being inserted in which you want to inject error.