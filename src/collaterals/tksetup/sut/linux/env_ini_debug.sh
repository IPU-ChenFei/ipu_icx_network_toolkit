#！/usr/bin/sh
#date:2021-12-23

# set yum_repo
curl -o ./a.txt https://mirrors.aliyun.com/repo/Centos-8.repo --proxy child-prc.intel.com:913
if [ $? -ne 0 ];then
    echo ". . . . . . Error: network wrong!"
    exit 3
fi
sed '$aproxy=child-prc.intel.com:913' /etc/yum.conf
sh ./init_yum_repos.sh
yum install lm_sensors
yum install lm_sensors-devel
yum install acpica-tools
yum install hddtemp