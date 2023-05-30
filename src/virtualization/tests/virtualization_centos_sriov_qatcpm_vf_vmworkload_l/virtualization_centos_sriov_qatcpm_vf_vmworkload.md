Make sure VT-d, SR-IOV & QAT accelertor enabled thru BIOS settigns
- EDKII Menu -> Socket Configuration -> IIO Configuration -> Intel VT for Directed I/O (VT-d)  -> Yes   
- EDKII Menu -> Platform Configuration -> Miscellaneous Configuration -> SR-IOV Support  -> [Enable]

- Enable QAT accelerator thru below
   EDKII Menu -> Socket Configuration -> IIO Configuration -> IOAT Configuration > Sck0 IOAT Config
   EDKII Menu -> Socket Configuration -> IIO Configuration -> IOAT Configuration > Sck1 IOAT Config

Make sure to set kernel command line parameter intel_iommu=on,sm_on
Verify current kernel boot parameter via ‘cat /proc/cmdline’. 
If needed, modify ‘/etc/default/grub’ file to set required value, then run ‘grub2-mkconfig -o /etc/grub2-efi.cfg’ and do reboot/power cycle.