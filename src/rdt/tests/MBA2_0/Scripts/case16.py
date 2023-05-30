# -*- coding: utf-8 -*-
"""
Created on Mon Jun  8 09:28:57 2020

@author: leirong
"""

import argparse
import time
import os
import sys
import random
import logging
from common import toolbox
from testmodule import PqosChecker
from testmodule import PySVStartTool
from testmodule import StressTools
from testmodule import TERMINATE_ERROR
curPath = os.path.abspath(os.path.dirname(__file__))
sys.path.append(curPath)
sys.path.append("./")
if not os.path.exists(os.path.join(curPath,"log")):
    os.makedirs(os.path.join(curPath,"log"))
APP_NAME = 'case16'
log_doc = os.path.join(curPath,'log')
log_path=os.path.join(curPath,'log',APP_NAME + "_" + time.strftime("%Y-%m-%d_%H-%M-%S",time.localtime()) + '.log')
# Init logging for itself to track execution status
console = logging.StreamHandler()
console.setLevel(logging.INFO)
APP_LOG = toolbox.getLogger(APP_NAME)
APP_LOG.setFile(log_path)
APP_LOG.addHandler(console)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--patten', 
                            help='Chose the parameter with random or traversal, default is random',
                            dest='patten',
                            default='regular')
    arg_parser.add_argument('--iteration', 
                            help='Iteration number',
                            dest='iteration',
                            type=int,
                            default=1)
    arg_parser.add_argument('--stress_tool_path', 
                            help='Path of stress tool, default is /home/',
                            dest='stress_tool_path',
                            default='/home')
    arg_parser.add_argument('-t','--toolname', 
                            help='specify stress tool',
                            dest='toolname',
                            default=None)
    arg_parser.add_argument('-f','--traffic', 
                            help='traffic type of stress tool',
                            dest='traffic',
                            default=None)
    args = arg_parser.parse_args()
    #start pysvtool
    svstart = PySVStartTool(APP_LOG)
    #start pqos checker
    pqos = PqosChecker(APP_LOG)
    pqos.reset()
    pqos.refresh()
    #Read System info
    pqos.readsysinfo()
    pqos.printsysinfo()
    #case13 initial
    APP_LOG.info('='*50)
    APP_LOG.info('='*19+'  '+APP_NAME+'  '+'='*19)
    APP_LOG.info('='*50)
    successcount = 0
    failcount = 0
    maxcos = pqos.max_cos
    maxdelay = None
    cos = random.sample(range(0,pqos.max_cos), 1)[0]
    core = random.sample(range(0,pqos.max_core), 1)[0]
    request_socket = int(2*core/pqos.max_core)
    throttlepercentlist=[100,90,80,70,60,50,40,30,20,10]
    mbmcount = 3
    mbl0 = []
    mbl1 = []
    svstart.build_socket_list(request_socket)
    #get default unthrottle delay
    default_unthrottleddelay = svstart.get_unthrottleddelay(request_socket)
    #set unthrottle delay list
    # unthrottleddelay = [x for x in range(2,91,8)]
    unthrottleddelay = [2,4,7,10,14,19,25,30,35,45]
    #setup stress tool
    if args.toolname:
        toolname = args.toolname
    else:
        toollist = ['stream','mlc']
        toolname = random.sample(toollist, 1)[0]
    cachesize = 100
    if args.traffic:
        traffic = args.traffic
    else:
        trafficlist = ['W2','W3','W4','W5','W6','W7','W8','W9','W10','W11','W12','R']
        if toolname == 'mlc':
            traffic = random.sample(trafficlist, 1)[0]
        elif toolname == 'membw':
            traffic = random.sample(['read','nt-write'],1)[0]
        else:
            traffic = None
    #start test
    if args.patten == 'regular':
        k=0
        benchmarkscale_standard = 0.15
        with open(os.path.join(log_doc,'{}_result.log'.format(APP_NAME)),'w') as file:
            file.write('stresstool:{}, traffic:{}\n'.format(toolname,traffic))
            file.write('throttle percent\t')
            file.write('origin\t')
            for unt in unthrottleddelay:
                file.write('unthrottledelay{}\t'.format(unt))
            file.write('\n')
            for index,throttlepercent in enumerate(throttlepercentlist):
                time.sleep(15)
                APP_LOG.info('-'*50)
                APP_LOG.info('[test info]>>Change throttle percent')
                file.write(str(throttlepercent)+'\t')
                #run stresstool
                stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
                stresstool.setDaemon(True)
                stresstool.start()
                time.sleep(3)
                pqos.refresh()
                pqos.bindllc(cos, core)
                pqos.bindmba(cos, request_socket, throttlepercent)
                svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                pqos.refresh()
                time.sleep(5)
                mbl_1,mbr_,errorflag1 = pqos.getmbm(core)
                pqos.refresh()
                time.sleep(5)
                mbl_2,mbr_,errorflag2 = pqos.getmbm(core)
                mbl_ = (mbl_1 + mbl_2)/2
                mbl0.append(mbl_)
                file.write(str(mbl_))
                stresstool.stop()
                APP_LOG.info('MBL value after change throttle percent:{}'.format(mbl_))
                mbl1=[]
                if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                    APP_LOG.info('Find error in test, early terminate!')
                    APP_LOG.info('[warning]Please reboot system, then retest this case!')
                    svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                    sys.exit(1)
                for undelay in unthrottleddelay:
                    time.sleep(15)
                    if throttlepercent <= 20:
                        benchmarkscale = 0.3
                    else:
                        benchmarkscale = benchmarkscale_standard
                    APP_LOG.info('-'*50)
                    APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:random, test tool:{} {}'.format(k+1, len(unthrottleddelay)*len(throttlepercentlist),toolname,traffic))
                    APP_LOG.info('[pqos info]>>Socket:{}, logic Core:{}, COS:{}, unthrottle delay:{}, throttle percent:{}'.format(request_socket,core,cos,undelay,throttlepercent))
                    #run stresstool
                    stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
                    stresstool.setDaemon(True)
                    stresstool.start()
                    time.sleep(3)
                    #Reset to default MBA setting 
                    pqos.refresh()
                    svstart.change_unthrottleddelay(request_socket, undelay)
                    time.sleep(10)
                    mbl_1,mbr_,errorflag2 = pqos.getmbm(core)
                    pqos.refresh()
                    time.sleep(5)
                    mbl_2,mbr_,errorflag1 = pqos.getmbm(core)
                    mbl_ = (mbl_1 + mbl_2)/2
                    mbl1.append(mbl_)
                    APP_LOG.info('MBL value after change unthrottledelay:{}'.format(mbl_))
                    file.write('\t'+str(mbl_))
                    if len(mbl1) == 1:
                        if mbl1[0] < mbl0[-1]*(1+benchmarkscale):
                            APP_LOG.info('[test result]>>MBL {} < {}*{} test success'.format(mbl1[0],1+benchmarkscale,mbl0[-1]))
                            successcount+=1
                        else:
                            APP_LOG.info('[test result]>>MBL {} > {}*{} test fail'.format(mbl1[0],1+benchmarkscale,mbl0[-1]))
                            failcount+=1
                    # elif len(mbl1) == len(unthrottleddelay):
                    #     if mbl1[-1] > mbl1[0]*0.33:
                    #         APP_LOG.info('[test result]>>MBL {} > 0.33*{} test fail'.format(mbl1[-1],mbl1[0]))
                    #         failcount+=1
                    #     elif mbl1[-1] < mbl1[-2]*(1+benchmarkscale):
                    #         APP_LOG.info('[test result]>>MBL {} < {}*{} test success'.format(mbl1[-1],1+benchmarkscale,mbl1[-2]))
                    #         successcount+=1
                    #     else:
                    #         APP_LOG.info('[test result]>>MBL {} > {}*{} test fail'.format(mbl1[-1],1+benchmarkscale,mbl1[-2]))
                    #         failcount+=1
                    else:
                        if mbl1[-1] < mbl1[-2]*(1+benchmarkscale):
                            APP_LOG.info('[test result]>>MBL {} < {}*{} test success'.format(mbl1[-1],1+benchmarkscale,mbl1[-2]))
                            successcount+=1
                        else:
                            APP_LOG.info('[test result]>>MBL {} > {}*{} test fail'.format(mbl1[-1],1+benchmarkscale,mbl1[-2]))
                            failcount+=1
                    stresstool.stop()
                    if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                        APP_LOG.info('Find error in test, early terminate!')
                        APP_LOG.info('[warning]Please reboot system, then retest this case!')
                        svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                        sys.exit(1)
                    k+=1
                file.write('\n')
        pqos.reset()
        svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                    
    if args.patten == 'random':
        default_unthrottleddelay = 11
        #set unthrottle delay list
        unthrottleddelay = [x for x in range(default_unthrottleddelay,128)]
        throttlepercent = 50 #throttlepercent map: 10>3, 20>4, 30>5, 40>6, 50>7, 60>9, 70>12, 80>20, 90>39 
        for k in range(args.iteration):
            APP_LOG.info('-'*50)
            APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:random, test tool:{} {}'.format(k, args.iteration,toolname,traffic))
            APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} COS:{} throttle percent:{}'.format(request_socket,core,cos,throttlepercent))
            svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
            #run stresstool
            stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
            stresstool.setDaemon(True)
            stresstool.start()
            time.sleep(3)
            #Reset to default MBA setting 
            pqos.reset()
            pqos.bindllc(cos, core)
            pqos.bindmba(cos, request_socket, throttlepercent)
            pqos.refresh()
            mbl_,mbr_,errorflag1 = pqos.getmbm(core)
            APP_LOG.info('MBL value before change:{}'.format(mbl_))
            mbl0.append(mbl_)
            #Random select unthrottled delay
            undelay = random.sample(unthrottleddelay, 1)[0]
            #change unthrottled delay
            svstart.change_unthrottleddelay(request_socket, undelay)
            pqos.refresh()
            time.sleep(3)
            mbl_,mbr_,errorflag2 = pqos.getmbm(core)
            APP_LOG.info('MBL value after change:{}'.format(mbl_))
            mbl1.append(mbl_)
            if  mbl0[k] - mbl1[k] > mbl0[k]*0.02:
                APP_LOG.info('[test result]>>Throttling percent changed, mbl {} >> {} test success'.format(mbl0[k],mbl1[k]))
                successcount+=1
            else:
                APP_LOG.info('[test result]>>Throttling fail mbl {} >> {}'.format(mbl0[k],mbl1[k]))
                failcount+=1
            stresstool.stop()
            if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                APP_LOG.info('Find error in test, early terminate!')
                APP_LOG.info('[warning]Please reboot system, then retest this case!')
                svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                sys.exit(1)
        svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)

    elif args.patten == 'traversal':
        default_unthrottleddelay = 11
        throttlepercent = 50 #throttlepercent map: 10>3, 20>4, 30>5, 40>6, 50>7, 60>9, 70>12, 80>20, 90>39 
        #set unthrottle delay list
        unthrottleddelay = [x for x in range(default_unthrottleddelay,128)]
        with open(os.path.join(log_doc,'{}_result.log'.format(APP_NAME)),'w') as file:
            file.write('unthrottleddelay\t')
            file.write('beforechange\t afterchange\n')
            k=0
            for undelay in unthrottleddelay:
                file.write(str(undelay)+'\t')
                APP_LOG.info('-'*50)
                APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:traversal, test tool:{} {}'.format(k+1, len(unthrottleddelay),toolname,traffic))
                APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} COS:{} throttle percent:{}'.format(request_socket,core,cos,throttlepercent))
                svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                #run stresstool
                stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
                stresstool.setDaemon(True)
                stresstool.start()
                time.sleep(3)
                #Reset to default MBA setting 
                pqos.reset()
                pqos.bindllc(cos, core)
                pqos.bindmba(cos, request_socket, throttlepercent)
                pqos.refresh()
                mbl_,mbr_,errorflag1 = pqos.getmbm(core)
                APP_LOG.info('MBL value before change:{}'.format(mbl_))
                mbl0.append(mbl_)
                #change unthrottled delay
                svstart.change_unthrottleddelay(request_socket, undelay)
                time.sleep(3)
                pqos.refresh()
                mbl_,mbr_,errorflag2 = pqos.getmbm(core)
                APP_LOG.info('MBL value after change:{}'.format(mbl_))
                mbl1.append(mbl_)
                if  mbl0[k] - mbl1[k] > mbl0[k]*0.02:
                    APP_LOG.info('[test result]>>Throttling percent changed, mbl {} >> {} test success'.format(mbl0[k],mbl1[k]))
                    successcount+=1
                else:
                    APP_LOG.info('[test result]>>Throttling fail mbl {} >> {}'.format(mbl0[k],mbl1[k]))
                    failcount+=1
                file.write(str(mbl0[k])+'\t'+str(mbl1[k])+'\n')
                k+=1
                stresstool.stop()
                if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                    APP_LOG.info('Find error in test, early terminate!')
                    APP_LOG.info('[warning]Please reboot system, then retest this case!')
                    svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                    sys.exit(1)
            svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
    APP_LOG.info('#'*18+'  Test End  '+'#'*18)
    APP_LOG.info('Total test count:{}'.format(successcount+failcount))
    APP_LOG.info('Test success count:{}'.format(successcount))
    APP_LOG.info('Test fail count:{}'.format(failcount))
    
    
  