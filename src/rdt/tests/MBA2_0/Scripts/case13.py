# -*- coding: utf-8 -*-
"""
Created on Wed May 20 16:16:01 2020

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
APP_NAME = 'case13'
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
    restartnumber = 0
    maxcos = pqos.max_cos
    maxdelay = None
    cos = random.sample(range(0,pqos.max_cos), 1)[0]
    core = random.sample(range(0,pqos.max_core), 1)[0]
    request_socket = int(2*core/pqos.max_core)
    mbmcount = 3
    cycle_flag = True
    mbl0 = []
    mbl1 = []
    throttlepercentlist=[100,90,80,70,60,50,40,30,20,10]
    svstart.build_socket_list(request_socket)
    
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
        with open(os.path.join(log_doc,'{}_result.log'.format(APP_NAME)),'w') as file:
            file.write('stresstool:{}, traffic:{}\n'.format(toolname,traffic))
            file.write('percent\t')
            file.write('origin\tafter change\tnext level\tdelta_f\tdelta_b\tresult')
            file.write('\n')
            for index,throttlepercent in enumerate(throttlepercentlist):
                time.sleep(15)
                #get default timewindow and MBAdelay
                default_timewindow = svstart.get_timewindow_ubox(request_socket, throttlepercent)
                default_mbadelay = svstart.get_mbadelay_ubox(request_socket, throttlepercent)
                if not index == 9:
                    next_timewindow = svstart.get_timewindow_ubox(request_socket, throttlepercentlist[index+1])
                    next_mbadelay = svstart.get_mbadelay_ubox(request_socket, throttlepercentlist[index+1])
                else:
                    next_timewindow = default_timewindow + 20
                    next_mbadelay = default_mbadelay + 20
                if next_timewindow < default_timewindow:
                    x_ = next_timewindow
                    next_timewindow = default_timewindow
                    default_timewindow = x_
                if next_mbadelay < default_mbadelay:
                    x_ = next_mbadelay
                    next_mbadelay = default_mbadelay
                    default_mbadelay = x_
                #set timewindow and MBAdelay list
                mid_tw = int((default_timewindow + next_timewindow)/2)
                mid_delay = int((default_mbadelay + next_mbadelay)/2)
                timewindow = int((random.randint(default_timewindow, min(255,mid_tw))+random.randint(min(255,mid_tw), min(255,next_timewindow)))/2)
                MBAdelay = int((random.randint(default_mbadelay, min(255,mid_delay))+random.randint(min(255,mid_delay), min(255,next_mbadelay)))/2)
                if timewindow > 255: timewindow = 255
                if MBAdelay > 255: MBAdelay = 255
                APP_LOG.info('-'*50)
                APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:regular, test tool:{} {}'.format(k+1, len(throttlepercentlist),toolname,traffic))
                APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} COS:{} Throttle Percent:{}% '.format(request_socket,core,cos,throttlepercent))
                #run stresstool
                stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
                stresstool.setDaemon(True)
                stresstool.start()
                time.sleep(4)
                #Reset to default MBA setting 
                pqos.reset()
                pqos.bindllc(cos, core)
                pqos.bindmba(cos, request_socket, throttlepercent)
                pqos.refresh()
                mbl_,mbr_,errorflag1 = pqos.getmbm(core)
                APP_LOG.info('MBL value before change:{}'.format(mbl_))
                mbl0.append(mbl_)
                svstart.change_timewindow(request_socket, cos, timewindow)
                svstart.change_mbadelay(request_socket, cos, MBAdelay)
                time.sleep(4)
                pqos.refresh()
                mbl_,mbr_,errorflag2 = pqos.getmbm(core)
                APP_LOG.info('MBL value after change:{}'.format(mbl_))
                mbl1.append(mbl_)
                
                k+=1
                stresstool.stop()
                if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                    APP_LOG.info('Find error in test, early terminate!')
                    APP_LOG.info('[warning]Please reboot system, then retest this case!')
                    sys.exit(1)
            benchmarkscale=0.10
            for index,mbl in enumerate(mbl0):
                throttlepercent = throttlepercentlist[index]
                if index+1 < len(mbl0):
                    file.write(str(throttlepercent)+'\t'+str(mbl0[index])+'\t'+str(mbl1[index])+'\t'+str(mbl0[index+1])+'\t'+str(round(100*(mbl0[index]-mbl1[index])/mbl0[index],2))+'\t')
                    file.write(str(round(100*(mbl1[index]-mbl0[index+1])/mbl0[index+1],2))+'\t')
                    if mbl1[index] < mbl0[index]*(1+benchmarkscale) and mbl1[index] > mbl0[index+1]*(1-benchmarkscale):
                        APP_LOG.info('[test result]>>Cycle:{}, Upper mbl {}*{} > Throttling mbl {} > Lower mbl {}*{}, test success!'.format(index+1,
                                                                                                                                             mbl0[index],
                                                                                                                                             1+benchmarkscale,
                                                                                                                                             mbl1[index],
                                                                                                                                             mbl0[index+1],
                                                                                                                                             1-benchmarkscale))
                        file.write('pass\n')
                        successcount+=1
                    elif mbl1[index] > mbl0[index]*(1+benchmarkscale):
                        APP_LOG.info('[test result]>>Cycle:{}, Upper mbl {}*{} < Throttling mbl {}, test fail!'.format(index+1,
                                                                                                                        mbl0[index],
                                                                                                                        1+benchmarkscale,
                                                                                                                        mbl1[index],
                                                                                                                        ))
                        file.write('fail\n')
                        failcount+=1
                    elif mbl1[index] < mbl0[index+1]*(1-benchmarkscale):
                        APP_LOG.info('[test result]>>Cycle:{}, Throttling mbl {} < Lower mbl {}*{}, test fail!'.format(index+1,
                                                                                                                        mbl1[index],
                                                                                                                        mbl0[index+1],
                                                                                                                        1-benchmarkscale))
                        file.write('fail\n')
                        failcount+=1
            
        
    if args.patten == 'random':
        throttlepercent=100
        #set timewindow and MBAdelay list
        timewindow = [x for x in range(0,128)]
        MBAdelay = [x for x in range(0,128)]
        for k in range(args.iteration):
            APP_LOG.info('-'*50)
            APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:random, test tool:{} {}'.format(k, args.iteration,toolname,traffic))
            APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} COS:{} '.format(request_socket,core,cos))
            #run stresstool
            stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
            stresstool.setDaemon(True)
            stresstool.start()
            time.sleep(2)
            #Reset to default MBA setting 
            pqos.reset()
            pqos.bindllc(cos, core)
            pqos.bindmba(cos, request_socket, throttlepercent)
            #Random select timewindow MBAdelay 
            tw = random.sample(timewindow, 1)[0]
            delay = random.sample(MBAdelay, 1)[0]
            pqos.refresh()
            mbl_,mbr_,errorflag1 = pqos.getmbm(core)
            APP_LOG.info('MBL value before change:{}'.format(mbl_))
            mbl0.append(mbl_)
            svstart.change_timewindow(request_socket, cos, tw)
            svstart.change_mbadelay(request_socket, cos, delay)
            time.sleep(2)
            pqos.refresh()
            mbl_,mbr_,errorflag2 = pqos.getmbm(core)
            APP_LOG.info('MBL value after change:{}'.format(mbl_))
            mbl1.append(mbl_)
            if  mbl0[k]*0.02 > (mbl1[k] - mbl0[k]) or mbl0[k] >mbl1[k]:
                APP_LOG.info('[test result]>>Throttling mbl {} >> {}, test success!'.format(mbl0[k],mbl1[k]))
                successcount+=1
            else:
                APP_LOG.info('[test result]>>Throttling mbl {} >> {}, test fail!'.format(mbl0[k],mbl1[k]))
                failcount+=1
            stresstool.stop()
            if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                APP_LOG.info('Find error in test, early terminate!')
                sys.exit(1)

    elif args.patten == 'traversal':
        throttlepercent = 100
        timewindow = [x for x in range(0,128)]
        MBAdelay = [x for x in range(0,128)]
        with open(os.path.join(log_doc,'{}_result.log'.format(APP_NAME)),'w') as file:
            file.write('delayvalue\\timewindow\t')
            for tw in timewindow:
                file.write(str(tw)+'\t')
            file.write('\n')
            k=0
            for delay in MBAdelay:
                file.write(str(delay)+'\t')
                for tw in timewindow:
                    APP_LOG.info('-'*50)
                    APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:traversal, test tool:{} {}'.format(k+1, len(MBAdelay)*(len(timewindow)),toolname, traffic))
                    APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} COS:{} '.format(request_socket,core,cos))
                    #run stresstool
                    stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
                    stresstool.setDaemon(True)
                    stresstool.start()
                    time.sleep(2)
                    #Reset to default MBA setting 
                    pqos.reset()
                    pqos.bindllc(cos, core)
                    pqos.bindmba(cos, request_socket, throttlepercent)
                    pqos.refresh()
                    mbl_,mbr_,errorflag1 = pqos.getmbm(core)
                    APP_LOG.info('MBL value before change:{}'.format(mbl_))
                    mbl0.append(mbl_)
                    svstart.change_timewindow(request_socket, cos, tw)
                    svstart.change_mbadelay(request_socket, cos, delay)
                    time.sleep(2)
                    pqos.refresh()
                    mbl_,mbr_,errorflag2 = pqos.getmbm(core)
                    APP_LOG.info('MBL value after change:{}'.format(mbl_))
                    mbl1.append(mbl_)
                    if  mbl0[k]*0.02 > (mbl1[k] - mbl0[k]) or mbl0[k] >mbl1[k]:
                        APP_LOG.info('[test result]>>Throttling mbl {} >> {}, test success!'.format(mbl0[k],mbl1[k]))
                        successcount+=1
                    else:
                        APP_LOG.info('[test result]>>Throttling mbl {} >> {}, test fail!'.format(mbl0[k],mbl1[k]))
                        failcount+=1
                    file.write(str(mbl_)+'\t')
                    k+=1
                    stresstool.stop()
                file.write('\n')
                if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                    APP_LOG.info('Find error in test, early terminate!')
                    sys.exit(1)
                    
    APP_LOG.info('#'*18+'  Test End  '+'#'*18)
    APP_LOG.info('Total test count:{}'.format(successcount+failcount))
    APP_LOG.info('Test success count:{}'.format(successcount))
    APP_LOG.info('Test fail count:{}'.format(failcount))
    
    
            
            