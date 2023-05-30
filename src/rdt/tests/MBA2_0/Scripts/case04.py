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
    def case04(self, method, core1, core2, cos1, cos2, mba1, cycle=1):
        sys_info().show_sys_info()
        TESTMBA2().reset()
        global testnum
        global passnum
        global failnum
        global knownum
        global testnum1
        global testnum2
        knownum = 0
        testnum = 0
        testnum1 = 0
        testnum2 = 0
        passnum = 0
        failnum = 0
        result = []
        if method == "custom":
            mbmresult = []
            mbm2result = []
            core1list = []
            cos1list = []
            core2list = []
            cos2list = []
            status1list = []
            status2list = []
            mba1list = []
            mba2list = []
            delta1list = []
            delta2list = []
            trafficlist1 = []
            trafficlist2 = []
            last_mbm2result = []
            randcos1 = cos1
            randcore1 = core1
            traffic_info1 = TrafficType().get_traffic(randcore1)
            command1 = traffic_info1[1]
            traffic1 = traffic_info1[0]
            randcos2 = cos2
            randcore2 = core2
            traffic_info2 = TrafficType().get_traffic(randcore2)
            command2 = traffic_info2[1]
            traffic2 = traffic_info2[0]
            for k in range(100, 0, -10):
                        mbm = TESTMBA2().case04_unusedCOS(command1,command2,randcore1,randcore2, cos1, cos2, mba1, k)
                        mbm1 = int(mbm[0])
                        mbm2 = int(mbm[1])
                        result.append(mbm1)
                        mbmresult.append(mbm1)
                        mbm2result.append(mbm2)
                        core1list.append(randcore1)
                        core2list.append(randcore2)
                        cos1list.append(cos1)
                        cos2list.append(cos2)
                        trafficlist1.append(traffic1)
                        trafficlist2.append(traffic2)
                        mba1list.append(mba1)
                        mba2list.append(k)
                        delta1 = 100*abs(mbm1-mbmresult[0])/mbmresult[0]
                        percent1 = format(delta1,".2f")
                        delta1list.append(percent1)
                        if abs(mbm1-result[0])<=result[0]*0.10:
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
                                status2 = "Known Issue"
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
                        testnum = testnum1 + testnum2
                        print("Cycle: ",cycle, "Core1: ",randcore1,"COS1: ",cos1,"Traffic: ",traffic1,"MBA percentage: ",mba1,"MBM: ", mbm1, "MBM1 delta: ", percent1, "Status: ", status1)
                        print("Cycle: ",cycle, "Core2: ",randcore2,"COS2: ",cos2,"Traffic: ",traffic2,"MBA percentage: ",k,"MBM: ", mbm2,"Percent: ", percent2, "Status: ", status2)
            print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core1","COS1","Traffic1","MBM1","MBA1","Delta","Status","Core2","COS2","Traffic2","MBA2","MBM2","Percent(<110)","Status"))
            for c1,cs1,tf1,ma1,m1,dt1,st1,c2,cs2,tf2,ma2,m2,dt2,st2 in zip(core1list,cos1list,trafficlist1,mbmresult,mba1list,delta1list,status1list,core2list,cos2list,trafficlist2,mba2list,mbm2result,delta2list,status2list):
                    print ("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format(c1,cs1,tf1,ma1,m1,dt1,st1,c2,cs2,tf2,ma2,m2,dt2,st2))
            print("\n")
            print(judge)
        else:
            print("Wrong input")
        print("\n"*2)
        print("Number of tests: ", testnum, " Passed: ", passnum, " Known Issue: ",knownum ," Failed: ", failnum)
        TESTMBA2().reset()


# Choose a method from iteration, random, custom
method = "custom"
core1 = 1
cos1 = 1
core2 = 20
cos2 = 2
mba1 = 100
cycle = 1
gettime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
cpath = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(cpath,"log")):
    os.makedirs(os.path.join(cpath,"log"))
logname = r"{}/log/Case04_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case04(method, core1, core2, cos1, cos2, mba1, cycle)


