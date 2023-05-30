from mba2_functions import *
import re
import random
import sys
import time
import os
import argparse
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
    def case02(self, method, core, cos, cycle=1):
        sys_info().show_sys_info()
        TESTMBA2().reset()
        global testnum
        global passnum
        global failnum
        global knownum
        knownum = 0
        testnum = 0
        passnum = 0
        failnum = 0
        if method == "iteration":
            mbmresult = []
            mbalist = []
            corelist = []
            coslist = []
            statuslist = []
            deltalist = []
            for i in range(0, core):
                for j in range(0, cos):
                    for k in range(100, 0, -10):
                        mbm = TESTMBA2().case02_MBA(i, j, k)
                        mbm1 = int(mbm)
                        mbmresult.append(mbm1)
                        corelist.append(i)
                        coslist.append(j)
                        mbalist.append(k)
                        delta = 100*mbm1/mbmresult[0]
                        deltalist.append(delta)
                        if abs(k-delta)<=10:
                            status = "Pass"
                            passnum = passnum+1
                            statuslist.append(status)
                        else: 
                            status = "Fail"
                            failnum = failnum+1
                            statuslist.append(status)
                        testnum = testnum+1
                        print("Core: ",i,"COS: ",j,"MBA percentage: ",k,"MBM: ", mbm, "Percentage: ", delta, "Status: ", status)
                    print("\n")
                    print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","MBA Percentage","MBM","Percentage","Status"))
                    for cores, coss, key, value, pc, st in zip(corelist, coslist, mbalist, memresult,deltalist, statuslist):
                        print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t {:>12}\t".format(cores,coss, key, value,pc,st))
        elif method == "random":
            for i in range(0, cycle):
                global judge
                mbmresult = []
                mbalist = []
                corelist = []
                coslist = []
                statuslist = []
                deltalist = []
                trafficlist = []
                last_mbmresult = []
                randcore = random.randint(0, core-1)
                randcos = random.randint(0,cos-1)
                traffic_info = TrafficType().get_traffic(randcore)
                command = "/home/intel-cmt-cat-master/tools/membw/membw -c "+str(randcore)+" -b 100000 --read"
                #traffic = traffic_info[0]
                traffic = "membw_r"
                for k in range(100, 0, -10):
                        mbm = TESTMBA2().case02_MBA(command,randcore, randcos, k)
                        mbm1 = int(mbm)
                        corelist.append(randcore)
                        coslist.append(randcos)
                        mbmresult.append(mbm1)
                        mbalist.append(k)
                        trafficlist.append(traffic)
                        #delta = 100*mbm1/mbmresult[0]
                        #deltalist.append(delta)
                        if k==100:
                            last = mbm1
                            last_mbmresult.append(last)
                            status = "Pass"
                            passnum = passnum+1
                            statuslist.append(status)
                            delta = 100*mbm1/mbm1
                            percent = format(delta,".2f")
                            deltalist.append(percent)
                        elif k<100 and k>10:
                            last = mbmresult[-2]
                            last_mbmresult.append(last)
                            delta = 100*mbm1/mbmresult[-2]
                            percent = format(delta,".2f")
                            deltalist.append(percent)
                            if delta<=110:
                                status = "Pass"
                                passnum = passnum+1
                                statuslist.append(status)
                            elif delta>110 and k== 60:
                                status = "Known Issue"
                                knownum = knownum+1
                                statuslist.append(status)
                            else:
                                status = "Fail"
                                failnum = failnum+1
                                statuslist.append(status)
                        elif k==10:
                            last = mbmresult[-2]
                            last_mbmresult.append(last)
                            delta = 100*mbm1/mbmresult[-2]
                            percent = format(delta,".2f")
                            deltalist.append(percent)
                            if  delta<= 110 and mbm1/mbmresult[0]<0.33:
                                status = "Pass"
                                passnum = passnum+1
                                statuslist.append(status)
                            else:
                                status = "Fail"
                                failnum = failnum+1
                                statuslist.append(status)
                            if mbm1/mbmresult[0]<0.33:
                                judge = "MBA10/MBA100 = "+str(format(mbm1/mbmresult[0],".2f"))+" (< 0.33 P)"
                            else:
                                judge = "MBA10/MBA100 = "+str(format(mbm1/mbmresult[0],".2f"))+" (>= 0.33 F)"
                        testnum = testnum+1
                        print("Cycle: ", i, "Core: ",randcore,"COS: ",randcos,"Traffic: ",traffic,"MBA percentage: ",k,"Last MBM: ",last,"MBM: ", mbm1,"Percentage: ",percent ,"Status: ", status)
                print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","Traffic","MBA Percentage","Last MBM","MBM","Percent(<110)","Status"))        
                for cores, coss, tf,ma,lm,m,pc,st in zip(corelist, coslist,trafficlist, mbalist,last_mbmresult,mbmresult,deltalist,statuslist):
                    print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t {:>12}\t".format(cores,coss,tf,ma,lm,m,pc,st))
                print("\n")
                print(judge)
        elif method == "custom":
            mbmresult = []
            mba_pct = []
            statuslist = []
            deltalist = []
            for k in range(100, 0, -10):
                        mbm = TESTMBA2().case02_MBA(core, cos, k)
                        mbm1 = int(mbm)
                        mbmresult.append(mbm1)
                        mba_pct.append(k)
                        delta = 100*mbm1/mbmresult[0]
                        deltalist.append(delta)
                        if abs(k-delta)<=5:
                            status = "Pass"
                            passnum = passnum+1
                            statuslist.append(status)
                        else:
                            status = "Fail"
                            failnum = failnum+1
                            statuslist.append(status)
                        testnum = testnum+1
                        print("Core: ",core,"COS: ",cos,"MBA percentage: ",k,"MBM: ", mbm, "Percentage: ", delta, "Status: ", status)
            print("\n")
            print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Core","COS","MBA Percentage","MBM","Percentage","Status"))
            for key, value ,pc,st in zip(mba_pct,mbmresult,deltalist,statuslist):
                print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t".format(core,cos,key,value))
        else:
            print("Wrong input")
        print("\n"*2)
        print("Number of tests: ", testnum,"Passed: ", passnum, "Known Issue: ",knownum ,"Failed: ", failnum)
        TESTMBA2().reset()


# Choose a method from iteration, random, custom
parser = argparse.ArgumentParser()
parser.add_argument("-allcores","--allcores", help="Choose to iter with all cores", action="store_true")
args = parser.parse_args()
if args.allcores:
    method = "iteration"
else:
    method = "random"
print("Run method: ", method)
core = sys_info().max_thread()
cos = sys_info().max_cos()
cycle = 10
gettime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
cpath = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(cpath,"log")):
    os.makedirs(os.path.join(cpath,"log"))
logname = r"{}/log/Case02_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case02(method, core, cos, cycle)


