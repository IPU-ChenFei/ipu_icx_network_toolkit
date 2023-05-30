import os


def free_ssd():
    partitions_num = os .popen("wmic diskdrive get /value | find \"Par\"").read().strip().split("\n\n")
    partitions_num1 = [i[-1] for i in partitions_num]
    device_name = os.popen("wmic diskdrive get /value | find \"Name=\\\"").read().strip().split("\n\n")
    device_name1 = [i.split("\\.\\")[1] for i in device_name]
    dict1 =dict(zip(device_name1,partitions_num1))
    ssd_list = []
    for i in device_name1:
        if dict1.get(i) == "0":
            ssd_list.append(i)
    return ssd_list


def update_disk(log_full_name,log_path):
    free_disk = free_ssd()
    os.system(f"intelMAS.exe show -intelssd > {log_path}/intelssd.txt")
    ssd_index = os.popen("intelMAS show -intelssd | find \"Index\"").read().strip().split("\n")
    ssd_index_l = [i[-1] for i in ssd_index]
    devicepath = os.popen("intelMas show -intelssd |find \"DevicePath\"").read().strip().split("\n")
    devicepath_l = [i.split("\\.\\")[-1] for i in devicepath]
    dict1 = dict(zip(devicepath_l,ssd_index_l))
    for i in range(0, len(free_disk)):
        index = dict1.get(free_disk[i])
        print(index)
        os.system(f"echo y| intelMAS.exe load -intelssd {index} >> {log_full_name}")



def check_log(log_full_name):
    with open(log_full_name) as f:
        log_info =f.read()
        if "Firmware update failed" in log_info:
            # print("******************************\n"
            #       "********update failed*********\n"
            #       "******************************",
            #       log_info)
            raise Exception("update ssd FW failed")

        elif "updated successfully" or "contains current firmware" in log_info:
            print("update successful or is already the latest version" , log_info)


def delete_log(log_full_name):
    if os.path.exists(log_full_name):
        os.remove(log_full_name)


if __name__ == "__main__":

    log_name = "update.txt"
    log_path = "C:\BKCPkg\domains\storage"
    log_full_name = os.path.join(log_path,log_name)
    delete_log(log_full_name)
    update_disk(log_full_name,log_path)
    check_log(log_full_name)
