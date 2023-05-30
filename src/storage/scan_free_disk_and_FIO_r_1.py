import os
import time
from pathlib import Path
import re

def mprint(item):
    print("\n\n","-"*7,item)

def check_tool_installation(tool_name):
    tool = tool_name
    mprint("Checking tool installation:")
    result=os.popen(f"whereis {tool}")
    result=result.read()
    if re.findall(r'/usr/bin',result) or re.findall(r'/usr/sbin',result):
        print(f"Tool:{tool} has been installed")
        print(result)
    else:
        print(f"Tool:{tool} has not been installed !")

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

def run_test(test_name,disk_label,log_path):
    disk = disk_label
    log = log_path
    test = test_name
    mprint(f"Running {test} on {disk}, Start !   Test log : {log}")
#    print(f"fio -filename={disk} -direct=1 -iodepth 1 -thread -rw=randrw -rwmixread=70 -ioengine=psync -bs=4k -size=300G -numjobs=50 -runtime=180 -group_reporting -name=randrw_70read_4k -output={log}")
    print(f"fio -filename={disk} -direct=1 -iodepth 16 -thread -rw=read -ioengine=libaio -bs=64k -size=300G -numjobs=1 -runtime=180 -time_based -group_reporting -name=seq_100read64k -output={log}")
    os.system(f"fio -filename={disk} -direct=1 -iodepth 16 -thread -rw=read -ioengine=libaio -bs=64k -size=300G -numjobs=1 -runtime=30 -time_based -group_reporting -name=seq_100read64k -output={log}")
    os.system(f"echo Running FIO on {disk}, Done ! >> {log}")
    print(f"Running {test} on {disk}, Done !")

def log_check(test_name,log_full_name):
    test = test_name
    mprint(f"checking {test} log:")
    log = log_full_name
    log_content=open(log,'r')
    log_content=log_content.readlines()
    log_summary=[]
    log_pass_flag=0
    test_status_flag = "Running " + test + " on"    
    try:
        for line in log_content:
            if "read: IOPS=" in line:
                log_summary.append(line)
                log_pass_flag=log_pass_flag+1
            if "write: IOPS=" in line:
                log_summary.append(line)
                log_pass_flag=log_pass_flag+1
            if test_status_flag and "Done !" in line:
                log_summary.append(line)
                log_pass_flag=log_pass_flag+1
        if log_pass_flag >0:
            print("-"*30)
            print(f"{test} log check PASS!")
            print("-"*30)
            print(f"{test} log Summary:")
            for line in log_summary:
                line=line.strip()
                print(line)
        else:
            raise StopIteration
    except StopIteration:
        print(f"{test} log check fail: log_pass_flag={log_pass_flag}")


def log_exist_check(log_full_name):
    log = log_full_name
    log_is_exist=os.path.exists(log)
    if log_is_exist:
        print("Old fio log exist, backup it")
        os.system(f'"mv {log_path} "+ " "+ {log_path}+"_bk"  ' )
    else:
        pass


def create_log_file(log_path,test_name):
    mprint(f"Creating the log name:")

    test_time=str(time.strftime('%Y%m%d%H%M%S',time.localtime(time.time())))
    
    log_full_name=log_path + test_name + "_" + test_time + ".log"

    print(log_full_name)
    
    return log_full_name


def clean_test_env(free_disk):
    mprint("Cleanning the test env!")
    format_disk(free_disk)



if __name__ == '__main__':
    

#    check_tool_installation("fio++")
    check_tool_installation("fio")

    test_name="FIO_test"

    log_path="/var/log/"

    log_full_name=create_log_file(log_path,test_name)
   
    log_exist_check(log_full_name)

    free_disk=scan_disks()
    
    if free_disk == 0:
        print("No free disk found!")
    else:
        mprint("Free disk found:")
        print("+"*30)
        print(free_disk) 
        print("+"*30)

        format_disk(free_disk)

        run_test(test_name,free_disk,log_full_name)

        log_check(test_name,log_full_name)

        clean_test_env(free_disk)
