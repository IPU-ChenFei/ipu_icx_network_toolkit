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
    def case19(self, method, core1, cos1, cos2, cycle=1):
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
        multilist = [0,1]
        if method == "random":
            for i in range(0, cycle):
                randcore1 = random.randint(0, core1-1)
                randcore2 = random.randint(0, core2-1)
                randcos2 = random.randint(1, cos2 - 1)
                while randcore1 == randcore2 or abs(randcore1-randcore2)==int(core1/2):
                    randcore2= random.randint(0, core2 - 1)
                traffic_info = TrafficType().get_same_traffics(randcore1,randcore2)
                command1 = traffic_info[1]
                command2 = traffic_info[2]
                traffic1 = traffic_info[0]
                traffic2 = traffic_info[0]
                #membwntw1 = "/home/intel-cmt-cat-master/tools/membw/membw -c "+str(randcore1)+" -b 20000 --nt-write"
                #membwntw2 = "/home/intel-cmt-cat-master/tools/membw/membw -c "+str(randcore2)+" -b 20000 --nt-write"
                multilist = [0,1]
                for j in multilist:
                        result = []
                        mbl1result = []
                        mbl2result = []
                        core1list = []
                        cos1list = []
                        core2list = []
                        cos2list = []
                        status1list = []
                        status2list = []
                        mba2list = []
                        mba1list = []
                        c1list = []
                        c2list = []
                        delta1list = []
                        delta2list = []
                        multi = []
                        toollist = []
                        reset1 = "pqos -R"
                        aaa = subprocess.Popen(reset1,shell=True)
                        time.sleep(3)
                        tool =traffic1
                        for k in range(100, 0, -10):
                            mbm = TESTMBA2().case19_MBAonCOS0(randcore1, randcore2, randcos2, k, command1, command2, j)
                            mbl1 = float(mbm[0])
                            mbl2 = float(mbm[1])
                            while mbl1<100 or mbl2<100:
                                mbm = TESTMBA2().case19_MBAonCOS0(randcore1, randcore2, randcos2, k, command1, command2, j)
                                mbl1 = float(mbm[0])
                                mbl2 = float(mbm[1])
                            mbl1result.append(mbl1)
                            mbl2result.append(mbl2)
                            core1list.append(randcore1)
                            core2list.append(randcore2)
                            cos1list.append(0)
                            cos2list.append(randcos2)
                            mba1list.append(k)
                            mba2list.append(50)
                            multi.append(j)
                            toollist.append(tool)
                            #delta1 = 100*mbl1/mbl1result[0]
                            #percent1 = format(delta1,".2f")
                            delta2 = 100*abs(mbl2-mbl2result[0])/mbl2result[0]
                            percent2 = format(delta2,".2f")
                            #delta1list.append(str(percent1)+"%")
                            delta2list.append(str(percent2)+"%")
                            #if abs(k-float(percent1)) <= 5:
                            #    status1 = "Pass"
                            #    status1list.append(status1)
                            #    passnum = passnum + 1
                            #else:
                            #    status1 = "Fail"
                            #    status1list.append(status1)
                            #    failnum = failnum + 1
                            #testnum=testnum+1
                            if float(percent2) <= 10:
                                status2 = "Pass"
                                status2list.append(status2)
                                passnum = passnum+1
                            else:
                                status2 = "Fail"
                                status2list.append(status2)
                                failnum = failnum + 1
                            testnum = testnum+1
                            print("Cycle:", i, "Core1: ", randcore1, "COS1:  0", "MBA percentage: ", k)
                            print("Cycle:", i, "Core2: ", randcore2, "COS2: ", randcos2, "MBA percentage: 50")
                            print("MBM1:",mbl1,"MBM2",mbl2 )
                        print("\n")
                        print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core1","COS1","MBA1","Core2","COS2","MBA2","Tool","Multi","MBL1","MBL2","Delta_pct","Status"))
                        for c1,cs1,ma1,c2,cs2,ma2,tl,mt,m1,m2,dt,st2 in zip(core1list,cos1list,mba1list,core2list,cos2list,mba2list,toollist,multi,mbl1result,mbl2result,delta2list,status2list):
                            print ("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format(c1,cs1,ma1,c2,cs2,ma2,tl,mt,m1,m2,dt,st2))
        else:
            print("Wrong input")
        print("\n"*2)
        print("Number of tests: ", testnum, " Passed: ", passnum, " Failed: ", failnum)
        TESTMBA2().reset()


# Choose a method from iteration, random, custom
method = "random"
core1 = sys_info().max_thread()
cos1 = sys_info().max_cos()
core2 = sys_info().max_thread()
cos2 = sys_info().max_cos()
mba1 = 100
cycle = 10
gettime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
cpath = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(cpath,"log")):
    os.makedirs(os.path.join(cpath,"log"))
logname = r"{}/log/Case19_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case19(method, core1, cos1, cos2,  cycle)


