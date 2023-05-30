
import os
import re

#Setting proxy for yum install

def mprint(item):
        print("\n\n","-"*7,item)

def mprint2(item):
        print("-"*30)
        print(item)
        print("-"*30)

def mprint3():
    print("\n", "-"*30, "\n")



def set_proxy():
    mprint("Setting temp proxy")
    #os.system("export http_proxy=http://proxy-prc.intel.com:911")
    #os.system("export ftp_proxy=http://proxy-prc.intel.com:911")
    #os.system("export https_proxy=https://proxy-prc.intel.com:912")
    #os.system("export  no_proxy=intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,.local,127.0.0.0/8,134.134.0.0/16")
    
    os.environ['http_proxy']='http://proxy-prc.intel.com:913'
    os.environ['ftp_proxy']='http://proxy-prc.intel.com:913'
    os.environ['https_proxy']='http://proxy-prc.intel.com:913'
    os.environ['no_proxy']='no_proxy=intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,.local,127.0.0.0/8,134.134.0.0/16'
    os.system("env | grep proxy")


#Clear and download redhat repos

def check_OS_version():

    mprint("Checking OS type and verison")
    OS_version = os.popen("cat /etc/*release")

    OS_version = OS_version.read()
    
    OS=[]

    for line in OS_version.splitlines():
        if "ID=" in line:
            OS.append(line.split("ID=")[1].replace('"',''))
        if "VERSION_ID=" in line:
            OS.append(line.split("VERSION_ID=")[1].replace('"',''))
    OS_version = OS[0]+"-"+OS[1]
    print(OS_version)
    print("change format for repo:")
    OS_version = OS_version.upper()+".0-GA"
    print(OS_version)
    return OS_version

    
def download_repos(OS_version):
    
    
    OS = OS_version
    if "RHEL" in OS:
        mprint("Backing up the original repos: ")
        backup_exist=os.path.exists("/etc/yum.repos.d/org_repo.tar.gz")
        if backup_exist:
            os.system("rm -rf /etc/yum.repos.d/*.repo")
            print("yum repo files has already been backup !")
        else: 
            os.system("tar -czf /etc/yum.repos.d/org_repo.tar.gz /etc/yum.repos.d/*.repo")
            os.system("rm -rf /etc/yum.repos.d/*.repo")

        mprint(f"Downloading the repos for {OS}")
        os.system(f"wget http://linux-ftp.intel.com/pub/ISO/redhat/redhat-rhel/{OS}/RHEL-8-appstream.repo  -O /etc/yum.repos.d/RHEL-8-appstream.repo")
        os.system(f"wget http://linux-ftp.intel.com/pub/ISO/redhat/redhat-rhel/{OS}/RHEL-8-baseos.repo  -O /etc/yum.repos.d/RHEL-8-baseos.repo")
        os.system(f"wget http://linux-ftp.intel.com/pub/ISO/redhat/redhat-rhel/{OS}/RHEL-8-crb.repo  -O /etc/yum.repos.d/RHEL-8-crb.repo")
        os.system(f"wget http://linux-ftp.intel.com/pub/ISO/redhat/redhat-rhel/{OS}/RHEL-8-highavailability.repo  -O /etc/yum.repos.d/RHEL-8-highavailability.repo")
        os.system(f"wget http://linux-ftp.intel.com/pub/ISO/redhat/redhat-rhel/{OS}/RHEL-8-rt.repo  -O /etc/yum.repos.d/RHEL-8-rt.repo")
        os.system(f"wget http://linux-ftp.intel.com/pub/ISO/redhat/redhat-rhel/{OS}/RHEL-8-sap.repo  -O /etc/yum.repos.d/RHEL-8-sap.repo")
        os.system(f"wget http://linux-ftp.intel.com/pub/ISO/redhat/redhat-rhel/{OS}/RHEL-8-saphana.repo  -O /etc/yum.repos.d/RHEL-8-saphana.repo")

        #Create an epel repo manually
        epel="""
                [epel]
                baseurl = http://linux-ftp.jf.intel.com/pub/mirrors/fedora-epel/8/Everything/x86_64/
                enabled = 1
                gpgcheck = 0
                gpgkey = file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8
                name = Extra Packages for Enterprise Linux 8 - x86_64
                
                [epel-debuginfo]
                baseurl = http://linux-ftp.jf.intel.com/pub/mirrors/fedora-epel/8/Everything/x86_64//debug/
                enabled = 0
                gpgcheck = 1
                gpgkey = file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8
                name = Extra Packages for Enterprise Linux 8 - x86_64 - Debug
                
                [epel-source]
                baseurl = http://linux-ftp.jf.intel.com/pub/mirrors/fedora-epel/8/Everything/SRPMS/
                enabled = 0
                gpgcheck = 1
                gpgkey = file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8
                name = Extra Packages for Enterprise Linux 8 - x86_64 - Source
                """
        epel_content=[]
        for line in epel.split('\n'):
            os.system(f"echo {line} >> /etc/yum.repos.d/epel.repo")
        mprint("epel repo created!")
    elif "centos" or "CENTOS" in OS:
        print(f"Do nothing to the original repos for CentOS")
        pass
    else:
        mprint(f"Error:  {OS} is not POR OS for BKC test! pls check! ")
        raise



def check_tool_installation(tool_name):
    tool = tool_name
    mprint("Checking tool installation:")
    result=os.popen(f"whereis {tool}")
    result=result.read()
    rpm_check_return=os.popen(f"rpm -qa |grep {tool}").read()
    rpm_check_flag = len(rpm_check_return)
    if re.findall(r'/usr/bin',result) or re.findall(r'/usr/sbin',result) or rpm_check_flag:
        print(f"Tool:[ {tool} ] has been installed")
        print(result)
        print(rpm_check_return)
        return True
    else:
        print(f"Tool:[ {tool} ] has not been installed !")
        return False


def yum_install_packages(yum_install_pkg_list):
    mprint("Installing some tools by yum:")
    pkg_list=yum_install_pkg_list
    for item in pkg_list:
        if not check_tool_installation(item):
            mprint(f"Installing the tool:{item}")
            os.system(f"yum install --nobest -y {item}")
            mprint(f"Installing the tool: [ {item} ], Done! ")

def install_source_code_packages(source_code_pkg_list):
    tool_list = source_code_pkg_list
    mprint("Installing source code packages....")
    for item in tool_list:
        if "prime95" in item:
            print(f"Installing [ {item} ] ")
            os.system("mkdir -p /opt/prime95/")
            os.system(" wget http://www.mersenne.org/ftp_root/gimps/p95v308b9.linux64.tar.gz -O /opt/prime95/p95v308b9.linux64.tar.gz --no-check-certificate ")
            os.system("tar -zxvf /opt/prime95/p95v308b9.linux64.tar.gz -C /opt/prime95")
    

def install_rpm_packages(rpm_install_tool_name):
    mprint("Installing some tools by rpm packages:")
    pkg_list = rpm_install_tool_name
    for item in pkg_list:
        if "docker" in item and not check_tool_installation(item):
            mprint(f"Installing the tool:[ {item} ], start! ")
            os.system("mkdir -p /opt/docker_pkgs/")
            os.system("wget https://download.docker.com/linux/centos/8/x86_64/stable/Packages/containerd.io-1.5.11-3.1.el8.x86_64.rpm -O /opt/docker_pkgs/containerd.io-1.5.11-3.1.el8.x86_64.rpm --no-check-certificate")
            os.system("wget https://download.docker.com/linux/centos/8/x86_64/stable/Packages/docker-ce-20.10.14-3.el8.x86_64.rpm -O /opt/docker_pkgs/docker-ce-20.10.14-3.el8.x86_64.rpm --no-check-certificate")
            os.system("wget https://download.docker.com/linux/centos/8/x86_64/stable/Packages/docker-ce-cli-20.10.14-3.el8.x86_64.rpm -O /opt/docker_pkgs/docker-ce-cli-20.10.14-3.el8.x86_64.rpm --no-check-certificate")
            os.system("wget https://download.docker.com/linux/centos/8/x86_64/stable/Packages/docker-ce-rootless-extras-20.10.14-3.el8.x86_64.rpm -O /opt/docker_pkgs/docker-ce-rootless-extras-20.10.14-3.el8.x86_64.rpm --no-check-certificate")
            os.system("wget https://download.docker.com/linux/centos/8/x86_64/stable/Packages/docker-scan-plugin-0.17.0-3.el8.x86_64.rpm -O /opt/docker_pkgs/docker-scan-plugin-0.17.0-3.el8.x86_64.rpm --no-check-certificate")
            os.system("rpm -e runc")
            os.system("rpm -ivh /opt/docker_pkgs/*.rpm")
            mprint(f"Installing the tool:[ {item} ], Done! ")

            mprint(f"Enable the tool:{item}")
            os.system("systemctl daemon-reload")
            os.system("systemctl enable docker")
            os.system("systemctl daemon-reload")
            #to start the docker in a new shell or will start failed
            os.popen("systemctl start docker")
        if "burnin" in item:
            mprint(f"Installing the tool:{item}, Start! ")
            os.system("mkdir -p /home/BurnIn/")
            os.system("wget www.baidu.com")
            os.system("wget https://vault.centos.org/centos/8/BaseOS/x86_64/os/Packages/ncurses-compat-libs-6.1-9.20180224.el8.x86_64.rpm --no-check-certificate -O /home/BurnIn/ncurses-compat-libs-6.1-9.20180224.el8.x86_64.rpm")
            os.system("wget https://vault.centos.org/centos/8/BaseOS/x86_64/os/Packages/ncurses-base-6.1-9.20180224.el8.noarch.rpm --no-check-certificate -O /home/BurnIn/ncurses-base-6.1-9.20180224.el8.noarch.rpm")
            os.system("rpm -ivh /home/BurnIn/ncurses-base-6.1-9.20180224.el8.noarch.rpm  /home/BurnIn/ncurses-compat-libs-6.1-9.20180224.el8.x86_64.rpm  --nodeps")
            os.system("wget http://www.passmark.com/downloads/bitlinux.tar.gz --no-check-certificate -O /home/BurnIn/bitlinux.tar.gz")
            os.system("tar -zxvf /home/BurnIn/bitlinux.tar.gz -C /home/BurnIn/")
            if not os.path.exists("/usr/bin/burnin"): 
                os.system("ln -s /home/BurnIn/burnintest/64bit/bit_cmd_line_x64 /usr/bin/burnin")
            mprint(f"Installing the tool:{item}, Done! ")
            free_disk=scan_disks()

            if free_disk == 0:
                print("No free disk found!")
            else:
                mprint("Free disk found:")
                print("+"*30)
                print(free_disk)
                print("+"*30)
                format_disk(free_disk)
                mprint("Config the BurnIn tool,Start!")
                test_disk_device="Device"+" "+free_disk
                print(test_disk_device)
                config_file="/home/BurnIn/burnintest/64bit/cmdline_config.txt"
                print(config_file)
                File_exist = os.path.exists(config_file)
                if File_exist:
                    fp = open(config_file,'r+')
                    lines = []
                    for line in fp:
                        line=line.strip()
                        if "Device /dev/sda1" in line:
                            line="#" + line
                        lines.append(line)
                    line_num =os.popen(f"cat {config_file} |grep sda -n | awk -F ':' '{{print $1}}'").read().strip()
                    line_num=int(line_num)
                    lines.insert(line_num,test_disk_device)
                    config_content='\n'.join(lines)
                    fp = open(config_file, 'w')
                    fp.write(config_content)
                    fp.close()
                    mprint("Config the BurnIn tool, Done!")
                else:
                    print("Failed to config the BurnIn, config file not found!")
                    raise FileNotFoundError


def scan_disks():
    scan_out=os.popen("lsblk -dpn |awk '{print $1}'")
    scan_out=scan_out.read()
    disk_list=[]
    free_disk_list=[]

    for line in scan_out.splitlines():
        disk_status=os.popen("lsblk -lpn " + line + " | awk '{print $1}'").read()
        disk_partition_number = os.popen(f"lsblk -lpn {line} |grep -i 'part' -c").read()

        if int(disk_partition_number) == 0:
            free_disk_list.append(line)

        disk_list.append(line)

    return free_disk_list[-1]


def format_disk(disk_label):
    disk = disk_label
    mprint("Formating the free disk for FIO")
    os.system(f"mkfs.ext4 -F {disk}")


if __name__ == "__main__":
    
    set_proxy()

    OS=check_OS_version()

    download_repos(OS)

    yum_install_pkg_list=["ipmitool","bonnie++","fio","container-selinux","iperf3"]

    yum_install_packages(yum_install_pkg_list)

    rpm_install_pkg_list=["docker","burnin"]

    install_rpm_packages(rpm_install_pkg_list)

    source_code_pkg_list=["prime95"]

    install_source_code_packages(source_code_pkg_list)
        
    all_installion_list = yum_install_pkg_list + rpm_install_pkg_list

    print("=============================================")
    mprint("Checking all the tools installation status.....")

    for item in all_installion_list:
        if  check_tool_installation(item):
            pass
        else:
            raise
