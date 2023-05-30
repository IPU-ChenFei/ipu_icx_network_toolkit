from mba2_functions import *
import re
import random
import sys
import time
import os
from traffics import *

class Logger(object):
    def __init__(self, filename='default.log', stream=sys.stdout):
	    self.terminal = stream
	    self.log = open(filename, 'a')

    def write(self, message):
	    self.terminal.write(message)
	    self.log.write(message)

    def flush(self):
	    pass


class case_execute:
    def case08(self, method, core, cos, cycle=1):
        sys_info().show_sys_info()
       # TESTMBA2().reset()
       # TESTMBA2().refresh()
       # stress_tools().kill_tool()
        #libpath = "source /opt/intel/bin/compilervars.sh intel64"
        #exec(libpath)
        #libCommand = subprocess.Popen(libpath, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        #                               stderr=subprocess.PIPE,shell=True, executable="/bin/bash")
        global testnum
        global passnum
        global failnum
        testnum = 0
        passnum = 0
        failnum = 0
        testnum1 = 0
        testnum2 = 0
        if method == "random":
            for i in range(0, cycle):
                global judge
                mbmresult1 = []
                cachewaylist = []
                corelist = []
                coslist = []
                status1list = []
                delta1list = []
                trafficlist = []
                last_mbmresult = []
                status2list = []
                delta2list = []
                randcore = random.randint(0, core-1)
                randcos = random.randint(0,cos-1)
                #traffic_info = TrafficType().get_traffic(randcore)
                #command = traffic_info[1]
                #traffic = traffic_info[0]
                #command = "/home/mlc_v3.7/Linux/mlc_internal --loaded_latency -T -d0 -b6m -u -t10 -k"+str(randcore)
                traffic = "mlc_R"
                cacheway = ["0xfff", "0xff", "0xf", "0x1"]
                for k in cacheway:
                    mbm1 = TESTMBA2().case08_CDP(randcore,randcos,k)
                    corelist.append(randcore)
                    cachewaylist.append(k)
                    coslist.append(randcos)
                    mbmresult1.append(mbm1)
                    trafficlist.append(traffic)
                    if k == "0xfff":
                        last = mbm1
                        last_mbmresult.append(last)
                        status1 = "Pass"
                        status1list.append(status1)
                        passnum = passnum+1
                        delta = 100*mbm1/mbm1
                        percent = format(delta,".2f")
                        delta1list.append(percent)
                    else:
                        last = mbmresult1[-2]
                        last_mbmresult.append(last)
                        delta = 100*mbm1/mbmresult1[-2]
                        percent = format(delta,".2f")
                        delta1list.append(percent)
                        if delta<=110:
                            status1 = "Pass"
                            passnum = passnum+1
                            status1list.append(status1)
                        else:
                            status1 = "Fail"
                            failnum = failnum+1
                            status1list.append(status1)
                    testnum = testnum+1
                    print("Traffic:", traffic,"Core:", randcore,"COS:", randcos, "Cacheway:", k, "MLC:", mbm1, "Delta:",percent,"Status:",status1)
                print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Traffic","Core","COS","Cacheway","MLC","Delta","Status"))
                for tf,c,cs,cw,m1,dt1,st1 in zip(trafficlist,corelist,coslist,cachewaylist,mbmresult1,delta1list,status1list):
                    print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t".format(tf,c,cs,cw,m1,dt1,st1))
        else:
            print("Wrong Input")
            print("\n")
        print("\n"*2)
        print("Number of tests: ", testnum, " Passed: ", passnum, " Failed: ", failnum)
        TESTMBA2().reset()


# Choose a method from iteration, random, custom
method = "random"
core = sys_info().max_thread()
cos = sys_info().max_cos()
cycle = 10
gettime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
cpath = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(cpath,"log")):
    os.makedirs(os.path.join(cpath,"log"))
logname = r"{}/log/Case08_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case08(method, core, cos, cycle)

