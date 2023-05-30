import subprocess
import sys
print("-----",len(sys.argv))
allocation_id= sys.argv[1]
ret=subprocess.check_output("setx CAPI_ALLOC_ID "+allocation_id,shell=True)
if(ret != -1):
    print("system_environemnt Set")
else:
    print("Faield to Set it")