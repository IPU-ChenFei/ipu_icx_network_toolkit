#!/bin/bash

cd /home/administrator

dos2unix grub.txt

pwd=$1

echo ${pwd} | sudo -S dpkg -i linux-*

sleep 30s

var_1="$(cat /home/administrator/grub.txt)"

echo $var_1

echo ${pwd} | sudo -S sed -i "/GRUB_CMDLINE_LINUX_DEFAULT/c ${var_1}" /etc/default/grub
sleep 5s

echo ${pwd} | sudo -S update-grub
sleep 5s

echo ${pwd} | sudo -S sed -i -e 's/panic=-1//' /boot/grub/grub.cfg
sleep 5s
