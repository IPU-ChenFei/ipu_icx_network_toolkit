import time
import os

def mprint(item):
    print("\n\n","-"*7,item)

def mprint2(item):
    print("-"*30)
    print(item)
    print("-"*30)

def create_log_file(log_path,test_name):
    mprint(f"Creating the log name:")

    test_time=str(time.strftime('%Y%m%d%H%M%S',time.localtime(time.time())))

    log_full_name=log_path + test_name + "_" + test_time + ".log"

    print(log_full_name)

    return log_full_name


def get_bmc_sel_list(log_full_name):
    log = log_full_name
    os.system(f"ipmitool sel list > {log}")

def get_bmc_sel_detail(sel_id, log_full_name):
    ID = sel_id
    log = log_full_name
    os.system(f"ipmitool sel get 0x{ID} >> {log}  ")
    os.system(f"echo '-------------------------------------' >> {log}  ")
    
def check_sel_log(test_name,log_full_name):
    test = test_name
    mprint(f"checking {test} log:")
    log = log_full_name

    log_file=open(log,'r')
    log_content=log_file.readlines()
    log_error_ID=[]
    for line in log_content:
        if "error" in line or "Error" in line or "fail" in line or "Fail" in line or "Critical" in line or "recoverable" in line:
        #if "error" in line or "Error" in line or "fail" in line or "Fail" in line or "Critical" in line:
            error_ID = line.split()[0]
            log_error_ID.append(error_ID)
    
    if len(log_error_ID) == 0:
        mprint("No error or fail found in BMC sel log !")
    else:
        mprint("Found error or fail in BMC sel log !")
        print("Getting error details info...")
        for item in log_error_ID:
            print(" sel log ID: ",item)
            get_bmc_sel_detail(item,log)
        #raise False

    log_file.close()


if __name__ == '__main__':

    test_name="bmc_sel"

    mprint2(test_name)

    log_path="/var/log/"

    log_full_name=create_log_file(log_path,test_name)

    get_bmc_sel_list(log_full_name)

    check_sel_log(test_name,log_full_name)
