import os
from datetime import datetime

def free_disks():
    scan_out = os.popen("lsblk -dpn |awk '{print $1}'")
    scan_out = scan_out.read()
    disk_list = []
    free_disk_list = []

    for line in scan_out.splitlines():
        disk_status = os.popen("lsblk -lpn " + line + " | awk '{print $1}'").read()
        disk_partition_number = os.popen(f"lsblk -lpn {line} |grep -i 'part' -c").read()

        if int(disk_partition_number) == 0:
            free_disk_list.append(line)
        disk_list.append(line)
    return free_disk_list


def update_disk_index(log_fullname):
    free_disk = free_disks()
    os.system("intelmas show -intelssd | tee intelssd.txt")
    ssd_index = os.popen(r"intelmas show -intelssd |grep -i 'index' | awk '{print $3}'")
    ssd_index_l = ssd_index.read().splitlines()
    ssd_dev_path = os.popen(r"intelmas show -intelssd |grep -i 'DevicePath' | awk '{print $3}'")
    ssd_dev_path_l = ssd_dev_path.read().splitlines()
    all_ssd = dict(zip(ssd_dev_path_l,ssd_index_l))
    for i in range(0, len(free_disk)):
        index = all_ssd.get(free_disk[i])
        os.system(f"echo y| intelmas load -intelssd {index} >> {log_fullname}")
        print(log_fullname)

def check_log(log_fullname):
    with open(f"{log_fullname}","r") as f:
        intelmas_log = f.read()
        if "Firmware update failed" in intelmas_log:
            # print("update successful or is already the latest version" , intelmas_log)
            raise Exception("update ssd FW failed")
        elif "updated successfully" or "contains current firmware" in intelmas_log:
            print("update successful or is already the latest version")


def delete_log(log_fullname):
     if os.path.exists(log_fullname):
         os.remove(log_fullname)

# def clean_env(log_fullname):
#     os.remove(f"{log_fullname}")
if __name__ == "__main__":
    nowtime = datetime.now().strftime('%Y%m%dZ%Hh%Mm%Ss')
    log_fullname = f"/var/log/intelmas{nowtime}.txt"
    delete_log(log_fullname)
    update_disk_index(log_fullname)
    check_log(log_fullname)
    # clean_env(log_fullname)
