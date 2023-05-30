#!/usr/bin/env bash

#######################################################################
# When the installation begins, the client will query the DHCP server,
# obtain boot files from the TFTP server,
# and download the installation image from the HTTP, FTP or NFS server.
#
#
# This script just used for verifying nic pxe capability,
# not include the whole OS image installation
#
#
# Script Usage:
#    sh pxe_uefi_centos.sh 192.168.18.7 (pxe server addr)
#######################################################################



#######################################################################
# 0. RPM Package installation: dhcp-server, tftp-server, ftp-server, syslinux
#######################################################################

# Set proxy
echo ----------------------------------
echo Provide below proxy for reference
echo ----------------------------------
echo China: child-prc.intel.com:913
echo India: proxy01.iind.intel.com:911
echo America: proxy-us.intel.com:911
echo Common: proxy-chain.intel.com:911
echo ----------------------------------

unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY

if [ "$2" == "" ];then
  echo No need to set proxy
else
  if [ "$3" == "" ];then
    export HTTP_PROXY=$2
    export HTTP_PROXY=$2
  else
    export HTTP_PROXY=$2
    export HTTP_PROXY=$3
  fi
fi

# Intel Yum Repos
rm -rf /etc/yum.repos.d/*
cat <<EOF > /etc/yum.repos.d/intel-centos.repo
[centos-base]
name=centos base
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.2.0-GA/BaseOS/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[centos-optional]
name=centos optional
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.2.0-GA/CRB/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[centos-appstream]
name=centos appstream
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.2.0-GA/AppStream/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
EOF


# Setup Essential Servers
yum install -y dhcp-server
yum install -y tftp-server
yum install -y vsftpd
yum install -y syslinux


#######################################################################
# 1. Disable firewalld for simplicity
#######################################################################
systemctl stop firewalld
systemctl disable firewalld


#######################################################################
# 2. Setup DHCP Server: Assign ip for PXE client
#######################################################################
cat <<EOF > /etc/dhcp/dhcpd.conf
# DHCP Server Configuration file
# see /usr/share/doc/dhcp-server/dhcpd.conf.example
# see dhcpd.conf(5) man page
#

default-lease-time 600;
max-lease-time 7200;
ignore client-updates;
allow booting;
allow bootp;
allow unknown-clients;


# Initial Boot Files for PXE Clients
# Note: filename may change for different Linux OSes, such as shim.efi, pxelinux.0, ...
filename "grubx64.efi";
#next-server 0.0.0.0;


# Possible Subnets
subnet 192.168.1.0 netmask 255.255.255.0
{
  range 192.168.1.100 192.168.1.200;
}

subnet 192.168.2.0 netmask 255.255.255.0
{
  range 192.168.2.100 192.168.2.200;
}

subnet 192.168.3.0 netmask 255.255.255.0
{
  range 192.168.3.100 192.168.3.200;
}

subnet 192.168.4.0 netmask 255.255.255.0
{
  range 192.168.4.100 192.168.4.200;
}

subnet 192.168.5.0 netmask 255.255.255.0
{
  range 192.168.5.100 192.168.5.200;
}

subnet 192.168.6.0 netmask 255.255.255.0
{
  range 192.168.6.100 192.168.6.200;
}

subnet 192.168.7.0 netmask 255.255.255.0
{
  range 192.168.7.100 192.168.7.200;
}

subnet 192.168.8.0 netmask 255.255.255.0
{
  range 192.168.8.100 192.168.8.200;
}

subnet 192.168.9.0 netmask 255.255.255.0
{
  range 192.168.9.100 192.168.9.200;
}

subnet 192.168.10.0 netmask 255.255.255.0
{
  range 192.168.10.100 192.168.10.200;
}

subnet 192.168.11.0 netmask 255.255.255.0
{
  range 192.168.11.100 192.168.11.200;
}

subnet 192.168.12.0 netmask 255.255.255.0
{
  range 192.168.12.100 192.168.12.200;
}

subnet 192.168.13.0 netmask 255.255.255.0
{
  range 192.168.13.100 192.168.13.200;
}

subnet 192.168.14.0 netmask 255.255.255.0
{
  range 192.168.14.100 192.168.14.200;
}

subnet 192.168.15.0 netmask 255.255.255.0
{
  range 192.168.15.100 192.168.15.200;
}

subnet 192.168.16.0 netmask 255.255.255.0
{
  range 192.168.16.100 192.168.16.200;
}

subnet 192.168.17.0 netmask 255.255.255.0
{
  range 192.168.17.100 192.168.17.200;
}

subnet 192.168.18.0 netmask 255.255.255.0
{
  range 192.168.18.100 192.168.18.200;
}

subnet 192.168.19.0 netmask 255.255.255.0
{
  range 192.168.19.100 192.168.19.200;
}

subnet 192.168.20.0 netmask 255.255.255.0
{
  range 192.168.20.100 192.168.20.200;
}
EOF

IP=$1
echo "next-server $IP;" >> /etc/dhcp/dhcpd.conf

systemctl restart dhcpd.service

#######################################################################
# 3. Setup FTP Server: NFS/HTTPS/HTTP/FTP for exporting installation images
#######################################################################


#######################################################################
# 4. Setup TFTP Server: for network initial bootloaders
#######################################################################
/bin/cp -rf -v /usr/share/syslinux/* /var/lib/tftpboot

# Copy grubx64.efi to tftpboot, it maybe different in other OSes: CentOS/SLES/... (initial uefi bootloader)
/bin/cp -rf -v /boot/efi/EFI/centos/*.efi /var/lib/tftpboot

chmod 777 /var/lib/tftpboot/*

systemctl restart tftp.service


