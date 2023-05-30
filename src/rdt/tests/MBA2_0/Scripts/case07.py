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
    def case07(self, method, core, cos, cycle=1):
        sys_info().show_sys_info()
        TESTMBA2().reset()
        global testnum
        global passnum
        global failnum
        testnum = 0
        passnum = 0
        failnum = 0
        if method == "iteration":
            mbmresult = []
            mbalist = []
            corelist = []
            coslist = []
            for i in range(0, core):
                for j in range(0, cos):
                    for k in range(100, 0, -10):
                        mbm = TESTMBA2().case07_varyCOS(i, j, k)
                        mbm1 = int(mbm)
                        mbmresult.append(mbm1)
                        corelist.append(i)
                        coslist.append(j)
                        mbalist.append(k)
                        testnum = testnum+1
                        print("Core: ",i,"COS: ",j,"MBA percentage: ",k,"MBM: ", mbm)
                    print("\n")
                    print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","MBA Percentage","MBM"))
                    for cores, coss, key, value in zip(corelist, coslist, mbalist, memresult):
                        print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t".format(cores,coss, key, value))
        elif method == "random":
            for i in range(0, cycle):
                randcore = random.randint(0, core-1)
                traffic_info = TrafficType().get_traffic(randcore)
                command = traffic_info[1]
                traffic = traffic_info[0]
                for k in range(100, 0, -10):
                    mbmresult = []
                    mbalist = []
                    corelist = []
                    coslist = []
                    deltalist = []
                    statuslist = []
                    trafficlist = []
                    for j in range(0, cos):
                        mbm = TESTMBA2().case07_varyCOS(command,randcore, j, k)
                        mbm1 = int(mbm)
                        corelist.append(randcore)
                        coslist.append(j)
                        mbmresult.append(mbm1)
                        mbalist.append(k)
                        trafficlist.append(traffic)
                        delta = 100*abs(mbm1-mbmresult[0])/mbmresult[0]
                        percent = format(delta,".2f")
                        deltalist.append(percent)
                        if abs(mbm1-mbmresult[0])<=mbmresult[0]*0.15:
                            status = "Pass"
                            statuslist.append(status)
                            passnum = passnum + 1
                        else:
                            status = "Fail"
                            statuslist.append(status)
                            failnum = failnum + 1
                        testnum = testnum+1
                        print("Cycle: ", i, "Core: ",randcore,"COS: ", j,"Traffic: ",traffic,"MBA percentage: ",k,"MBM: ", mbm, "Delta: ",percent,"Status: ", status)
                    print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","Traffic","MBA Percentage","MBM","Delta", "Status"))
                    for cores, coss, tf,key, value,dt, st in zip(corelist, coslist, trafficlist,mbalist,mbmresult,deltalist, statuslist):
                        print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t".format(cores,coss,tf,key,value,dt,st))
        elif method == "custom":
            for k in range(100, 0, -10):
                mbmresult = []
                mbalist = []
                corelist = []
                coslist = []
                deltalist = []
                statuslist = []
                for j in range(0, cos):
                        mbm = TESTMBA2().case07_varyCOS(core, j, k)
                        mbm1 = int(mbm)
                        corelist.append(core)
                        coslist.append(j)
                        mbmresult.append(mbm1)
                        mbalist.append(k)
                        delta = abs(mbm1-mbmresult[0])
                        deltalist.append(100*delta/mbmresult[0])
                        if abs(mbm1-mbmresult[0])<=mbmresult[0]*0.10:
                            status = "Pass"
                            passnum = passnum + 1
                        else:
                            status = "Fail"
                            failnum = failnum + 1
                        testnum = testnum+1
                        print("Core: ",core,"COS: ",cos,"MBA percentage: ",k,"MBM: ", mbm, "Delta: ",delta,"Status: ", status)
                print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","MBA Percentage","MBM","Delta", "Status"))
                for cores, coss, key, value,dt,st in zip(corelist, coslist, mbalist,mbmresult,deltalist, statuslist):
                    print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t".format(cores,coss,key,value,dt,st))
        else:
            print("Wrong input")
        print("\n"*2)
        print("Number of tests: ", testnum, "Passed: ", passnum, "Failed: ", failnum)
        TESTMBA2().reset()


# Choose a method from iteration, random, custom
method = "random"
core = sys_info().max_thread()
cos = sys_info().max_cos()
cycle = 1
gettime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
cpath = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(cpath,"log")):
    os.makedirs(os.path.join(cpath,"log"))
logname = r"{}/log/Case07_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case07(method, core, cos, cycle)


