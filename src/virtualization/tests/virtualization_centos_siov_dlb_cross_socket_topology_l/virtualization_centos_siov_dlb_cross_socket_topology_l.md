Enable following BIOS settings

EDKII Menu -> Socket Configuration ->Processor Configuration -> VMX -> Enable

EDKII Menu -> Socket Configuration -> IIO Configuration -> Intel VT for Directed I/O (VT-d)  -> Yes

EDKII Menu -> Socket Configuration -> IIO Configuration -> PCIe ENQCMD/ENQCMDS -> Yes

EDKII Menu > Socket Configuraiton > IIO Configuration >IOAT configuration >socket <n> IOAT configure > HQM = enabled 

Host kernel cmdline :
-------------------------
[root@localhost ~]# cat /proc/cmdline

BOOT_IMAGE=(hd1,gpt2)/vmlinuz-5.12.0-0507.intel_next.08_16.2_po.36.x86_64+server root=/dev/mapper/cl-root ro crashkernel=auto resume=/dev/mapper/cl-swap rd.lvm.lv=cl/root rd.lvm.lv=cl/swap rhgb quiet intel_iommu=on,sm_on iommu=on

Guest kernel cmdline :
------------------------
[root@embargo ~]# cat /proc/cmdline

BOOT_IMAGE=(hd0,msdos1)/vmlinuz-5.12.0-0507.intel_next.08_16.2_po.36.x86_64+server root=/dev/mapper/cl-root ro crashkernel=auto resume=/dev/mapper/cl-swap rd.lvm.lv=cl/root rd.lvm.lv=cl/swap rhgb quiet console=tty0 console=ttyS0,115200,8n1 intel_iommu=on,sm_on iommu=pt no5lvl idle=poll