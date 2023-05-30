Test that all the memory in the system can be allocated and to test ESX's ability to overcommit a certain amount of memory.

Before you begin testing, verify that the correct amount of memory in the system is correct.  If there are special memory settings on the BIOS that is set, ensure that VMware is correctly seeing them.
All memory can be allocated based on the memory setup on BIOS..

Step 0
Create and assign enough virtual machines with VMtools installed to have more memory than the system has.  A couple of gigabyes should suffice.  For example, if the SUT has 32Gb of total RAM, assign the virtual machines to have a sum of 34Gb of RAM.
No error is encountered.
Step 1
Power on the virtual machines.
No error is encountered.
Step 2
On vSphere/vCenter, click on the performance tab and select memory Memory in the "switch to" drop down.vCenter will require you to click on Advanced before you see the Switch to Drop down.On the Key below, there should be a measurement for balloon and it should currently have values of 0.
The Balloon "driver" is inactive.
Step 3
Using a memory stress test, begin full memory stress test on all virtual machines.Once the memory is fully stressed, there should be  metric values for the Balloon driver. This will indicate that the Balloon driver is working and that ESX is swapping extra memory into the hard drive.
The Balloon driver should begin showing values in the Performance measurements indicating that memory is being over commited.
Step 4
Allow the system to stress for a few hours to ensure that the balloon driver is properly working