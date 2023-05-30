Purpose of this test case is to configure SIOV using QAT and run workload on host and VM simultaneously.

Please use CentOS Embargo Server Image for host and VM both with all kernel devel packages [headers and sources].
This also requires the kernel devel package to be installed as per the Image kernel version==>
dnf install https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202109221317/repo/x86_64/kernel-next-server-devel-5.12.0-2021.05.07_39.el8.x86_64.rpm

so first need to check the kernel version and then install devel package of same version as per the path below ==> 
https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202109221317/repo/x86_64/kernel-next-server-devel-*
https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/{$BKC_NUMBER_of_image}/repo/x86_64/kernel-next-server-devel-*

Make sure VT-d, SR-IOV & QAT accelertor enabled thru BIOS settigns
- EDKII Menu -> Socket Configuration -> IIO Configuration -> Intel VT for Directed I/O (VT-d)  -> Yes   
- EDKII Menu -> Platform Configuration -> Miscellaneous Configuration -> SR-IOV Support  -> [Enable]

- Enable QAT accelerator thru below
   EDKII Menu -> Socket Configuration -> IIO Configuration -> IOAT Configuration > Sck0 IOAT Config
   EDKII Menu -> Socket Configuration -> IIO Configuration -> IOAT Configuration > Sck1 IOAT Config

Make sure to set kernel command line parameter intel_iommu=on,sm_on
Verify current kernel boot parameter via ‘cat /proc/cmdline’. 
If needed, modify ‘/etc/default/grub’ file to set required value, then run ‘grub2-mkconfig -o /etc/grub2-efi.cfg’ and do reboot/power cycle.