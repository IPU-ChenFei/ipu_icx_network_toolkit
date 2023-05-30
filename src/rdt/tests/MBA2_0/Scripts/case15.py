# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 09:59:04 2020

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
APP_NAME = 'case15'
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
                            default='traversal')
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
    APP_LOG.info('='*20+'  '+APP_NAME+'  '+'='*20)
    APP_LOG.info('='*50)
    successcount = 0
    failcount = 0
    maxcos = pqos.max_cos
    maxdelay = None
    cos = random.sample(range(0,pqos.max_cos), 1)[0]
    core = random.sample(range(0,pqos.max_core), 1)[0]
    request_socket = int(2*core/pqos.max_core)
    mbmcount = 3
    mbl0 = []
    mbl1 = []
    throttlepercent = 100
    svstart.build_socket_list(request_socket)
    #get default unthrottle delay
    default_unthrottleddelay = svstart.get_unthrottleddelay(request_socket)
    #set unthrottle delay list
    unthrottleddelay = [x for x in range(2,91)]
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
    benchmarkscale_standard = 0.10
    inflection_standard = 0.10
    if args.patten == 'random':
        for k in range(args.iteration):
            APP_LOG.info('-'*50)
            APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:random, test tool:{} {}'.format(k, args.iteration,toolname,traffic))
            APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} COS:{} '.format(request_socket,core,cos))
            svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
            #run stresstool
            stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
            stresstool.setDaemon(True)
            stresstool.start()
            time.sleep(3)
            #Reset to default MBA setting 
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
            if  mbl0[k] - mbl1[k] > mbl0[k]*0.01:
                APP_LOG.info('[test result]>>Throttling success, mbl {} change to {}'.format(mbl0[k],mbl1[k]))
                successcount+=1
            else:
                APP_LOG.info('[test result]>>Throttling fail, mbl {} change to {}'.format(mbl0[k],mbl1[k]))
                failcount+=1
            stresstool.stop()
            if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                APP_LOG.info('Find error in test, early terminate!')
                APP_LOG.info('[warning]Please reboot system, then retest this case!')
                svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                sys.exit(1)
        svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)

    elif args.patten == 'traversal':
        with open(os.path.join(log_doc,'{}_result.log'.format(APP_NAME)),'w') as file:
            file.write('stresstool:{}, traffic:{}\n'.format(toolname,traffic))
            file.write('unthrottleddelay\t')
            file.write('beforechange\tafterchange\tdelta\tresult\n')
            k=0
            for undelay in unthrottleddelay:
                time.sleep(15)
                
                APP_LOG.info('-'*50)
                APP_LOG.info('[test info]>>Start cycle:{}/{}, parameter mode:traversal, test tool:{} {}'.format(k+1, len(unthrottleddelay),toolname,traffic))
                APP_LOG.info('[pqos info]>>Socket:{} logic Core:{} COS:{} '.format(request_socket,core,cos))
                svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                #run stresstool
                stresstool = StressTools(args.stress_tool_path, toolname=toolname,core=core,cachesize=cachesize,request_socket=request_socket,traffic=traffic)
                stresstool.setDaemon(True)
                stresstool.start()
                time.sleep(3)
                #Reset to default MBA setting 
                pqos.refresh()
                mbl_,mbr_,errorflag1 = pqos.getmbm(core)
                APP_LOG.info('MBL value before change:{}'.format(mbl_))
                mbl0.append(mbl_)
                #get uncore frequency and expect target
                #change unthrottled delay
                svstart.change_unthrottleddelay(request_socket, undelay)
                #change timewindow
                # svstart.change_timewindow(request_socket, cos, undelay)
                time.sleep(3)
                pqos.refresh()
                mbl_,mbr_,errorflag2 = pqos.getmbm(core)
                APP_LOG.info('MBL value after change:{}'.format(mbl_))
                mbl1.append(mbl_)
                inflection = False
                if not inflection and abs(mbl1[k] - mbl0[k]) < mbl0[k]*inflection_standard:
                    APP_LOG.info('[test result]>>Unthrottle delay has not reach the inflection point, difference of before {} and after {} is less than {}%'.format(mbl0[k],mbl1[k],inflection_standard*100))
                else:
                    inflection = True
                if  inflection and (mbl0[k] - mbl1[k]) >= mbl0[k]*benchmarkscale_standard:
                    APP_LOG.info('[test result]>>Throttling success, mbl after change {} has decreased more than {}% of before {}'.format(mbl1[k],benchmarkscale_standard*100,mbl0[k]))
                    successcount+=1
                    file.write(str(undelay)+'\t')
                    file.write(str(mbl0[k])+'\t'+str(mbl1[k])+'\t'+str(round(100*(mbl0[k]-mbl1[k])/mbl0[k],2))+'%\t'+'pass'+'\n')
                elif inflection and (mbl0[k] - mbl1[k]) < mbl0[k]*benchmarkscale_standard:
                    APP_LOG.info('[test result]>>Throttling fail, mbl after change {} has not decreased more than {}% of before {}'.format(mbl1[k],benchmarkscale_standard*100,mbl0[k]))
                    failcount+=1
                    file.write(str(undelay)+'\t')
                    file.write(str(mbl0[k])+'\t'+str(mbl1[k])+'\t'+str(round(100*(mbl0[k]-mbl1[k])/mbl0[k],2))+'%\t'+'fail'+'\n')
                k+=1
                stresstool.stop()
                if errorflag1 in TERMINATE_ERROR or errorflag2 in TERMINATE_ERROR:
                    APP_LOG.info('Find error in test, early terminate!')
                    APP_LOG.info('[warning]Please reboot system, then retest this case!')
                    svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
                    sys.exit(1)
            svstart.change_unthrottleddelay(request_socket, default_unthrottleddelay)
    APP_LOG.info('#'*18+'  Test End  '+'#'*18)
    if successcount + failcount == 0:
        APP_LOG.info('No valid test exist, test fail!')
    else:
        APP_LOG.info('Total test count:{}'.format(successcount+failcount))
        APP_LOG.info('Test success count:{}'.format(successcount))
        APP_LOG.info('Test fail count:{}'.format(failcount))
    
    
       