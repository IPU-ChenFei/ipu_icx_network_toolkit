For test case PI_Virtualization_PassThroughUSB_L_CannotRemote,

1) We need to connect USB drive to the banino board and USB switching should be enabled. 
2) We need to update connected USB BCD value in the content_configuration.xml under tags,
usb->device->type as Mass Storage for USB and usb->device->bcd.
we will get the bcd value of the connected USB in lsusb command :
3) We need to update the memory_size, no_of_cpu, disk_size, image_host_location in the content_configuration.xml under 
tags, virtualization->linux->RHEL->ISO
 