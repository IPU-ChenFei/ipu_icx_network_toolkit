from mba2_functions import *
import re
import random
import sys
import time
import os

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
    def case17(self, method, core, cos, cycle=1):
        sys_info().show_sys_info()
        l3=sys_info().L3_cache_size()[0]
        steplist = []
        upper = min(l3-10,int(l3*0.6))
        lower = 3
        if upper < lower:
            print("L3 cache too small")
            sys.exit(1)
        step_size = max(1,int(upper/10))
        for i in range(lower,upper,step_size):
            steplist.append(i)
        TESTMBA2().reset()
        global testnum
        global passnum
        global failnum
        testnum = 0
        passnum = 0
        failnum = 0
        if method == "iteration":
            mlc1result = []
            mlc2result = []
            mbalist = []
            corelist = []
            coslist = []
            statuslist1 = []
            statuslist2 = []
            deltalist1 = []
            deltalist2 = []
            bufferlist = []
            for i in range(0, core):
                for j in range(0, cos):
                    for m in steplist:
                        for k in range(100, 0, -10):
                            mlc = TESTMBA2().case17_CacheSize(i, j, k, m)
                            mlc2 = float(mlc[0])

                            mlc2result.append(mlc2)
                            corelist.append(i)
                            coslist.append(j)
                            mbalist.append(k)
                            bufferlist.append(m)
                            delta2 = 100*abs(mlc2-mlc2result[0])/mlc2result[0]
                            percent2 = format(delta2,".2f")
                            deltalist2.append(percent2)
                            if float(delta2) <= 5:
                                status2 = "Pass"
                                statuslist2.append(status2)
                                passnum = passnum+1
                            else:
                                status2 = "Fail"
                                statuslist2.append(status2)
                                failnum = failnum + 1
                        testnum = testnum+1
                        print("Core: ",i,"COS: ",j,"MBA percentage: ",k,"Buffersize: ",m,"MLC: ", mlc2,"Delta_pct: ",percent2,"Status: ", status2)
                        print("\n")
                        print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","MBA Percentage","Buffersize","MLC2","Delta_pct", "Status"))
                        for cores, coss, mba, bf, mlc2, pc2, st2 in zip(corelist, coslist, mbalist, bufferlist, mlc2result, deltalist2,statuslist2):
                            print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t".format(cores, coss, mba, bf, mlc2, pc2, st2))
        elif method == "random":
            for i in range(0, cycle):
                randcore = random.randint(0, core-1)
                randcos = random.randint(1,cos-1)
                for j in steplist:
                    mbm2result = []
                    mlc2result = []
                    mbalist = []
                    corelist = []
                    coslist = []
                    statuslist1 = []
                    statuslist2 = []
                    deltalist1 = []
                    deltalist2 = []
                    bufferlist = []
                    for k in range(100, 0, -10):
                        mlc = TESTMBA2().case17_CacheSize(randcore, randcos, k, j)
                        mlc2 = float(mlc[0])
                        mbm2 = float(mlc[1])
                        mlc2result.append(mlc2)
                        mbm2result.append(mbm2)
                        corelist.append(randcore)
                        coslist.append(randcos)
                        mbalist.append(k)
                        bufferlist.append(j)
                        delta2 = 100*abs(mlc2-mlc2result[0])/mlc2result[0]
                        percent2 = format(delta2,".2f")
                        deltalist2.append(percent2)
                        if float(delta2) <= 15 or mbm2 > 50:
                            status2 = "Pass"
                            statuslist2.append(status2)
                            passnum = passnum+1
                        else:
                            status2 = "Fail"
                            statuslist2.append(status2)
                            failnum = failnum + 1
                        testnum = testnum+1
                        print("Core: ",randcore,"COS: ",randcos,"MBA percentage: ",k,"Buffersize: ",j,"MLC2: ", mlc2,"Delta_pct: ",percent2,"Status: ", status2)
                        print("MBM: ", mbm2)
                    print("\n")
                    print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","MBA Percentage","Buffersize","MLC","Delta_pct", "Status","MBM"))
                    for cores, coss, mba, bf, mlc2, pc2, st2,m2 in zip(corelist, coslist, mbalist, bufferlist,mlc2result, deltalist2,statuslist2,mbm2result):
                         print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t".format(cores, coss, mba, bf, mlc2, pc2, st2,m2))
        print("\n"*2)
        print("Number of tests: ", testnum,"Passed: ", passnum, "Failed: ", failnum)
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
logname = r"{}/log/Case17_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case17(method, core, cos, cycle)


