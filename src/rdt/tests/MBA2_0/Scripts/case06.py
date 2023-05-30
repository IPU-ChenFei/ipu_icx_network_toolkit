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
    def case06(self, core, cos, cycle=1):
        sys_info().show_sys_info()
        TESTMBA2().reset()
        TESTMBA2().refresh()
        global testnum
        global passnum
        global failnum
        testnum = 0
        passnum = 0
        failnum = 0
        for i in range(0, cycle):
            randcore = random.randint(0, core-1)
            randcos = random.randint(0, cos-1)
            randmba = random.randrange(0, 110, 10)
            traffic_info = TrafficType().get_traffic(randcore)
            command = traffic_info[1]
            traffic = traffic_info[0]
            mblresult = []
            mbrresult = []
            corelist = []
            coslist = []
            deltalist = []
            statuslist = []
            trafficlist = []
            rmidlist = []
            mbalist = []
            rmid = int(sys_info().max_rmid())
            for j in range(0,rmid):
                mbl=TESTMBA2().case06_RMID(command, randcore, randcos, randmba, j)
                mblresult.append(mbl)
                delta = abs(mbl-mblresult[0])
                delta_pct = 100*float(delta)/float(mblresult[0])
                percent = format(delta_pct,".2f")
                deltalist.append(str(percent))
                corelist.append(randcore)
                coslist.append(randcos)
                mbalist.append(randmba)
                rmidlist.append(j)
                trafficlist.append(traffic)
                if delta_pct<=20 and mbl < MBM_UPPER_LIMITATION:
                    status = "Pass"
                    passnum = passnum+1
                    statuslist.append(status)
                else:
                    status = "Fail"
                    failnum = failnum + 1
                    statuslist.append(status)
                testnum = testnum + 1
                print("Traffic: ",traffic,"RMID: ",j,"Core: ",randcore,"COS: ",randcos,"MBA: ",randmba,"MBM: ", mbl,"Delta_pct: ",percent,"Status",status)
            print("{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format("Traffic","MBA","RMID","Core","COS","MBL","Delta_pct", "Status"))
            for tf, ma, rm,cores, coss, ml, dt, st in zip(trafficlist, mbalist, rmidlist,  corelist, coslist,mblresult, deltalist, statuslist):
                print ("{:>12}\t {:>12}\t{:>12}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t".format(tf, ma, rm, cores,coss,ml,dt,st))
        print("\n"*2)
        print("Number of tests: ", testnum, "Passed: ", passnum, "Failed: ", failnum)
        TESTMBA2().reset()


# Choose a method from iteration, random, custom
core = sys_info().max_thread()
cos = sys_info().max_cos()
cycle = 1
gettime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
cpath = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists(os.path.join(cpath,"log")):
    os.makedirs(os.path.join(cpath,"log"))
logname = r"{}/log/Case06_result_".format(cpath)+gettime+".log"
if __name__ == '__main__':
    sys.stdout = Logger(logname, sys.stdout)
    case_execute().case06(core, cos, cycle)
    TESTMBA2().refresh()



