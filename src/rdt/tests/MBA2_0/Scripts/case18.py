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
    def case18(self, method, core, cos1, cos2, cycle=1):
        sys_info().show_sys_info()
        TESTMBA2().reset()
        global knownum
        global testnum
        global passnum
        global failnum
        knownum = 0
        testnum = 0
        passnum = 0
        failnum = 0
        if method == "random":
            for i in range(0, cycle):
                global judge
                mbmresult1 = []
                mbmresult2 = []
                mbalist = []
                corelist = []
                coslist1 = []
                coslist2 = []
                statuslist1 = []
                statuslist2 = []
                deltalist1 = []
                deltalist2 = []
                trafficlist = []
                last_mbmresult = []
                randcore = random.randint(0, core-1)
                traffic_info = TrafficType().get_traffic(randcore)
                command = traffic_info[1]
                traffic = traffic_info[0]
                randcos1 = random.randint(1,cos1-1)
                randcos2 = random.randint(1,cos2-1)
                while randcos1 ==randcos2:
                    randcos2 = random.randint(1,cos2-1)
                for k in range(100, 0, -10):
                        mbm = TESTMBA2().case18_StopThrottle(command, randcore, randcos1,randcos2, k)
                        mbm1 = mbm[0]
                        mbm2 = mbm[1]
                        while mbm1 <100 or mbm2<100:
                            mbm = TESTMBA2().case18_StopThrottle(command, randcore, randcos1,randcos2, k)
                            mbm1=mbm[0]
                            mbm2=mbm[1]
                        corelist.append(randcore)
                        coslist1.append(randcos1)
                        coslist2.append(randcos2)
                        mbmresult2.append(mbm2)
                        mbmresult1.append(mbm1)
                        mbalist.append(k)
                        #delta1 = 100*mbm1/mbmresult1[0]
                        #percent1 = format(delta1,".2f")
                        delta2 = 100*abs(mbm2-mbmresult2[0])/mbmresult2[0]
                        percent2 = format(delta2,".2f")
                        #deltalist1.append(percent1)
                        deltalist2.append(percent2)
                        trafficlist.append(traffic)
                        #if abs(k-delta1)<=5:
                        #    status1 = "Pass"
                        #    passnum = passnum+1
                        #    statuslist1.append(status1)
                        #else:
                        #    status1 = "Fail"
                        #    failnum = failnum+1
                        #    statuslist1.append(status1)
                        #testnum = testnum+1
                        if k==100:
                            last = mbm1
                            last_mbmresult.append(last)
                            status1 = "Pass"
                            passnum = passnum+1
                            statuslist1.append(status1)
                            delta1 = 100*mbm1/mbm1
                            percent1 = format(delta1,".2f")
                            deltalist1.append(percent1)
                        elif k<100 and k>10:
                            last = mbmresult1[-2]
                            last_mbmresult.append(last)
                            delta1 = 100*mbm1/mbmresult1[-2]
                            percent1 = format(delta1,".2f")
                            deltalist1.append(percent1)
                            if delta1<=110:
                                status1 = "Pass"
                                passnum = passnum+1
                                statuslist1.append(status1)
                            elif delta1>110 and k== 60:
                                status1 = "Known Issue"
                                knownum = knownum+1
                                statuslist1.append(status1)
                            else:
                                status1 = "Fail"
                                failnum = failnum+1
                                statuslist1.append(status1)
                        elif k==10:
                            last = mbmresult1[-2]
                            last_mbmresult.append(last)
                            delta1 = 100*mbm1/mbmresult1[-2]
                            percent1 = format(delta1,".2f")
                            deltalist1.append(percent1)
                            if  delta1<= 110 and mbm1/mbmresult1[0]<0.33:
                                status1 = "Pass"
                                passnum = passnum+1
                                statuslist1.append(status1)
                            else:
                                status1 = "Fail"
                                failnum = failnum+1
                                statuslist1.append(status1)
                            if mbm1/mbmresult1[0]<0.33:
                                judge = "MBA10/MBA100 = "+str(format(mbm1/mbmresult1[0],".2f"))+" (< 0.33 P)"
                            else:
                                judge = "MBA10/MBA100 = "+str(format(mbm1/mbmresult1[0],".2f"))+" (>= 0.33 F)"
                        testnum = testnum+1
                        if float(delta2) <= 10:
                            status2 = "Pass"
                            statuslist2.append(status2)
                            passnum = passnum+1
                        else:
                            status2 = "Fail"
                            statuslist2.append(status2)
                            failnum = failnum + 1
                        testnum = testnum+1
                        print("Cycle: ", i, "Core: ",randcore,"COS1: ",randcos1,"COS2: ",randcos2, "Traffic",traffic,"MBA percentage: ",k,"MBM1: ", mbm1, "Percentage: ", percent1, "Status: ", status1,"MBM2: ", mbm2,"Delta_pct: ", percent2,"Status: ",status2 )
                print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","Traffic","COS1","MBA Percentage","MBM1","Percentage","Status","COS2","MBM2","Delta_pct","Status"))        
                for c, tf,cs1, ma, m1, pc, st1, cs2, m2, dt, st2 in zip(corelist, trafficlist,coslist1, mbalist,mbmresult1,deltalist1,statuslist1,coslist2,mbmresult2,deltalist2,statuslist2):
                    print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format(c,tf,cs1,ma,m1,pc,st1,cs2,m2,dt,st2))
                print("\n")
                print(judge)
        else:
            print("Wrong input")
        print("\n"*2)
        print("Number of tests: ", testnum, " Passed: ", passnum, " Known Issue: ", knownum," Failed: ", failnum)
        TESTMBA2().reset()
# Choose a method from iteration, random, custom
method = "random"
core = sys_info().max_thread()
cos1 = sys_info().max_cos()
cos2 = sys_info().max_cos()
cycle = 10
gettime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
cpath = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(cpath,"log")):
    os.makedirs(os.path.join(cpath,"log"))
logname = r"{}/log/Case18_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case18(method, core, cos1,cos2, cycle)


