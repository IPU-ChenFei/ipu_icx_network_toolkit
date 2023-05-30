#!/bin/bash

# reset password
#esxcli system account set -i root -p intel@123 -c intel@123

# set ipv4
#esxcli network ip interface ipv4 set -i vmk0 -I 192.168.0.2 -N 255.255.255.0 -t static

# disable firewall
esxcli network firewall set --enabled false

# print promption info
echo "---------------------------------------------------------------------------"
echo "|                               PROMPTION                                 |"
echo "---------------------------------------------------------------------------"
echo "| Don't forget to check your ssh communication network port, if use dhcp, |"
echo "| make sure it works fine; if use back-to-back connection to sut, make    |"
echo "| sure the internal static ip  address is assigned, such as 192.168.1.x   |"
echo "| And also, you need to configure this ip address to host config file:    |"
echo "| sut.ini/[sutos] section.                                                |"
echo "---------------------------------------------------------------------------"
