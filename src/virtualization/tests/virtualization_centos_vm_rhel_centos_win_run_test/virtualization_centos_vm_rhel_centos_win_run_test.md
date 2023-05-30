Please make sure of the following before running the testcase:

1. Make sure VT-d, VMX enabled thru BIOS settigns
- EDKII Menu -> Socket Configuration -> IIO Configuration -> Intel VT for Directed I/O (VT-d)  -> Yes   

2. Sets and verifies host is CentOS + Intel next
3. Requires Fully populated memory config - 2 DPC with Max Storage (2 - PCIe gen 4 NVMe )
4. Make sure to set kernel command line parameter intel_iommu=on,sm_on