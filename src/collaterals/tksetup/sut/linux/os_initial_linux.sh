#！/usr/bin/sh
#date:2021-05-19
basepath=`dirname $0`
toolpath=/home/BKCPkg/tools
tools_url=sut_linux_tools.txt
sut_linux_tools=https://ubit-artifactory-sh.intel.com/artifactory/validationtools-sh-local/env/sut/linux/$tools_url

rm -rf $toolpath

if [ ! -d $toolpath ];then
  mkdir -p $toolpath
fi

# 1. init intel yum repos
cd $basepath
dos2unix ./init_yum_repos.sh
sh ./init_yum_repos.sh

# 1.download tools from artifactory
yum install -y wget
cd $toolpath
wget $sut_linux_tools --no-check-certificate
wget -i $tools_url --no-check-certificate

# 2.install python36 interpreter
cd $toolpath
rpm -ivh python3-setuptools-39.2.0-5.el8.noarch.rpm --force --nodeps
rpm -ivh python3-pip-9.0.3-16.el8.noarch.rpm --force --nodeps
rpm -ivh python36-3.6.8-2.module+el8.1.0+3334+5cb623d7.x86_64.rpm --force --nodeps
ln -s /usr/bin/python3 /usr/bin/python
cp $toolpath/set_toolkit_src_root.py /usr/lib64/python3.6/site-packages

# 3.copy xmlcli tool
cd $toolpath
xmlcli_zip=`ls | grep xmlcli`
echo $xmlcli_zip
xmlcli_name=${xmlcli_zip%.zip}
xmlcli_zip_fqdn=$toolpath/$xmlcli_zip
dst_dir='/opt/APP'

if [ ! -d $dst_dir ];then
  mkdir -p $dst_dir
fi

if [ -d $xmlcli_name ];then
  rm -rf $xmlcli_name
fi

unzip $xmlcli_zip_fqdn > sut_init.log && \
/usr/bin/cp -rf xmlcli $dst_dir && \
rm -rf $xmlcli_name
if [ $? -eq 0 ];then
  echo ". . . . . . init xmlcli tool Successfully!"
else
  echo ". . . . . . Error: init xmlcli tool Failed!"
fi

# 4.install uefi tools
efixmlcli_fqdn=$toolpath/XmlCliKnobs.efi
cmdtool_wht=$toolpath/cmdtool_wht.efi
cmdtool_egs=$toolpath/cmdtool_egs.efi
dst_dir='/boot/efi/bkc_tool'

if [ ! -d $dst_dir ];then
  mkdir -p $dst_dir
fi

/usr/bin/cp -a cmdtool_wht $dst_dir
if [ $? -eq 0 ];then
  echo ". . . . . . copy cmdtool_wht.efi tool Successfully!"
else
  echo ". . . . . . Error: copy cmdtool_wht.efi tool Failed!"
fi
/usr/bin/cp -a cmdtool_egs $dst_dir
if [ $? -eq 0 ];then
  echo ". . . . . . copy cmdtool_egs.efi tool Successfully!"
else
  echo ". . . . . . Error: copy cmdtool_egs.efi tool Failed!"
fi
/usr/bin/cp -a $efixmlcli_fqdn $dst_dir
if [ $? -eq 0 ];then
  echo ". . . . . . init XmlCliKnobs.efi tool Successfully!"
else
  echo ". . . . . . Error: init XmlCliKnobs.efi tool Failed!"
fi

# 5.install screen for async cmd execution
screen_name=`ls | grep screen-.*x86_64.rpm`
screen_name_fqdn=$toolpath/$screen_name
for i in $(seq 3);do
  rpm -ivh $screen_name_fqdn >> sut_init.log 2>&1
  rpm -qa screen >> sut_init.log
  if [ $? -eq 0 ];then
    echo ". . . . . . install screen Successfully!"
    break
  else
    if [ $i -eq 3 ];then
      echo ". . . . . . Error: install screen Failed!"
      exit 4
    fi
  fi
done

# 7.shutdown firewall and selinux
systemctl stop firewalld
systemctl disable firewalld
if [ $? -eq 0 ];then
  echo ". . . . . . disable firewalld Successfully!"
else
  echo ". . . . . . disable firewalld Failed!"
  exit 6
fi

se_flag=0
se_file='/etc/selinux/config'
selinux_option=$(cat /etc/selinux/config |grep "^SELINUX="|awk -F"=" '{print $2}')
if [ $selinux_option != 'disabled' ];then
  sed -i '/^SELINUX=/{s/SELINUX=.*/SELINUX=disabled/}' $se_file
  if [ $? -eq 0 ];then
  echo ". . . . . . disable selinux Successfully!"
  else
  echo ". . . . . . disable selinux Failed!"
  exit 7
  fi
  se_flag=1
else
  echo ". . . . . . selinux is already Disabled!"
fi

# 9.reboot when selinux config is changed
if [ $se_flag -eq 1 ];then
  for i in 3 2 1;do
    echo "\n system will rboot after $i seconds ..."
    sleep 1
  done
  reboot
fi

# 10.install ipmitool tools
cd $toolpath
rpm -ivh ipmitool-1.8.18-14.el8.x86_64.rpm --force --nodeps
rpm -ivh OpenIPMI-2.0.27-1.el8.x86_64.rpm --force --nodeps

# 11. print promption info
echo "---------------------------------------------------------------------------"
echo "|                               PROMPTION                                 |"
echo "---------------------------------------------------------------------------"
echo "| Don't forget to check your ssh communication network port, if use dhcp, |"
echo "| make sure it works fine; if use back-to-back connection to sut, make    |"
echo "| sure the internal static ip  address is assigned, such as 192.168.1.x   |"
echo "| And also, you need to configure this ip address to host config file:    |"
echo "| sut.ini/[sutos] section.                                                |"
echo "---------------------------------------------------------------------------"
