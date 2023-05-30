import os

burnInLog_exist=os.path.exists("/tmp/BiTLog2.log")
result = os.popen('cat /tmp/BiTLog2.log |grep "TEST RUN PASSED"').read().strip()
if burnInLog_exist:
    if result == "TEST RUN PASSED":
        pass
    else:
        raise
        print(" burnIn run failed!")
else:
    print("No burnIn log found!")
    raise
