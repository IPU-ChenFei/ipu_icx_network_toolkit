Configuiration:
Hardware Requirements:

VT-X and VT-D enabled on BIOS
SRIOV capable PCI Ethernet device for the complete supported list see here: 
https://www.intel.com/content/www/us/en/support/articles/000005722/network-and-io/ethernet-products.html
A server platform with an available PCI Express slot.

**************************************Note: Network Stress test using ilvss*******************************************
It is not feasible to automate the ilvss for network stressing, so this test
case is not using ilvss for network stress testing. (which was otherwise a
requirement for this TC)
***************************************Note: Network Stress test using ilvss******************************************

Software Requirements:
ILVSS tool = ilvss-3.6.25.run
ILVSS License = VSS_Site_01-01-2022_license.key
Prime tool = prime95.tar.gz