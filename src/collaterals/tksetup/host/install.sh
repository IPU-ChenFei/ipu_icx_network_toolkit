#!/bin/bash
toolpath=`dirname $0`/tools
pip_dir=/root/pip
pip_ini=$pip_dir/pip.ini

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

if [ "$1" == "" ];then
  echo No need to set proxy
else
  if [ "$2" == "" ];then
    export http_proxy=$1
    export https_proxy=$1
  else
    export http_proxy=$1
    export https_proxy=$2
  fi
fi

# Disable firewall
systemctl stop firewalld
systemctl disable firewalld

echo "gsettings set org.gnome.desktop.session idle-delay 0" >>/etc/profile
echo "gsettings set org.gnome.desktop.screensaver lock-enabled false" >>/etc/profile
source /etc/profile


# install python3
tar -zxvf $toolpath/Python-3.6.8.tgz
chmod +x $toolpath/Python-3.6.8/*
cd $toolpath/Python-3.6.8 && ./configure

ln -s /usr/bin/python3 /usr/bin/python


# configure pip
if [ ! -d $pip_dir ];then
  mkdir $pip_dir
fi

echo [global] > $pip_ini
echo index-url = https://af01p-png.devtools.intel.com/artifactory/api/pypi/dtaf-framework-release-png-local/simple >> $pip_ini
echo extra-index-url = https://pypi.org/simple >> $pip_ini
echo proxy = http://child-prc.intel.com:913 >> $pip_ini

python -m pip3 install --upgrade pip3


# install python libs
pip install --upgrade dtaf-core
pip install xmltodict wcwidth pathlib2 artifactory anybadge
pip install pyqt5 pywin32 prettytable
