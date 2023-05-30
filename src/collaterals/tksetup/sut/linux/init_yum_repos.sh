#!/bin/bash
# A script to set up a linux server to use linux.ftp.intel.com.

if [ -z "$LINUX_FTP" ]; then
    # set default linux-ftp
    LINUX_FTP='linux-ftp.jf.intel.com'
fi

function fedora_setup(){
    echo 'Setting up for Fedora... '
    os_version=`cat /etc/fedora-release | awk '{print $3}'`
    rm -rf /etc/yum.repos.d/*
    cat <<EOF > /etc/yum.repos.d/intel-rhel8.repo
[rhel8-base]
name=rhel8 base
baseurl=https://linux-ftp.jf.intel.com/pub/mirrors/fedora/linux/releases/$os_version/Server/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-optional]
name=rhel8 optional
baseurl=https://linux-ftp.jf.intel.com/pub/mirrors/fedora/linux/releases/$os_version/Server/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-appstream]
name=rhel8 appstream
baseurl=https://linux-ftp.jf.intel.com/pub/mirrors/fedora/linux/releases/$os_version/Server/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
EOF
}

function centos_setup(){
    echo 'Setting up for CentOS... '
    os_version=`cat /etc/redhat-release | awk '{print $6}'`
    rm -rf /etc/yum.repos.d/*
    cat <<EOF > /etc/yum.repos.d/intel-centos.repo
[centos-base]
name=centos base
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-$os_version.0-GA/BaseOS/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[centos-optional]
name=centos optional
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-$os_version.0-GA/CRB/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[centos-appstream]
name=centos appstream
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-$os_version.0-GA/AppStream/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
EOF
}

function debian_setup(){
    echo 'Setting up for Debian... '
    codename=$(lsb_release -cs)
    debian_like_setup "$codename ${codename}-updates ${codename}-backports" "main contrib"
}

function opensuse_setup(){
    echo  'Setting up for OpenSuSE... '
    zypper lr -d | grep $LINUX_FTP > /dev/null 2>&1
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "Backing up config files..."
        echo "Old config files will be found in /etc/zypp/repos.d.$(date +%Y%m%d).bak "
        mv -f /etc/zypp/repos.d /etc/zypp/repos.d.$(date +%Y%m%d).bak > /dev/null 2>&1
        mkdir /etc/zypp/repos.d/
        zypper ar "http://${LINUX_FTP}/pub/mirrors/opensuse/distribution/leap/${VERSION}/repo/non-oss/" non-oss >/dev/null
        zypper ar "http://${LINUX_FTP}/pub/mirrors/opensuse/distribution/leap/${VERSION}/repo/oss/" oss >/dev/null
        zypper ar "http://${LINUX_FTP}/pub/mirrors/opensuse/update/leap/${VERSION}/non-oss/" update-non-oss >/dev/null
        zypper ar "http://${LINUX_FTP}/pub/mirrors/opensuse/update/leap/${VERSION}/oss/" update-oss >/dev/null
        zypper refresh > /dev/null
        echo 'DONE!'
    else
        echo 'N/A'
        echo
        echo "This system is already configured for ${LINUX_FTP}."
    fi
    
}

function ubuntu_setup(){
    echo 'Setting up for Ubuntu... '
    codename=$(lsb_release -cs)
    debian_like_setup "$codename ${codename}-updates ${codename}-security ${codename}-backports" "main restricted universe multiverse"
}


function debian_like_setup(){
    suites=$1
    components=$2
    codename=$(lsb_release -cs)
    apt-cache policy |grep $LINUX_FTP > /dev/null 2>&1
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "Backing up config files..."
        echo "Old config files will be found in /etc/apt/ with .$(date +%Y%m%d).bak appended."
        mv /etc/apt/sources.list /etc/apt/sources.list.$(date +%Y%m%d).bak
        mv /etc/apt/apt.conf /etc/apt/apt.conf.$(date +%Y%m%d).bak
        for suite in $suites; do
            for component in $components; do
                echo "deb http://${LINUX_FTP}/pub/mirrors/${ID} $suite $component" >> /etc/apt/sources.list
            done
        done
        echo "Acquire::http::Proxy::$LINUX_FTP \"DIRECT\";" >> /etc/apt/apt.conf
        echo "Acquire::https::Proxy::$LINUX_FTP \"DIRECT\";" >> /etc/apt/apt.conf
        echo "Acquire::http::Proxy \"http://proxy-dmz.intel.com:911\";" >> /etc/apt/apt.conf
        echo "Acquire::https::Proxy \"http://proxy-dmz.intel.com:912\";" >> /etc/apt/apt.conf
        apt-get update > /dev/null 2>&1
        echo 'DONE!'
    else
        echo 'N/A'
        echo
        echo "This system is already configured for ${LINUX_FTP}."
    fi

}



function rhel_setup(){
    echo 'Setting up for RedHat... '
    os_version=`cat /etc/redhat-release | awk '{print $6}'`
    rm -rf /etc/yum.repos.d/*
    cat <<EOF > /etc/yum.repos.d/intel-rhel8.repo
[rhel8-base]
name=rhel8 base
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-$os_version.0/BaseOS/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-optional]
name=rhel8 optional
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-$os_version.0-GA/CRB/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[rhel8-appstream]
name=rhel8 appstream
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-$os_version.0-GA/AppStream/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
EOF
}

###MAIN SCRIPT###
echo "This script will configure your system to use $LINUX_FTP for your OS repositories."
echo "If you encounter issues, please file a ticket at: https://opensource.intel.com/jira/servicedesk/customer/portal/1"

if [ -f /etc/os-release ]; then
    . /etc/os-release
else
    echo "Error: Cannot determine OS release.  Exiting." >&2
    exit 1
fi

if [ $(id -u) -ne 0 ]; then 
    echo "Error: This script must be run as sudo/root.  Exiting." >&2
    exit 1
fi

# ID is sourced from /etc/os-release
# call one of the above setup functions.
${ID}_setup 2>/dev/null
ret=$?

if [ $ret -eq 127 ]; then
    echo "Error: unsupported OS.  Exiting."
    exit 1
fi

