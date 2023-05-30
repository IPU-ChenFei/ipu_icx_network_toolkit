The objective to this TC is to verify that VT-d (or also knowned as VMdirectPath) functions properly and
that the virtual machine that is assigned to the device is able to see the device.

Configuiration:
This requires vSphere to be installed on a management system and ESXi 4.0 or above on the SUT. SUT must also support VT-d.

Tester may also want to obtain the drivers (windows/linux/etc) for the device that will be used for VT-d testing for use in the VM as
VMtools will not take care of that.

NOTE: Do not use VT-d (SRIOV - Pass-through) on the NIC ports that the Service Console resides on. Meaning, 
if the device is a 4 port NIC and one of them is the service console, do not use VT-d on any of those ports. 
Doing so may render the service console useless.