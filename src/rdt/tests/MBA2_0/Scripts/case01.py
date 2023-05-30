from mba2_functions import *
import re
import random
import sys
import time
import os
from mba2_functions import MBM_UPPER_LIMITATION
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
    def case01(self, method, core, cos, cycle=1):
        sys_info().show_sys_info()
        TESTMBA2().reset()
        global testnum
        global passnum
        global failnum
        testnum = 0
        passnum = 0
        failnum = 0
        if method == "iteration":
            mblresult = []
            mbrresult = []
            corelist = []
            coslist = []
            statuslist = []

            for i in range(0, core):
                for j in range(0, cos):
                    TESTMBA2().reset()
                    mbm = TESTMBA2().case01_MBR(i, j)
                    mbl = float(mbm[0])
                    mbr = float(mbm[1])
                    mblresult.append(mbl)
                    mbrresult.append(mbr)
                    corelist.append(i)
                    coslist.append(j)
                    if mbr <= 100:
                        status = "Pass"
                        statuslist.append(status)
                        passnum = passnum+1
                    else:
                        status = "Fail"
                        statuslist.append(status)
                        failnum = failnum+1
                    testnum = testnum+1
                    print("Core: ",i,"COS: ",j,"MBL: ",mbl,"MBR: ",mbr,"Status: ",status)
            print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","MBL","MBR","Status"))
            for key,value,i,j,statuss in zip(mblresult,mbrresult,corelist,coslist,statuslist):
                    print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t".format(i,j,key,value,statuss))

        elif method == "random":
            for i in range(0, cycle):
                mblresult = []
                mbrresult = []
                mbalist = []
                corelist = []
                coslist = []
                statuslist = []
                trafficlist = []
                randcore = random.randint(0, core-1)
                traffic_info = TrafficType().get_traffic(randcore)
                command = traffic_info[1]
                traffic = traffic_info[0]
                randcos = random.randint(1,cos-1)
                for k in range(100, 0, -10):
                    mbm = TESTMBA2().case01_MBR(command,randcore, randcos,k)
                    mbl = float(mbm[0])
                    mbr = float(mbm[1])
                    mblresult.append(mbl)
                    mbrresult.append(mbr)
                    corelist.append(randcore)
                    coslist.append(randcos)
                    mbalist.append(k)
                    trafficlist.append(traffic)
                    if mbr <= 100:
                        status = "Pass"
                        statuslist.append(status)
                        passnum = passnum+1
                    else:
                        status = "Fail"
                        statuslist.append(status)
                        failnum = failnum+1
                    testnum = testnum+1
                    print("Core: ", randcore, "COS: ", randcos, "Traffic: ",traffic,"MBA percentage: ",k , "MBL: ", mbl, "MBR: ", mbr, "Status: ", status)
                print("\n")
                print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","Traffic","MBA","MBL","MBR","Status"))
                for key, value, cores, coss, statuss ,ma,tf in zip(mblresult,mbrresult,corelist,coslist,statuslist,mbalist,trafficlist):
                    print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t".format(cores,coss,tf,ma,key,value,statuss))
        elif method == "custom":
                TESTMBA2().reset()
                mbm = TESTMBA2().case01_MBR(core, cos)
                mbl = float(mbm[0])
                mbr = float(mbm[1])
                if mbr <= 100:
                    status = "Pass"
                    passnum = passnum+1
                else:
                    status = "Fail"
                    failnum = failnum+1
                testnum = testnum+1
                print("Core: ", randcore, "COS: ", randcos, "MBL: ", mbl, "MBR: ", mbr, "Status: ", status)
        else:
            print("Wrong input")
        print("\n"*2)
        print("Number of tests: ", testnum, " Passed: ", passnum, " Failed: ", failnum)
        TESTMBA2().reset()


# Choose a method from iteration, random, custom
method = "random"
core = sys_info().max_thread()
cos = sys_info().max_cos()
cycle = 10
gettime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
path = r"/home/log"
cpath = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(cpath,"log")):
    os.makedirs(os.path.join(cpath,"log"))  
logname = r"{}/log/Case01_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case01(method, core, cos, cycle)


