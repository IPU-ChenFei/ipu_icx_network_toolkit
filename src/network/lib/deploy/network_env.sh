#!/bin/bash
toolpath=/home/BKCPkg/domains/network

# Download tools
scp -r root@10.239.115.67:/localdisk/test_tools/network/linux/* $toolpath
chmod 777 $toolpath/*

# Intel Proxy
export http_proxy=child-prc.intel.com:913
export https_proxy=child-prc.intel.com:913


# Intel Yum Repos
rm -rf /etc/yum.repos.d/*
version=`cat /etc/redhat-release | awk '{print $6}'`

if [ $version == "8.0" ]; then
cat <<EOF > /etc/yum.repos.d/intel-rhel8.repo
[rhel8-base]
name=rhel8 base
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.0.0-GA/BaseOS/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-optional]
name=rhel8 optional
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.0.0-GA/CRB/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-appstream]
name=rhel8 appstream
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.0.0-GA/AppStream/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
EOF
elif [ $version == "8.1" ]; then
cat <<EOF > /etc/yum.repos.d/intel-rhel8.repo
[rhel8-base]
name=rhel8 base
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.1.0-GA/BaseOS/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-optional]
name=rhel8 optional
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.1.0-GA/CRB/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-appstream]
name=rhel8 appstream
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.1.0-GA/AppStream/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
EOF
elif [ $version == "8.2" ]; then
cat <<EOF > /etc/yum.repos.d/intel-rhel8.repo
[rhel8-base]
name=rhel8 base
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.2.0-GA/BaseOS/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-optional]
name=rhel8 optional
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.2.0-GA/CRB/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-appstream]
name=rhel8 appstream
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.2.0-GA/AppStream/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
EOF
elif [ $version == "8.3" ]; then
cat <<EOF > /etc/yum.repos.d/intel-rhel8.repo
[rhel8-base]
name=rhel8 base
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.3.0-GA/BaseOS/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-optional]
name=rhel8 optional
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.3.0-GA/CRB/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-appstream]
name=rhel8 appstream
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.3.0-GA/AppStream/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
EOF
elif [ $version == "8.4" ]; then
cat <<EOF > /etc/yum.repos.d/intel-rhel8.repo
[rhel8-base]
name=rhel8 base
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.4.0-GA/BaseOS/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-optional]
name=rhel8 optional
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.4.0-GA/CRB/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-appstream]
name=rhel8 appstream
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-8.4.0-GA/AppStream/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
EOF
fi

# Set PXE Environment
sh $toolpath/pxe_uefi_redhat.sh

# install ilvss
tar -zxvf $toolpath/ilvss/ilvss-3.6.23.tar.gz
chmod +x $toolpath/ilvss-3.6.23/*
cd $toolpath/ilvss-3.6.23 && ./install --nodeps
cp $toolpath/ilvss/license.key $toolpath/ilvss-3.6.23
date -s "2021-09-01 00:00:00"

# install iperf3
rpm -ivh $toolpath/iperf3-3.1.3-1.fc24.x86_64.rpm --force --nodeps

# install Mellanox Driver
#yum install gcc-gfortran tcsh kernel-modules-extra tk
#tar -xvf $toolpath/MLNX_OFED_LINUX-5.4-1.0.3.0-rhel8.2-x86_64.tgz
#chmod +x $toolpath/MLNX_OFED_LINUX-5.4-1.0.3.0-rhel8.2-x86_64
#cd $toolpath/MLNX_OFED_LINUX-5.4-1.0.3.0-rhel8.2-x86_64 && ./mlnxofedinstall
#rmmod rpcrdma
#rmmod ib_srpt
#rmmod ib_isert
#rmmod i40iw
#cd /home/BKCPkg/domains/network/MLNX_OFED_LINUX-5.4-1.0.3.0-rhel8.2-x86_64 && ./mlnxofedinstall

# install vm
rpm -ivh $toolpath/kernel-modules-extra-4.18.0-193.el8.x86_64.rpm --force --nodeps
rpm -ivh $toolpath/python3-pexpect-4.3.1-3.el8.noarch.rpm --force --nodeps
rpm -ivh $toolpath/python3-ptyprocess-0.5.2-4.el8.noarch.rpm --force --nodeps

# install fio
# firstly check if fio is already installed, if return 0, then no need to install again
rpm -qa | grep -i fio
if [ $? -eq 0 ]; then
  echo "fio already installed"
else
  yum -y install fio
fi

# install libpcap*
# firstly check if libpcap* is already installed, if return 0, then no need to install again
rpm -qa | grep -i libpcap*
if [ $? -eq 0 ]; then
  echo "libpcap* already installed"
else
  yum -y install libpcap*
fi

# modify cmd "cp"
echo "unalias cp" >> ~/.bash_profile
source ~/.bash_profile