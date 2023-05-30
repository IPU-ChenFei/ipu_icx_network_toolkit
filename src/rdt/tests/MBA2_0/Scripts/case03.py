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
    def case03(self, method, core, cos, traffic, pattern, socket, cycle=1):
        sys_info().show_sys_info()
        TESTMBA2().reset()
        global testnum
        global passnum
        global failnum
        global knownnum
        testnum = 0
        passnum = 0
        failnum = 0
        knownnum = 0
        result = []
        seqtrafficlist = ["R", "W2","W3", "W5", "W6", "W7", "W8", "W10"]
        randtrafficlist = ["R", "W2", "W5", "W6"]
        patternlist = ["seq", "rand"]
        socketlist = [0, 1]
        if method == "iteration":
            for i in range(0, core):
                for j in range(0, cos):
                    for k in socketlist:
                        for n in patternlist:
                            if n == "seq":
                                for m in seqtrafficlist:
                                    result = TESTMBA2().case03_mlcvsmbm(i, j, m, n, k)
                                    mlc = float(result[0])
                                    mbm = float(result[1])
                                    if abs(mbm - mlc) <= mbm*0.10:
                                        status = "Pass"
                                        passnum = passnum + 1
                                    else:
                                        status = "Fail"
                                        failnum = failnum + 1
                                    testnum = testnum + 1
                                    print("Core: {} COS: {} Traffic: {} Pattern: {} Numa: {} MBM: {} MLC: {} Status: {}".format(i,j,m,n,k,mbm,mlc,status))
                            else:
                                for v in randtrafficlist:
                                    result = TESTMBA2().case03_mlcvsmbm(i, j, v, n, k)
                                    mlc = float(result[0])
                                    mbm = float(result[1])
                                    testnum = testnum + 1
                                    print("Core: {} COS: {} Traffic: {} Pattern: {} Numa: {} MBM: {} MLC: {}".format(i,j,v,n,k,mbm,mlc))
        elif method == "random":
            for i in range(0, cycle):
                corelist = []
                coslist = []
                patterns = []
                traffics = []
                socketa = []
                mlclist = []
                mbmlist = []
                deltalist = []
                statuslist=[]
                randcore = random.randint(0, core-1)
                randcos = random.randint(1,cos-1)
                for m in socketlist:
                    for n in patternlist:
                        if n == "seq":
                            for k in seqtrafficlist:
                                result = TESTMBA2().case03_mlcvsmbm(randcore, randcos, k, n, m)
                                mlc = float(result[0])
                                mbm = float(result[1])
                                mlclist.append(mlc)
                                mbmlist.append(mbm)
                                corelist.append(randcore)
                                coslist.append(randcos)
                                patterns.append(n)
                                traffics.append(k)
                                socketa.append(m)
                                testnum = testnum + 1
                                delta = abs(mlc-mbm)/mlc*100
                                percent = format(delta,".2f")
                                deltalist.append(percent)
                                if delta <=20:
                                    status = "Pass"
                                    statuslist.append(status)
                                    passnum=passnum+1
                                elif delta > 20 and k in ["W6", "W7", "W8", "W10"]:
                                    status = "Known Issue"
                                    statuslist.append(status)
                                    knownnum = knownnum + 1
                                else:
                                    status = "Fail"
                                    statuslist.append(status)
                                    failnum = failnum+1
                                print("Core: {} COS: {} Traffic: {} Pattern: {} Numa: {} MBM: {} MLC: {} Delta: {} Status: {}".format(randcore,randcos,k,n,m,mbm,mlc,percent, status))
                        else:
                            for v in randtrafficlist:
                                result = TESTMBA2().case03_mlcvsmbm(randcore, randcos, v, n, m)
                                mlc = float(result[0])
                                mbm = float(result[1])
                                mlclist.append(mlc)
                                mbmlist.append(mbm)
                                corelist.append(randcore)
                                coslist.append(randcos)
                                patterns.append(n)
                                traffics.append(v)
                                socketa.append(m)
                                testnum = testnum + 1
                                delta = abs(mlc-mbm)/mlc*100
                                percent = format(delta,".2f")
                                deltalist.append(percent)
                                if delta <=20:
                                    status = "Pass"
                                    statuslist.append(status)
                                    passnum=passnum+1
                                elif delta > 20 and k in ["W6", "W7", "W8", "W10"]:
                                    status = "Known Issue"
                                    statuslist.append(status)
                                    knownnum = knownnum + 1
                                else:
                                    status = "Fail"
                                    statuslist.append(status)
                                    failnum = failnum+1
                                print("Core: {} COS: {} Traffic: {} Pattern: {} Numa: {} MBM: {} MLC: {} Delta: {} Status: {}".format(randcore,randcos,v,n,m,mbm,mlc,percent,status))
                print("\n")
                print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","Traffic","Pattern","Numa","MBM","MLC","Delta","Status"))
                for c, cs, tr, pa, nu, mb, ml,dt,st in zip(corelist, coslist, traffics, patterns, socketa, mbmlist, mlclist,deltalist,statuslist):
                    print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format(c,cs,tr,pa,nu,mb,ml,dt,st))

        elif method =="custom":
            result = TESTMBA2().case03_mlcvsmbm(core, cos, traffic, pattern, socket)
            mlc = float(result[0])
            mbm = float(result[1])
            testnum = testnum + 1
            print("Core: {} COS: {} Traffic: {} Pattern: {} Numa: {} MBM: {} MLC: {}".format(core,cos,traffic,pattern,socket,mbm,mlc))

        else:
            print("Wrong input")
        print("\n"*2)
        print("Number of tests: ", testnum,"Passed: ", passnum, "Failed: ", failnum, "Known Issue: ", knownnum)
        print('There is an known sighting that "[HCC][XCC PO]The MBM report wrong memory bandwidth for remote NUMA access" as')
        print('https://hsdes.intel.com/appstore/article/#/1507329155')
        print('https://hsdes.intel.com/appstore/article/#/2207584685')
        TESTMBA2().reset()
method = "random"
core = sys_info().max_thread()
cos = sys_info().max_cos()
traffic = "R"
pattern = "seq"
socket = 1
cycle = 10
gettime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
cpath = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(cpath,"log")):
    os.makedirs(os.path.join(cpath,"log"))
logname = r"{}/log/Case03_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case03(method, core, cos, traffic, pattern, socket, cycle)




