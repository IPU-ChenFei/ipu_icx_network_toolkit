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
    def case05(self, method, core1, core2, cos1, cos2, mba1, cycle=1):
        sys_info().show_sys_info()
        TESTMBA2().reset()
        global testnum1
        global testnum
        global passnum
        global failnum
        global testnum2
        global knownum
        knownum = 0
        testnum1 = 0
        testnum2 = 0
        passnum = 0
        failnum = 0
        testnum = 0
        if method == "iteration":
            mbmresult = []
            mbm2result = []
            core1list = []
            cos1list = []
            core2list = []
            cos2list = []
            statuslist = []
            mbalist = []
            deltalist = []
            randmba1 = random.randrange(10, 110, 10)
            for i in range(0, core1):
                for j in range(0, cos1):
                    for m in range(0, core2):
                        for n in range(0, cos2):
                            result = []
                            for k in range(10, 110, 10):
                                mbm = TESTMBA2().case05_unusedCOS(i, m, j, n, randmba1, k)
                                mbm1 = float(mbm[0])
                                mbm2 = float(mbm[1])
                                result.append(mbm1)
                                mbmresult.append(mbm1)
                                mbm2result.append(mbm2)
                                core1list.append(i)
                                core2list.append(m)
                                cos1list.append(j)
                                cos2list.append(n)
                                mbalist.append(k)
                                delta = 100*abs(mbm1-mbmresult[0])/mbmresult[0]
                                percent = format(delta,".2f")
                                deltalist.append(percent)
                                if abs(mbm1 - result[0]) <= result[0]*0.1:
                                    status = "Pass"
                                    statuslist.append(status)
                                    passnum = passnum + 1
                                else:
                                    status = "Fail"
                                    statuslist.append(status)
                                    failnum = failnum + 1
                                testnum = testnum + 1
                                print("Core1: ",i,"COS1: ",j,"MBA percentage: ",randmba1,"MBM: ", mbm1, "MBM delta: ", abs(mbm1-result[0]), "Status: ", status)
                                print("Core2: ",m,"COS2: ",n,"MBA percentage: ",k,"MBM: ", mbm2)
                            print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core1","COS1","MBM1","Core2","COS2","MBA2","MBM2","Delta","Status"))
                            for c1,cs1,m1,c2,cs2,ma1,m2,dt,s in zip(core1list,cos1list,mbmresult,core2list,cos2list,mbalist,mbm2result,deltalist,statuslist):
                                print ("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t".format(c1,cs1,m1,c2,cs2,ma1,m2,dt,s))

        elif method == "random":
            for i in range(0, cycle):
                randcos1 = random.randint(1,cos1-1)
                randcos2 = random.randint(1, cos2 - 1)
                randmba1 = random.randrange(10, 110, 10)
                randcore1 = random.randint(0, core1-1)
                randcore2 = random.randint(0, core2-1)
                traffic_info1 = TrafficType().get_traffic(randcore1)
                command1 = traffic_info1[1]
                traffic1 = traffic_info1[0]
                traffic_info2 = TrafficType().get_traffic(randcore2)
                command2 = traffic_info2[1]
                traffic2 = traffic_info2[0]
                while randcore1 == randcore2:
                    randcore2 = random.randint(0, core2-1)
                while randcos1 == randcos2:
                    randcos2= random.randint(1, cos2 - 1)
                while abs(randcore1-randcore2)== int(core1/2):
                    randcore2 = random.randint(0, core2-1)
                result = []
                mbmresult = []
                mbm2result = []
                core1list = []
                cos1list = []
                core2list = []
                cos2list = []
                status1list = []
                status2list = []
                mba2list = []
                mba1list = []
                delta1list = []
                delta2list = []
                trafficlist1 = []
                trafficlist2 = []
                last_mbm2result = []
                for k in range(100, 0, -10):
                        mbm = TESTMBA2().case05_unusedCOS(command1,command2,randcore1, randcore2, randcos1, randcos2, randmba1, k)
                        mbm1 = int(mbm[0])
                        mbm2 = int(mbm[1])
                        while mbm1<100 or mbm2<100:
                            mbm = TESTMBA2().case05_unusedCOS(command1,command2,randcore1, randcore2, randcos1, randcos2, randmba1, k)
                            mbm1 = int(mbm[0])
                            mbm2 = int(mbm[1])
                        result.append(mbm1)
                        mbmresult.append(mbm1)
                        mbm2result.append(mbm2)
                        core1list.append(randcore1)
                        core2list.append(randcore2)
                        cos1list.append(randcos1)
                        cos2list.append(randcos2)
                        mba1list.append(randmba1)
                        mba2list.append(k)
                        trafficlist1.append(traffic1)
                        trafficlist2.append(traffic2)
                        delta1 = 100*abs(mbm1-mbmresult[0])/mbmresult[0]
                        percent1 = format(delta1,".2f")
                        delta1list.append(percent1)
                        if float(percent1) <= 10:
                            status1 = "Pass"
                            status1list.append(status1)
                            passnum = passnum + 1
                        else:
                            status1 = "Fail"
                            status1list.append(status1)
                            failnum = failnum + 1
                        testnum1 = testnum1+1
                        if k==100:
                            last = mbm2
                            last_mbm2result.append(last)
                            status2 = "Pass"
                            passnum = passnum+1
                            status2list.append(status2)
                            delta2 = 100*mbm2/mbm2
                            percent2 = format(delta2,".2f")
                            delta2list.append(percent2)
                        elif k<100 and k>10:
                            last = mbm2result[-2]
                            last_mbm2result.append(last)
                            delta2 = 100*mbm2/mbm2result[-2]
                            percent2 = format(delta2,".2f")
                            delta2list.append(percent2)
                            if delta2<=110:
                                status2 = "Pass"
                                passnum = passnum+1
                                status2list.append(status2)
                            elif delta2>110 and k== 60:
                                status = "Known Issue"
                                knownum = knownum+1
                                status2list.append(status2)
                            else:
                                status2 = "Fail"
                                failnum = failnum+1
                                status2list.append(status2)
                        elif k==10:
                            last = mbm2result[-2]
                            last_mbm2result.append(last)
                            delta2 = 100*mbm2/mbm2result[-2]
                            percent2 = format(delta2,".2f")
                            delta2list.append(percent2)
                            if  delta2<= 110 and mbm2/mbm2result[0]<0.33:
                                status2 = "Pass"
                                passnum = passnum+1
                                status2list.append(status2)
                            else:
                                status2 = "Fail"
                                failnum = failnum+1
                                status2list.append(status2)
                            if mbm2/mbm2result[0]<0.33:
                                judge = "MBA10/MBA100 = "+str(format(mbm2/mbm2result[0],".2f"))+" (< 0.33 P)"
                            else:
                                judge = "MBA10/MBA100 = "+str(format(mbm2/mbm2result[0],".2f"))+" (>= 0.33 F)"
                        testnum2 = testnum2+1
                        testnum = testnum1+testnum2
                        #delta2 = 100*mbm2/mbm2result[0]
                        #percent2 = format(delta2,".2f")
                        #delta2list.append(percent2)
                        #if abs(k-delta2)<=5:
                        #    status2 = "Pass"
                        #    passnum = passnum+1
                        #    status2list.append(status2)
                        #else:
                        #    status2 = "Fail"
                        #    failnum = failnum+1
                        #    status2list.append(status2)
                        #testnum2 = testnum2+1
                        print("Cycle:", i, "Core1: ", randcore1, "COS1: ", randcos1, "Traffic: ",traffic1,"MBA percentage: ", randmba1, "MBM: ", mbm1, "MBM1 delta: ",percent1, "Status: ", status1)
                        print("Cycle:", i, "Core2: ", randcore2, "COS2: ", randcos2, "Traffic: ",traffic2,"MBA percentage: ", k, "MBM: ", mbm2,"MBM2 delta: ",percent2,"Status: ",status2)
                print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core1","COS1","Traffic1","MBA1","MBM1","Delta","Status","Core2","COS2","Traffic2","MBA2","MBM2","Percent(<105)","Status"))
                for c1,cs1,tf1,m1,ma1,dt1,st1,c2,cs2,tf2,ma2,m2,dt2,st2 in zip(core1list,cos1list,trafficlist1,mba1list,mbmresult,delta1list,status1list,core2list,cos2list,trafficlist2,mba2list,mbm2result,delta2list,status2list):
                    print ("{:>12}\t{:>12}\t{:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format(c1,cs1,tf1,m1,ma1,dt1,st1,c2,cs2,tf2,ma2,m2,dt2,st2))
                print("\n")
                print(judge)
        elif method == "custom":
            result = []
            mbmresult = []
            mbm2result = []
            core1list = []
            cos1list = []
            core2list = []
            cos2list = []
            statuslist = []
            mbalist = []
            for k in range(10, 110, 10):
                        mbm = TESTMBA2().case05_unusedCOS(core1, core2, cos1, cos2, mba1, k)
                        mbm1 = int(mbm[0])
                        mbm2 = int(mbm[1])
                        result.append(mbm1)
                        mbmresult.append(mbm1)
                        mbm2result.append(mbm2)
                        core1list.append(core1)
                        core2list.append(core2)
                        cos1list.append(cos1)
                        cos2list.append(cos2)
                        mbalist.append(k)
                        if abs(mbm1-result[0])<=result[0]*0.05:
                            status = "Pass"
                            statuslist.append(status)
                            passnum = passnum + 1
                        else:
                            status = "Fail"
                            statuslist.append(status)
                            failnum = failnum + 1
                        testnum = testnum+1
                        print("Cycle: ",cycle, "Core1: ",core1,"COS1: ",cos1,"MBA percentage: ",mba1,"MBM: ", mbm1, "MBM delta: ", abs(mbm1-result[0]), "Status: ", status)
                        print("Cycle: ",cycle, "Core2: ",core2,"COS2: ",cos2,"MBA percentage: ",k,"MBM: ", mbm2)
            print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core1","COS1","MBM1","Core2","COS2","MBA2","MBM2","Status"))
            for c1,cs1,m1,c2,cs2,ma1,m2,s in zip(core1list,cos1list,mbmresult,core2list,cos2list,mbalist,mbm2result,statuslist):
                    print ("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t {:>12}\t{:>12}\t".format(c1,cs1,m1,c2,cs2,ma1,m2,s))
        else:
            print("Wrong input")
        print("\n"*2)
        print("Number of tests: ", testnum, " Passed: ", passnum," Known Issue: ",knownum, " Failed: ", failnum)
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
logname = r"{}/log/Case05_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case05(method, core1, core2, cos1, cos2, mba1, cycle)


