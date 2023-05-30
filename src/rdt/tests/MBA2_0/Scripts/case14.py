# -*- coding: utf-8 -*-
"""
Created on Fri May 29 14:07:28 2020

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
APP_NAME = 'case14'
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
    mbmcount = 3
    mbl0 = []
    mbl1 = []
    request_socket = int(2*core/pqos.max_core)
    throttlepercentlist=[100,90,80,70,60,50,40,30,20,10]
    throttlepercent = 100
    svstart.build_socket_list(request_socket)
    coslist = [x for x in range(pqos.max_cos)]
    LeakyBucketSize = [x for x in range(pow(2,16))]
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
        random.shuffle(coslist)
        if not len(coslist)%2 == 0:
            coslist.pop(-1)
        cosgroup = [coslist[i:i+2] for i in range(0,len(coslist),2)]
        k=0
        timewindow = [x for x in range(0,128)]
        MBAdelay = [x for x in range(0,128)]
        for group in cosgroup:
            if not group[1] == 0:
                stress_cos = group[0]
                cos = group[1]
            else:
                stress_cos = group[1]
                cos = group[0]
            with open(os.path.join(log_doc,'{}_S'.format(APP_NAME)+str(stress_cos)+'_A'+str(cos)+'_result.log'),'w') as file:
                file.write('stresstool:{}, traffic:{}\n'.format(toolname,traffic))
                file.write('percent\t')
                file.write('origin\tafter change\tdelta\tresult')
                file.write('\n')
                for index,throttlepercent in enumerate(throttlepercentlist):
                    time.sleep(15)
                    file.write(str(throttlepercent)+'\t')
                    # for lbsize in LeakyBucketSize:
                    APP_LOG.info('-'*50)
                    APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:traversal, test tool:{} {}'.format(k+1, len(cosgroup)*len(throttlepercentlist),toolname, traffic))
                    APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} Stress COS:{} Applied COS:{} Throttle Percent:{}'.format(request_socket,core,stress_cos,cos,throttlepercent))
                    #run stresstool
                    stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
                    stresstool.setDaemon(True)
                    stresstool.start()
                    time.sleep(2)
                    #Reset to default MBA setting 
                    pqos.reset()
                    pqos.bindllc(stress_cos, core)
                    pqos.bindmba(stress_cos, request_socket, throttlepercent)
                    pqos.refresh()
                    mbl_,mbr_,errorflag1 = pqos.getmbm(core)
                    APP_LOG.info('MBL value before change:{}'.format(mbl_))
                    mbl0.append(mbl_)
                    #Random select timewindow MBAdelay
                    tw = random.sample(timewindow, 1)[0]
                    delay = random.sample(MBAdelay, 1)[0]
                    svstart.change_timewindow(request_socket, cos, tw)
                    svstart.change_mbadelay(request_socket, cos, delay)
                    # svstart.change_leakybucketsize(request_socket, lbsize)
                    time.sleep(2)
                    pqos.refresh()
                    mbl_,mbr_,errorflag2 = pqos.getmbm(core)
                    APP_LOG.info('MBL value after change:{}'.format(mbl_))
                    mbl1.append(mbl_)
                    if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                        APP_LOG.info('Find error in test, early terminate!')
                        APP_LOG.info('[warning]Please reboot system, then retest this case!')
                        sys.exit(1)
                    if  mbl0[k]*0.1 > abs(mbl0[k] - mbl1[k]):
                        APP_LOG.info('[test result]>>No throttling, mbl {} change to {}, test success!'.format(mbl0[k],mbl1[k]))
                        successcount+=1
                        file.write(str(mbl0[-1])+'\t'+str(mbl1[-1])+'\t'+str(round(100*(mbl0[-1]-mbl1[-1])/mbl0[-1],2))+'%\t'+'pass'+'\n')
                    else:
                        APP_LOG.info('[test result]>>Throttling, mbl {} change to {}, test fail!'.format(mbl0[k],mbl1[k]))
                        failcount+=1
                        file.write(str(mbl0[-1])+'\t'+str(mbl1[-1])+'\t'+str(round(100*(mbl0[-1]-mbl1[-1])/mbl0[-1],2))+'%\t'+'fail'+'\n')
                    
                    k+=1
                    stresstool.stop()
                    
                    
    if args.patten == 'random':
        #get default timewindow and MBAdelay
        default_timewindow = svstart.get_timewindow(request_socket, cos)
        default_mbadelay = svstart.get_mbadelay(request_socket, cos)
        #set timewindow and MBAdelay list
        timewindow = [x for x in range(default_timewindow,80)]
        MBAdelay = [x for x in range(default_mbadelay,80)]
        for k in range(args.iteration):
            #Generate cos
            chose_cos = random.sample(coslist, 2)
            stress_cos = chose_cos[0]
            cos = chose_cos[1]
            while cos==0:
                chose_cos = random.sample(coslist, 2)
                stress_cos = chose_cos[0]
                cos = chose_cos[1]
            #print info
            APP_LOG.info('-'*50)
            APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:random, test tool:{} {}'.format(k, args.iteration,toolname,traffic))
            APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} Stress COS:{} Applied COS:{}'.format(request_socket,core,stress_cos,cos))
            #run stresstool
            stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
            stresstool.setDaemon(True)
            stresstool.start()
            time.sleep(2)
            #Reset to default MBA setting 
            pqos.reset()
            pqos.bindllc(stress_cos, core)
            pqos.bindmba(stress_cos, request_socket, throttlepercent)
            #Random select timewindow MBAdelay 
            tw = random.sample(timewindow, 1)[0]
            delay = random.sample(MBAdelay, 1)[0]
            # lbsize = random.sample(LeakyBucketSize, 1)[0]
            pqos.refresh()
            mbl_,mbr_,errorflag1 = pqos.getmbm(core)
            APP_LOG.info('MBL value before change:{}'.format(mbl_))
            mbl0.append(mbl_)
            svstart.change_timewindow(request_socket, cos, tw)
            svstart.change_mbadelay(request_socket, cos, delay)
            # svstart.change_leakybucketsize(request_socket, lbsize)
            time.sleep(2)
            pqos.refresh()
            mbl_,mbr_,errorflag2 = pqos.getmbm(core)
            APP_LOG.info('MBL value after change:{}'.format(mbl_))
            mbl1.append(mbl_)
            if  mbl0[k]*0.05 > abs(mbl0[k] - mbl1[k]):
                APP_LOG.info('[test result]>>No throttling, mbl {} change to {}, test success!'.format(mbl0[k],mbl1[k]))
                successcount+=1
            else:
                APP_LOG.info('[test result]>>Throttling, mbl {} change to {}, test fail!'.format(mbl0[k],mbl1[k]))
                failcount+=1
            stresstool.stop()
            if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                APP_LOG.info('Find error in test, early terminate!')
                APP_LOG.info('[warning]Please reboot system, then retest this case!')
                sys.exit(1)

    elif args.patten == 'traversal':
       #get default timewindow and MBAdelay
        default_timewindow = svstart.get_timewindow(request_socket, cos)
        default_mbadelay = svstart.get_mbadelay(request_socket, cos)
        #set timewindow and MBAdelay list
        timewindow = [x for x in range(default_timewindow,80)]
        MBAdelay = [x for x in range(default_mbadelay,80)]
        for stress_cos in coslist:
            for cos in coslist[1:]:
                if not cos == stress_cos:
                     with open(os.path.join(log_doc,'{}_S'.format(APP_NAME)+str(stress_cos)+'_A'+str(cos)+'_result.log'),'w') as file:
                        file.write('delayvalue\\timewindow\t')
                        for tw in timewindow:
                            file.write(str(tw)+'\t')
                        file.write('\n')
                        k=0
                        mbl0 = []
                        mbl1 = []
                        for delay in MBAdelay:
                            file.write(str(delay)+'\t')
                            for tw in timewindow:
                                # for lbsize in LeakyBucketSize:
                                APP_LOG.info('-'*50)
                                APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:traversal, test tool:{} {}'.format(k+1, len(MBAdelay)*(len(timewindow)),toolname,traffic))
                                APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} Stress COS:{} Applied COS:{}'.format(request_socket,core,stress_cos,cos))
                                #run stresstool
                                stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
                                stresstool.setDaemon(True)
                                stresstool.start()
                                time.sleep(2)
                                #Reset to default MBA setting 
                                pqos.reset()
                                pqos.bindllc(stress_cos, core)
                                pqos.bindmba(stress_cos, request_socket, throttlepercent)
                                pqos.refresh()
                                mbl_,mbr_,errorflag1 = pqos.getmbm(core)
                                APP_LOG.info('MBL value before change:{}'.format(mbl_))
                                mbl0.append(mbl_)
                                svstart.change_timewindow(request_socket, cos, tw)
                                svstart.change_mbadelay(request_socket, cos, delay)
                                # svstart.change_leakybucketsize(request_socket, lbsize)
                                time.sleep(2)
                                pqos.refresh()
                                mbl_,mbr_,errorflag2 = pqos.getmbm(core)
                                APP_LOG.info('MBL value after change:{}'.format(mbl_))
                                mbl1.append(mbl_)
                                if  mbl0[k]*0.05 > abs(mbl0[k] - mbl1[k]):
                                    APP_LOG.info('[test result]>>No throttling, mbl {} change to {}, test success!'.format(mbl0[k],mbl1[k]))
                                    successcount+=1
                                else:
                                    APP_LOG.info('[test result]>>Throttling, mbl {} change to {}, test fail!'.format(mbl0[k],mbl1[k]))
                                    failcount+=1
                                file.write(str(mbl_)+'\t')
                                k+=1
                                stresstool.stop()
                                if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                                    APP_LOG.info('Find error in test, early terminate!')
                                    APP_LOG.info('[warning]Please reboot system, then retest this case!')
                                    sys.exit(1)
                            file.write('\n')
                            
                        
    APP_LOG.info('#'*18+'  Test End  '+'#'*18)
    APP_LOG.info('Total test count:{}'.format(successcount+failcount))
    APP_LOG.info('Test success count:{}'.format(successcount))
    APP_LOG.info('Test fail count:{}'.format(failcount))
    
    
            