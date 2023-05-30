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
    def case11(self, method, core1,core2, cos1, cycle=1):
        sys_info().show_sys_info()
        TESTMBA2().reset()
        TESTMBA2().refresh()
        stress_tools().kill_tool()
        resetmsrCommand = "wrmsr -a 0xC84 2"
        resetmsr = subprocess.Popen(resetmsrCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,shell=True)
        global testnum
        global passnum
        global failnum
        global knownum
        knownum = 0
        testnum = 0
        passnum = 0
        failnum = 0
        testnum1 = 0
        testnum2 = 0
        testnum3 = 0
        testnum4 = 0
        if method == "random":
            for i in range(0, cycle):
                randcore1 = random.randint(0, core1-1)
                randcos1 = random.randint(1,cos1-1)
                randcore2 = random.randint(0, core2-1)
                while randcore1 == randcore2:
                    randcore2 = randcore2 = random.randint(0, core2-1)
                randcos2 = randcos1
                traffic_info = TrafficType().get_same_traffics(randcore1,randcore2)
                command1 = traffic_info[1]
                command2 = traffic_info[2]
                traffic1 = traffic_info[0]
                traffic2 = traffic_info[0]
                result = []
                mbmmax1result = []
                mbmmin1result = []
                mbmmax2result = []
                mbmmin2result = []
                core1list = []
                cos1list = []
                core2list = []
                cos2list = []
                status1list = []
                status2list = []
                status3list = []
                status4list = []
                mba2list = []
                mba1list = []
                delta1list = []
                delta2list = []
                delta3list = []
                delta4list = []
                traffic1list = []
                traffic2list = []
                last_mbm1result = []
                last_mbm2result = []
                for k in range(100, 0, -10):
                        mbm = TESTMBA2().case11_MinMax_DiffCore_SameCOS(command1, command2, randcore1, randcos1, randcore2, randcos2, k)
                        mbmmax1 = float(mbm[0])
                        mbmmin1 = float(mbm[1])
                        mbmmax2 = float(mbm[2])
                        mbmmin2 = float(mbm[3])
                        mbmmax1result.append(mbmmax1)
                        mbmmin1result.append(mbmmin1)
                        mbmmax2result.append(mbmmax2)
                        mbmmin2result.append(mbmmin2)
                        core1list.append(randcore1)
                        core2list.append(randcore2)
                        cos1list.append(randcos1)
                        cos2list.append(randcos2)
                        mba1list.append(k)
                        traffic1list.append(traffic1)
                        if k==100:
                            last1 = mbmmax1
                            last_mbm1result.append(last1)
                            status1 = "Pass"
                            passnum = passnum+1
                            status1list.append(status1)
                            delta1 = 100*mbmmax1/mbmmax1
                            percent1 = format(delta1,".2f")
                            delta1list.append(percent1)
                        elif k<100 and k>10:
                            last1 = mbmmax1result[-2]
                            last_mbm1result.append(last1)
                            delta1 = 100*mbmmax1/mbmmax1result[-2]
                            percent1 = format(delta1,".2f")
                            delta1list.append(percent1)
                            if delta1<=110:
                                status1 = "Pass"
                                passnum = passnum+1
                                status1list.append(status1)
                            elif delta1>110 and k== 60:
                                status1 = "Known Issue"
                                knownum = knownum+1
                                status1list.append(status1)
                            else:
                                status1 = "Fail"
                                failnum = failnum+1
                                status1list.append(status1)
                        elif k==10:
                            last1 = mbmmax1result[-2]
                            last_mbm1result.append(last1)
                            delta1 = 100*mbmmax1/mbmmax1result[-2]
                            percent1 = format(delta1,".2f")
                            delta1list.append(percent1)
                            if  delta1<= 110 and mbmmax1/mbmmax1result[0]<0.33:
                                status1 = "Pass"
                                passnum = passnum+1
                                status1list.append(status1)
                            else:
                                status1 = "Fail"
                                failnum = failnum+1
                                status1list.append(status1)
                            if mbmmax1/mbmmax1result[0]<0.33:
                                judge1 = "For core1: MBA10/MBA100 = "+str(format(mbmmax1/mbmmax1result[0],".2f"))+" (< 0.33 P)"
                            else:
                                judge1 = "For core2: MBA10/MBA100 = "+str(format(mbmmax1/mbmmax1result[0],".2f"))+" (>= 0.33 F)"
                        testnum1 = testnum1+1
                        if k==100:
                            last2 = mbmmax2
                            last_mbm2result.append(last2)
                            status2 = "Pass"
                            passnum = passnum+1
                            status2list.append(status2)
                            delta2 = 100*mbmmax2/mbmmax2
                            percent2 = format(delta2,".2f")
                            delta2list.append(percent2)
                        elif k<100 and k>10:
                            last2 = mbmmax2result[-2]
                            last_mbm2result.append(last2)
                            delta2 = 100*mbmmax2/mbmmax2result[-2]
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
                            last2 = mbmmax2result[-2]
                            last_mbm2result.append(last2)
                            delta2 = 100*mbmmax2/mbmmax2result[-2]
                            percent2 = format(delta2,".2f")
                            delta2list.append(percent2)
                            if  delta2<= 110 and mbmmax2/mbmmax2result[0]<0.33:
                                status2 = "Pass"
                                passnum = passnum+1
                                status2list.append(status2)
                            else:
                                status2 = "Fail"
                                failnum = failnum+1
                                status2list.append(status2)
                            if mbmmax2/mbmmax2result[0]<0.33:
                                judge2 = "For core2: MBA10/MBA100 = "+str(format(mbmmax2/mbmmax2result[0],".2f"))+" (< 0.33 P)"
                            else:
                                judge2 = "For core2: MBA10/MBA100 = "+str(format(mbmmax2/mbmmax2result[0],".2f"))+" (>= 0.33 F)"
                        testnum2 = testnum2+1
                        #delta1 = 100*mbmmax1/mbmmax1result[0]
                        #percent1 = format(delta1,".2f")
                        #delta2 = 100*abs(mbmmin1-mbmmin1result[0])/mbmmin1result[0]
                        #percent2 = format(delta2,".2f")
                        #delta3 = 100*mbmmax2/mbmmax2result[0]
                        #percent3 = format(delta3,".2f")
                        #delta4 = 100*abs(mbmmin2-mbmmin2result[0])/mbmmin2result[0]
                        #percent4 = format(delta4,".2f")
                        #delta1list.append(str(percent1)+"%")
                        #delta2list.append(str(percent2)+"%")
                        #delta3list.append(str(percent3)+"%")
                        #delta4list.append(str(percent4)+"%")
                        #if abs(k-float(percent1)) <= 5:
                        #    status1 = "Pass"
                        #    status1list.append(status1)
                        #    passnum = passnum + 1
                        #else:
                        #    status1 = "Fail"
                        #    status1list.append(status1)
                        #    failnum = failnum + 1
                        #testnum1=testnum1+1
                        #if float(percent2) <= 5:
                        #    status2 = "Pass"
                        #    status2list.append(status2)
                            #passnum = passnum+1
                        #else:
                        #    status2 = "Fail"
                        #    status2list.append(status2)
                            #failnum = failnum + 1
                        #testnum2 = testnum2+1
                        #if abs(k-float(percent3)) <= 5:
                        #    status3 = "Pass"
                        #    status3list.append(status3)
                        #    passnum = passnum + 1
                        #else:
                        #    status3 = "Fail"
                        #    status3list.append(status3)
                        #    failnum = failnum + 1
                        #testnum3=testnum3+1
                        #if float(percent2) <= 5:
                        #    status2 = "Pass"
                        #    status2list.append(status2)
                            #passnum = passnum+1
                        #else:
                        #    status2 = "Fail"
                        #    status2list.append(status2)
                            #failnum = failnum + 1
                        #testnum2 = testnum2+1
                        testnum = testnum1+testnum2+testnum3+testnum4
                        print("Cycle:", i,"Traffic",traffic1, "Core1: ", randcore1, "COS1: ", randcos1, "MBA percentage: ", k)
                        print("Cycle:", i, "Core2: ", randcore2, "COS2: ", randcos2)
                        print("MBMMax1:",mbmmax1,"MBMMax2",mbmmax2 )
                print("\n")
                print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core1","Traffic","COS1","MBA","MBMMax1","Percent1<105","Status1","Core2","COS2","MBMMax2","Percent2<105","Status2"))
                for tf,c1,cs1,ma1,m1,pc1,st1,c2,cs2,m2,pc2,st2 in zip(traffic1list, core1list,cos1list,mba1list,mbmmax1result,delta1list,status1list,core2list,cos2list,mbmmax2result,delta2list,status2list):
                    print ("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t".format(tf, c1,cs1,ma1,m1,pc1,st1,c2,cs2,m2,pc2,st2))
                print("\n")
                print(judge1)
                print(judge2)
        else:
            print("Wrong input")
        print("\n"*2)
        print("Number of tests: ", testnum, " Passed: ", passnum, " Known Issue: ", knownum," Failed: ", failnum)
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
logname = r"{}/log/Case11_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case11(method, core1, core2, cos1, cycle)


