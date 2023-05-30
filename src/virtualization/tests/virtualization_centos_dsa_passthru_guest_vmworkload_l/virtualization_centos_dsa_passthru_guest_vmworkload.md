===========================================================================================
This TC requires below settings to be enabled on the SUT
===========================================================================================
Current TC Status: Not working as Manually it is not passing, to be updated once Steps are provided.

Verify the following BIOS settings. 

EDKII Menu > Socket Configuration > IIO configuration > PCIe ENQCMD > ENQCMDS = enabled 
EDKII Menu > Socket Configuraiton > IIO Configuration >IOAT configuration >socket <n> IOAT configure > DSA = enabled 
EDKII Menu > Socket Configuraiton > IIO Configuration > VT-d = enabled 
EDKII Menu > Socket Configuration > Processor Configuration > VMX = enabled

kernel command line of host :
[root@embargo spr-po-qemu]# cat /proc/cmdline
BOOT_IMAGE=(hd0,gpt2)/vmlinuz-5.12.0-0507.intel_next.08_16.2_po.36.x86_64+server root=/dev/mapper/cl-root ro crashkernel=auto resume=/dev/mapper/cl-swap rd.lvm.lv=cl/root rd.lvm.lv=cl/swap rhgb quiet intel_iommu=on,sm_on iommu=on ats_with_iommu_swizzle

kernel command line of guest VM :
[root@embargo ~]# cat /proc/cmdline
BOOT_IMAGE=(hd0,gpt2)/vmlinuz-5.12.0-0507.intel_next.08_16.2_po.36.x86_64+server root=UUID=0307c09b-cabe-47da-af87-67a7df45fe6a ro rhgb console=tty0 console=ttyS0,115200n8 earlyprintk=ttyS0,115200n8 intel_iommu=on,sm_on ats_with_iommu_swizzle iommu=pt no5lvl
