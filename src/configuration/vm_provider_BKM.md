# BKM for build IOS images which support unattended installation

## Linux OS
### Introduction
The basic process is to get an ordinary OS release(ISO image) and prepare a kickstart file which contains the configuration needed during installation and build a new ISO image based on the original one and the kickstart file.
### Steps
 1. get an ordinary OS release(ISO image), taking RHEL iso as an example.
 2. Mount .iso file to SUT (/run/media/root/RHEL-8-2-0-BaseOS-x86_64 )
 3. Create a new iso folder on /root
	*#mkdir /root/iso*
4.	Copy Redhat8.2 iso files to iso folder
	*#cp -ar /run/media/root/RHEL-8-2-0-BaseOS-x86_64/  /root/iso/*
5.	Configure kickstart ks.cfg file by following https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/installation_guide/s1-kickstart2-file
6.	Copy ks.cfg file to /root/iso/
	*#cp ks.cfg /root/iso/*
7.	Add "**ks=cdrom:/ks.cfg**" into isolinux.cfg file
	*#vim /root/iso/isolinux/isolinux.cfg*
	*label linux
	  menu label ^Install Redhat8.2 x64 System.   
	  menu default
	  kernel vmlinuz
	  append initrd=initrd.img **ks=cdrom:/ks.cfg***  
8.	Go to the new iso directory
	*#cd /root/iso*
9.	Install mkisofs package
	*#yum install mkisofs*
10. Encapsulate the target iso image: **Redhat-8-2.iso**
	*#mkisofs -o /root/**Redhat-8-2.iso** -V redhat8 -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -R -J -T -v *
### Reference: 
http://www.softpanorama.org/Commercial_linuxes/RHEL/Installation/Kickstart/modifing_iso_image_to_include_kickstart_file.shtml

## Windows OS

### Introduction
If you want to automate a Windows install, you must create a .XML file containing the responses to any prompts for input. Microsoft provides a tool to create these .XML files. It's called the Windows System Image Manager (WSIM). Once you got the .XML, you can build a new ISO image by using the .XML and the original ISO image.

### Steps
Go to the [vm_provider_BKM_for_Windows.docx](vm_provider_BKM_for_Windows.docx) for the details.

### Reference
https://taylor.dev/how-to-create-an-automated-install-for-windows-server-2019/